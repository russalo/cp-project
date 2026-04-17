"""
EWO calculation services — the single boundary for all currency arithmetic.

All money math lives here. Never perform currency calculations in views,
serializers, or models. Use decimal.ROUND_UP at every calculation step
per DEC-023. See DEC-003 and DEC-031 for the calculation timing policy.

Per DEC-064, daily dollar amounts (OH&P, fuel, bond) are computed on each
WorkDay using the EWO-level percentages. The EWO's rolled-up totals are
the sum across its WorkDays.

Fuel surcharge math (DEC-062): the per-day fuel amount is
``fuel_surcharge_pct × Σ(fuel-eligible equipment line totals on that day)``.
Fuel is equipment-related, so it enters the Equipment+Materials OH&P base
(chain B) — ``OH&P_EM = (equip + mat + fuel) × equip_mat_ohp_pct``. Bond
applies on top of everything.

Public API
----------
get_labor_rate(trade_classification, work_date)   -> LaborRate
get_equipment_rates(equipment_type, work_date)    -> (reg, ot, standby, ct_fk)
calculate_labor_line(line)                        -> Decimal (line_total)
calculate_equipment_line(line)                    -> Decimal (line_total)
calculate_material_line(line)                     -> Decimal (line_total)
calculate_workday_totals(work_day)                -> dict  (recomputes all lines)
calculate_ewo_totals(ewo)                         -> dict  (recomputes all lines)
rollup_workday_totals(work_day)                   -> dict  (uses stored line_total)
rollup_ewo_totals(ewo)                            -> dict  (uses stored line_total)
submit_ewo(ewo)                                   -> ExtraWorkOrder (submitted)
create_ewo_from_job(...)                          -> ExtraWorkOrder (pct snapshotted)

Two recompute paths intentionally coexist:

* ``calculate_*_totals`` re-snapshots every line by calling the per-line
  calculators. Used by ``submit_ewo`` for a canonical "freshen everything"
  pass before locking, and by the tests that assert line snapshot fields.
* ``rollup_*_totals`` aggregates existing ``line_total`` values without
  touching line rows. Used by CRUD recalc hooks so editing a single line
  doesn't produce an audit row on every other line in the EWO.
"""

from decimal import ROUND_UP, Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

# All currency values are rounded to this precision using ROUND_UP (DEC-023).
_CENT = Decimal('0.01')
_ZERO = Decimal('0.00')


def _round(value):
    """Round a Decimal value UP to the nearest cent (DEC-023)."""
    return value.quantize(_CENT, rounding=ROUND_UP)


# ─── Rate lookups ─────────────────────────────────────────────────────────────


def get_labor_rate(trade_classification, work_date):
    """
    Return the LaborRate active for trade_classification on work_date.
    Selects the latest effective_date that is on or before work_date (DEC-014).
    Raises ValueError if no rate is found.
    """
    from resources.models import LaborRate

    rate = (
        LaborRate.objects
        .filter(
            trade_classification=trade_classification,
            effective_date__lte=work_date,
        )
        .order_by('-effective_date')
        .first()
    )
    if rate is None:
        raise ValueError(
            f'No labor rate found for "{trade_classification}" on {work_date}. '
            f'Ensure a LaborRate with effective_date ≤ {work_date} exists.'
        )
    return rate


def get_equipment_rates(equipment_type, work_date):
    """
    Return the current rates for an EquipmentType (DEC-060).

    ``work_date`` is preserved in the signature for symmetry with
    ``get_labor_rate`` but does not drive a per-date Caltrans lookup —
    historical effective-dating is provided by line-level snapshots.

    Returns ``(rate_reg, rate_ot, rate_standby, caltrans_rate_line_or_None)``.
    Raises ValueError if the EquipmentType has no rates configured.
    """
    if (
        equipment_type.rate_reg == 0
        and equipment_type.rate_ot == 0
        and equipment_type.rate_standby == 0
    ):
        raise ValueError(
            f'EquipmentType "{equipment_type}" has no rates configured. '
            f'Set rate_reg / rate_ot / rate_standby on the EquipmentType, '
            f'or run the Caltrans ingest to populate them from a linked CT row.'
        )
    return (
        equipment_type.rate_reg,
        equipment_type.rate_ot,
        equipment_type.rate_standby,
        equipment_type.caltrans_rate_line,
    )


# ─── Line calculators ─────────────────────────────────────────────────────────


