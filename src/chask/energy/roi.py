"""ROI analysis — three scenarios for the USD 85,000 plant modernization.

Assumptions (all named constants — see also ``docs/energy-analysis.md``):
    - TOTAL_INVESTMENT_USD: 85,000
    - DISCOUNT_RATE: 10% per annum
    - PROJECTION_YEARS: 5
    - ENERGY_TARIFF_USD_KWH: 0.065 (from chask.config)
    - POST_CAPACITY_MULTIPLIER: 1.5 (from engineering report)
    - CAPACITY_RAMP_YEARS: 3 — years to fully utilize the +50% capacity

Scenarios:
    Conservative: energy savings + downtime cost reduction only.
    Base:         Conservative + incremental margin from observed production growth.
    Optimistic:   Base + progressive utilization of the +50% installed capacity
                  over CAPACITY_RAMP_YEARS.

Honest conclusions:
    - The conservative scenario yields a negative 5-year NPV: energy alone
      does not justify the investment.
    - The base scenario is marginal (NPV near zero at 5 years) — justified
      only if production growth is sustained.
    - The optimistic scenario is positive: the full capacity utilization
      unlocks the financial case. The post-intervention dataset already shows
      partial materialization (+11.5% production, +7.5 pp margin).
"""

from __future__ import annotations

import pandas as pd

from chask.config import (
    DISCOUNT_RATE,
    ENERGY_TARIFF_USD_KWH,
    INTERVENTION_CUTOFF,
    MONTHLY_OPERATING_HOURS,
    POST_CAPACITY_MULTIPLIER,
    TOTAL_INVESTMENT_USD,
)

# Capacity ramp duration (years to reach full +50% utilization)
CAPACITY_RAMP_YEARS: int = 3
# NPV projection horizon
PROJECTION_YEARS: int = 5
# Fraction of extra capacity unlocked each ramp year (linear ramp)
_RAMP_FRACTIONS: list[float] = [
    round((i + 1) / CAPACITY_RAMP_YEARS, 6) for i in range(CAPACITY_RAMP_YEARS)
]


def _pre_post_ss_stats(df: pd.DataFrame) -> dict:
    """Extract pre, post, and steady-state means for key variables."""
    cutoff = pd.Timestamp(INTERVENTION_CUTOFF)
    ss_start = pd.Timestamp("2021-12-31")
    pre = df[df["fecha"] <= cutoff]
    post = df[df["fecha"] > cutoff]
    ss = df[df["fecha"] >= ss_start]
    return {
        "pre_kwh_mo": pre["consumo_kwh"].mean(),
        "ss_kwh_mo": ss["consumo_kwh"].mean(),
        "pre_inact_h_mo": pre["tiempo_inactividad_horas"].mean(),
        "ss_inact_h_mo": ss["tiempo_inactividad_horas"].mean(),
        "pre_prod_kg_mo": pre["produccion_kg"].mean(),
        "post_prod_kg_mo": post["produccion_kg"].mean(),
        "post_margin_pct": post["gross_margin_pct"].mean() / 100.0,
        "post_ventas_usd_mo": post["ventas_usd"].mean(),
        "post_operational_h_mo": MONTHLY_OPERATING_HOURS - post["tiempo_inactividad_horas"].mean(),
    }


def npv(cash_flows: list[float], discount_rate: float = DISCOUNT_RATE) -> float:
    """Compute Net Present Value of a series of annual cash flows.

    Year 0 is the initial investment (negative).  Years 1–N are benefits.

    Args:
        cash_flows: List of cash flows [CF_0, CF_1, …, CF_N].
            CF_0 is typically ``-TOTAL_INVESTMENT_USD``.
        discount_rate: Annual discount rate (default from config).

    Returns:
        NPV in USD.
    """
    return float(sum(cf / (1 + discount_rate) ** t for t, cf in enumerate(cash_flows)))


def simple_payback(annual_benefit: float, investment: float = TOTAL_INVESTMENT_USD) -> float:
    """Simple (undiscounted) payback period in years.

    Args:
        annual_benefit: Constant annual net benefit in USD.
        investment: Total investment in USD.

    Returns:
        Payback in years (float inf if benefit ≤ 0).
    """
    if annual_benefit <= 0:
        return float("inf")
    return investment / annual_benefit


