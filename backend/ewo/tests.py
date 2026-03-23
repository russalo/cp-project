"""
Tests for ewo/services.py — the single currency calculation boundary.

Coverage strategy
-----------------
- get_labor_rate         : precedence, no-rate error
- get_equipment_rates    : schedule match, fallback, no-rate-line error
- calculate_labor_line   : per-time-type ROUND_UP, snapshot fields, saves
- calculate_equipment_line: all three usage_type paths, snapshot fields
- calculate_material_line : ROUND_UP, catalog stats update, no-catalog path
- calculate_ewo_totals    : OH&P, bond on/off, return dict, writes to EWO
- submit_ewo              : open→submitted transition, timestamp, non-open rejection

All monetary assertions use Decimal — never float.
"""

import pytest
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APITestCase
from freezegun import freeze_time
from model_bakery import baker

from ewo.models import EquipmentLine, ExtraWorkOrder, LaborLine, MaterialLine
from ewo.services import (
    calculate_equipment_line,
    calculate_ewo_totals,
    calculate_labor_line,
    calculate_material_line,
    get_equipment_rates,
    get_labor_rate,
    submit_ewo,
)
from jobs.models import Job
from resources.models import (
    CaltransRateLine,
    CaltransSchedule,
    EquipmentType,
    LaborRate,
    MaterialCatalog,
    TradeClassification,
)


# ─── Shared helpers ────────────────────────────────────────────────────────────


def make_trade(**kwargs):
    """Create a TradeClassification with sensible defaults."""
    defaults = {'name': 'Operator', 'union_name': 'IUOE Local 12', 'union_abbrev': 'IUOE'}
    defaults.update(kwargs)
    return baker.make(TradeClassification, **defaults)


def make_labor_rate(trade, effective_date, rate_reg='50.00', rate_ot='75.00', rate_dt='100.00'):
    return baker.make(
        LaborRate,
        trade_classification=trade,
        effective_date=effective_date,
        rate_reg=Decimal(rate_reg),
        rate_ot=Decimal(rate_ot),
        rate_dt=Decimal(rate_dt),
    )


def make_schedule(effective_date, expiry_date, year=None):
    return baker.make(
        CaltransSchedule,
        schedule_year=year or str(effective_date.year),
        effective_date=effective_date,
        expiry_date=expiry_date,
    )


def make_rate_line(schedule=None, class_code='AA', make_code='CAT', model_code='D8',
                   rental_rate='150.00', rw_delay_rate='75.00', overtime_rate='50.00'):
    if schedule is None:
        schedule = make_schedule(date(2025, 1, 1), date(2025, 12, 31))
    return baker.make(
        CaltransRateLine,
        schedule=schedule,
        class_code=class_code,
        make_code=make_code,
        model_code=model_code,
        rental_rate=Decimal(rental_rate),
        rw_delay_rate=Decimal(rw_delay_rate),
        overtime_rate=Decimal(overtime_rate),
        unit='HR',
    )


def make_equip_type(rate_line=None):
    if rate_line is None:
        rate_line = make_rate_line()
    return baker.make(EquipmentType, caltrans_rate_line=rate_line)


def make_open_ewo(work_date=None, **kwargs):
    """Create a minimal open EWO against a fresh job+user."""
    job = baker.make(Job, job_number='1886', name='Test Job')
    user = baker.make(User)
    defaults = {
        'job': job,
        'created_by': user,
        'work_date': work_date or date(2025, 6, 15),
        'status': ExtraWorkOrder.Status.OPEN,
        'ewo_type': ExtraWorkOrder.EwoType.TM,
        'description': 'Test EWO',
        'labor_ohp_pct': Decimal('0.1500'),
        'equip_mat_ohp_pct': Decimal('0.1500'),
        'bond_pct': Decimal('0.0100'),
        'bond_required': False,
    }
    defaults.update(kwargs)
    return baker.make(ExtraWorkOrder, **defaults)


