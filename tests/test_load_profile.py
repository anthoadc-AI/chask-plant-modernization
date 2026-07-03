"""Tests for chask.energy.load_profile (uses synthetic daily data — demo only)."""

import pandas as pd
import pytest

from chask.config import ANALYTICS_DIR
from chask.energy.load_profile import anomalous_base_months, peak_day_of_week, weekly_load_profile


@pytest.fixture(scope="module")
def daily_df() -> pd.DataFrame:
    path = ANALYTICS_DIR / "daily_synthetic.csv"
    df = pd.read_csv(path, parse_dates=["fecha"])
    return df


class TestWeeklyLoadProfile:
    def test_returns_dataframe(self, daily_df):
        result = weekly_load_profile(daily_df)
        assert isinstance(result, pd.DataFrame)

    def test_has_seven_rows(self, daily_df):
        result = weekly_load_profile(daily_df)
        assert len(result) == 7

    def test_has_required_columns(self, daily_df):
        result = weekly_load_profile(daily_df)
        for col in ("mean_kwh", "median_kwh", "std_kwh", "day_label"):
            assert col in result.columns

    def test_mean_kwh_positive(self, daily_df):
        result = weekly_load_profile(daily_df)
        assert (result["mean_kwh"] > 0).all()

    def test_labels_correct(self, daily_df):
        result = weekly_load_profile(daily_df)
        assert list(result["day_label"]) == ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class TestPeakDayOfWeek:
    def test_returns_dict(self, daily_df):
        result = peak_day_of_week(daily_df)
        assert isinstance(result, dict)

    def test_has_required_keys(self, daily_df):
        result = peak_day_of_week(daily_df)
        assert {"dow", "day_label", "mean_kwh"} == set(result.keys())

    def test_dow_in_range(self, daily_df):
        result = peak_day_of_week(daily_df)
        assert 0 <= result["dow"] <= 6

    def test_peak_is_high_production_day(self, daily_df):
        # Synthetic data has higher weights on Fri/Sat (dow 4 or 5)
        result = peak_day_of_week(daily_df)
        assert result["dow"] in (4, 5, 6)


class TestAnomalousBaseMonths:
    def test_returns_dataframe(self, daily_df):
        result = anomalous_base_months(daily_df)
        assert isinstance(result, pd.DataFrame)

    def test_has_required_columns(self, daily_df):
        result = anomalous_base_months(daily_df)
        for col in ("year_month", "min_kwh_day", "z_base", "anomalous"):
            assert col in result.columns

    def test_row_count_equals_months(self, daily_df):
        n_months = daily_df["fecha"].dt.to_period("M").nunique()
        result = anomalous_base_months(daily_df)
        assert len(result) == n_months

    def test_some_months_flagged(self, daily_df):
        result = anomalous_base_months(daily_df)
        # With threshold 1.5, approximately 14% of months should be flagged
        assert result["anomalous"].sum() >= 1