def calculate_labor_line(line):
    """
    Snapshot rates and calculate line_total for a LaborLine.

    Each time-type component is rounded independently before summing (DEC-025).
    Snapshots all three rate tiers regardless of which hours are non-zero
    so the full rate context is preserved for audit (DEC-015).

    Returns the calculated line_total (Decimal).
    """
    rate = get_labor_rate(line.trade_classification, line.work_day.work_date)

    line.rate_reg_snapshot = rate.rate_reg
    line.rate_ot_snapshot = rate.rate_ot
    line.rate_dt_snapshot = rate.rate_dt

    reg_total = _round(line.reg_hours * rate.rate_reg)
    ot_total = _round(line.ot_hours * rate.rate_ot)
    dt_total = _round(line.dt_hours * rate.rate_dt)

    line.line_total = reg_total + ot_total + dt_total
    line.save(update_fields=[
        'rate_reg_snapshot', 'rate_ot_snapshot', 'rate_dt_snapshot', 'line_total',
    ])
    return line.line_total


def calculate_equipment_line(line):
    """
    Snapshot rates and calculate line_total for an EquipmentLine (DEC-066).

    line_total = qty × (reg_hrs × rate_reg + ot_hrs × rate_ot + standby_hrs × rate_standby)

    Each per-unit time-type component is rounded independently before
    combining (DEC-023, DEC-025). The qty multiplier is applied to the
    already-rounded per-unit total.
    """
    rate_reg, rate_ot, rate_standby, caltrans_line = get_equipment_rates(
        line.equipment_type, line.work_day.work_date
    )

    line.caltrans_rate_line = caltrans_line
    line.rental_rate_snapshot = rate_reg
    line.rw_delay_rate_snapshot = rate_standby
    line.ot_rate_snapshot = rate_ot

    reg_total = _round(line.reg_hours * rate_reg)
    ot_total = _round(line.ot_hours * rate_ot)
    standby_total = _round(line.standby_hours * rate_standby)
    per_unit = reg_total + ot_total + standby_total

    line.line_total = per_unit * line.qty
    line.save(update_fields=[
        'caltrans_rate_line', 'rental_rate_snapshot', 'rw_delay_rate_snapshot',
        'ot_rate_snapshot', 'line_total',
    ])
    return line.line_total


def calculate_material_line(line):
    """
    Calculate line_total for a MaterialLine.

    Total is always unit_cost × quantity, rounded UP (DEC-022, DEC-023).
    If the line references a catalog item, updates that item's cost and
    usage stats so the catalog stays current.
    """
    line.line_total = _round(line.quantity * line.unit_cost)
    line.save(update_fields=['line_total'])

    if line.catalog_item_id:
        _update_catalog_stats(line)

    return line.line_total


def _update_catalog_stats(material_line):
    """Refresh catalog item cost / usage counters after a material line saves."""
    from django.db.models import F
    from resources.models import MaterialCatalog

    MaterialCatalog.objects.filter(pk=material_line.catalog_item_id).update(
        last_unit_cost=material_line.unit_cost,
        last_cost_date=material_line.work_day.work_date,
        use_count=F('use_count') + 1,
        last_used=material_line.work_day.work_date,
    )


# ─── WorkDay and EWO totals ───────────────────────────────────────────────────


