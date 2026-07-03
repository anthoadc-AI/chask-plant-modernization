"""Tests for chask.energy.kpis."""

import pandas as pd
import pytest

from chask.energy.kpis import annualized_savings, energy_intensity_rolling, monthly_savings
from chask.pipeline.ingest import load_raw
from chask.pipeline.transform import to_analytics
from chask.pipeline.validate import validate


@pytest.fixture(scope="module")
def enriched() -> pd.DataFrame:
    return to_analytics(validate(load_raw()))


class TestEnergyIntensityRolling:
    def test_adds_intensity_rolling_column(self, enriched):
        result = energy_intensity_rolling(enriched)
        assert "intensity_rolling" in result.columns

    def test_rolling_has_no_nulls(self, enriched):
        result = energy_intensity_rolling(enriched)
        assert result["intensity_rolling"].isnull().sum() == 0

    def test_rolling_is_smoothed(self, enriched):
        result = energy_intensity_rolling(enriched)
        # Rolling std should be ≤ raw std (smoothing reduces variance)
        assert result["intensity_rolling"].std() <= result["intensity_kwh_kg"].std()

    def test_row_count_preserved(self, enriched):
        result = energy_intensity_rolling(enriched)
        assert len(result) == len(enriched)

    def test_first_row_equals_raw(self, enriched):
        # With min_periods=1, first rolling value = first raw value
        result = energy_intensity_rolling(enriched)
        first_roll = result["intensity_rolling"].iloc[0]
        first_raw = enriched["intensity_kwh_kg"].iloc[0]
        assert abs(first_roll - first_raw) < 1e-9


class TestMonthlySavings:
    def test_adds_required_columns(self, enriched):
        result = monthly_savings(enriched)
        for col in ("baseline_kwh", "savings_kwh", "savings_usd", "co2_avoided_kg"):
            assert col in result.columns

    def test_baseline_is_constant(self, enriched):
        result = monthly_savings(enriched)
        assert result["baseline_kwh"].nunique() == 1

    def test_post_period_has_positive_savings(self, enriched):
        result = monthly_savings(enriched)
        post = result[result["period"] == "post"]
        assert post["savings_kwh"].mean() > 0

    def test_co2_never_negative(self, enriched):
        result = monthly_savings(enriched)
        assert (result["co2_avoided_kg"] >= 0).all()

    def test_savings_usd_proportional_to_kwh(self, enriched):
        result = monthly_savings(enriched)
        # savings_usd ≈ savings_kwh × tariff; check ratio is consistent
        non_zero = result[result["savings_kwh"] != 0]
        ratio = non_zero["savings_usd"] / non_zero["savings_kwh"]
        assert ratio.std() < 1e-9  # constant ratio = tariff


class TestAnnualizedSavings:
    def test_returns_dict(self, enriched):
        result = annualized_savings(enriched)
        assert isinstance(result, dict)

    def test_has_required_keys(self, enriched):
        result = annualized_savings(enriched)
        for key in (
            "baseline_kwh_mo",
            "post_mean_kwh_mo",
            "ss_mean_kwh_mo",
            "ss_savings_kwh_yr",
            "ss_savings_usd_yr",
            "ss_co2_avoided_kg_yr",
        ):
            assert key in result

    def test_ss_savings_positive(self, enriched):
        # Steady-state consumes less than baseline → positive savings
        result = annualized_savings(enriched)
        assert result["ss_savings_kwh_yr"] > 0
        assert result["ss_savings_usd_yr"] > 0

    def test_co2_savings_positive(self, enriched):
        result = annualized_savings(enriched)
        assert result["ss_co2_avoided_kg_yr"] > 0

    def test_ss_mean_less_than_baseline(self, enriched):
        result = annualized_savings(enriched)
        assert result["ss_mean_kwh_mo"] < result["baseline_kwh_mo"]

    def test_annual_savings_roughly_correct(self, enriched):
        # Hand-check: ~11,765 kWh/mo × 12 × 0.065 ≈ $9,177/yr
        result = annualized_savings(enriched)
        assert 8_000 < result["ss_savings_usd_yr"] < 14_000