# ─── get_labor_rate ────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestGetLaborRate:
    def test_returns_rate_effective_on_work_date(self):
        trade = make_trade()
        rate = make_labor_rate(trade, date(2025, 1, 1))
        result = get_labor_rate(trade, date(2025, 6, 15))
        assert result == rate

    def test_returns_latest_rate_when_multiple_exist(self):
        trade = make_trade()
        make_labor_rate(trade, date(2024, 1, 1), rate_reg='40.00')
        newer = make_labor_rate(trade, date(2025, 1, 1), rate_reg='50.00')
        result = get_labor_rate(trade, date(2025, 6, 15))
        assert result == newer

    def test_returns_rate_effective_on_exact_work_date(self):
        """effective_date == work_date is a valid match."""
        trade = make_trade()
        rate = make_labor_rate(trade, date(2025, 6, 15))
        result = get_labor_rate(trade, date(2025, 6, 15))
        assert result == rate

    def test_does_not_return_future_rate(self):
        """Rate with effective_date after work_date must be excluded."""
        trade = make_trade()
        make_labor_rate(trade, date(2025, 7, 1))  # future rate
        with pytest.raises(ValueError, match='No labor rate found'):
            get_labor_rate(trade, date(2025, 6, 15))

    def test_raises_when_no_rate_for_trade(self):
        trade = make_trade()
        with pytest.raises(ValueError, match='No labor rate found'):
            get_labor_rate(trade, date(2025, 6, 15))


# ─── get_equipment_rates ───────────────────────────────────────────────────────


@pytest.mark.django_db
class TestGetEquipmentRates:
    def test_returns_rate_line_from_matching_schedule(self):
        schedule = make_schedule(date(2025, 1, 1), date(2025, 12, 31))
        ref = make_rate_line(schedule)
        equip_type = make_equip_type(ref)
        # Matching line in the schedule
        result = get_equipment_rates(equip_type, date(2025, 6, 15))
        assert result == ref

    def test_picks_rate_line_from_dated_schedule(self):
        """When a dated schedule exists, use its rate line (not the equip_type's ref)."""
        old_schedule = make_schedule(date(2024, 1, 1), date(2024, 12, 31))
        old_line = make_rate_line(old_schedule, class_code='AA', make_code='CAT', model_code='D8',
                                  rental_rate='120.00')
        equip_type = make_equip_type(old_line)

        new_schedule = make_schedule(date(2025, 1, 1), date(2025, 12, 31))
        new_line = make_rate_line(new_schedule, class_code='AA', make_code='CAT', model_code='D8',
                                  rental_rate='150.00')

        result = get_equipment_rates(equip_type, date(2025, 6, 15))
        assert result == new_line
        assert result.rental_rate == Decimal('150.00')

    def test_falls_back_to_ref_when_no_schedule_covers_date(self):
        """No schedule covers work_date — fall back to equipment_type's rate line."""
        ref = make_rate_line()
        equip_type = make_equip_type(ref)
        # Schedule exists but does NOT cover 2023
        make_schedule(date(2025, 1, 1), date(2025, 12, 31))
        result = get_equipment_rates(equip_type, date(2023, 6, 15))
        assert result == ref

    def test_falls_back_when_schedule_has_no_matching_line(self):
        """Schedule covers work_date but has no line with matching codes."""
        schedule = make_schedule(date(2025, 1, 1), date(2025, 12, 31))
        # Rate line in schedule with different codes
        make_rate_line(schedule, class_code='ZZ', make_code='JD', model_code='850')

        # equip_type's ref uses different codes (AA/CAT/D8)
        ref = make_rate_line(make_schedule(date(2024, 1, 1), date(2024, 12, 31)),
                             class_code='AA', make_code='CAT', model_code='D8')
        equip_type = make_equip_type(ref)

        result = get_equipment_rates(equip_type, date(2025, 6, 15))
        assert result == ref  # fallback to equipment_type.caltrans_rate_line

    def test_raises_when_equip_type_has_no_rate_line(self):
        # caltrans_rate_line is a non-nullable FK: accessing the descriptor on
        # an unsaved instance with caltrans_rate_line_id=None raises
        # RelatedObjectDoesNotExist, not returns None. Use a Mock so the
        # attribute access returns None exactly as the service expects.
        from unittest.mock import Mock
        equip_type = Mock()
        equip_type.caltrans_rate_line = None
        with pytest.raises(ValueError, match='has no Caltrans rate line'):
            get_equipment_rates(equip_type, date(2025, 6, 15))


# ─── calculate_labor_line ──────────────────────────────────────────────────────


