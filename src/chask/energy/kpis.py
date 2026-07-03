"""Energy KPI computation: intensity, rolling averages, savings, emissions.

All monetary savings use ``ENERGY_TARIFF_USD_KWH`` from ``chask.config``.
CO₂ avoidance uses ``EMISSION_FACTOR_KG_CO2_KWH`` (Bolivia SIN grid, approx.).

Assumption table — see also ``docs/energy-analysis.md``:
    - Tariff: 0.065 USD/kWh (ENDE industrial rate, ~2021)
    - Emission factor: 0.40 kgCO₂/kWh (IEA 2020 / CNDC approximate)
    - Baseline: pre-intervention monthly mean energy (computed from dataset)
    - Steady-state: Dec 2021–May 2022 monthly mean energy
"""

import pandas as pd

from chask.config import (
    EMISSION_FACTOR_KG_CO2_KWH,
    ENERGY_TARIFF_USD_KWH,
    INTERVENTION_CUTOFF,
)

ROLLING_WINDOW_MONTHS: int = 3
STEADY_STATE_START: str = "2021-12-31"


def energy_intensity_rolling(
    df: pd.DataFrame,
    window: int = ROLLING_WINDOW_MONTHS,
) -> pd.DataFrame:
    """Add a rolling-average energy intensity column.

    Args:
        df: Monthly enriched DataFrame (must contain ``intensity_kwh_kg`` and
            ``fecha`` columns, sorted by date ascending).
        window: Rolling window in months (default 3).

    Returns:
        Copy of ``df`` with added column ``intensity_rolling`` (kWh/kg).
    """
    out = df.sort_values("fecha").copy()
    out["intensity_rolling"] = out["intensity_kwh_kg"].rolling(window=window, min_periods=1).mean()
    return out


def monthly_savings(
    df: pd.DataFrame,
    tariff: float = ENERGY_TARIFF_USD_KWH,
    emission_factor: float = EMISSION_FACTOR_KG_CO2_KWH,
) -> pd.DataFrame:
    """Compute monthly energy savings vs. the pre-intervention baseline.

    The baseline is the mean ``consumo_kwh`` of the pre-intervention period.
    Positive ``savings_kwh`` means the month consumed less than baseline.

    Args:
        df: Monthly enriched DataFrame with ``period`` and ``consumo_kwh``.
        tariff: Energy tariff in USD/kWh.
        emission_factor: CO₂ emission factor in kgCO₂/kWh.

    Returns:
        Copy of ``df`` with added columns:
        ``baseline_kwh``, ``savings_kwh``, ``savings_usd``,
        ``co2_avoided_kg``.
    """
    cutoff = pd.Timestamp(INTERVENTION_CUTOFF)
    baseline = df[df["fecha"] <= cutoff]["consumo_kwh"].mean()
    out = df.copy()
    out["baseline_kwh"] = baseline
    out["savings_kwh"] = baseline - out["consumo_kwh"]
    out["savings_usd"] = out["savings_kwh"] * tariff
    out["co2_avoided_kg"] = out["savings_kwh"].clip(lower=0) * emission_factor
    return out


def annualized_savings(
    df: pd.DataFrame,
    tariff: float = ENERGY_TARIFF_USD_KWH,
    emission_factor: float = EMISSION_FACTOR_KG_CO2_KWH,
) -> dict:
    """Summarize annualized energy savings for pre, post, and steady-state slices.

    Args:
        df: Monthly enriched DataFrame.
        tariff: Energy tariff in USD/kWh.
        emission_factor: CO₂ emission factor in kgCO₂/kWh.

    Returns:
        Dict with keys:
        ``baseline_kwh_mo`` (pre mean), ``post_mean_kwh_mo``,
        ``ss_mean_kwh_mo`` (steady-state mean),
        ``post_savings_kwh_yr``, ``post_savings_usd_yr``,
        ``ss_savings_kwh_yr``, ``ss_savings_usd_yr``,
        ``ss_co2_avoided_kg_yr``.
    """
    cutoff = pd.Timestamp(INTERVENTION_CUTOFF)
    ss_start = pd.Timestamp(STEADY_STATE_START)

    pre = df[df["fecha"] <= cutoff]
    post = df[df["fecha"] > cutoff]
    ss = df[df["fecha"] >= ss_start]

    baseline = pre["consumo_kwh"].mean()
    post_mean = post["consumo_kwh"].mean()
    ss_mean = ss["consumo_kwh"].mean()

    post_savings_mo = baseline - post_mean
    ss_savings_mo = baseline - ss_mean

    return {
        "baseline_kwh_mo": round(baseline, 1),
        "post_mean_kwh_mo": round(post_mean, 1),
        "ss_mean_kwh_mo": round(ss_mean, 1),
        "post_savings_kwh_yr": round(post_savings_mo * 12, 1),
        "post_savings_usd_yr": round(post_savings_mo * 12 * tariff, 2),
        "ss_savings_kwh_yr": round(ss_savings_mo * 12, 1),
        "ss_savings_usd_yr": round(ss_savings_mo * 12 * tariff, 2),
        "ss_co2_avoided_kg_yr": round(ss_savings_mo * 12 * emission_factor, 1),
    }
