"""Tests for chask.analysis.viz (smoke tests — verify files are generated)."""

import pathlib

import pandas as pd
import pytest

from chask.analysis.anomalies import combined_anomalies
from chask.analysis.stats import its_analysis
from chask.analysis.viz import (
    plot_anomalies,
    plot_boxplots,
    plot_correlation_heatmap,
    plot_its,
    plot_margin_sales,
    plot_time_series,
)
from chask.pipeline.ingest import load_raw
from chask.pipeline.transform import to_analytics
from chask.pipeline.validate import validate


@pytest.fixture(scope="module")
def enriched() -> pd.DataFrame:
    return to_analytics(validate(load_raw()))


@pytest.fixture
def tmp_figures(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path / "figures"


class TestPlotTimeSeries:
    def test_creates_png(self, enriched, tmp_figures):
        plot_time_series(enriched, tmp_figures)
        assert (tmp_figures / "01_time_series.png").exists()

    def test_creates_html(self, enriched, tmp_figures):
        plot_time_series(enriched, tmp_figures)
        assert (tmp_figures / "01_time_series_interactive.html").exists()


class TestPlotBoxplots:
    def test_creates_png(self, enriched, tmp_figures):
        plot_boxplots(enriched, tmp_figures)
        assert (tmp_figures / "02_boxplots_pre_post.png").exists()


class TestPlotCorrelationHeatmap:
    def test_creates_png(self, enriched, tmp_figures):
        plot_correlation_heatmap(enriched, tmp_figures)
        assert (tmp_figures / "03_correlation_heatmap.png").exists()


class TestPlotAnomalies:
    def test_creates_png(self, enriched, tmp_figures):
        anomaly_df = combined_anomalies(enriched)
        plot_anomalies(enriched, anomaly_df, tmp_figures)
        assert (tmp_figures / "04_anomalies.png").exists()


class TestPlotIts:
    def test_creates_png_and_html(self, enriched, tmp_figures):
        its = its_analysis(enriched, "consumo_kwh")
        plot_its(enriched, its, "consumo_kwh", tmp_figures)
        assert (tmp_figures / "05_its_consumo_kwh.png").exists()
        assert (tmp_figures / "05_its_consumo_kwh_interactive.html").exists()


class TestPlotMarginSales:
    def test_creates_png(self, enriched, tmp_figures):
        plot_margin_sales(enriched, tmp_figures)
        assert (tmp_figures / "06_margin_sales.png").exists()

    def test_creates_html(self, enriched, tmp_figures):
        plot_margin_sales(enriched, tmp_figures)
        assert (tmp_figures / "06_margin_sales_interactive.html").exists()
