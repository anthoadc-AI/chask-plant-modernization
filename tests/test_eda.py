"""Tests for chask.analysis.eda."""

import pandas as pd
import pytest

from chask.analysis.eda import correlation_matrix, descriptive_stats, headline_findings
from chask.pipeline.ingest import load_raw
from chask.pipeline.transform import to_analytics
from chask.pipeline.validate import validate


@pytest.fixture(scope="module")
def enriched() -> pd.DataFrame:
    return to_analytics(validate(load_raw()))


class TestDescriptiveStats:
    def test_returns_dataframe(self, enriched):
        result = descriptive_stats(enriched)
        assert isinstance(result, pd.DataFrame)

    def test_has_multiindex_columns(self, enriched):
        result = descriptive_stats(enriched)
        assert isinstance(result.columns, pd.MultiIndex)

    def test_has_expected_stats(self, enriched):
        result = descriptive_stats(enriched)
        assert set(result.index) == {"mean", "median", "std", "min", "max"}

    def test_pre_post_in_second_level(self, enriched):
        result = descriptive_stats(enriched)
        second_level = set(result.columns.get_level_values(1))
        assert {"pre", "post"} <= second_level

    def test_consumo_kwh_present(self, enriched):
        result = descriptive_stats(enriched)
        first_level = set(result.columns.get_level_values(0))
        assert "consumo_kwh" in first_level


class TestCorrelationMatrix:
    def test_returns_dataframe(self, enriched):
        result = correlation_matrix(enriched)
        assert isinstance(result, pd.DataFrame)

    def test_is_square(self, enriched):
        result = correlation_matrix(enriched)
        assert result.shape[0] == result.shape[1]

    def test_diagonal_is_one(self, enriched):
        result = correlation_matrix(enriched)
        assert all(abs(v - 1.0) < 1e-10 for v in result.values.diagonal())

    def test_symmetric(self, enriched):
        result = correlation_matrix(enriched)
        assert (result.values - result.values.T == 0).all()


class TestHeadlineFindings:
    def test_returns_dataframe(self, enriched):
        result = headline_findings(enriched)
        assert isinstance(result, pd.DataFrame)

    def test_has_seven_rows(self, enriched):
        result = headline_findings(enriched)
        assert len(result) == 7

    def test_expected_columns(self, enriched):
        result = headline_findings(enriched)
        assert set(result.columns) == {"metric", "pre_mean", "post_mean", "change", "direction"}

    def test_energy_improved(self, enriched):
        result = headline_findings(enriched)
        row = result[result["metric"] == "Energy consumption (kWh)"].iloc[0]
        assert row["direction"] == "improved"
        assert row["post_mean"] < row["pre_mean"]

    def test_margin_improved(self, enriched):
        result = headline_findings(enriched)
        row = result[result["metric"] == "Gross margin (%)"].iloc[0]
        assert row["direction"] == "improved"
        assert row["post_mean"] > row["pre_mean"]

    def test_failures_improved(self, enriched):
        result = headline_findings(enriched)
        row = result[result["metric"] == "Machine failures /month"].iloc[0]
        assert row["direction"] == "improved"
        assert row["post_mean"] < row["pre_mean"]

    def test_production_improved(self, enriched):
        result = headline_findings(enriched)
        row = result[result["metric"] == "Production (kg)"].iloc[0]
        assert row["direction"] == "improved"
        assert row["post_mean"] > row["pre_mean"]

    def test_all_directions_improved(self, enriched):
        result = headline_findings(enriched)
        assert (result["direction"] == "improved").all(), (
            f"Some metrics not improved:\n{result[result['direction'] != 'improved']}"
        )
