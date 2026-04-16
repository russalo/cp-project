"""
EWO calculation services — the single boundary for all currency arithmetic.

All money math lives here. Never perform currency calculations in views,
serializers, or models. Use decimal.ROUND_UP at every calculation step
per DEC-023. See DEC-003 and DEC-031 for the calculation timing policy.

Public API
----------
get_labor_rate(trade_classification, work_date)   -> LaborRate
get_equipment_rates(equipment_type, work_date)    -> CaltransRateLine
calculate_labor_line(line)                        -> Decimal (line_total)
calculate_equipment_line(line)                    -> Decimal (line_total)
calculate_material_line(line)                     -> Decimal (line_total)
calculate_ewo_totals(ewo)                         -> dict of computed totals
submit_ewo(ewo)                                   -> ExtraWorkOrder (submitted)
"""

from decimal import ROUND_UP, Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

# All currency values are rounded to this precision using ROUND_UP (DEC-023).
_CENT = Decimal('0.01')


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

    Per DEC-060, ``EquipmentType`` owns authoritative billing rates. Annual
    Caltrans re-ingest refreshes them from factors × rental_rate; items with
    no CT match carry manually-entered (in-house / FMV) rates. ``work_date``
    is preserved in the signature for API symmetry with ``get_labor_rate``
    but historical effective-dating is provided by on-line snapshots, not by
    stepping back through EquipmentType rate history.

    Returns ``(rate_reg, rate_ot, rate_standby, caltrans_rate_line_or_None)``
    where ``caltrans_rate_line`` is the provenance FK for audit, if any.

    Raises ValueError if no rates are configured (all three fields are zero).
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
    rate = get_labor_rate(line.trade_classification, line.ewo.work_date)

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
    Snapshot rates and calculate line_total for an EquipmentLine.

    Rates come from the ``EquipmentType`` (DEC-060). All three components
    are snapshotted regardless of ``usage_type`` so the full rate context is
    preserved for audit (DEC-021, DEC-015).

    usage_type determines which rate is applied (DEC-021):
      operating → rate_reg
      standby   → rate_standby
      overtime  → rate_ot  (Caltrans OT is rental × ot_factor, not a surcharge)

    Returns the calculated line_total (Decimal).
    """
    from ewo.models import EquipmentLine

    rate_reg, rate_ot, rate_standby, caltrans_line = get_equipment_rates(
        line.equipment_type, line.ewo.work_date
    )

    line.caltrans_rate_line = caltrans_line
    line.rental_rate_snapshot = rate_reg
    line.rw_delay_rate_snapshot = rate_standby
    line.ot_rate_snapshot = rate_ot

    if line.usage_type == EquipmentLine.UsageType.OPERATING:
        rate = rate_reg
    elif line.usage_type == EquipmentLine.UsageType.STANDBY:
        rate = rate_standby
    elif line.usage_type == EquipmentLine.UsageType.OVERTIME:
        rate = rate_ot
    else:
        raise ValueError(f'Unknown usage_type: {line.usage_type!r}')

    line.line_total = _round(line.hours * rate)
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

    Returns the calculated line_total (Decimal).
    """
    line.line_total = _round(line.quantity * line.unit_cost)
    line.save(update_fields=['line_total'])

    if line.catalog_item_id:
        _update_catalog_stats(line)

    return line.line_total


def _update_catalog_stats(material_line):
    """
    Refresh last_unit_cost, last_cost_date, use_count, and last_used on the
    referenced MaterialCatalog item. Uses F() to avoid race conditions on use_count.
    """
    from django.db.models import F
    from resources.models import MaterialCatalog

    MaterialCatalog.objects.filter(pk=material_line.catalog_item_id).update(
        last_unit_cost=material_line.unit_cost,
        last_cost_date=material_line.ewo.work_date,
        use_count=F('use_count') + 1,
        last_used=material_line.ewo.work_date,
    )


# ─── EWO totals ───────────────────────────────────────────────────────────────