@pytest.mark.django_db
class TestCalculateLaborLine:
    def _setup(self, work_date=date(2025, 6, 15)):
        trade = make_trade()
        make_labor_rate(trade, date(2025, 1, 1),
                        rate_reg='50.00', rate_ot='75.00', rate_dt='100.00')
        ewo = make_open_ewo(work_date=work_date)
        line = baker.make(
            LaborLine,
            ewo=ewo,
            trade_classification=trade,
            labor_type=LaborLine.LaborType.GENERIC,
            reg_hours=Decimal('8.0'),
            ot_hours=Decimal('2.0'),
            dt_hours=Decimal('0.0'),
        )
        return line

    def test_calculates_line_total(self):
        line = self._setup()
        total = calculate_labor_line(line)
        # 8 * 50 + 2 * 75 + 0 * 100 = 400 + 150 + 0
        assert total == Decimal('550.00')

    def test_snapshots_all_three_rates(self):
        line = self._setup()
        calculate_labor_line(line)
        line.refresh_from_db()
        assert line.rate_reg_snapshot == Decimal('50.00')
        assert line.rate_ot_snapshot == Decimal('75.00')
        assert line.rate_dt_snapshot == Decimal('100.00')

    def test_saves_line_total_to_db(self):
        line = self._setup()
        calculate_labor_line(line)
        line.refresh_from_db()
        assert line.line_total == Decimal('550.00')

    def test_rounds_each_time_type_independently(self):
        """Each time-type is rounded ROUND_UP before summing (DEC-025).

        1.5 hr * 33.33 = 49.995 → ROUND_UP → 50.00
        0.5 hr * 33.33 = 16.665 → ROUND_UP → 16.67
        0.5 hr * 33.33 = 16.665 → ROUND_UP → 16.67
        Total = 83.34 (not 83.33 which would result from rounding the sum only)
        """
        trade = make_trade(name='Laborer')
        make_labor_rate(trade, date(2025, 1, 1),
                        rate_reg='33.33', rate_ot='33.33', rate_dt='33.33')
        ewo = make_open_ewo()
        line = baker.make(
            LaborLine,
            ewo=ewo,
            trade_classification=trade,
            labor_type=LaborLine.LaborType.GENERIC,
            reg_hours=Decimal('1.5'),
            ot_hours=Decimal('0.5'),
            dt_hours=Decimal('0.5'),
        )
        total = calculate_labor_line(line)
        # Round each: 49.995→50.00, 16.665→16.67, 16.665→16.67 = 83.34
        assert total == Decimal('83.34')

    def test_zero_hours_contribute_zero(self):
        line = self._setup()
        line.reg_hours = Decimal('0.0')
        line.ot_hours = Decimal('0.0')
        line.dt_hours = Decimal('0.0')
        line.save()
        total = calculate_labor_line(line)
        assert total == Decimal('0.00')


# ─── calculate_equipment_line ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestCalculateEquipmentLine:
    def _setup(self, usage_type=EquipmentLine.UsageType.OPERATING, hours='8.0', work_date=date(2025, 6, 15)):
        schedule = make_schedule(date(2025, 1, 1), date(2025, 12, 31))
        rate_line = make_rate_line(
            schedule,
            rental_rate='150.00',
            rw_delay_rate='75.00',
            overtime_rate='50.00',
        )
        equip_type = make_equip_type(rate_line)
        ewo = make_open_ewo(work_date=work_date)
        line = baker.make(
            EquipmentLine,
            ewo=ewo,
            equipment_type=equip_type,
            usage_type=usage_type,
            hours=Decimal(hours),
            unit='HR',
        )
        return line, rate_line

    def test_operating_uses_rental_rate(self):
        line, _ = self._setup(EquipmentLine.UsageType.OPERATING)
        total = calculate_equipment_line(line)
        assert total == Decimal('1200.00')  # 8 * 150

    def test_standby_uses_rw_delay_rate(self):
        line, _ = self._setup(EquipmentLine.UsageType.STANDBY)
        total = calculate_equipment_line(line)
        assert total == Decimal('600.00')  # 8 * 75

    def test_overtime_uses_rental_plus_ot_rate(self):
        line, _ = self._setup(EquipmentLine.UsageType.OVERTIME)
        total = calculate_equipment_line(line)
        assert total == Decimal('1600.00')  # 8 * (150 + 50)

    def test_snapshots_all_three_rate_components(self):
        line, rate_line = self._setup()
        calculate_equipment_line(line)
        line.refresh_from_db()
        assert line.rental_rate_snapshot == Decimal('150.00')
        assert line.rw_delay_rate_snapshot == Decimal('75.00')
        assert line.ot_rate_snapshot == Decimal('50.00')

    def test_caltrans_rate_line_fk_set_on_line(self):
        line, rate_line = self._setup()
        calculate_equipment_line(line)
        line.refresh_from_db()
        assert line.caltrans_rate_line_id == rate_line.pk

    def test_round_up_applied_to_result(self):
        """2.5 hr * 33.33 = 83.325 → ROUND_UP → 83.33."""
        schedule = make_schedule(date(2025, 1, 1), date(2025, 12, 31))
        rate_line = make_rate_line(schedule, rental_rate='33.33')
        equip_type = make_equip_type(rate_line)
        ewo = make_open_ewo()
        line = baker.make(
            EquipmentLine,
            ewo=ewo,
            equipment_type=equip_type,
            usage_type=EquipmentLine.UsageType.OPERATING,
            hours=Decimal('2.5'),
        )
        total = calculate_equipment_line(line)
        # 2.5 * 33.33 = 83.325 → ROUND_UP → 83.33
        assert total == Decimal('83.33')

    def test_saves_line_total_to_db(self):
        line, _ = self._setup()
        calculate_equipment_line(line)
        line.refresh_from_db()
        assert line.line_total == Decimal('1200.00')


