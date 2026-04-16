from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from simple_history.models import HistoricalRecords

from jobs.models import Job
from resources.models import (
    CaltransRateLine,
    Employee,
    EquipmentType,
    MaterialCatalog,
    TradeClassification,
)


def _validate_half_hour(value):
    """Hours must be in half-hour increments per DEC-020."""
    if value < 0:
        raise ValidationError('Hours cannot be negative.')
    # Multiply by 2 and check it is a whole number
    if (value * 2) % 1 != 0:
        raise ValidationError('Hours must be in half-hour increments (0.5, 1.0, 1.5, …).')


_MARKUP_VALIDATORS = [MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('1'))]


class ExtraWorkOrder(models.Model):
    """
    The core EWO record — one event that may span multiple workdays (DEC-065).

    Lifecycle: open → submitted → approved → sent → billed.
    Rejected EWOs revert to open. Post-approval changes create a new revision
    linked via parent_ewo (DEC-016, DEC-027).

    Labor / equipment / material lines live on WorkDay children, not on the
    EWO directly. Daily math (OH&P, fuel, bond) is computed per WorkDay using
    the EWO-level percentages; the EWO's rolled-up totals are the sum across
    WorkDays (DEC-064).

    Markup percentages are snapshotted from Job at EWO creation (DEC-063).
    Fuel surcharge is situational — entered per-EWO (or seeded from the most
    recent EWO on the same Job) to reflect bid-time vs. current prices (DEC-062).
    """

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        SUBMITTED = 'submitted', 'Submitted'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        SENT = 'sent', 'Sent to GC'
        BILLED = 'billed', 'Billed'

    class EwoType(models.TextChoices):
        TM = 'tm', 'Time & Materials'
        CHANGE_ORDER = 'change_order', 'Change Order / Quote'

    class GcAckMethod(models.TextChoices):
        SIGNATURE = 'signature', 'Signature'
        EMAIL = 'email', 'Email'
        VERBAL = 'verbal', 'Verbal'

    # Core references
    job = models.ForeignKey(Job, on_delete=models.PROTECT, related_name='ewos')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='ewos_created')

    # Numbering — populated on first save via _assign_ewo_number() (DEC-018, DEC-067)
    ewo_number = models.CharField(max_length=30, unique=True, editable=False)
    ewo_sequence = models.PositiveIntegerField(default=0, editable=False)

    # Revision model (DEC-027): revision=0 is original; >0 is a revision
    parent_ewo = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.PROTECT, related_name='revisions'
    )
    revision = models.PositiveSmallIntegerField(default=0)

    ewo_type = models.CharField(max_length=20, choices=EwoType.choices)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)

    # GC acknowledgment — absence is itself a meaningful state (CHARTER)
    gc_ack_name = models.CharField(max_length=100, blank=True)
    gc_ack_date = models.DateField(null=True, blank=True)
    gc_ack_method = models.CharField(
        max_length=20, choices=GcAckMethod.choices, blank=True
    )

    # Optional cross-reference fields (DEC-018)
    rfi_reference = models.CharField(max_length=50, blank=True)
    addendum_ref = models.CharField(max_length=50, blank=True)
    plan_revision = models.CharField(max_length=50, blank=True)

    # Markup percentages — snapshotted from Job at EWO creation (DEC-063).
    # Stored on EWO (not WorkDay) so a multi-day EWO bills at a consistent rate;
    # day-level dollar amounts on WorkDay are computed from these.
    labor_ohp_pct = models.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal('0.1500'),
        validators=_MARKUP_VALIDATORS,
        verbose_name='Labor OH&P %',
    )
    equip_mat_ohp_pct = models.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal('0.1500'),
        validators=_MARKUP_VALIDATORS,
        verbose_name='Equipment & Materials OH&P %',
    )
    bond_pct = models.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal('0.0150'),
        validators=_MARKUP_VALIDATORS,
        verbose_name='Bond %',
    )
    bond_required = models.BooleanField(default=False)

    # Fuel surcharge % applied to fuel-eligible equipment line subtotals on
    # each WorkDay (DEC-062). Situational — default 0; seed from the most
    # recent EWO on this Job at the service layer.
    fuel_surcharge_pct = models.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal('0.0000'),
        validators=_MARKUP_VALIDATORS,
        verbose_name='Fuel Surcharge %',
    )

    # Computed totals — null until submission; sum of WorkDay fields (DEC-064).
    labor_subtotal = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    labor_ohp_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    equip_mat_subtotal = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    equip_mat_ohp_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    fuel_subtotal = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    bond_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    total = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    submitted_at = models.DateTimeField(null=True, blank=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['-ewo_sequence', 'ewo_number']
        verbose_name = 'Extra Work Order'
        verbose_name_plural = 'Extra Work Orders'

    def __str__(self):
        return f'{self.ewo_number} — {self.job}'

    @property
    def is_locked(self):
        """True when the EWO can no longer be edited."""
        return self.status not in (self.Status.OPEN, self.Status.REJECTED)

    def save(self, *args, **kwargs):
        if not self.pk and not self.ewo_number:
            self._assign_ewo_number()
        super().save(*args, **kwargs)

    def _assign_ewo_number(self):
        """
        Atomically assign an EWO number with the DEC-067 format:
        ``EWO-{job_number}-{nnn}`` (job-scoped, zero-padded 3-digit serial).
        Revisions append ``.{revision}``.

        Locks the Job row to prevent concurrent assignment for the same job.
        """
        with transaction.atomic():
            job = Job.objects.select_for_update().get(pk=self.job_id)
            last_seq = (
                ExtraWorkOrder.objects
                .filter(job=job, revision=0)
                .order_by('-ewo_sequence')
                .values_list('ewo_sequence', flat=True)
                .first()
            ) or 0
            self.ewo_sequence = last_seq + 1
            base_number = f'EWO-{job.job_number}-{self.ewo_sequence:03d}'
            if self.revision == 0:
                self.ewo_number = base_number
            else:
                self.ewo_number = f'{self.parent_ewo.ewo_number}.{self.revision}'


class WorkDay(models.Model):
    """
    One day's worth of labor / equipment / materials under an EWO (DEC-065).

    An EWO has 1..N WorkDays. Per-day metadata (foreman, supt, weather,
    location, description) lives here — these are report fields for now;
    FK to a ``Party`` model is deferred (DEC-047 / DEC-070).

    Daily dollar amounts (labor_subtotal, equip_subtotal, material_subtotal,
    fuel_amount, labor_ohp_amount, equip_mat_ohp_amount, bond_amount,
    day_total) are computed on EWO submission using the EWO's percentages
    (DEC-064). Null until then.
    """
    ewo = models.ForeignKey(
        ExtraWorkOrder, on_delete=models.CASCADE, related_name='work_days'
    )
    work_date = models.DateField()

    # Report fields — free-text for now; FK to Party in a later phase
    location = models.CharField(max_length=200, blank=True)
    weather = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    foreman_name = models.CharField(max_length=100, blank=True)
    superintendent_name = models.CharField(max_length=100, blank=True)

    # Computed daily totals — null until EWO submission (DEC-064)
    labor_subtotal = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
    )
    equip_subtotal = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
    )
    material_subtotal = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
    )
    fuel_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
    )
    labor_ohp_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
    )
    equip_mat_ohp_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
    )
    bond_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
    )
    day_total = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
    )

    history = HistoricalRecords()

    class Meta:
        ordering = ['ewo', 'work_date']
        constraints = [
            models.UniqueConstraint(
                fields=['ewo', 'work_date'],
                name='unique_workday_per_ewo_date',
            ),
        ]
        verbose_name = 'Work Day'
        verbose_name_plural = 'Work Days'

    def __str__(self):
        return f'{self.ewo.ewo_number} · {self.work_date}'


