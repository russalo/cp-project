"""
Tests for the resources app.

Covers the schema shifts from DEC-059/060/061/062:
  - CaltransRateLine stores factors (not rates); dollar rates are derived.
  - EquipmentType owns authoritative rate_reg / rate_ot / rate_standby.
  - caltrans_rate_line FK is nullable (28% of fleet has no CT match).
  - ct_match_quality enum tracks rate provenance.
  - fuel_surcharge_eligible flag gates equipment from the fuel pool.
"""

from datetime import date
from decimal import Decimal

import pytest
from model_bakery import baker

from resources.models import (
    CaltransRateLine,
    CaltransSchedule,
    EquipmentType,
)


@pytest.mark.django_db
class TestCaltransRateLineDerivedRates:
    """DEC-059: store factors; standby_rate and ot_rate are derived."""

    def _make_schedule(self):
        return baker.make(
            CaltransSchedule,
            schedule_year='2026-2027',
            effective_date=date(2026, 4, 1),
            expiry_date=date(2027, 3, 31),
        )

    def test_standby_rate_is_rental_times_rw_delay_factor(self):
        crl = baker.make(
            CaltransRateLine,
            schedule=self._make_schedule(),
            rental_rate=Decimal('100.00'),
            rw_delay_factor=Decimal('0.1400'),
            ot_factor=Decimal('0.8700'),
        )
        assert crl.standby_rate == Decimal('14.0000')

    def test_ot_rate_is_rental_times_ot_factor(self):
        crl = baker.make(
            CaltransRateLine,
            schedule=self._make_schedule(),
            rental_rate=Decimal('100.00'),
            rw_delay_factor=Decimal('0.1400'),
            ot_factor=Decimal('0.8700'),
        )
        assert crl.ot_rate == Decimal('87.0000')

    def test_zero_factors_produce_zero_derived_rates(self):
        """Safe sentinel: a mis-ingested row with zero factors returns zero, not garbage."""
        crl = baker.make(
            CaltransRateLine,
            schedule=self._make_schedule(),
            rental_rate=Decimal('50.00'),
        )
        # Compare numerically — Decimal equality across exponents is loose
        # (Decimal('0') == Decimal('0.00') == Decimal('0.000000') are all True),
        # but we keep the cast explicit in case someone adds rounding later.
        assert crl.standby_rate == 0
        assert crl.ot_rate == 0


@pytest.mark.django_db
class TestEquipmentTypeOwnRates:
    """DEC-060: EquipmentType owns rate_reg/rate_ot/rate_standby; CT FK is nullable provenance."""

    def test_equipment_type_without_caltrans_link_is_valid(self):
        """In-house / FMV equipment has no CT match but still bills."""
        et = baker.make(
            EquipmentType,
            name='In-house shoring rig',
            caltrans_rate_line=None,
            ct_match_quality=EquipmentType.CtMatchQuality.FMV,
            rate_reg=Decimal('75.00'),
            rate_ot=Decimal('56.25'),
            rate_standby=Decimal('10.00'),
        )
        et.full_clean()  # no validation errors
        assert et.caltrans_rate_line is None
        assert et.ct_match_quality == EquipmentType.CtMatchQuality.FMV

    def test_default_ct_match_quality_is_none(self):
        et = baker.make(EquipmentType, name='Untracked', caltrans_rate_line=None)
        assert et.ct_match_quality == EquipmentType.CtMatchQuality.NONE

    def test_fuel_surcharge_eligible_defaults_true(self):
        """Most diesel equipment is eligible; admins flip off for attachments/trailers."""
        et = baker.make(EquipmentType, name='Generic')
        assert et.fuel_surcharge_eligible is True

    def test_ct_match_quality_choices_cover_lifecycle(self):
        choices = {c[0] for c in EquipmentType.CtMatchQuality.choices}
        assert choices == {'exact', 'close', 'none', 'retired', 'fmv'}
