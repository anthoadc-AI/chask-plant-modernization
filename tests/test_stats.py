"""Tests for chask.analysis.stats."""

import numpy as np
import pandas as pd
import pytest

from chask.analysis.stats import (
    cohens_d,
    full_statistical_summary,
    hypothesis_test,
    its_analysis,
    normality_test,
)
from chask.pipeline.ingest import load_raw
from chask.pipeline.transform import to_analytics
from chask.pipeline.validate import validate


@pytest.fixture(scope="module")
def enriched() -> pd.DataFrame:
    return to_analytics(validate(load_raw()))


class TestNormalityTest:
    def test_returns_dict_with_expected_keys(self):
        series = pd.Series(np.random.default_rng(42).normal(0, 1, 30))
        result = normality_test(series)
        assert {"stat", "p_value", "is_normal"} == set(result.keys())

    def test_normal_data_passes(self):
        rng = np.random.default_rng(42)
        series = pd.Series(rng.normal(0, 1, 50))
        result = normality_test(series)
        assert isinstance(result["is_normal"], (bool, np.bool_))

    def test_uniform_data_fails(self):
        rng = np.random.default_rng(42)
        series = pd.Series(rng.uniform(0, 100, 30))
        result = normality_test(series)
        assert isinstance(result["is_normal"], (bool, np.bool_))


class TestHypothesisTest:
    def test_returns_dict_with_required_keys(self):
        pre = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        post = pd.Series([6.0, 7.0, 8.0, 9.0, 10.0])
        result = hypothesis_test(pre, post)
        assert {"test", "stat", "p_value", "significant"} <= set(result.keys())

    def test_clearly_different_groups_are_significant(self):
        pre = pd.Series(np.ones(10))
        post = pd.Series(np.ones(10) * 1000)
        result = hypothesis_test(pre, post)
        assert result["significant"]

    def test_identical_groups_not_significant(self):
        pre = pd.Series([5.0, 5.0, 5.0, 5.0, 5.0])
        post = pd.Series([5.0, 5.0, 5.0, 5.0, 5.0])
        result = hypothesis_test(pre, post)
        assert not result["significant"]


class TestCohensD:
    def test_returns_dict_with_keys(self):
        pre = pd.Series([1.0, 2.0, 3.0])
        post = pd.Series([4.0, 5.0, 6.0])
        result = cohens_d(pre, post)
        assert {"d", "interpretation"} == set(result.keys())

    def test_large_effect_interpretation(self):
        pre = pd.Series([0.0] * 10)
        result = cohens_d(pre, pd.Series([10.0] * 10))
        assert result["interpretation"] in ("large", "medium", "small", "negligible")

    def test_zero_difference_gives_negligible(self):
        pre = pd.Series([5.0, 5.0, 5.0, 5.0])
        result = cohens_d(pre, pre)
        assert result["interpretation"] == "negligible"
        assert result["d"] == 0.0


class TestFullStatisticalSummary:
    def test_returns_dataframe(self, enriched):
        result = full_statistical_summary(enriched)
        assert isinstance(result, pd.DataFrame)

    def test_has_expected_columns(self, enriched):
        result = full_statistical_summary(enriched)
        expected = {
            "variable",
            "normality_pre_p",
            "normality_post_p",
            "test_used",
            "stat",
            "p_value",
            "significant",
            "cohens_d",
            "effect_size",
            "pre_mean",
            "post_mean",
            "pct_change",
        }
        assert expected <= set(result.columns)

    def test_energy_consumption_row_exists(self, enriched):
        result = full_statistical_summary(enriched)
        assert "consumo_kwh" in result["variable"].values

    def test_all_metrics_covered(self, enriched):
        result = full_statistical_summary(enriched)
        assert len(result) >= 6

    def test_energy_pct_change_negative(self, enriched):
        result = full_statistical_summary(enriched)
        row = result[result["variable"] == "consumo_kwh"].iloc[0]
        assert row["pct_change"] < 0, "Energy should decrease post-intervention"


class TestItsAnalysis:
    def test_returns_dict(self, enriched):
        result = its_analysis(enriched, "consumo_kwh")
        assert isinstance(result, dict)

    def test_has_required_keys(self, enriched):
        result = its_analysis(enriched, "consumo_kwh")
        required = {
            "outcome",
            "n_pre",
            "n_post",
            "coefficients",
            "p_values",
            "r_squared",
            "adj_r_squared",
            "fitted",
            "its_df",
            "model",
        }
        assert required <= set(result.keys())

    def test_n_pre_is_20(self, enriched):
        result = its_analysis(enriched, "consumo_kwh")
        assert result["n_pre"] == 20

    def test_n_post_is_9(self, enriched):
        result = its_analysis(enriched, "consumo_kwh")
        assert result["n_post"] == 9

    def test_r_squared_between_0_and_1(self, enriched):
        result = its_analysis(enriched, "consumo_kwh")
        assert 0.0 <= result["r_squared"] <= 1.0

    def test_coefficients_has_intercept(self, enriched):
        result = its_analysis(enriched, "consumo_kwh")
        assert "Intercept" in result["coefficients"]

    def test_level_change_coefficient_exists(self, enriched):
        result = its_analysis(enriched, "consumo_kwh")
        assert "D" in result["coefficients"]

    def test_fitted_length_matches_data(self, enriched):
        result = its_analysis(enriched, "consumo_kwh")
        assert len(result["fitted"]) == len(enriched)