def calculate_ewo_totals(ewo):
    """
    Calculate and write all line totals and EWO-level totals.

    Order of operations (CHARTER billing structure):
      1. Labor subtotal        — sum of labor line totals
      2. Labor OH&P            — labor_subtotal × labor_ohp_pct, rounded UP
      3. Equip+Mat subtotal    — sum of equipment and material line totals
      4. Equip+Mat OH&P        — equip_mat_subtotal × equip_mat_ohp_pct, rounded UP
      5. Bond (if required)    — (subtotal before bond) × bond_pct, rounded UP
      6. Total

    Does NOT change EWO status — call submit_ewo() for the full transition.
    This separation keeps this function pure and independently testable.

    Returns a dict of the computed totals for inspection/testing.
    Raises ValueError if any rate lookup fails.
    """
    # Calculate all lines
    for line in ewo.labor_lines.select_related('trade_classification', 'ewo').all():
        calculate_labor_line(line)

    for line in ewo.equipment_lines.select_related('equipment_type', 'ewo').all():
        calculate_equipment_line(line)

    for line in ewo.material_lines.select_related('catalog_item', 'ewo').all():
        calculate_material_line(line)

    # Aggregate subtotals (re-query after saves to get fresh values)
    labor_subtotal = _sum_line_totals(ewo.labor_lines.all())
    equip_subtotal = _sum_line_totals(ewo.equipment_lines.all())
    mat_subtotal = _sum_line_totals(ewo.material_lines.all())
    equip_mat_subtotal = equip_subtotal + mat_subtotal

    # Apply OH&P markups
    labor_ohp_amount = _round(labor_subtotal * ewo.labor_ohp_pct)
    equip_mat_ohp_amount = _round(equip_mat_subtotal * ewo.equip_mat_ohp_pct)

    subtotal_before_bond = (
        labor_subtotal + labor_ohp_amount
        + equip_mat_subtotal + equip_mat_ohp_amount
    )

    # Bond is applied to the pre-bond total, not just the base (CHARTER)
    bond_amount = (
        _round(subtotal_before_bond * ewo.bond_pct)
        if ewo.bond_required
        else Decimal('0.00')
    )

    total = subtotal_before_bond + bond_amount

    # Write computed totals to the EWO record
    ewo.labor_subtotal = labor_subtotal
    ewo.labor_ohp_amount = labor_ohp_amount
    ewo.equip_mat_subtotal = equip_mat_subtotal
    ewo.equip_mat_ohp_amount = equip_mat_ohp_amount
    ewo.bond_amount = bond_amount
    ewo.total = total
    ewo.save(update_fields=[
        'labor_subtotal', 'labor_ohp_amount',
        'equip_mat_subtotal', 'equip_mat_ohp_amount',
        'bond_amount', 'total',
    ])

    return {
        'labor_subtotal': labor_subtotal,
        'labor_ohp_amount': labor_ohp_amount,
        'equip_mat_subtotal': equip_mat_subtotal,
        'equip_mat_ohp_amount': equip_mat_ohp_amount,
        'bond_amount': bond_amount,
        'total': total,
    }


def _sum_line_totals(queryset):
    """Sum line_total values from a queryset, treating None as zero."""
    return sum(
        (line.line_total for line in queryset if line.line_total is not None),
        Decimal('0.00'),
    )


# ─── State transition ─────────────────────────────────────────────────────────


def submit_ewo(ewo):
    """
    Transition an EWO from open → submitted (DEC-016, DEC-031).

    Wraps calculate_ewo_totals() and the status change in a single database
    transaction. After this call, the EWO and all its lines are locked.

    Raises ValidationError if the EWO is not in open status.
    Raises ValueError if any rate lookup fails (propagated from line calculators).
    """
    from ewo.models import ExtraWorkOrder

    if ewo.status != ExtraWorkOrder.Status.OPEN:
        raise ValidationError(
            f'EWO {ewo.ewo_number} cannot be submitted from status '
            f'"{ewo.get_status_display()}". Only open EWOs can be submitted.'
        )

    with transaction.atomic():
        # Re-fetch with a lock to prevent concurrent submission
        ewo = ExtraWorkOrder.objects.select_for_update().get(pk=ewo.pk)

        # Double-check status inside the lock
        if ewo.status != ExtraWorkOrder.Status.OPEN:
            raise ValidationError(
                f'EWO {ewo.ewo_number} was already submitted by another process.'
            )

        calculate_ewo_totals(ewo)

        ewo.status = ExtraWorkOrder.Status.SUBMITTED
        ewo.submitted_at = timezone.now()
        ewo.save(update_fields=['status', 'submitted_at'])

    return ewo