def rollup_workday_totals(work_day):
    """
    Aggregate daily totals from already-computed ``line_total`` values
    without re-saving any line rows. Same math as ``calculate_workday_totals``
    minus the per-line recompute pass.

    Order of operations — "chain B" per the fuel-surcharge design:
      1. Labor subtotal       — sum of labor line totals
      2. Labor OH&P           — labor_subtotal × EWO.labor_ohp_pct
      3. Equip subtotal       — sum of equipment line totals (all equipment)
      4. Material subtotal    — sum of material line totals
      5. Fuel amount          — EWO.fuel_surcharge_pct × sum of fuel-eligible
                                equipment line totals only (DEC-062)
      6. Equip+Mat OH&P       — (equip + mat + fuel) × EWO.equip_mat_ohp_pct
                                (fuel enters this OH&P base — chain B)
      7. Bond (if required)   — (everything above) × EWO.bond_pct
      8. day_total            — sum of all of the above

    Returns a dict of the computed amounts. Does not change status.
    """
    ewo = work_day.ewo

    labor_lines = list(work_day.labor_lines.all())
    equipment_lines = list(
        work_day.equipment_lines.select_related('equipment_type').all()
    )
    material_lines = list(work_day.material_lines.all())

    labor_subtotal = _sum_line_totals(labor_lines)
    equip_subtotal = _sum_line_totals(equipment_lines)
    material_subtotal = _sum_line_totals(material_lines)

    # Fuel surcharge base: only equipment lines whose type is fuel_eligible.
    fuel_base = _sum_line_totals(
        [line for line in equipment_lines if line.equipment_type.fuel_surcharge_eligible]
    )
    fuel_amount = _round(fuel_base * ewo.fuel_surcharge_pct)

    labor_ohp_amount = _round(labor_subtotal * ewo.labor_ohp_pct)
    # Chain B: fuel enters the equip+mat OH&P base.
    equip_mat_ohp_amount = _round(
        (equip_subtotal + material_subtotal + fuel_amount) * ewo.equip_mat_ohp_pct
    )

    subtotal_before_bond = (
        labor_subtotal + labor_ohp_amount
        + equip_subtotal + material_subtotal + fuel_amount
        + equip_mat_ohp_amount
    )
    bond_amount = (
        _round(subtotal_before_bond * ewo.bond_pct)
        if ewo.bond_required
        else _ZERO
    )
    day_total = subtotal_before_bond + bond_amount

    work_day.labor_subtotal = labor_subtotal
    work_day.equip_subtotal = equip_subtotal
    work_day.material_subtotal = material_subtotal
    work_day.fuel_amount = fuel_amount
    work_day.labor_ohp_amount = labor_ohp_amount
    work_day.equip_mat_ohp_amount = equip_mat_ohp_amount
    work_day.bond_amount = bond_amount
    work_day.day_total = day_total
    work_day.save(update_fields=[
        'labor_subtotal', 'equip_subtotal', 'material_subtotal',
        'fuel_amount', 'labor_ohp_amount', 'equip_mat_ohp_amount',
        'bond_amount', 'day_total',
    ])

    return {
        'labor_subtotal': labor_subtotal,
        'equip_subtotal': equip_subtotal,
        'material_subtotal': material_subtotal,
        'fuel_amount': fuel_amount,
        'labor_ohp_amount': labor_ohp_amount,
        'equip_mat_ohp_amount': equip_mat_ohp_amount,
        'bond_amount': bond_amount,
        'day_total': day_total,
    }


def calculate_workday_totals(work_day):
    """
    Recompute every line on a WorkDay and roll up daily totals (DEC-064).

    Use this on submit (canonical "freshen everything" pass). CRUD hooks
    should prefer ``rollup_workday_totals`` so editing one line does not
    produce an audit row on every other line in the day.
    """
    for line in work_day.labor_lines.select_related('trade_classification').all():
        calculate_labor_line(line)
    for line in work_day.equipment_lines.select_related('equipment_type').all():
        calculate_equipment_line(line)
    for line in work_day.material_lines.select_related('catalog_item').all():
        calculate_material_line(line)

    return rollup_workday_totals(work_day)


def rollup_ewo_totals(ewo):
    """
    Roll up already-computed WorkDay totals onto the EWO record (DEC-064).

    Calls ``rollup_workday_totals`` for each WorkDay so daily amounts stay
    consistent with current line_total values, then sums onto the EWO.
    Does not touch line rows.

    Returns a dict of the rolled-up totals.
    """
    for work_day in ewo.work_days.all():
        rollup_workday_totals(work_day)
    return _sum_days_onto_ewo(ewo)


def calculate_ewo_totals(ewo):
    """
    Recompute every line on every WorkDay, then roll up to the EWO.

    Used by ``submit_ewo`` to guarantee rates are re-snapshotted against
    the current work_date before the EWO is locked. CRUD hooks should
    use ``rollup_ewo_totals`` instead.

    Raises ValueError if any rate lookup fails during line calculation.
    """
    for work_day in ewo.work_days.all():
        calculate_workday_totals(work_day)
    return _sum_days_onto_ewo(ewo)