# ─── calculate_material_line ───────────────────────────────────────────────────


@pytest.mark.django_db
class TestCalculateMaterialLine:
    def test_calculates_quantity_times_unit_cost(self):
        ewo = make_open_ewo()
        line = baker.make(
            MaterialLine,
            ewo=ewo,
            description='PVC Pipe 6"',
            quantity=Decimal('10.000'),
            unit='LF',
            unit_cost=Decimal('12.50'),
        )
        total = calculate_material_line(line)
        assert total == Decimal('125.00')

    def test_round_up_applied(self):
        """3.333 * 3.33 = 11.09889 → ROUND_UP → 11.10."""
        ewo = make_open_ewo()
        line = baker.make(
            MaterialLine,
            ewo=ewo,
            description='Widget',
            quantity=Decimal('3.333'),
            unit='EA',
            unit_cost=Decimal('3.33'),
        )
        total = calculate_material_line(line)
        # 3.333 * 3.33 = 11.09889 → ROUND_UP → 11.10
        assert total == Decimal('11.10')

    def test_saves_line_total_to_db(self):
        ewo = make_open_ewo()
        line = baker.make(
            MaterialLine,
            ewo=ewo,
            description='Gasket',
            quantity=Decimal('5.000'),
            unit='EA',
            unit_cost=Decimal('2.00'),
        )
        calculate_material_line(line)
        line.refresh_from_db()
        assert line.line_total == Decimal('10.00')

    def test_updates_catalog_stats_when_catalog_item_set(self):
        ewo = make_open_ewo(work_date=date(2025, 6, 15))
        catalog = baker.make(
            MaterialCatalog,
            description='Unique Catalog Item',
            default_unit='LF',
            use_count=3,
        )
        line = baker.make(
            MaterialLine,
            ewo=ewo,
            catalog_item=catalog,
            description=catalog.description,
            quantity=Decimal('5.000'),
            unit='LF',
            unit_cost=Decimal('20.00'),
        )
        calculate_material_line(line)
        catalog.refresh_from_db()
        assert catalog.use_count == 4
        assert catalog.last_unit_cost == Decimal('20.00')
        assert catalog.last_cost_date == date(2025, 6, 15)
        assert catalog.last_used == date(2025, 6, 15)

    def test_does_not_update_catalog_when_no_catalog_item(self):
        """No catalog_item — no crash, no update attempted."""
        ewo = make_open_ewo()
        line = baker.make(
            MaterialLine,
            ewo=ewo,
            catalog_item=None,
            description='Ad-hoc material',
            quantity=Decimal('1.000'),
            unit='LS',
            unit_cost=Decimal('500.00'),
        )
        # Should not raise
        total = calculate_material_line(line)
        assert total == Decimal('500.00')

    def test_lump_sum_quantity_one(self):
        """LS items: quantity=1, unit='LS', total equals unit_cost."""
        ewo = make_open_ewo()
        line = baker.make(
            MaterialLine,
            ewo=ewo,
            description='Mobilization',
            quantity=Decimal('1.000'),
            unit='LS',
            unit_cost=Decimal('1500.00'),
        )
        total = calculate_material_line(line)
        assert total == Decimal('1500.00')


# ─── calculate_ewo_totals ─────────────────────────────────────────────────────