class LaborLine(models.Model):
    """
    One line per worker per WorkDay.
    Supports named (specific employee) and generic (placeholder) labor (DEC-029).
    Three time-type hour fields per DEC-025; trade override per DEC-030.
    Rate snapshots are null until EWO submission.
    """

    class LaborType(models.TextChoices):
        NAMED = 'named', 'Named Employee'
        GENERIC = 'generic', 'Generic / Placeholder'

    work_day = models.ForeignKey(
        WorkDay, on_delete=models.CASCADE, related_name='labor_lines'
    )
    labor_type = models.CharField(max_length=10, choices=LaborType.choices)

    # Nullable for generic labor (DEC-029)
    employee = models.ForeignKey(
        Employee, null=True, blank=True,
        on_delete=models.PROTECT, related_name='labor_lines'
    )

    # Snapshotted at line creation from employee.trade_classification (DEC-030)
    employee_default_trade = models.ForeignKey(
        TradeClassification, null=True, blank=True,
        on_delete=models.PROTECT, related_name='+'
    )
    # The trade actually billed — may differ from employee_default_trade
    trade_classification = models.ForeignKey(
        TradeClassification, on_delete=models.PROTECT, related_name='labor_lines'
    )
    trade_override_reason = models.CharField(max_length=200, blank=True)

    # Hours in half-hour increments (DEC-020)
    reg_hours = models.DecimalField(
        max_digits=5, decimal_places=1, default=Decimal('0.0'),
        validators=[_validate_half_hour]
    )
    ot_hours = models.DecimalField(
        max_digits=5, decimal_places=1, default=Decimal('0.0'),
        validators=[_validate_half_hour]
    )
    dt_hours = models.DecimalField(
        max_digits=5, decimal_places=1, default=Decimal('0.0'),
        validators=[_validate_half_hour]
    )

    # Rate snapshots — null until EWO submission (DEC-025, DEC-031)
    rate_reg_snapshot = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    rate_ot_snapshot = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    rate_dt_snapshot = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    line_total = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Labor Line'
        verbose_name_plural = 'Labor Lines'

    def __str__(self):
        name = self.employee.full_name if self.employee else 'Generic'
        return f'{name} / {self.trade_classification} / {self.work_day}'

    @property
    def is_trade_override(self):
        if self.labor_type == self.LaborType.GENERIC:
            return False
        if not self.employee_default_trade_id:
            return False
        return self.employee_default_trade_id != self.trade_classification_id

    def clean(self):
        if self.is_trade_override and not self.trade_override_reason:
            raise ValidationError({
                'trade_override_reason': (
                    'A reason is required when billing under a non-default '
                    'trade classification.'
                )
            })

    def save(self, *args, **kwargs):
        # Auto-snapshot the employee's default trade on named lines (DEC-030)
        if (
            self.labor_type == self.LaborType.NAMED
            and self.employee_id
            and not self.employee_default_trade_id
        ):
            self.employee_default_trade_id = self.employee.trade_classification_id
        super().save(*args, **kwargs)


