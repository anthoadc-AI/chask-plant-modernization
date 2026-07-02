"""Tests for chask.pipeline.transform."""

import pandas as pd
import pytest

from chask.config import ANALYTICS_DIR, INTERVENTION_CUTOFF, STAGING_DIR
from chask.pipeline.ingest import load_raw
from chask.pipeline.transform import to_analytics, to_staging
from chask.pipeline.validate import validate


@pytest.fixture()
def validated_df() -> pd.DataFrame:
    return validate(load_raw())


def test_to_staging_writes_file(validated_df: pd.DataFrame, tmp_path):
    import chask.pipeline.transform as t_mod

    original = t_mod.STAGING_DIR
    t_mod.STAGING_DIR = tmp_path
    try:
        to_staging(validated_df)
        assert (tmp_path / "monthly_validated.csv").exists()
    finally:
        t_mod.STAGING_DIR = original


def test_to_staging_returns_same_df(validated_df: pd.DataFrame):
    result = to_staging(validated_df)
    pd.testing.assert_frame_equal(result, validated_df)


def test_to_analytics_adds_intensity(validated_df: pd.DataFrame):
    enriched = to_analytics(validated_df)
    assert "intensity_kwh_kg" in enriched.columns
    expected = validated_df["consumo_kwh"] / validated_df["produccion_kg"]
    pd.testing.assert_series_equal(enriched["intensity_kwh_kg"], expected, check_names=False)


def test_to_analytics_adds_gross_margin(validated_df: pd.DataFrame):
    enriched = to_analytics(validated_df)
    assert "gross_margin_pct" in enriched.columns
    expected = (
        (validated_df["ventas_usd"] - validated_df["costos_usd"]) / validated_df["ventas_usd"] * 100
    )
    pd.testing.assert_series_equal(enriched["gross_margin_pct"], expected, check_names=False)


def test_to_analytics_adds_profit(validated_df: pd.DataFrame):
    enriched = to_analytics(validated_df)
    assert "profit_usd" in enriched.columns
    expected = validated_df["ventas_usd"] - validated_df["costos_usd"]
    pd.testing.assert_series_equal(enriched["profit_usd"], expected, check_names=False)


def test_to_analytics_adds_cost_per_kg(validated_df: pd.DataFrame):
    enriched = to_analytics(validated_df)
    assert "cost_per_kg" in enriched.columns
    expected = validated_df["costos_usd"] / validated_df["produccion_kg"]
    pd.testing.assert_series_equal(enriched["cost_per_kg"], expected, check_names=False)


def test_to_analytics_period_column(validated_df: pd.DataFrame):
    cutoff = pd.Timestamp(INTERVENTION_CUTOFF)
    enriched = to_analytics(validated_df)
    assert "period" in enriched.columns
    pre = enriched[enriched["fecha"] <= cutoff]["period"]
    post = enriched[enriched["fecha"] > cutoff]["period"]
    assert (pre == "pre").all()
    assert (post == "post").all()


def test_to_analytics_pre_count(validated_df: pd.DataFrame):
    enriched = to_analytics(validated_df)
    assert (enriched["period"] == "pre").sum() == 20


def test_to_analytics_post_count(validated_df: pd.DataFrame):
    enriched = to_analytics(validated_df)
    assert (enriched["period"] == "post").sum() == 9


def test_to_analytics_writes_file(validated_df: pd.DataFrame):
    to_analytics(validated_df)
    assert (ANALYTICS_DIR / "monthly_enriched.csv").exists()


def test_staging_written_by_pipeline(validated_df: pd.DataFrame):
    to_staging(validated_df)
    assert (STAGING_DIR / "monthly_validated.csv").exists()
