"""
Schema shifts from DEC-059 / DEC-060 / DEC-061 / DEC-062a.

Safe upgrade path for CaltransRateLine and EquipmentType:
  1. Add the new fields (factors on CaltransRateLine; own rates + flags on
     EquipmentType). All new fields default to 0 / 'none' / True so
     existing rows satisfy non-null constraints at creation.
  2. Relax EquipmentType.caltrans_rate_line FK to nullable.
  3. RunPython: backfill new fields from the old ones for existing rows
     (``factor = old_rate / rental_rate``; EquipmentType rate_reg/rate_ot/
     rate_standby populated from the linked Caltrans row when present).
  4. Remove the old rate fields on CaltransRateLine.

This ordering means a populated database does not lose information —
every rate migrates into the factor model before the old columns go away.
On an empty DB (like current dev) the RunPython is a no-op.
"""

from decimal import Decimal

import django.db.models.deletion
from django.db import migrations, models


CT_MATCH_CHOICES = [
    ('exact', 'Exact'),
    ('close', 'Close'),
    ('none', 'No Match'),
    ('retired', 'CT Code Retired'),
    ('fmv', 'Fair Market Value'),
]


def backfill_factors_and_rates(apps, schema_editor):
    """Populate factor fields on CaltransRateLine; populate own rates on EquipmentType."""
    CaltransRateLine = apps.get_model('resources', 'CaltransRateLine')
    HistoricalCaltransRateLine = apps.get_model('resources', 'HistoricalCaltransRateLine')
    EquipmentType = apps.get_model('resources', 'EquipmentType')
    HistoricalEquipmentType = apps.get_model('resources', 'HistoricalEquipmentType')

    # CaltransRateLine: derive factors from the old rate columns.
    # Old columns are still present at this point in the migration chain.
    for crl in CaltransRateLine.objects.all().only(
        'id', 'rental_rate', 'rw_delay_rate', 'overtime_rate',
    ):
        if crl.rental_rate:
            crl.rw_delay_factor = (crl.rw_delay_rate or Decimal('0')) / crl.rental_rate
            crl.ot_factor = (crl.overtime_rate or Decimal('0')) / crl.rental_rate
        else:
            crl.rw_delay_factor = Decimal('0')
            crl.ot_factor = Decimal('0')
        crl.save(update_fields=['rw_delay_factor', 'ot_factor'])

    # Keep historical rows consistent so django-simple-history comparisons stay sane.
    for h in HistoricalCaltransRateLine.objects.all().only(
        'history_id', 'rental_rate', 'rw_delay_rate', 'overtime_rate',
    ):
        if h.rental_rate:
            h.rw_delay_factor = (h.rw_delay_rate or Decimal('0')) / h.rental_rate
            h.ot_factor = (h.overtime_rate or Decimal('0')) / h.rental_rate
        else:
            h.rw_delay_factor = Decimal('0')
            h.ot_factor = Decimal('0')
        h.save(update_fields=['rw_delay_factor', 'ot_factor'])

    # EquipmentType: when a CaltransRateLine is linked, copy rental and compute
    # OT/standby from the now-backfilled factors. When unlinked (new nullable FK)
    # the defaults of 0 stand until an admin fills them in.
    for et in EquipmentType.objects.select_related('caltrans_rate_line').all():
        crl = et.caltrans_rate_line
        if crl is None:
            continue
        et.rate_reg = crl.rental_rate or Decimal('0')
        et.rate_ot = (crl.rental_rate or Decimal('0')) * (crl.ot_factor or Decimal('0'))
        et.rate_standby = (crl.rental_rate or Decimal('0')) * (crl.rw_delay_factor or Decimal('0'))
        et.save(update_fields=['rate_reg', 'rate_ot', 'rate_standby'])

    # Likewise for history rows.
    for h in HistoricalEquipmentType.objects.all():
        if h.caltrans_rate_line_id is None:
            continue
        try:
            crl = CaltransRateLine.objects.get(pk=h.caltrans_rate_line_id)
        except CaltransRateLine.DoesNotExist:
            continue
        h.rate_reg = crl.rental_rate or Decimal('0')
        h.rate_ot = (crl.rental_rate or Decimal('0')) * (crl.ot_factor or Decimal('0'))
        h.rate_standby = (crl.rental_rate or Decimal('0')) * (crl.rw_delay_factor or Decimal('0'))
        h.save(update_fields=['rate_reg', 'rate_ot', 'rate_standby'])