class EquipmentLine(models.Model):
    """
    One line per equipment type per WorkDay (DEC-066).

    ``qty`` is the number of identical units on this line; hours are
    per-unit. When multiple units worked different hours, enter them as
    multiple lines. All three hour buckets (reg, ot, standby) apply to
    each unit on this line.

    line_total = qty × (reg_hrs × rate_reg + ot_hrs × rate_ot + standby_hrs × rate_standby)

    Rates snapshot EquipmentType's own rates (authoritative under DEC-060);
    ``caltrans_rate_line`` records the provenance FK in effect at snapshot
    time (null when the equipment has no Caltrans match).
    """

    work_day = models.ForeignKey(
        WorkDay, on_delete=models.CASCADE, related_name='equipment_lines'
    )
    equipment_type = models.ForeignKey(
        EquipmentType, on_delete=models.PROTECT, related_name='equipment_lines'
    )
    # Recorded for traceability; which schedule line were rates drawn from.
    caltrans_rate_line = models.ForeignKey(
        CaltransRateLine, null=True, blank=True,
        on_delete=models.PROTECT, related_name='equipment_lines'
    )

    qty = models.PositiveSmallIntegerField(default=1)
    # Per-unit hour buckets (DEC-066). Any equipment may log standby.
    reg_hours = models.DecimalField(
        max_digits=5, decimal_places=1, default=Decimal('0.0'),
        validators=[_validate_half_hour],
    )
    ot_hours = models.DecimalField(
        max_digits=5, decimal_places=1, default=Decimal('0.0'),
        validators=[_validate_half_hour],
    )
    standby_hours = models.DecimalField(
        max_digits=5, decimal_places=1, default=Decimal('0.0'),
        validators=[_validate_half_hour],
    )

    # Rate snapshots — all three components stored regardless of hours logged (DEC-021)
    rental_rate_snapshot = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    rw_delay_rate_snapshot = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    ot_rate_snapshot = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    line_total = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Equipment Line'
        verbose_name_plural = 'Equipment Lines'

    def __str__(self):
        return f'{self.equipment_type} × {self.qty} / {self.work_day}'


class MaterialLine(models.Model):
    """
    One material line per WorkDay. Total is always unit_cost × quantity (DEC-022).
    Lump-sum items use unit='LS', quantity=1 (DEC-022).
    is_subcontractor flags outside equipment invoices and rental invoices
    that land in materials rather than equipment lines.
    """
    work_day = models.ForeignKey(
        WorkDay, on_delete=models.CASCADE, related_name='material_lines'
    )
    # Optional catalog reference; description may be entered fresh without one
    catalog_item = models.ForeignKey(
        MaterialCatalog, null=True, blank=True,
        on_delete=models.PROTECT, related_name='material_lines'
    )
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    unit = models.CharField(max_length=50)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )

    is_subcontractor = models.BooleanField(default=False)
    reference_number = models.CharField(max_length=100, blank=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Material Line'
        verbose_name_plural = 'Material Lines'

    def __str__(self):
        return f'{self.description} / {self.work_day}'