def _sum_days_onto_ewo(ewo):
    """Sum per-day amounts onto the EWO and save. Shared by rollup + calculate paths."""
    days = list(ewo.work_days.all())

    labor_subtotal = sum((d.labor_subtotal or _ZERO for d in days), _ZERO)
    equip_subtotal = sum((d.equip_subtotal or _ZERO for d in days), _ZERO)
    material_subtotal = sum((d.material_subtotal or _ZERO for d in days), _ZERO)
    equip_mat_subtotal = equip_subtotal + material_subtotal
    fuel_subtotal = sum((d.fuel_amount or _ZERO for d in days), _ZERO)
    labor_ohp_amount = sum((d.labor_ohp_amount or _ZERO for d in days), _ZERO)
    equip_mat_ohp_amount = sum((d.equip_mat_ohp_amount or _ZERO for d in days), _ZERO)
    bond_amount = sum((d.bond_amount or _ZERO for d in days), _ZERO)
    total = sum((d.day_total or _ZERO for d in days), _ZERO)

    ewo.labor_subtotal = labor_subtotal
    ewo.equip_mat_subtotal = equip_mat_subtotal
    ewo.fuel_subtotal = fuel_subtotal
    ewo.labor_ohp_amount = labor_ohp_amount
    ewo.equip_mat_ohp_amount = equip_mat_ohp_amount
    ewo.bond_amount = bond_amount
    ewo.total = total
    ewo.save(update_fields=[
        'labor_subtotal', 'equip_mat_subtotal', 'fuel_subtotal',
        'labor_ohp_amount', 'equip_mat_ohp_amount', 'bond_amount', 'total',
    ])

    return {
        'labor_subtotal': labor_subtotal,
        'equip_mat_subtotal': equip_mat_subtotal,
        'fuel_subtotal': fuel_subtotal,
        'labor_ohp_amount': labor_ohp_amount,
        'equip_mat_ohp_amount': equip_mat_ohp_amount,
        'bond_amount': bond_amount,
        'total': total,
    }


def _sum_line_totals(lines):
    """Sum line_total values from a queryset or iterable, treating None as zero."""
    return sum(
        (line.line_total for line in lines if line.line_total is not None),
        _ZERO,
    )


# ─── Creation helpers ─────────────────────────────────────────────────────────


def create_ewo_from_job(job, created_by, **fields):
    """
    Construct an EWO with Job-level defaults snapshotted onto it (DEC-063).

    Fuel surcharge % is seeded from the most recent EWO on the same Job
    (DEC-062 — last-used default); falls back to zero if this is the first
    EWO on the job.

    Any explicit ``labor_ohp_pct`` / ``equip_mat_ohp_pct`` / ``bond_pct`` /
    ``fuel_surcharge_pct`` passed in ``fields`` overrides the snapshot.
    """
    from ewo.models import ExtraWorkOrder

    # Last-used fuel % on this job
    previous_fuel_pct = (
        ExtraWorkOrder.objects
        .filter(job=job)
        .order_by('-ewo_sequence')
        .values_list('fuel_surcharge_pct', flat=True)
        .first()
    )

    defaults = {
        'labor_ohp_pct': job.labor_ohp_pct,
        'equip_mat_ohp_pct': job.equip_mat_ohp_pct,
        'bond_pct': job.bond_pct,
        'fuel_surcharge_pct': (
            previous_fuel_pct if previous_fuel_pct is not None else Decimal('0.0000')
        ),
    }
    defaults.update(fields)
    return ExtraWorkOrder.objects.create(job=job, created_by=created_by, **defaults)


# ─── State transition ─────────────────────────────────────────────────────────


def submit_ewo(ewo):
    """
    Transition an EWO from open → submitted (DEC-016, DEC-031).

    Wraps ``calculate_ewo_totals`` and the status change in a single
    database transaction. After this call, the EWO and all its lines
    are locked.

    Raises ValidationError if the EWO is not in open status.
    Raises ValueError if any rate lookup fails.
    """
    from ewo.models import ExtraWorkOrder

    if ewo.status != ExtraWorkOrder.Status.OPEN:
        raise ValidationError(
            f'EWO {ewo.ewo_number} cannot be submitted from status '
            f'"{ewo.get_status_display()}". Only open EWOs can be submitted.'
        )

    with transaction.atomic():
        ewo = ExtraWorkOrder.objects.select_for_update().get(pk=ewo.pk)

        if ewo.status != ExtraWorkOrder.Status.OPEN:
            raise ValidationError(
                f'EWO {ewo.ewo_number} was already submitted by another process.'
            )

        calculate_ewo_totals(ewo)

        ewo.status = ExtraWorkOrder.Status.SUBMITTED
        ewo.submitted_at = timezone.now()
        ewo.save(update_fields=['status', 'submitted_at'])

    return ewo