def reverse_backfill(apps, schema_editor):
    """Reconstitute old rate columns from factors × rental so this migration is reversible."""
    CaltransRateLine = apps.get_model('resources', 'CaltransRateLine')
    HistoricalCaltransRateLine = apps.get_model('resources', 'HistoricalCaltransRateLine')

    for crl in CaltransRateLine.objects.all():
        rental = crl.rental_rate or Decimal('0')
        crl.rw_delay_rate = rental * (crl.rw_delay_factor or Decimal('0'))
        crl.overtime_rate = rental * (crl.ot_factor or Decimal('0'))
        crl.save(update_fields=['rw_delay_rate', 'overtime_rate'])

    for h in HistoricalCaltransRateLine.objects.all():
        rental = h.rental_rate or Decimal('0')
        h.rw_delay_rate = rental * (h.rw_delay_factor or Decimal('0'))
        h.overtime_rate = rental * (h.ot_factor or Decimal('0'))
        h.save(update_fields=['rw_delay_rate', 'overtime_rate'])


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0001_initial'),
    ]

    operations = [
        # Step 1: Add the new factor fields on CaltransRateLine. Default 0 so
        # rows already in the table satisfy the non-null constraint.
        migrations.AddField(
            model_name='caltransrateline',
            name='rw_delay_factor',
            field=models.DecimalField(decimal_places=4, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name='caltransrateline',
            name='ot_factor',
            field=models.DecimalField(decimal_places=4, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name='historicalcaltransrateline',
            name='rw_delay_factor',
            field=models.DecimalField(decimal_places=4, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name='historicalcaltransrateline',
            name='ot_factor',
            field=models.DecimalField(decimal_places=4, default=0, max_digits=5),
        ),

        # Step 2: Add the new EquipmentType fields. rate_reg / rate_ot /
        # rate_standby default to 0 (safe sentinel that surfaces ingest
        # misconfiguration rather than silently producing wrong totals).
        migrations.AddField(
            model_name='equipmenttype',
            name='rate_reg',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Operating rate ($/hr).', max_digits=8),
        ),
        migrations.AddField(
            model_name='equipmenttype',
            name='rate_ot',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Overtime rate ($/hr).', max_digits=8),
        ),
        migrations.AddField(
            model_name='equipmenttype',
            name='rate_standby',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Standby (RW delay) rate ($/hr).', max_digits=8),
        ),
        migrations.AddField(
            model_name='equipmenttype',
            name='ct_match_quality',
            field=models.CharField(choices=CT_MATCH_CHOICES, default='none', help_text='Provenance of the rates — documents defensibility in claims.', max_length=10),
        ),
        migrations.AddField(
            model_name='equipmenttype',
            name='fuel_surcharge_eligible',
            field=models.BooleanField(default=True, help_text='Whether this equipment type participates in the fuel surcharge pool.'),
        ),
        migrations.AddField(
            model_name='historicalequipmenttype',
            name='rate_reg',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Operating rate ($/hr).', max_digits=8),
        ),
        migrations.AddField(
            model_name='historicalequipmenttype',
            name='rate_ot',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Overtime rate ($/hr).', max_digits=8),
        ),
        migrations.AddField(
            model_name='historicalequipmenttype',
            name='rate_standby',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Standby (RW delay) rate ($/hr).', max_digits=8),
        ),
        migrations.AddField(
            model_name='historicalequipmenttype',
            name='ct_match_quality',
            field=models.CharField(choices=CT_MATCH_CHOICES, default='none', help_text='Provenance of the rates — documents defensibility in claims.', max_length=10),
        ),
        migrations.AddField(
            model_name='historicalequipmenttype',
            name='fuel_surcharge_eligible',
            field=models.BooleanField(default=True, help_text='Whether this equipment type participates in the fuel surcharge pool.'),
        ),

        # Step 3: Relax the CT FK to nullable (DEC-060 — ~28% of fleet has no CT match).
        migrations.AlterField(
            model_name='equipmenttype',
            name='caltrans_rate_line',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='equipment_types',
                to='resources.caltransrateline',
            ),
        ),

        # Step 4: Backfill new columns from old data before the old columns are dropped.
        migrations.RunPython(backfill_factors_and_rates, reverse_backfill),

        # Step 5: Drop the old rate columns on CaltransRateLine.
        migrations.RemoveField(model_name='caltransrateline', name='rw_delay_rate'),
        migrations.RemoveField(model_name='caltransrateline', name='overtime_rate'),
        migrations.RemoveField(model_name='historicalcaltransrateline', name='rw_delay_rate'),
        migrations.RemoveField(model_name='historicalcaltransrateline', name='overtime_rate'),
    ]