def compute_roi_scenarios(
    df: pd.DataFrame,
    investment: float = TOTAL_INVESTMENT_USD,
    tariff: float = ENERGY_TARIFF_USD_KWH,
    discount_rate: float = DISCOUNT_RATE,
) -> pd.DataFrame:
    """Compute ROI table for all three scenarios.

    Args:
        df: Monthly enriched DataFrame.
        investment: Total project investment (USD).
        tariff: Energy tariff (USD/kWh).
        discount_rate: Annual discount rate.

    Returns:
        DataFrame with columns ``scenario``, ``annual_benefit_usd``,
        ``payback_years``, ``npv_5yr_usd``, ``notes``.
    """
    s = _pre_post_ss_stats(df)

    # ---- CONSERVATIVE: energy + downtime reduction -------------------------
    energy_savings_yr = (s["pre_kwh_mo"] - s["ss_kwh_mo"]) * 12 * tariff

    # Hourly margin = monthly gross profit / operational hours
    hourly_margin_usd = (s["post_ventas_usd_mo"] * s["post_margin_pct"]) / s[
        "post_operational_h_mo"
    ]
    downtime_reduction_h_mo = s["pre_inact_h_mo"] - s["ss_inact_h_mo"]
    downtime_savings_yr = downtime_reduction_h_mo * 12 * hourly_margin_usd

    conservative_yr = energy_savings_yr + downtime_savings_yr
    conservative_cfs = [-investment] + [conservative_yr] * PROJECTION_YEARS
    conservative_npv = npv(conservative_cfs, discount_rate)
    conservative_pb = simple_payback(conservative_yr, investment)

    # ---- BASE: conservative + incremental production margin ----------------
    prod_growth_kg_mo = s["post_prod_kg_mo"] - s["pre_prod_kg_mo"]
    margin_per_kg = (s["post_ventas_usd_mo"] * s["post_margin_pct"]) / s["post_prod_kg_mo"]
    prod_margin_yr = prod_growth_kg_mo * 12 * margin_per_kg

    base_yr = conservative_yr + prod_margin_yr
    base_cfs = [-investment] + [base_yr] * PROJECTION_YEARS
    base_npv = npv(base_cfs, discount_rate)
    base_pb = simple_payback(base_yr, investment)

    # ---- OPTIMISTIC: base + capacity ramp ----------------------------------
    # Full extra capacity = pre_prod * (POST_CAPACITY_MULTIPLIER - 1)
    max_extra_kg_mo = s["pre_prod_kg_mo"] * (POST_CAPACITY_MULTIPLIER - 1.0)
    # Post dataset already captures partial utilization; extra ramp is above base
    already_captured_kg_mo = prod_growth_kg_mo
    rampable_kg_mo = max(max_extra_kg_mo - already_captured_kg_mo, 0.0)

    # Build year-by-year cash flows
    opt_cfs: list[float] = [-investment]
    for yr in range(1, PROJECTION_YEARS + 1):
        if yr <= CAPACITY_RAMP_YEARS:
            fraction = _RAMP_FRACTIONS[yr - 1]
        else:
            fraction = 1.0
        extra_yr = rampable_kg_mo * fraction * 12 * margin_per_kg
        opt_cfs.append(base_yr + extra_yr)

    optimistic_yr_1 = opt_cfs[1]
    optimistic_npv = npv(opt_cfs, discount_rate)
    # Approximate payback from constant-benefit phase
    optimistic_pb = simple_payback(opt_cfs[-1], investment)

    rows = [
        {
            "scenario": "Conservative",
            "annual_benefit_usd": round(conservative_yr, 0),
            "payback_years": round(conservative_pb, 1),
            "npv_5yr_usd": round(conservative_npv, 0),
            "notes": "Energy savings + downtime reduction only (SS vs pre)",
        },
        {
            "scenario": "Base",
            "annual_benefit_usd": round(base_yr, 0),
            "payback_years": round(base_pb, 1),
            "npv_5yr_usd": round(base_npv, 0),
            "notes": "Conservative + observed production growth margin",
        },
        {
            "scenario": "Optimistic",
            "annual_benefit_usd": round(optimistic_yr_1, 0),
            "payback_years": round(optimistic_pb, 1),
            "npv_5yr_usd": round(optimistic_npv, 0),
            "notes": (
                f"Base + full +{int((POST_CAPACITY_MULTIPLIER - 1) * 100)}%"
                f" capacity ramp over {CAPACITY_RAMP_YEARS}yr"
            ),
        },
    ]
    return pd.DataFrame(rows)


def payback_curves(
    df: pd.DataFrame,
    investment: float = TOTAL_INVESTMENT_USD,
    tariff: float = ENERGY_TARIFF_USD_KWH,
    discount_rate: float = DISCOUNT_RATE,
) -> pd.DataFrame:
    """Return cumulative discounted cash flows per year for each scenario.

    Args:
        df: Monthly enriched DataFrame.
        investment: Total investment (USD).
        tariff: Energy tariff (USD/kWh).
        discount_rate: Annual discount rate.

    Returns:
        DataFrame with columns ``year``, ``Conservative``, ``Base``,
        ``Optimistic`` containing cumulative NPV including initial investment.
    """
    s = _pre_post_ss_stats(df)

    energy_savings_yr = (s["pre_kwh_mo"] - s["ss_kwh_mo"]) * 12 * tariff
    hourly_margin_usd = (s["post_ventas_usd_mo"] * s["post_margin_pct"]) / s[
        "post_operational_h_mo"
    ]
    downtime_savings_yr = (s["pre_inact_h_mo"] - s["ss_inact_h_mo"]) * 12 * hourly_margin_usd
    conservative_yr = energy_savings_yr + downtime_savings_yr

    prod_growth_kg_mo = s["post_prod_kg_mo"] - s["pre_prod_kg_mo"]
    margin_per_kg = (s["post_ventas_usd_mo"] * s["post_margin_pct"]) / s["post_prod_kg_mo"]
    base_yr = conservative_yr + prod_growth_kg_mo * 12 * margin_per_kg

    max_extra_kg_mo = s["pre_prod_kg_mo"] * (POST_CAPACITY_MULTIPLIER - 1.0)
    rampable_kg_mo = max(max_extra_kg_mo - prod_growth_kg_mo, 0.0)

    years = list(range(PROJECTION_YEARS + 1))
    cum_con = [-investment]
    cum_base = [-investment]
    cum_opt = [-investment]

    for yr in range(1, PROJECTION_YEARS + 1):
        disc = (1 + discount_rate) ** yr
        cum_con.append(cum_con[-1] + conservative_yr / disc)
        cum_base.append(cum_base[-1] + base_yr / disc)
        if yr <= CAPACITY_RAMP_YEARS:
            frac = _RAMP_FRACTIONS[yr - 1]
        else:
            frac = 1.0
        opt_yr = base_yr + rampable_kg_mo * frac * 12 * margin_per_kg
        cum_opt.append(cum_opt[-1] + opt_yr / disc)

    return pd.DataFrame(
        {"year": years, "Conservative": cum_con, "Base": cum_base, "Optimistic": cum_opt}
    )
