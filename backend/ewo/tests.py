"""
Tests for ewo/services.py — the single currency calculation boundary.

Coverage strategy (post Phase 2)
--------------------------------
- get_labor_rate           : precedence, no-rate error
- get_equipment_rates      : rates-from-EquipmentType, null CT FK, no-rates error
- calculate_labor_line     : per-time-type ROUND_UP, snapshot fields, saves
- calculate_equipment_line : qty × (reg + ot + standby), snapshot fields
- calculate_material_line  : ROUND_UP, catalog stats update, no-catalog path
- calculate_workday_totals : per-day OH&P, fuel, bond math (DEC-064, chain B)
- calculate_ewo_totals     : rollup across WorkDays, writes to EWO
- submit_ewo               : open→submitted transition, timestamp, non-open rejection

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

from ewo.models import EquipmentLine, ExtraWorkOrder, LaborLine, MaterialLine, WorkDay
from ewo.services import (
    calculate_equipment_line,
    calculate_ewo_totals,
    calculate_labor_line,
    calculate_material_line,
    calculate_workday_totals,
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
                   rental_rate='100.00', rw_delay_factor='0.5000', ot_factor='0.7500'):
    """
    Create a CaltransRateLine with factor-based fields (DEC-059).
    Defaults: rental_rate=$100/hr, standby rate = $50/hr, OT rate = $75/hr.
    """
    if schedule is None:
        schedule = make_schedule(date(2025, 1, 1), date(2025, 12, 31))
    return baker.make(
        CaltransRateLine,
        schedule=schedule,
        class_code=class_code,
        make_code=make_code,
        model_code=model_code,
        rental_rate=Decimal(rental_rate),
        rw_delay_factor=Decimal(rw_delay_factor),
        ot_factor=Decimal(ot_factor),
        unit='HR',
    )


def make_equip_type(rate_line=None, fuel_eligible=True, **overrides):
    """
    Create an EquipmentType with its own rates populated (DEC-060).
    Rates default to rate_line.rental_rate × factors so the EquipmentType
    bills identically to the Caltrans row it references.
    """
    if rate_line is None:
        rate_line = make_rate_line()
    defaults = {
        'caltrans_rate_line': rate_line,
        'ct_match_quality': EquipmentType.CtMatchQuality.EXACT,
        'rate_reg': rate_line.rental_rate,
        'rate_ot': rate_line.rental_rate * rate_line.ot_factor,
        'rate_standby': rate_line.rental_rate * rate_line.rw_delay_factor,
        'fuel_surcharge_eligible': fuel_eligible,
    }
    defaults.update(overrides)
    return baker.make(EquipmentType, **defaults)


def make_open_ewo(**kwargs):
    """Create a minimal open EWO against a fresh job + user."""
    job_kwargs = {}
    for jk in ('job_number', 'name'):
        if jk in kwargs:
            job_kwargs[jk] = kwargs.pop(jk)
    job_kwargs.setdefault('job_number', '1886')
    job_kwargs.setdefault('name', 'Test Job')
    job = baker.make(Job, **job_kwargs)
    user = baker.make(User)
    defaults = {
        'job': job,
        'created_by': user,
        'status': ExtraWorkOrder.Status.OPEN,
        'ewo_type': ExtraWorkOrder.EwoType.TM,
        'description': 'Test EWO',
        'labor_ohp_pct': Decimal('0.1500'),
        'equip_mat_ohp_pct': Decimal('0.1500'),
        'bond_pct': Decimal('0.0150'),
        'fuel_surcharge_pct': Decimal('0.0000'),
        'bond_required': False,
    }
    defaults.update(kwargs)
    return baker.make(ExtraWorkOrder, **defaults)


def make_work_day(ewo, work_date=None, **kwargs):
    """Create a WorkDay under the given EWO."""
    defaults = {
        'ewo': ewo,
        'work_date': work_date or date(2025, 6, 15),
    }
    defaults.update(kwargs)
    return baker.make(WorkDay, **defaults)


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
        trade = make_trade()
        rate = make_labor_rate(trade, date(2025, 6, 15))
        result = get_labor_rate(trade, date(2025, 6, 15))
        assert result == rate

    def test_does_not_return_future_rate(self):
        trade = make_trade()
        make_labor_rate(trade, date(2025, 7, 1))
        with pytest.raises(ValueError, match='No labor rate found'):
            get_labor_rate(trade, date(2025, 6, 15))

    def test_raises_when_no_rate_for_trade(self):
        trade = make_trade()
        with pytest.raises(ValueError, match='No labor rate found'):
            get_labor_rate(trade, date(2025, 6, 15))


# ─── get_equipment_rates ───────────────────────────────────────────────────────


@pytest.mark.django_db
class TestGetEquipmentRates:
    def test_returns_rates_from_equipment_type(self):
        equip_type = make_equip_type()  # rental 100, rw 0.5, ot 0.75
        equip_type.refresh_from_db()
        rate_reg, rate_ot, rate_standby, _ = get_equipment_rates(
            equip_type, date(2025, 6, 15)
        )
        assert rate_reg == Decimal('100.00')
        assert rate_ot == Decimal('75.00')
        assert rate_standby == Decimal('50.00')

    def test_returns_caltrans_fk_when_linked(self):
        equip_type = make_equip_type()
        _, _, _, ct_line = get_equipment_rates(equip_type, date(2025, 6, 15))
        assert ct_line == equip_type.caltrans_rate_line

    def test_works_when_caltrans_rate_line_is_null(self):
        equip_type = baker.make(
            EquipmentType,
            name='In-house grader',
            caltrans_rate_line=None,
            ct_match_quality=EquipmentType.CtMatchQuality.FMV,
            rate_reg=Decimal('80.00'),
            rate_ot=Decimal('60.00'),
            rate_standby=Decimal('20.00'),
        )
        rate_reg, _, _, ct_line = get_equipment_rates(equip_type, date(2025, 6, 15))
        assert rate_reg == Decimal('80.00')
        assert ct_line is None

    def test_raises_when_equip_type_has_no_rates(self):
        equip_type = baker.make(
            EquipmentType,
            name='Unrated',
            caltrans_rate_line=None,
            rate_reg=Decimal('0'),
            rate_ot=Decimal('0'),
            rate_standby=Decimal('0'),
        )
        with pytest.raises(ValueError, match='no rates configured'):
            get_equipment_rates(equip_type, date(2025, 6, 15))


# ─── calculate_labor_line ──────────────────────────────────────────────────────


@pytest.mark.django_db
class TestCalculateLaborLine:
    def _setup(self, work_date=date(2025, 6, 15)):
        trade = make_trade()
        make_labor_rate(trade, date(2025, 1, 1),
                        rate_reg='50.00', rate_ot='75.00', rate_dt='100.00')
        ewo = make_open_ewo()
        wd = make_work_day(ewo, work_date=work_date)
        line = baker.make(
            LaborLine,
            work_day=wd,
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
        assert total == Decimal('550.00')  # 8*50 + 2*75

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
        trade = make_trade(name='Laborer')
        make_labor_rate(trade, date(2025, 1, 1),
                        rate_reg='33.33', rate_ot='33.33', rate_dt='33.33')
        ewo = make_open_ewo()
        wd = make_work_day(ewo)
        line = baker.make(
            LaborLine,
            work_day=wd,
            trade_classification=trade,
            labor_type=LaborLine.LaborType.GENERIC,
            reg_hours=Decimal('1.5'),
            ot_hours=Decimal('0.5'),
            dt_hours=Decimal('0.5'),
        )
        total = calculate_labor_line(line)
        # 49.995→50.00, 16.665→16.67, 16.665→16.67 = 83.34
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
    """
    Defaults from make_equip_type: rate_reg=100, rate_ot=75, rate_standby=50.
    line_total = qty × (reg_hrs × rate_reg + ot_hrs × rate_ot + standby_hrs × rate_standby)
    """

    def _setup(self, qty=1, reg_hours='8.0', ot_hours='0.0', standby_hours='0.0',
               work_date=date(2025, 6, 15)):
        rate_line = make_rate_line(make_schedule(date(2025, 1, 1), date(2025, 12, 31)))
        equip_type = make_equip_type(rate_line)
        ewo = make_open_ewo()
        wd = make_work_day(ewo, work_date=work_date)
        line = baker.make(
            EquipmentLine,
            work_day=wd,
            equipment_type=equip_type,
            qty=qty,
            reg_hours=Decimal(reg_hours),
            ot_hours=Decimal(ot_hours),
            standby_hours=Decimal(standby_hours),
        )
        return line, rate_line

    def test_reg_only_single_unit(self):
        line, _ = self._setup()  # 1 unit × 8h @ 100 = 800
        total = calculate_equipment_line(line)
        assert total == Decimal('800.00')

    def test_standby_only(self):
        line, _ = self._setup(reg_hours='0.0', standby_hours='8.0')
        total = calculate_equipment_line(line)
        assert total == Decimal('400.00')  # 8 × 50

    def test_ot_only(self):
        line, _ = self._setup(reg_hours='0.0', ot_hours='8.0')
        total = calculate_equipment_line(line)
        assert total == Decimal('600.00')  # 8 × 75

    def test_qty_multiplier(self):
        line, _ = self._setup(qty=3)  # 3 × 8h × 100 = 2400
        total = calculate_equipment_line(line)
        assert total == Decimal('2400.00')

    def test_mixed_hours_per_unit_then_qty(self):
        line, _ = self._setup(qty=2, reg_hours='4.0', ot_hours='2.0', standby_hours='1.0')
        # per-unit: 4×100 + 2×75 + 1×50 = 400 + 150 + 50 = 600
        # total  : 2 × 600 = 1200
        total = calculate_equipment_line(line)
        assert total == Decimal('1200.00')

    def test_snapshots_all_three_rate_components(self):
        line, _ = self._setup()
        calculate_equipment_line(line)
        line.refresh_from_db()
        assert line.rental_rate_snapshot == Decimal('100.00')
        assert line.rw_delay_rate_snapshot == Decimal('50.00')
        assert line.ot_rate_snapshot == Decimal('75.00')

    def test_caltrans_rate_line_fk_set_on_line(self):
        line, rate_line = self._setup()
        calculate_equipment_line(line)
        line.refresh_from_db()
        assert line.caltrans_rate_line_id == rate_line.pk

    def test_caltrans_fk_null_on_line_when_equipment_type_has_no_ct_link(self):
        equip_type = baker.make(
            EquipmentType,
            name='In-house pump',
            caltrans_rate_line=None,
            ct_match_quality=EquipmentType.CtMatchQuality.FMV,
            rate_reg=Decimal('25.00'),
            rate_ot=Decimal('18.00'),
            rate_standby=Decimal('5.00'),
        )
        ewo = make_open_ewo()
        wd = make_work_day(ewo)
        line = baker.make(
            EquipmentLine,
            work_day=wd,
            equipment_type=equip_type,
            qty=1,
            reg_hours=Decimal('8.0'),
        )
        calculate_equipment_line(line)
        line.refresh_from_db()
        assert line.caltrans_rate_line_id is None
        assert line.rental_rate_snapshot == Decimal('25.00')
        assert line.line_total == Decimal('200.00')

    def test_round_up_applied_to_per_unit_subtotal(self):
        """2.5 hr × 33.33 = 83.325 → ROUND_UP → 83.33 (per unit)."""
        rate_line = make_rate_line(
            make_schedule(date(2025, 1, 1), date(2025, 12, 31)),
            rental_rate='33.33',
        )
        equip_type = make_equip_type(rate_line, rate_reg=Decimal('33.33'))
        ewo = make_open_ewo()
        wd = make_work_day(ewo)
        line = baker.make(
            EquipmentLine,
            work_day=wd,
            equipment_type=equip_type,
            qty=1,
            reg_hours=Decimal('2.5'),
        )
        total = calculate_equipment_line(line)
        assert total == Decimal('83.33')


# ─── calculate_material_line ───────────────────────────────────────────────────


@pytest.mark.django_db
class TestCalculateMaterialLine:
    def _new_work_day(self):
        ewo = make_open_ewo()
        return make_work_day(ewo)

    def test_calculates_quantity_times_unit_cost(self):
        wd = self._new_work_day()
        line = baker.make(
            MaterialLine,
            work_day=wd,
            description='PVC Pipe 6"',
            quantity=Decimal('10.000'),
            unit='LF',
            unit_cost=Decimal('12.50'),
        )
        total = calculate_material_line(line)
        assert total == Decimal('125.00')

    def test_round_up_applied(self):
        wd = self._new_work_day()
        line = baker.make(
            MaterialLine,
            work_day=wd,
            description='Widget',
            quantity=Decimal('3.333'),
            unit='EA',
            unit_cost=Decimal('3.33'),
        )
        total = calculate_material_line(line)
        assert total == Decimal('11.10')

    def test_saves_line_total_to_db(self):
        wd = self._new_work_day()
        line = baker.make(
            MaterialLine,
            work_day=wd,
            description='Gasket',
            quantity=Decimal('5.000'),
            unit='EA',
            unit_cost=Decimal('2.00'),
        )
        calculate_material_line(line)
        line.refresh_from_db()
        assert line.line_total == Decimal('10.00')

    def test_updates_catalog_stats_when_catalog_item_set(self):
        ewo = make_open_ewo()
        wd = make_work_day(ewo, work_date=date(2025, 6, 15))
        catalog = baker.make(
            MaterialCatalog,
            description='Unique Catalog Item',
            default_unit='LF',
            use_count=3,
        )
        line = baker.make(
            MaterialLine,
            work_day=wd,
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
        wd = self._new_work_day()
        line = baker.make(
            MaterialLine,
            work_day=wd,
            catalog_item=None,
            description='Ad-hoc material',
            quantity=Decimal('1.000'),
            unit='LS',
            unit_cost=Decimal('500.00'),
        )
        total = calculate_material_line(line)
        assert total == Decimal('500.00')

    def test_lump_sum_quantity_one(self):
        wd = self._new_work_day()
        line = baker.make(
            MaterialLine,
            work_day=wd,
            description='Mobilization',
            quantity=Decimal('1.000'),
            unit='LS',
            unit_cost=Decimal('1500.00'),
        )
        total = calculate_material_line(line)
        assert total == Decimal('1500.00')


# ─── calculate_workday_totals / calculate_ewo_totals ──────────────────────────


@pytest.mark.django_db
class TestCalculateWorkDayAndEwoTotals:
    """
    Chain B (DEC-062): fuel enters the Equipment+Materials OH&P base.

    Example shape used below (one WorkDay):
      Labor: 8 reg @ $50  = $400.00
      Equip: 4 reg @ $100 = $400.00 (fuel-eligible)
      Mat  : 10 LF @ $10  = $100.00
      pct  : labor_ohp 15%, equip_mat_ohp 15%, bond 1% or 1.5%
    """

    def _full_day(self, ewo, fuel_eligible=True):
        trade = make_trade()
        make_labor_rate(trade, date(2025, 1, 1),
                        rate_reg='50.00', rate_ot='75.00', rate_dt='100.00')
        rate_line = make_rate_line(
            make_schedule(date(2025, 1, 1), date(2025, 12, 31)),
            rental_rate='100.00',
        )
        equip_type = make_equip_type(rate_line, fuel_eligible=fuel_eligible)

        wd = make_work_day(ewo, work_date=date(2025, 6, 15))
        baker.make(
            LaborLine,
            work_day=wd,
            trade_classification=trade,
            labor_type=LaborLine.LaborType.GENERIC,
            reg_hours=Decimal('8.0'),
            ot_hours=Decimal('0.0'),
            dt_hours=Decimal('0.0'),
        )
        baker.make(
            EquipmentLine,
            work_day=wd,
            equipment_type=equip_type,
            qty=1,
            reg_hours=Decimal('4.0'),
        )
        baker.make(
            MaterialLine,
            work_day=wd,
            description='Test pipe',
            quantity=Decimal('10.000'),
            unit='LF',
            unit_cost=Decimal('10.00'),
            catalog_item=None,
        )
        return wd

    def test_workday_totals_no_fuel_no_bond(self):
        ewo = make_open_ewo(
            labor_ohp_pct=Decimal('0.1500'),
            equip_mat_ohp_pct=Decimal('0.1500'),
            fuel_surcharge_pct=Decimal('0.0000'),
            bond_required=False,
        )
        wd = self._full_day(ewo)
        result = calculate_workday_totals(wd)

        # labor 400 ; labor OH&P 60
        assert result['labor_subtotal'] == Decimal('400.00')
        assert result['labor_ohp_amount'] == Decimal('60.00')
        # equip 400 + mat 100 + fuel 0 = 500 ; OH&P 75
        assert result['equip_subtotal'] == Decimal('400.00')
        assert result['material_subtotal'] == Decimal('100.00')
        assert result['fuel_amount'] == Decimal('0.00')
        assert result['equip_mat_ohp_amount'] == Decimal('75.00')
        assert result['bond_amount'] == Decimal('0.00')
        assert result['day_total'] == Decimal('1035.00')

    def test_workday_totals_with_fuel_chain_b(self):
        """Chain B: fuel (DEC-062) rolls into the equip+mat OH&P base."""
        ewo = make_open_ewo(
            labor_ohp_pct=Decimal('0.1500'),
            equip_mat_ohp_pct=Decimal('0.1500'),
            fuel_surcharge_pct=Decimal('0.0500'),  # 5% of fuel-eligible equip
            bond_required=False,
        )
        wd = self._full_day(ewo, fuel_eligible=True)
        result = calculate_workday_totals(wd)

        # fuel = 5% × equip_fuel_eligible ($400) = 20.00
        assert result['fuel_amount'] == Decimal('20.00')
        # equip+mat+fuel = 400 + 100 + 20 = 520 ; OH&P 78
        assert result['equip_mat_ohp_amount'] == Decimal('78.00')
        # labor 400 + labor OH&P 60 + 520 + 78 + 0 = 1058
        assert result['day_total'] == Decimal('1058.00')

    def test_workday_totals_fuel_ineligible_equipment_contributes_nothing_to_fuel(self):
        ewo = make_open_ewo(
            fuel_surcharge_pct=Decimal('0.0500'),
        )
        wd = self._full_day(ewo, fuel_eligible=False)
        result = calculate_workday_totals(wd)
        assert result['fuel_amount'] == Decimal('0.00')

    def test_workday_totals_with_bond(self):
        ewo = make_open_ewo(
            bond_pct=Decimal('0.0150'),
            bond_required=True,
        )
        wd = self._full_day(ewo)
        result = calculate_workday_totals(wd)
        # Subtotal before bond = 1035.00 (same as no-fuel case)
        # Bond = 1035.00 × 0.015 = 15.525 → ROUND_UP → 15.53
        assert result['bond_amount'] == Decimal('15.53')
        assert result['day_total'] == Decimal('1050.53')

    def test_ewo_rollup_sums_workdays(self):
        """EWO totals = Σ WorkDay totals (DEC-064)."""
        ewo = make_open_ewo(bond_required=False)
        self._full_day(ewo)  # day 1
        # second day with slightly different lines
        trade = TradeClassification.objects.first()
        rate_line = CaltransRateLine.objects.first()
        equip_type = EquipmentType.objects.first()
        wd2 = make_work_day(ewo, work_date=date(2025, 6, 16))
        baker.make(
            LaborLine,
            work_day=wd2,
            trade_classification=trade,
            labor_type=LaborLine.LaborType.GENERIC,
            reg_hours=Decimal('4.0'),
            ot_hours=Decimal('0.0'),
            dt_hours=Decimal('0.0'),
        )

        result = calculate_ewo_totals(ewo)
        ewo.refresh_from_db()
        # day 1 labor 400 + day 2 labor 200 = 600
        assert result['labor_subtotal'] == Decimal('600.00')
        assert ewo.labor_subtotal == Decimal('600.00')

    def test_empty_ewo_totals_zero(self):
        ewo = make_open_ewo()
        result = calculate_ewo_totals(ewo)
        assert result['total'] == Decimal('0.00')
        assert result['fuel_subtotal'] == Decimal('0.00')

    def test_calculate_ewo_totals_does_not_change_status(self):
        ewo = make_open_ewo()
        self._full_day(ewo)
        calculate_ewo_totals(ewo)
        ewo.refresh_from_db()
        assert ewo.status == ExtraWorkOrder.Status.OPEN


# ─── submit_ewo ────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestSubmitEwo:
    def _ewo_with_labor(self, ewo_status=ExtraWorkOrder.Status.OPEN):
        trade = make_trade()
        make_labor_rate(trade, date(2025, 1, 1))
        ewo = make_open_ewo(status=ewo_status)
        wd = make_work_day(ewo, work_date=date(2025, 6, 15))
        baker.make(
            LaborLine,
            work_day=wd,
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
        assert result.total is not None
        assert result.total > Decimal('0.00')

    def test_raises_if_not_open(self):
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
                status=bad_status,
                ewo_type=ExtraWorkOrder.EwoType.TM,
                description='Test',
                labor_ohp_pct=Decimal('0.1500'),
                equip_mat_ohp_pct=Decimal('0.1500'),
                bond_pct=Decimal('0.0150'),
                fuel_surcharge_pct=Decimal('0.0000'),
                bond_required=False,
            )
            wd = make_work_day(ewo, work_date=date(2025, 6, 15))
            baker.make(
                LaborLine,
                work_day=wd,
                trade_classification=trade,
                labor_type=LaborLine.LaborType.GENERIC,
                reg_hours=Decimal('8.0'),
                ot_hours=Decimal('0.0'),
                dt_hours=Decimal('0.0'),
            )
            with pytest.raises(ValidationError):
                submit_ewo(ewo)

    def test_rejected_ewo_cannot_be_submitted(self):
        ewo = self._ewo_with_labor(ewo_status=ExtraWorkOrder.Status.REJECTED)
        with pytest.raises(ValidationError):
            submit_ewo(ewo)

    @freeze_time('2025-06-15 14:30:00')
    def test_submit_empty_ewo_produces_zero_total(self):
        ewo = make_open_ewo()
        result = submit_ewo(ewo)
        result.refresh_from_db()
        assert result.status == ExtraWorkOrder.Status.SUBMITTED
        assert result.total == Decimal('0.00')


# ─── API surface ───────────────────────────────────────────────────────────────


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
        self.equipment_type = make_equip_type(rate_line, name='Dozer')
        self.catalog_item = baker.make(
            'resources.MaterialCatalog',
            description='Pipe',
            default_unit='LF',
        )
        self.ewo = baker.make(
            ExtraWorkOrder,
            job=self.job,
            created_by=self.user,
            status=ExtraWorkOrder.Status.OPEN,
            ewo_type=ExtraWorkOrder.EwoType.TM,
            description='Open trench repair',
        )
        self.work_day = baker.make(
            WorkDay, ewo=self.ewo, work_date=date(2025, 6, 15),
        )
        self.locked_ewo = baker.make(
            ExtraWorkOrder,
            job=self.job,
            created_by=self.user,
            status=ExtraWorkOrder.Status.SUBMITTED,
            ewo_type=ExtraWorkOrder.EwoType.TM,
            description='Locked repair',
        )
        self.locked_work_day = baker.make(
            WorkDay, ewo=self.locked_ewo, work_date=date(2025, 6, 16),
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
            'description': 'Bypass line reroute',
            'bond_required': True,
        }
        response = self.client.post('/api/ewo/ewos/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        body = response.json()
        self.assertTrue(body['ewo_number'].startswith('EWO-1886-'))
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

    def test_workday_list(self):
        response = self.client.get('/api/ewo/work-days/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

    def test_workday_list_filter_by_ewo(self):
        response = self.client.get(f'/api/ewo/work-days/?ewo={self.ewo.pk}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rows = response.json()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['ewo'], self.ewo.pk)

    def test_create_workday(self):
        payload = {
            'ewo': self.ewo.pk,
            'work_date': '2025-06-20',
            'foreman_name': 'Larry Gregory',
            'superintendent_name': 'Mike Blough',
            'weather': 'Clear, 78°F',
            'location': 'Station 12+50 — Main St.',
        }
        response = self.client.post('/api/ewo/work-days/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cannot_create_workday_on_locked_ewo(self):
        payload = {
            'ewo': self.locked_ewo.pk,
            'work_date': '2025-07-01',
        }
        response = self.client.post('/api/ewo/work-days/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_labor_line(self):
        payload = {
            'work_day': self.work_day.pk,
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
            'work_day': self.work_day.pk,
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
            'work_day': self.work_day.pk,
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
            'work_day': self.work_day.pk,
            'equipment_type': self.equipment_type.pk,
            'qty': 1,
            'reg_hours': '4.0',
            'ot_hours': '0.0',
            'standby_hours': '0.0',
        }
        response = self.client.post('/api/ewo/equipment-lines/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(EquipmentLine.objects.count(), 1)

    def test_create_material_line(self):
        payload = {
            'work_day': self.work_day.pk,
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
            work_day=self.work_day,
            labor_type=LaborLine.LaborType.GENERIC,
            trade_classification=self.trade,
            reg_hours=Decimal('8.0'),
            ot_hours=Decimal('0.0'),
            dt_hours=Decimal('0.0'),
        )
        baker.make(
            LaborLine,
            work_day=self.locked_work_day,
            labor_type=LaborLine.LaborType.GENERIC,
            trade_classification=self.trade,
            reg_hours=Decimal('4.0'),
            ot_hours=Decimal('0.0'),
            dt_hours=Decimal('0.0'),
        )

        response = self.client.get(f'/api/ewo/labor-lines/?ewo={self.ewo.pk}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['work_day'], self.work_day.pk)

    def test_line_list_can_filter_by_work_day(self):
        baker.make(
            LaborLine,
            work_day=self.work_day,
            labor_type=LaborLine.LaborType.GENERIC,
            trade_classification=self.trade,
            reg_hours=Decimal('8.0'),
            ot_hours=Decimal('0.0'),
            dt_hours=Decimal('0.0'),
        )
        response = self.client.get(f'/api/ewo/labor-lines/?work_day={self.work_day.pk}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

    def test_locked_ewo_blocks_line_creation(self):
        payload = {
            'work_day': self.locked_work_day.pk,
            'equipment_type': self.equipment_type.pk,
            'qty': 1,
            'reg_hours': '4.0',
        }
        response = self.client.post('/api/ewo/equipment-lines/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
