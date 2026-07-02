"""Tests for chask.analysis.anomalies."""

import pandas as pd
import pytest

from chask.analysis.anomalies import (
    combined_anomalies,
    detect_isolation_forest,
    detect_zscore,
)
from chask.pipeline.ingest import load_raw
from chask.pipeline.transform import to_analytics
from chask.pipeline.validate import validate


@pytest.fixture(scope="module")
def enriched() -> pd.DataFrame:
    return to_analytics(validate(load_raw()))


class TestDetectZscore:
    def test_returns_dataframe(self, enriched):
        result = detect_zscore(enriched)
        assert isinstance(result, pd.DataFrame)

    def test_adds_zscore_anomaly_column(self, enriched):
        result = detect_zscore(enriched)
        assert "zscore_anomaly" in result.columns

    def test_adds_zscore_max_z_column(self, enriched):
        result = detect_zscore(enriched)
        assert "zscore_max_z" in result.columns

    def test_anomaly_column_is_bool(self, enriched):
        result = detect_zscore(enriched)
        assert result["zscore_anomaly"].dtype == bool

    def test_custom_threshold(self, enriched):
        result_low = detect_zscore(enriched, threshold=0.1)
        result_high = detect_zscore(enriched, threshold=5.0)
        assert result_low["zscore_anomaly"].sum() >= result_high["zscore_anomaly"].sum()

    def test_no_nulls_in_anomaly_col(self, enriched):
        result = detect_zscore(enriched)
        assert result["zscore_anomaly"].isnull().sum() == 0

    def test_known_outlier_detected(self):
        # n=5 max Z-score is ~1.79; need n>=10 to exceed threshold of 2.0
        df = pd.DataFrame({"x": [0.0] * 9 + [100.0]})
        result = detect_zscore(df, columns=["x"])
        assert result["zscore_anomaly"].iloc[-1]


class TestDetectIsolationForest:
    def test_returns_dataframe(self, enriched):
        result = detect_isolation_forest(enriched)
        assert isinstance(result, pd.DataFrame)

    def test_adds_if_anomaly_column(self, enriched):
        result = detect_isolation_forest(enriched)
        assert "if_anomaly" in result.columns

    def test_adds_if_score_column(self, enriched):
        result = detect_isolation_forest(enriched)
        assert "if_score" in result.columns

    def test_anomaly_is_bool(self, enriched):
        result = detect_isolation_forest(enriched)
        assert result["if_anomaly"].dtype == bool

    def test_reproducible_with_seed(self, enriched):
        r1 = detect_isolation_forest(enriched, seed=42)
        r2 = detect_isolation_forest(enriched, seed=42)
        pd.testing.assert_series_equal(r1["if_anomaly"], r2["if_anomaly"])

    def test_contamination_respected(self, enriched):
        # contamination=0.1 on n=29 → floor(0.1*29) = 2 anomalies
        result = detect_isolation_forest(enriched, contamination=0.1)
        n_anomalies = result["if_anomaly"].sum()
        assert n_anomalies >= 1


class TestCombinedAnomalies:
    def test_returns_dataframe(self, enriched):
        result = combined_anomalies(enriched)
        assert isinstance(result, pd.DataFrame)

    def test_any_anomaly_column_exists(self, enriched):
        result = combined_anomalies(enriched)
        assert "any_anomaly" in result.columns

    def test_any_anomaly_is_union(self, enriched):
        result = combined_anomalies(enriched)
        union = result["zscore_anomaly"] | result["if_anomaly"]
        assert (result["any_anomaly"].values == union.values).all()

    def test_row_count_preserved(self, enriched):
        result = combined_anomalies(enriched)
        assert len(result) == len(enriched)
