from django.db import models
from simple_history.models import HistoricalRecords


class TradeClassification(models.Model):
    """
    A union trade classification — the permanent reference for labor billing.
    Rate history is stored in LaborRate, not here.
    """
    name = models.CharField(max_length=100, unique=True)
    union_name = models.CharField(max_length=100)
    union_abbrev = models.CharField(max_length=20)  # IUOE, LIUNA, OPCMIA, IBT
    active = models.BooleanField(default=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['union_abbrev', 'name']
        verbose_name = 'Trade Classification'
        verbose_name_plural = 'Trade Classifications'

    def __str__(self):
        return f'{self.name} ({self.union_abbrev})'


class LaborRate(models.Model):
    """
    Versioned CBA rate for a trade classification.
    Add a new row per negotiation cycle — never edit old rows.
    The latest row with effective_date <= work_date is the active rate.
    """
    trade_classification = models.ForeignKey(
        TradeClassification, on_delete=models.PROTECT, related_name='rates'
    )
    rate_reg = models.DecimalField(max_digits=8, decimal_places=2)
    rate_ot = models.DecimalField(max_digits=8, decimal_places=2)
    rate_dt = models.DecimalField(max_digits=8, decimal_places=2)
    effective_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    notes = models.CharField(max_length=200, blank=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['trade_classification', '-effective_date']
        verbose_name = 'Labor Rate'
        verbose_name_plural = 'Labor Rates'

    def __str__(self):
        return f'{self.trade_classification} — eff. {self.effective_date}'


class Employee(models.Model):
    """
    A field employee. Separate from application users (DEC-012, DEC-029).
    One-time CSV seed, then CRUD only.
    """
    code = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=100)
    trade_classification = models.ForeignKey(
        TradeClassification, on_delete=models.PROTECT, related_name='employees'
    )
    active = models.BooleanField(default=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['full_name']
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'

    def __str__(self):
        return f'{self.full_name} ({self.code})'


class CaltransSchedule(models.Model):
    """
    One row per annual Caltrans equipment rental rate schedule publication.
    """
    schedule_year = models.CharField(max_length=20)  # e.g. "2025-2026"
    effective_date = models.DateField()
    expiry_date = models.DateField()
    source_file = models.CharField(max_length=200, blank=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['-effective_date']
        verbose_name = 'Caltrans Schedule'
        verbose_name_plural = 'Caltrans Schedules'

    def __str__(self):
        return f'Caltrans {self.schedule_year} (eff. {self.effective_date})'


class CaltransRateLine(models.Model):
    """
    One row per equipment record in the Caltrans rental rate schedule.
    Natural key: (schedule, class_code, make_code, model_code).
    Annual re-import upserts by natural key — old rows are never deleted
    so existing EWO snapshots remain intact.
    """
    schedule = models.ForeignKey(
        CaltransSchedule, on_delete=models.PROTECT, related_name='rate_lines'
    )
    class_code = models.CharField(max_length=20)
    class_desc = models.CharField(max_length=200)
    make_code = models.CharField(max_length=20)
    make_desc = models.CharField(max_length=200)
    model_code = models.CharField(max_length=50)
    model_desc = models.CharField(max_length=200)
    # Three billable rate components per DEC-021
    rental_rate = models.DecimalField(max_digits=8, decimal_places=2)    # operating
    rw_delay_rate = models.DecimalField(max_digits=8, decimal_places=2)  # standby
    overtime_rate = models.DecimalField(max_digits=8, decimal_places=2)  # OT adder
    unit = models.CharField(max_length=10)  # HR or DAY

    history = HistoricalRecords()

    class Meta:
        ordering = ['class_code', 'make_code', 'model_code']
        constraints = [
            models.UniqueConstraint(
                fields=['schedule', 'class_code', 'make_code', 'model_code'],
                name='unique_caltrans_rate_line',
            )
        ]
        verbose_name = 'Caltrans Rate Line'
        verbose_name_plural = 'Caltrans Rate Lines'

    def __str__(self):
        return f'{self.class_code} / {self.make_code} / {self.model_code} ({self.schedule.schedule_year})'


class EquipmentType(models.Model):
    """
    A category of equipment mapped to a Caltrans rate line.
    Shared across all individual units of that type.
    EWO lines reference EquipmentType — not individual units.
    """
    name = models.CharField(max_length=200)
    caltrans_rate_line = models.ForeignKey(
        CaltransRateLine, on_delete=models.PROTECT, related_name='equipment_types'
    )
    notes = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['name']
        verbose_name = 'Equipment Type'
        verbose_name_plural = 'Equipment Types'

    def __str__(self):
        return self.name


class EquipmentUnit(models.Model):
    """
    An individual unit in CP's fleet.
    Ownership flag is informational only — all equipment on an EquipmentLine
    bills at Caltrans published rate regardless of ownership source (DEC-021).
    Rented/outside equipment where CP receives an invoice goes to MaterialLine.
    """
    OWNED = 'owned'
    RENTED = 'rented'
    OUTSIDE = 'outside'

    OWNERSHIP_CHOICES = [
        (OWNED, 'CP Owned'),
        (RENTED, 'Rented'),
        (OUTSIDE, 'Outside / Subcontractor'),
    ]

    equipment_type = models.ForeignKey(
        EquipmentType, on_delete=models.PROTECT, related_name='units'
    )
    internal_code = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=200)
    ownership = models.CharField(max_length=10, choices=OWNERSHIP_CHOICES, default=OWNED)
    active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['internal_code']
        verbose_name = 'Equipment Unit'
        verbose_name_plural = 'Equipment Units'

    def __str__(self):
        return f'{self.internal_code} — {self.description}'


class MaterialCategory(models.Model):
    """
    Category for grouping MaterialCatalog entries.
    """
    name = models.CharField(max_length=100, unique=True)
    active = models.BooleanField(default=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['name']
        verbose_name = 'Material Category'
        verbose_name_plural = 'Material Categories'

    def __str__(self):
        return self.name


class MaterialCatalog(models.Model):
    """
    Company-wide material price book. Grows organically from field entries
    and is maintained by office staff. Not per-job.
    is_boilerplate distinguishes pre-seeded items from field-generated ones.
    """
    category = models.ForeignKey(
        MaterialCategory, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='items'
    )
    description = models.CharField(max_length=200, unique=True)
    default_unit = models.CharField(max_length=50)
    last_unit_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    last_cost_date = models.DateField(null=True, blank=True)
    use_count = models.PositiveIntegerField(default=0)
    last_used = models.DateField(null=True, blank=True)
    is_boilerplate = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['-use_count', 'description']
        verbose_name = 'Material Catalog Item'
        verbose_name_plural = 'Material Catalog'

    def __str__(self):
        return self.description
