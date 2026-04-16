"""
Phase 2 of the EWO build: introduces the ``WorkDay`` child model, re-parents
labor / equipment / material lines from EWO to WorkDay, changes the equipment
line shape to qty + per-unit reg/ot/standby hours, and adds fuel surcharge
fields to the EWO (DEC-062, DEC-064, DEC-065, DEC-066).

Safe-ordering approach:
  1. Add new fields / models / relations (all nullable where needed to coexist
     with the old columns).
  2. RunPython: for each existing ExtraWorkOrder, create a WorkDay keyed to
     the EWO's legacy ``work_date``; move all lines under it; translate
     EquipmentLine (usage_type + hours) → (qty=1, reg_hours / ot_hours /
     standby_hours) by usage_type.
  3. Tighten FK non-null, remove the old ``ewo`` FK on lines, drop the old
     EquipmentLine fields and ExtraWorkOrder.work_date.

The dev database currently has zero EWO rows so the RunPython is a no-op
here, but the defensive ordering preserves any populated deploy.
"""

from decimal import Decimal

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models

import ewo.models  # for the _validate_half_hour validator reference


_MARKUP_VALIDATORS = [
    django.core.validators.MinValueValidator(Decimal('0')),
    django.core.validators.MaxValueValidator(Decimal('1')),
]


def forward_reparent(apps, schema_editor):
    """
    Create a WorkDay per legacy EWO.work_date; move all lines under it.
    Uses ``.save()`` (not ``.update()``) so django-simple-history records each
    transition — audit trails win over perf here. ``.iterator()`` streams rows
    to keep memory bounded on larger deploys.
    """
    ExtraWorkOrder = apps.get_model('ewo', 'ExtraWorkOrder')
    WorkDay = apps.get_model('ewo', 'WorkDay')
    LaborLine = apps.get_model('ewo', 'LaborLine')
    EquipmentLine = apps.get_model('ewo', 'EquipmentLine')
    MaterialLine = apps.get_model('ewo', 'MaterialLine')

    # Legacy usage_type values on EquipmentLine (historic choices).
    OPERATING = 'operating'
    STANDBY = 'standby'
    OVERTIME = 'overtime'

    for ewo in ExtraWorkOrder.objects.iterator():
        wd = WorkDay.objects.create(ewo=ewo, work_date=ewo.work_date)

        for line in LaborLine.objects.filter(ewo=ewo).iterator():
            line.work_day = wd
            line.save(update_fields=['work_day'])

        for line in EquipmentLine.objects.filter(ewo=ewo).iterator():
            line.work_day = wd
            line.qty = 1
            hours = line.hours or Decimal('0.0')
            if line.usage_type == OPERATING:
                line.reg_hours = hours
            elif line.usage_type == OVERTIME:
                line.ot_hours = hours
            elif line.usage_type == STANDBY:
                line.standby_hours = hours
            line.save(update_fields=['work_day', 'qty', 'reg_hours', 'ot_hours', 'standby_hours'])

        for line in MaterialLine.objects.filter(ewo=ewo).iterator():
            line.work_day = wd
            line.save(update_fields=['work_day'])