@pytest.mark.django_db
class TestCalculateEwoTotals:
    """
    Billing structure (CHARTER):
      labor_subtotal             = sum of labor line_totals
      labor_ohp_amount           = ROUND_UP(labor_subtotal * labor_ohp_pct)
      equip_mat_subtotal         = sum of equipment + material line_totals
      equip_mat_ohp_amount       = ROUND_UP(equip_mat_subtotal * equip_mat_ohp_pct)
      subtotal_before_bond       = above four summed
      bond_amount (if required)  = ROUND_UP(subtotal_before_bond * bond_pct)
      total                      = subtotal_before_bond + bond_amount
    """

    def _full_ewo(self, bond_required=False):
        """Build an open EWO with one of each line type."""
        trade = make_trade()
        make_labor_rate(trade, date(2025, 1, 1),
                        rate_reg='50.00', rate_ot='75.00', rate_dt='100.00')

        schedule = make_schedule(date(2025, 1, 1), date(2025, 12, 31))
        rate_line = make_rate_line(schedule, rental_rate='100.00',
                                   rw_delay_rate='50.00', overtime_rate='25.00')
        equip_type = make_equip_type(rate_line)

        ewo = make_open_ewo(
            work_date=date(2025, 6, 15),
            labor_ohp_pct=Decimal('0.1500'),
            equip_mat_ohp_pct=Decimal('0.1500'),
            bond_pct=Decimal('0.0100'),
            bond_required=bond_required,
        )

        # Labor: 8 reg hours @ $50 = $400.00
        baker.make(
            LaborLine,
            ewo=ewo,
            trade_classification=trade,
            labor_type=LaborLine.LaborType.GENERIC,
            reg_hours=Decimal('8.0'),
            ot_hours=Decimal('0.0'),
            dt_hours=Decimal('0.0'),
        )

        # Equipment: 4 hr operating @ $100 = $400.00
        baker.make(
            EquipmentLine,
            ewo=ewo,
            equipment_type=equip_type,
            usage_type=EquipmentLine.UsageType.OPERATING,
            hours=Decimal('4.0'),
            unit='HR',
        )

        # Material: 10 LF @ $10.00 = $100.00
        baker.make(
            MaterialLine,
            ewo=ewo,
            description='Test pipe',
            quantity=Decimal('10.000'),
            unit='LF',
            unit_cost=Decimal('10.00'),
            catalog_item=None,
        )

        return ewo

    def test_returns_correct_totals_dict_no_bond(self):
        ewo = self._full_ewo(bond_required=False)
        result = calculate_ewo_totals(ewo)

        # labor: 400.00; OH&P: 60.00
        assert result['labor_subtotal'] == Decimal('400.00')
        assert result['labor_ohp_amount'] == Decimal('60.00')
        # equip+mat: 400+100=500.00; OH&P: 75.00
        assert result['equip_mat_subtotal'] == Decimal('500.00')
        assert result['equip_mat_ohp_amount'] == Decimal('75.00')
        # bond: 0
        assert result['bond_amount'] == Decimal('0.00')
        # total: 400+60+500+75+0 = 1035
        assert result['total'] == Decimal('1035.00')

    def test_returns_correct_totals_dict_with_bond(self):
        ewo = self._full_ewo(bond_required=True)
        result = calculate_ewo_totals(ewo)

        subtotal_before_bond = Decimal('1035.00')
        bond = subtotal_before_bond * Decimal('0.0100')
        # 1035 * 0.01 = 10.35 (exact, no rounding needed)
        assert result['bond_amount'] == Decimal('10.35')
        assert result['total'] == Decimal('1045.35')

    def test_writes_totals_to_ewo_record(self):
        ewo = self._full_ewo(bond_required=False)
        calculate_ewo_totals(ewo)
        ewo.refresh_from_db()
        assert ewo.labor_subtotal == Decimal('400.00')
        assert ewo.equip_mat_subtotal == Decimal('500.00')
        assert ewo.total == Decimal('1035.00')

    def test_ewo_with_no_lines_totals_zero(self):
        ewo = make_open_ewo()
        result = calculate_ewo_totals(ewo)
        assert result['labor_subtotal'] == Decimal('0.00')
        assert result['equip_mat_subtotal'] == Decimal('0.00')
        assert result['total'] == Decimal('0.00')

    def test_ohp_rounds_up(self):
        """OH&P on a subtotal that produces a fractional cent rounds UP."""
        trade = make_trade(name='Laborer')
        make_labor_rate(trade, date(2025, 1, 1),
                        rate_reg='33.34', rate_ot='0.00', rate_dt='0.00')
        # 3 reg hours * 33.34 = 100.02 labor subtotal
        # OH&P 15% = 100.02 * 0.15 = 15.003 → ROUND_UP → 15.01
        ewo = make_open_ewo(
            work_date=date(2025, 6, 15),
            labor_ohp_pct=Decimal('0.1500'),
            equip_mat_ohp_pct=Decimal('0.0000'),
            bond_required=False,
        )
        baker.make(
            LaborLine,
            ewo=ewo,
            trade_classification=trade,
            labor_type=LaborLine.LaborType.GENERIC,
            reg_hours=Decimal('3.0'),
            ot_hours=Decimal('0.0'),
            dt_hours=Decimal('0.0'),
        )
        result = calculate_ewo_totals(ewo)
        assert result['labor_subtotal'] == Decimal('100.02')
        assert result['labor_ohp_amount'] == Decimal('15.01')

    def test_does_not_change_ewo_status(self):
        ewo = self._full_ewo()
        calculate_ewo_totals(ewo)
        ewo.refresh_from_db()
        assert ewo.status == ExtraWorkOrder.Status.OPEN


