"""Tests for chask.energy.roi — validated against hand-calculated reference values."""

import pandas as pd
import pytest

from chask.config import TOTAL_INVESTMENT_USD
from chask.energy.roi import compute_roi_scenarios, npv, payback_curves, simple_payback
from chask.pipeline.ingest import load_raw
from chask.pipeline.transform import to_analytics
from chask.pipeline.validate import validate


@pytest.fixture(scope="module")
def enriched() -> pd.DataFrame:
    return to_analytics(validate(load_raw()))


class TestNpv:
    def test_zero_flows_returns_negative_investment(self):
        cfs = [-10_000.0, 0.0, 0.0, 0.0]
        result = npv(cfs, discount_rate=0.10)
        assert abs(result - (-10_000.0)) < 1e-6

    def test_hand_calculated_single_year(self):
        # -1000 + 1100/1.1 = -1000 + 1000 = 0
        result = npv([-1_000.0, 1_100.0], discount_rate=0.10)
        assert abs(result) < 1e-6

    def test_positive_npv_high_returns(self):
        cfs = [-100.0] + [50.0] * 5
        result = npv(cfs, discount_rate=0.10)
        assert result > 0

    def test_annuity_5yr_hand_calculation(self):
        # PV factor 5yr @ 10% = 3.7908; NPV = 1000×3.7908 - 3000 = 790.8
        result = npv([-3_000.0] + [1_000.0] * 5, discount_rate=0.10)
        assert abs(result - 790.8) < 1.0


class TestSimplePayback:
    def test_basic_payback(self):
        assert abs(simple_payback(10_000.0, 85_000.0) - 8.5) < 0.01

    def test_zero_benefit_returns_inf(self):
        assert simple_payback(0.0) == float("inf")

    def test_negative_benefit_returns_inf(self):
        assert simple_payback(-500.0) == float("inf")


class TestComputeRoiScenarios:
    def test_returns_dataframe(self, enriched):
        result = compute_roi_scenarios(enriched)
        assert isinstance(result, pd.DataFrame)

    def test_has_three_scenarios(self, enriched):
        result = compute_roi_scenarios(enriched)
        assert len(result) == 3

    def test_expected_scenario_names(self, enriched):
        result = compute_roi_scenarios(enriched)
        assert set(result["scenario"]) == {"Conservative", "Base", "Optimistic"}

    def test_annual_benefits_ordered(self, enriched):
        # Optimistic > Base > Conservative
        result = compute_roi_scenarios(enriched).set_index("scenario")
        assert (
            result.loc["Optimistic", "annual_benefit_usd"]
            > result.loc["Base", "annual_benefit_usd"]
            > result.loc["Conservative", "annual_benefit_usd"]
        )

    def test_payback_ordered(self, enriched):
        # Conservative has longest payback
        result = compute_roi_scenarios(enriched).set_index("scenario")
        assert result.loc["Conservative", "payback_years"] > result.loc["Base", "payback_years"]

    def test_conservative_npv_negative(self, enriched):
        # Honest finding: energy alone doesn't justify investment at 10% / 5yr
        result = compute_roi_scenarios(enriched).set_index("scenario")
        assert result.loc["Conservative", "npv_5yr_usd"] < 0

    def test_optimistic_npv_positive(self, enriched):
        # With full capacity utilization the investment is justified
        result = compute_roi_scenarios(enriched).set_index("scenario")
        assert result.loc["Optimistic", "npv_5yr_usd"] > 0

    def test_conservative_annual_benefit_plausible(self, enriched):
        # Energy savings alone: ~$9,000–15,000/yr + downtime reduction
        result = compute_roi_scenarios(enriched).set_index("scenario")
        ben = result.loc["Conservative", "annual_benefit_usd"]
        assert 6_000 < ben < 25_000


class TestPaybackCurves:
    def test_returns_dataframe(self, enriched):
        result = payback_curves(enriched)
        assert isinstance(result, pd.DataFrame)

    def test_has_year_column(self, enriched):
        result = payback_curves(enriched)
        assert "year" in result.columns

    def test_year_0_is_negative_investment(self, enriched):
        result = payback_curves(enriched)
        for col in ("Conservative", "Base", "Optimistic"):
            assert result.loc[result["year"] == 0, col].iloc[0] == pytest.approx(
                -TOTAL_INVESTMENT_USD
            )

    def test_optimistic_ends_above_zero(self, enriched):
        from chask.energy.roi import PROJECTION_YEARS

        result = payback_curves(enriched)
        last = result[result["year"] == PROJECTION_YEARS]["Optimistic"].iloc[0]
        assert last > 0
