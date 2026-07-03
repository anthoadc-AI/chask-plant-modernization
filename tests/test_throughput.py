"""Tests for chask.process.throughput."""

import pandas as pd
import pytest

from chask.pipeline.ingest import load_raw
from chask.pipeline.transform import to_analytics
from chask.pipeline.validate import validate
from chask.process.throughput import (
    capacity_utilization,
    production_per_available_hour,
    throughput_summary,
)


@pytest.fixture(scope="module")
def enriched() -> pd.DataFrame:
    return to_analytics(validate(load_raw()))


class TestProductionPerAvailableHour:
    def test_adds_operational_hours(self, enriched):
        result = production_per_available_hour(enriched)
        assert "operational_hours" in result.columns

    def test_adds_kg_per_op_hour(self, enriched):
        result = production_per_available_hour(enriched)
        assert "kg_per_op_hour" in result.columns

    def test_operational_hours_positive(self, enriched):
        result = production_per_available_hour(enriched)
        assert (result["operational_hours"] > 0).all()

    def test_operational_hours_less_than_monthly(self, enriched):
        from chask.config import MONTHLY_OPERATING_HOURS

        result = production_per_available_hour(enriched)
        assert (result["operational_hours"] <= MONTHLY_OPERATING_HOURS).all()

    def test_kg_per_op_hour_positive(self, enriched):
        result = production_per_available_hour(enriched)
        assert (result["kg_per_op_hour"] > 0).all()

    def test_hand_calculation(self, enriched):
        # For first pre row: prod / (720 - inact)
        result = production_per_available_hour(enriched)
        row = enriched.iloc[0]
        from chask.config import MONTHLY_OPERATING_HOURS

        expected = row["produccion_kg"] / (
            MONTHLY_OPERATING_HOURS - row["tiempo_inactividad_horas"]
        )
        assert abs(result["kg_per_op_hour"].iloc[0] - expected) < 0.001


class TestCapacityUtilization:
    def test_adds_required_columns(self, enriched):
        result = capacity_utilization(enriched)
        for col in ("capacity_pre_kg_mo", "capacity_post_kg_mo", "utilization_pre_pct"):
            assert col in result.columns

    def test_post_capacity_greater_than_pre(self, enriched):
        result = capacity_utilization(enriched)
        assert result["capacity_post_kg_mo"].iloc[0] > result["capacity_pre_kg_mo"].iloc[0]

    def test_post_capacity_is_1_5x_pre(self, enriched):
        from chask.config import POST_CAPACITY_MULTIPLIER

        result = capacity_utilization(enriched)
        ratio = result["capacity_post_kg_mo"].iloc[0] / result["capacity_pre_kg_mo"].iloc[0]
        assert abs(ratio - POST_CAPACITY_MULTIPLIER) < 1e-9

    def test_utilization_pct_positive(self, enriched):
        result = capacity_utilization(enriched)
        assert (result["utilization_pre_pct"] > 0).all()


class TestThroughputSummary:
    def test_returns_dataframe(self, enriched):
        result = throughput_summary(enriched)
        assert isinstance(result, pd.DataFrame)

    def test_has_expected_periods(self, enriched):
        result = throughput_summary(enriched)
        assert "pre" in result.index
        assert "steady_state" in result.index

    def test_ss_productivity_higher_than_pre(self, enriched):
        result = throughput_summary(enriched)
        assert (
            result.loc["steady_state", "mean_kg_per_op_hour"]
            > result.loc["pre", "mean_kg_per_op_hour"]
        )

    def test_ss_productivity_vs_pre_order_of_magnitude(self, enriched):
        # Dataset should show improvement in the right direction
        # Engineering report documents +22% at steady state
        result = throughput_summary(enriched)
        pct_change = result.loc["steady_state", "productivity_vs_pre_pct"]
        # Should be positive and within reasonable range (>5%)
        assert pct_change > 5.0

    def test_pre_n_months_is_20(self, enriched):
        result = throughput_summary(enriched)
        assert result.loc["pre", "n_months"] == 20