# ─── submit_ewo ────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestSubmitEwo:
    def _ewo_with_labor(self, status=ExtraWorkOrder.Status.OPEN):
        trade = make_trade()
        make_labor_rate(trade, date(2025, 1, 1))
        schedule = make_schedule(date(2025, 1, 1), date(2025, 12, 31))
        ewo = make_open_ewo(work_date=date(2025, 6, 15), status=status)
        baker.make(
            LaborLine,
            ewo=ewo,
            trade_classification=trade,
            labor_type=LaborLine.LaborType.GENERIC,
            reg_hours=Decimal('8.0'),
            ot_hours=Decimal('0.0'),
            dt_hours=Decimal('0.0'),
        )
        return ewo

    @freeze_time('2025-06-15 14:30:00')
    def test_transitions_open_to_submitted(self):
        ewo = self._ewo_with_labor()
        result = submit_ewo(ewo)
        result.refresh_from_db()
        assert result.status == ExtraWorkOrder.Status.SUBMITTED

    @freeze_time('2025-06-15 14:30:00')
    def test_sets_submitted_at_timestamp(self):
        from django.utils import timezone
        ewo = self._ewo_with_labor()
        result = submit_ewo(ewo)
        result.refresh_from_db()
        assert result.submitted_at == timezone.now()

    @freeze_time('2025-06-15 14:30:00')
    def test_returns_ewo_instance(self):
        ewo = self._ewo_with_labor()
        result = submit_ewo(ewo)
        assert result.pk == ewo.pk

    @freeze_time('2025-06-15 14:30:00')
    def test_calculates_totals_on_submit(self):
        ewo = self._ewo_with_labor()
        result = submit_ewo(ewo)
        result.refresh_from_db()
        # Labor lines exist → total must be non-zero
        assert result.total is not None
        assert result.total > Decimal('0.00')

    def test_raises_if_not_open(self):
        # Create shared job/user/trade once — make_open_ewo() hardcodes
        # job_number='1886' so calling it 4× in a loop would hit the unique
        # constraint on the second iteration.
        trade = make_trade(name='Operator-status-test')
        make_labor_rate(trade, date(2025, 1, 1))
        job = baker.make(Job, job_number='1886-status', name='Status Test Job')
        user = baker.make(User)
        for bad_status in (
            ExtraWorkOrder.Status.SUBMITTED,
            ExtraWorkOrder.Status.APPROVED,
            ExtraWorkOrder.Status.SENT,
            ExtraWorkOrder.Status.BILLED,
        ):
            ewo = baker.make(
                ExtraWorkOrder,
                job=job,
                created_by=user,
                work_date=date(2025, 6, 15),
                status=bad_status,
                ewo_type=ExtraWorkOrder.EwoType.TM,
                description='Test',
                labor_ohp_pct=Decimal('0.1500'),
                equip_mat_ohp_pct=Decimal('0.1500'),
                bond_pct=Decimal('0.0100'),
                bond_required=False,
            )
            baker.make(
                LaborLine,
                ewo=ewo,
                trade_classification=trade,
                labor_type=LaborLine.LaborType.GENERIC,
                reg_hours=Decimal('8.0'),
                ot_hours=Decimal('0.0'),
                dt_hours=Decimal('0.0'),
            )
            with pytest.raises(ValidationError):
                submit_ewo(ewo)

    def test_rejected_ewo_cannot_be_submitted(self):
        """Rejected EWOs revert to open before resubmission — not submitted directly."""
        ewo = self._ewo_with_labor(status=ExtraWorkOrder.Status.REJECTED)
        with pytest.raises(ValidationError):
            submit_ewo(ewo)

    @freeze_time('2025-06-15 14:30:00')
    def test_submit_empty_ewo_produces_zero_total(self):
        """EWO with no lines can be submitted; total will be zero."""
        ewo = make_open_ewo()
        result = submit_ewo(ewo)
        result.refresh_from_db()
        assert result.status == ExtraWorkOrder.Status.SUBMITTED
        assert result.total == Decimal('0.00')


