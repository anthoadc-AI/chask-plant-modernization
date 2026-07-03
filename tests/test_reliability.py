"""Tests for chask.process.reliability."""

import pandas as pd
import pytest

from chask.pipeline.ingest import load_raw
from chask.pipeline.transform import to_analytics
from chask.pipeline.validate import validate
from chask.process.reliability import (
    downtime_cost_monthly,
    failure_trends,
    mtbf_monthly,
    reliability_summary,
)


@pytest.fixture(scope="module")
def enriched() -> pd.DataFrame:
    return to_analytics(validate(load_raw()))


class TestMtbfMonthly:
    def test_adds_mtbf_h_column(self, enriched):
        result = mtbf_monthly(enriched)
        assert "mtbf_h" in result.columns

    def test_mtbf_positive(self, enriched):
        result = mtbf_monthly(enriched)
        assert (result["mtbf_h"] > 0).all()

    def test_no_division_by_zero(self, enriched):
        result = mtbf_monthly(enriched)
        assert result["mtbf_h"].isnull().sum() == 0

    def test_mtbf_increases_post_intervention(self, enriched):
        result = mtbf_monthly(enriched)
        pre = result[result["period"] == "pre"]["mtbf_h"].mean()
        post = result[result["period"] == "post"]["mtbf_h"].mean()
        assert post > pre


class TestDowntimeCostMonthly:
    def test_adds_required_columns(self, enriched):
        result = downtime_cost_monthly(enriched)
        assert "hourly_margin_usd" in result.columns
        assert "downtime_cost_usd" in result.columns

    def test_downtime_cost_non_negative(self, enriched):
        result = downtime_cost_monthly(enriched)
        assert (result["downtime_cost_usd"] >= 0).all()

    def test_hourly_margin_positive(self, enriched):
        result = downtime_cost_monthly(enriched)
        assert (result["hourly_margin_usd"] > 0).all()

    def test_post_downtime_cost_lower_than_pre(self, enriched):
        result = downtime_cost_monthly(enriched)
        pre_cost = result[result["period"] == "pre"]["downtime_cost_usd"].mean()
        post_cost = result[result["period"] == "post"]["downtime_cost_usd"].mean()
        assert post_cost < pre_cost


class TestFailureTrends:
    def test_returns_dataframe(self, enriched):
        result = failure_trends(enriched)
        assert isinstance(result, pd.DataFrame)

    def test_has_pre_and_ss_periods(self, enriched):
        result = failure_trends(enriched)
        assert "pre" in result.index
        assert "steady_state" in result.index

    def test_ss_fallas_lower_than_pre(self, enriched):
        result = failure_trends(enriched)
        assert result.loc["steady_state", "mean_fallas"] < result.loc["pre", "mean_fallas"]

    def test_ss_mtbf_higher_than_pre(self, enriched):
        result = failure_trends(enriched)
        assert result.loc["steady_state", "mean_mtbf_h"] > result.loc["pre", "mean_mtbf_h"]

    def test_transition_has_elevated_fallas(self, enriched):
        # Sep-Nov 2021: commissioning spike — fallas > pre mean
        result = failure_trends(enriched)
        if "transition" in result.index:
            assert result.loc["transition", "mean_fallas"] > result.loc["pre", "mean_fallas"]


class TestReliabilitySummary:
    def test_returns_dict(self, enriched):
        result = reliability_summary(enriched)
        assert isinstance(result, dict)

    def test_has_required_keys(self, enriched):
        result = reliability_summary(enriched)
        for key in (
            "pre_mean_mtbf_h",
            "ss_mean_mtbf_h",
            "mtbf_improvement_pct",
            "downtime_cost_reduction_usd_yr",
        ):
            assert key in result

    def test_mtbf_improves(self, enriched):
        result = reliability_summary(enriched)
        assert result["mtbf_improvement_pct"] > 0

    def test_downtime_cost_reduction_positive(self, enriched):
        result = reliability_summary(enriched)
        assert result["downtime_cost_reduction_usd_yr"] > 0
