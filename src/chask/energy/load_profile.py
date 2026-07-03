"""Weekly load profile and anomalous base-load detection on the synthetic daily dataset.

WARNING — SYNTHETIC DATA ONLY
    This module operates on ``data/analytics/daily_synthetic.csv``.
    The daily data is model-generated, NOT real measurements.
    Results are for visualization and demonstration purposes ONLY.
    Do NOT use these outputs for financial reporting, regulatory submissions,
    or statistical inference. See the data dictionary for full disclosure.
"""

import pandas as pd

# Day-of-week label order for display
DOW_LABELS: list[str] = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Z-score threshold for flagging months with anomalous base consumption
BASE_ANOMALY_ZSCORE: float = 1.5


def weekly_load_profile(df: pd.DataFrame) -> pd.DataFrame:
    """Compute mean and median daily energy consumption by day of week.

    Args:
        df: Daily synthetic DataFrame with ``fecha`` (datetime) and
            ``consumo_kwh`` columns.

    Returns:
        DataFrame with index = day of week (0=Mon … 6=Sun) and columns
        ``mean_kwh``, ``median_kwh``, ``std_kwh``, ``day_label``.
    """
    df = df.copy()
    df["dow"] = df["fecha"].dt.dayofweek
    profile = (
        df.groupby("dow")["consumo_kwh"]
        .agg(mean_kwh="mean", median_kwh="median", std_kwh="std")
        .reindex(range(7))
    )
    profile["day_label"] = DOW_LABELS
    return profile.reset_index()


def peak_day_of_week(df: pd.DataFrame) -> dict:
    """Identify the day of week with the highest mean energy consumption.

    Args:
        df: Daily synthetic DataFrame.

    Returns:
        Dict with ``dow`` (0–6), ``day_label``, ``mean_kwh``.
    """
    profile = weekly_load_profile(df)
    row = profile.loc[profile["mean_kwh"].idxmax()]
    return {
        "dow": int(row["dow"]),
        "day_label": row["day_label"],
        "mean_kwh": round(float(row["mean_kwh"]), 2),
    }


def anomalous_base_months(
    df: pd.DataFrame,
    zscore_threshold: float = BASE_ANOMALY_ZSCORE,
) -> pd.DataFrame:
    """Flag calendar months with anomalously high minimum daily energy consumption.

    The monthly minimum daily consumption (a proxy for base/idle load) is
    Z-score normalized. Months above ``zscore_threshold`` are flagged.

    Args:
        df: Daily synthetic DataFrame with ``fecha`` and ``consumo_kwh``.
        zscore_threshold: |Z| above which a month is flagged (default 1.5).

    Returns:
        DataFrame (one row per month) with columns:
        ``year_month``, ``min_kwh_day``, ``z_base``, ``anomalous``.
    """
    df = df.copy()
    df["year_month"] = df["fecha"].dt.to_period("M")
    monthly_min = df.groupby("year_month")["consumo_kwh"].min().rename("min_kwh_day")
    result = monthly_min.reset_index()
    mu = result["min_kwh_day"].mean()
    sigma = result["min_kwh_day"].std(ddof=1)
    result["z_base"] = (result["min_kwh_day"] - mu) / sigma
    result["anomalous"] = result["z_base"].abs() > zscore_threshold
    return result