class EwoApiTests(APITestCase):
    def setUp(self):
        self.user = baker.make(User)
        self.job = baker.make(Job, job_number='1886', name='Mainline Sewer')
        self.trade = make_trade(name='Operator-api')
        self.employee = baker.make(
            'resources.Employee',
            code='EMP-1',
            full_name='Alice Operator',
            trade_classification=self.trade,
        )
        schedule = make_schedule(date(2025, 1, 1), date(2025, 12, 31), year='2025-2026')
        rate_line = make_rate_line(schedule, class_code='AA', make_code='CAT', model_code='D8')
        self.equipment_type = baker.make('resources.EquipmentType', name='Dozer', caltrans_rate_line=rate_line)
        self.catalog_item = baker.make(
            'resources.MaterialCatalog',
            description='Pipe',
            default_unit='LF',
        )
        self.ewo = baker.make(
            ExtraWorkOrder,
            job=self.job,
            created_by=self.user,
            work_date=date(2025, 6, 15),
            status=ExtraWorkOrder.Status.OPEN,
            ewo_type=ExtraWorkOrder.EwoType.TM,
            description='Open trench repair',
        )
        self.locked_ewo = baker.make(
            ExtraWorkOrder,
            job=self.job,
            created_by=self.user,
            work_date=date(2025, 6, 16),
            status=ExtraWorkOrder.Status.SUBMITTED,
            ewo_type=ExtraWorkOrder.EwoType.TM,
            description='Locked repair',
        )

    def test_ewo_list(self):
        response = self.client.get('/api/ewo/ewos/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

    def test_create_ewo(self):
        payload = {
            'job': self.job.pk,
            'created_by': self.user.pk,
            'ewo_type': ExtraWorkOrder.EwoType.CHANGE_ORDER,
            'work_date': '2025-06-20',
            'description': 'Bypass line reroute',
            'bond_required': True,
        }

        response = self.client.post('/api/ewo/ewos/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        body = response.json()
        self.assertTrue(body['ewo_number'].startswith('1886-'))
        self.assertEqual(body['status'], ExtraWorkOrder.Status.OPEN)

    def test_patch_open_ewo(self):
        response = self.client.patch(
            f'/api/ewo/ewos/{self.ewo.pk}/',
            {'description': 'Updated trench repair'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ewo.refresh_from_db()
        self.assertEqual(self.ewo.description, 'Updated trench repair')

    def test_patch_ewo_cannot_change_job_after_number_assignment(self):
        other_job = baker.make(Job, job_number='1999', name='Other Job')

        response = self.client.patch(
            f'/api/ewo/ewos/{self.ewo.pk}/',
            {'job': other_job.pk},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('job', response.json())
        self.ewo.refresh_from_db()
        self.assertEqual(self.ewo.job_id, self.job.pk)

    def test_patch_locked_ewo_is_rejected(self):
        response = self.client.patch(
            f'/api/ewo/ewos/{self.locked_ewo.pk}/',
            {'description': 'Should fail'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Locked EWOs', str(response.json()))

    def test_delete_locked_ewo_is_rejected(self):
        response = self.client.delete(f'/api/ewo/ewos/{self.locked_ewo.pk}/')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_labor_line(self):
        payload = {
            'ewo': self.ewo.pk,
            'labor_type': LaborLine.LaborType.NAMED,
            'employee': self.employee.pk,
            'trade_classification': self.trade.pk,
            'reg_hours': '8.0',
            'ot_hours': '1.0',
            'dt_hours': '0.0',
        }

        response = self.client.post('/api/ewo/labor-lines/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        line = LaborLine.objects.get(pk=response.json()['id'])
        self.assertEqual(line.employee_default_trade_id, self.trade.pk)

    def test_create_named_labor_override_requires_reason(self):
        other_trade = baker.make(
            TradeClassification,
            name='Laborer',
            union_name='LIUNA Local 777',
            union_abbrev='LIUNA',
        )
        payload = {
            'ewo': self.ewo.pk,
            'labor_type': LaborLine.LaborType.NAMED,
            'employee': self.employee.pk,
            'trade_classification': other_trade.pk,
            'reg_hours': '8.0',
            'ot_hours': '0.0',
            'dt_hours': '0.0',
        }

        response = self.client.post('/api/ewo/labor-lines/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('trade_override_reason', str(response.json()))

    def test_create_generic_labor_line_rejects_employee(self):
        payload = {
            'ewo': self.ewo.pk,
            'labor_type': LaborLine.LaborType.GENERIC,
            'employee': self.employee.pk,
            'trade_classification': self.trade.pk,
            'reg_hours': '8.0',
            'ot_hours': '0.0',
            'dt_hours': '0.0',
        }

        response = self.client.post('/api/ewo/labor-lines/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('employee', response.json())

    def test_create_equipment_line(self):
        payload = {
            'ewo': self.ewo.pk,
            'equipment_type': self.equipment_type.pk,
            'usage_type': EquipmentLine.UsageType.OPERATING,
            'hours': '4.0',
            'unit': 'HR',
        }

        response = self.client.post('/api/ewo/equipment-lines/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(EquipmentLine.objects.count(), 1)

    def test_create_material_line(self):
        payload = {
            'ewo': self.ewo.pk,
            'catalog_item': self.catalog_item.pk,
            'description': 'Pipe',
            'quantity': '10.000',
            'unit': 'LF',
            'unit_cost': '12.50',
            'is_subcontractor': False,
            'reference_number': 'INV-100',
        }

        response = self.client.post('/api/ewo/material-lines/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MaterialLine.objects.count(), 1)

    def test_line_list_can_filter_by_ewo(self):
        baker.make(
            LaborLine,
            ewo=self.ewo,
            labor_type=LaborLine.LaborType.GENERIC,
            trade_classification=self.trade,
            reg_hours=Decimal('8.0'),
            ot_hours=Decimal('0.0'),
            dt_hours=Decimal('0.0'),
        )
        baker.make(
            LaborLine,
            ewo=self.locked_ewo,
            labor_type=LaborLine.LaborType.GENERIC,
            trade_classification=self.trade,
            reg_hours=Decimal('4.0'),
            ot_hours=Decimal('0.0'),
            dt_hours=Decimal('0.0'),
        )

        response = self.client.get(f'/api/ewo/labor-lines/?ewo={self.ewo.pk}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['ewo'], self.ewo.pk)

    def test_locked_ewo_blocks_line_creation(self):
        payload = {
            'ewo': self.locked_ewo.pk,
            'equipment_type': self.equipment_type.pk,
            'usage_type': EquipmentLine.UsageType.OPERATING,
            'hours': '4.0',
            'unit': 'HR',
        }

        response = self.client.post('/api/ewo/equipment-lines/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('locked EWOs', str(response.json()))

    def test_locked_ewo_blocks_line_patch_even_if_payload_points_to_open_ewo(self):
        line = baker.make(
            LaborLine,
            ewo=self.locked_ewo,
            labor_type=LaborLine.LaborType.GENERIC,
            trade_classification=self.trade,
            reg_hours=Decimal('4.0'),
            ot_hours=Decimal('0.0'),
            dt_hours=Decimal('0.0'),
        )

        response = self.client.patch(
            f'/api/ewo/labor-lines/{line.pk}/',
            {'ewo': self.ewo.pk, 'reg_hours': '6.0'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        line.refresh_from_db()
        self.assertEqual(line.ewo_id, self.locked_ewo.pk)
        self.assertEqual(line.reg_hours, Decimal('4.0'))

    def test_locked_ewo_blocks_line_delete(self):
        line = baker.make(
            MaterialLine,
            ewo=self.locked_ewo,
            description='Pipe',
            quantity=Decimal('1.000'),
            unit='LS',
            unit_cost=Decimal('100.00'),
        )

        response = self.client.delete(f'/api/ewo/material-lines/{line.pk}/')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