def reverse_reparent(apps, schema_editor):
    """
    Best-effort reverse of ``forward_reparent``. Several transforms are
    inherently lossy and cannot round-trip cleanly:

    * ``EquipmentLine.qty`` > 1 loses information — old schema had no qty.
    * Per-unit reg/ot/standby hour buckets collapse into a single ``hours``
      value + chosen ``usage_type``. Precedence: standby > overtime > regular
      (matches ``forward_reparent``'s choice semantics).
    * ``WorkDay.work_date`` is used to restore ``ExtraWorkOrder.work_date``
      (first WorkDay by date per EWO); multi-day EWOs collapse to their
      earliest date and the extra days are dropped along with their WorkDay.

    In practice this reverse path only runs locally for rollback testing —
    real deploys should not reverse once WorkDays carry meaningful data.
    """
    ExtraWorkOrder = apps.get_model('ewo', 'ExtraWorkOrder')
    WorkDay = apps.get_model('ewo', 'WorkDay')
    LaborLine = apps.get_model('ewo', 'LaborLine')
    EquipmentLine = apps.get_model('ewo', 'EquipmentLine')
    MaterialLine = apps.get_model('ewo', 'MaterialLine')

    for line in LaborLine.objects.iterator():
        line.ewo_id = line.work_day.ewo_id
        line.save(update_fields=['ewo'])

    for line in EquipmentLine.objects.iterator():
        line.ewo_id = line.work_day.ewo_id
        if line.standby_hours and line.standby_hours > 0:
            line.usage_type = 'standby'
            line.hours = line.standby_hours
        elif line.ot_hours and line.ot_hours > 0:
            line.usage_type = 'overtime'
            line.hours = line.ot_hours
        else:
            line.usage_type = 'operating'
            line.hours = line.reg_hours
        line.save(update_fields=['ewo', 'usage_type', 'hours'])

    for line in MaterialLine.objects.iterator():
        line.ewo_id = line.work_day.ewo_id
        line.save(update_fields=['ewo'])

    # Restore ExtraWorkOrder.work_date from the earliest WorkDay for each EWO.
    for ewo in ExtraWorkOrder.objects.iterator():
        earliest = (
            WorkDay.objects.filter(ewo=ewo)
            .order_by('work_date')
            .values_list('work_date', flat=True)
            .first()
        )
        if earliest is not None:
            ewo.work_date = earliest
            ewo.save(update_fields=['work_date'])

    WorkDay.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('ewo', '0001_initial'),
        ('jobs', '0002_job_ohp_bond_cp_role'),
        ('resources', '0003_alter_caltransrateline_ot_factor_and_more'),
    ]

    operations = [
        # ─── Step 1: add EWO fuel-surcharge fields + fuel_subtotal ──────────
        migrations.AddField(
            model_name='extraworkorder',
            name='fuel_surcharge_pct',
            field=models.DecimalField(
                decimal_places=4, default=Decimal('0.0000'), max_digits=5,
                validators=_MARKUP_VALIDATORS,
                verbose_name='Fuel Surcharge %',
            ),
        ),
        migrations.AddField(
            model_name='extraworkorder',
            name='fuel_subtotal',
            field=models.DecimalField(
                decimal_places=2, max_digits=12, null=True, blank=True,
            ),
        ),
        migrations.AddField(
            model_name='historicalextraworkorder',
            name='fuel_surcharge_pct',
            field=models.DecimalField(
                decimal_places=4, default=Decimal('0.0000'), max_digits=5,
                validators=_MARKUP_VALIDATORS,
                verbose_name='Fuel Surcharge %',
            ),
        ),
        migrations.AddField(
            model_name='historicalextraworkorder',
            name='fuel_subtotal',
            field=models.DecimalField(
                decimal_places=2, max_digits=12, null=True, blank=True,
            ),
        ),

        # ─── Step 2: align bond_pct default with Job-level default (0.0150) ─
        migrations.AlterField(
            model_name='extraworkorder',
            name='bond_pct',
            field=models.DecimalField(
                decimal_places=4, default=Decimal('0.0150'), max_digits=5,
                validators=_MARKUP_VALIDATORS,
                verbose_name='Bond %',
            ),
        ),
        migrations.AlterField(
            model_name='historicalextraworkorder',
            name='bond_pct',
            field=models.DecimalField(
                decimal_places=4, default=Decimal('0.0150'), max_digits=5,
                validators=_MARKUP_VALIDATORS,
                verbose_name='Bond %',
            ),
        ),

        # ─── Step 3: create WorkDay model ───────────────────────────────────
        migrations.CreateModel(
            name='WorkDay',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('work_date', models.DateField()),
                ('location', models.CharField(blank=True, max_length=200)),
                ('weather', models.CharField(blank=True, max_length=100)),
                ('description', models.TextField(blank=True)),
                ('foreman_name', models.CharField(blank=True, max_length=100)),
                ('superintendent_name', models.CharField(blank=True, max_length=100)),
                ('labor_subtotal', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('equip_subtotal', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('material_subtotal', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('fuel_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('labor_ohp_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('equip_mat_ohp_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('bond_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('day_total', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('ewo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='work_days', to='ewo.extraworkorder')),
            ],
            options={
                'verbose_name': 'Work Day',
                'verbose_name_plural': 'Work Days',
                'ordering': ['ewo', 'work_date'],
            },
        ),
        migrations.AddConstraint(
            model_name='workday',
            constraint=models.UniqueConstraint(
                fields=('ewo', 'work_date'), name='unique_workday_per_ewo_date'
            ),
        ),

        # HistoricalWorkDay — django-simple-history shadow
        migrations.CreateModel(
            name='HistoricalWorkDay',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('work_date', models.DateField()),
                ('location', models.CharField(blank=True, max_length=200)),
                ('weather', models.CharField(blank=True, max_length=100)),
                ('description', models.TextField(blank=True)),
                ('foreman_name', models.CharField(blank=True, max_length=100)),
                ('superintendent_name', models.CharField(blank=True, max_length=100)),
                ('labor_subtotal', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('equip_subtotal', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('material_subtotal', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('fuel_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('labor_ohp_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('equip_mat_ohp_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('bond_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('day_total', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('ewo', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='ewo.extraworkorder')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='auth.user')),
            ],
            options={
                'verbose_name': 'historical Work Day',
                'verbose_name_plural': 'historical Work Days',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(models.Model,),
        ),

        # ─── Step 4: add work_day FK to each line (nullable for now) ────────
        migrations.AddField(
            model_name='laborline',
            name='work_day',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='labor_lines', to='ewo.workday',
            ),
        ),
        migrations.AddField(
            model_name='equipmentline',
            name='work_day',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='equipment_lines', to='ewo.workday',
            ),
        ),
        migrations.AddField(
            model_name='materialline',
            name='work_day',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='material_lines', to='ewo.workday',
            ),
        ),
        migrations.AddField(
            model_name='historicallaborline',
            name='work_day',
            field=models.ForeignKey(
                blank=True, db_constraint=False, null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name='+', to='ewo.workday',
            ),
        ),
        migrations.AddField(
            model_name='historicalequipmentline',
            name='work_day',
            field=models.ForeignKey(
                blank=True, db_constraint=False, null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name='+', to='ewo.workday',
            ),
        ),
        migrations.AddField(
            model_name='historicalmaterialline',
            name='work_day',
            field=models.ForeignKey(
                blank=True, db_constraint=False, null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name='+', to='ewo.workday',
            ),
        ),

        # ─── Step 5: add new EquipmentLine fields (qty + hour buckets) ──────
        migrations.AddField(
            model_name='equipmentline',
            name='qty',
            field=models.PositiveSmallIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='equipmentline',
            name='reg_hours',
            field=models.DecimalField(
                decimal_places=1, default=Decimal('0.0'), max_digits=5,
                validators=[ewo.models._validate_half_hour],
            ),
        ),
        migrations.AddField(
            model_name='equipmentline',
            name='ot_hours',
            field=models.DecimalField(
                decimal_places=1, default=Decimal('0.0'), max_digits=5,
                validators=[ewo.models._validate_half_hour],
            ),
        ),
        migrations.AddField(
            model_name='equipmentline',
            name='standby_hours',
            field=models.DecimalField(
                decimal_places=1, default=Decimal('0.0'), max_digits=5,
                validators=[ewo.models._validate_half_hour],
            ),
        ),
        migrations.AddField(
            model_name='historicalequipmentline',
            name='qty',
            field=models.PositiveSmallIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='historicalequipmentline',
            name='reg_hours',
            field=models.DecimalField(
                decimal_places=1, default=Decimal('0.0'), max_digits=5,
                validators=[ewo.models._validate_half_hour],
            ),
        ),
        migrations.AddField(
            model_name='historicalequipmentline',
            name='ot_hours',
            field=models.DecimalField(
                decimal_places=1, default=Decimal('0.0'), max_digits=5,
                validators=[ewo.models._validate_half_hour],
            ),
        ),
        migrations.AddField(
            model_name='historicalequipmentline',
            name='standby_hours',
            field=models.DecimalField(
                decimal_places=1, default=Decimal('0.0'), max_digits=5,
                validators=[ewo.models._validate_half_hour],
            ),
        ),

        # ─── Step 6: data migration ─────────────────────────────────────────
        migrations.RunPython(forward_reparent, reverse_reparent),

        # ─── Step 7: tighten work_day FK to non-null ────────────────────────
        migrations.AlterField(
            model_name='laborline',
            name='work_day',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='labor_lines', to='ewo.workday',
            ),
        ),
        migrations.AlterField(
            model_name='equipmentline',
            name='work_day',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='equipment_lines', to='ewo.workday',
            ),
        ),
        migrations.AlterField(
            model_name='materialline',
            name='work_day',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='material_lines', to='ewo.workday',
            ),
        ),

        # ─── Step 8: drop old ewo FK from lines ─────────────────────────────
        migrations.RemoveField(model_name='laborline', name='ewo'),
        migrations.RemoveField(model_name='equipmentline', name='ewo'),
        migrations.RemoveField(model_name='materialline', name='ewo'),
        migrations.RemoveField(model_name='historicallaborline', name='ewo'),
        migrations.RemoveField(model_name='historicalequipmentline', name='ewo'),
        migrations.RemoveField(model_name='historicalmaterialline', name='ewo'),

        # ─── Step 9: drop legacy EquipmentLine fields ───────────────────────
        migrations.RemoveField(model_name='equipmentline', name='usage_type'),
        migrations.RemoveField(model_name='equipmentline', name='hours'),
        migrations.RemoveField(model_name='equipmentline', name='unit'),
        migrations.RemoveField(model_name='historicalequipmentline', name='usage_type'),
        migrations.RemoveField(model_name='historicalequipmentline', name='hours'),
        migrations.RemoveField(model_name='historicalequipmentline', name='unit'),

        # ─── Step 10: drop ExtraWorkOrder.work_date (now on WorkDay) ────────
        migrations.RemoveField(model_name='extraworkorder', name='work_date'),
        migrations.RemoveField(model_name='historicalextraworkorder', name='work_date'),

        # ─── Step 11: update EWO ordering (work_date is gone) ───────────────
        migrations.AlterModelOptions(
            name='extraworkorder',
            options={
                'ordering': ['-ewo_sequence', 'ewo_number'],
                'verbose_name': 'Extra Work Order',
                'verbose_name_plural': 'Extra Work Orders',
            },
        ),
    ]
