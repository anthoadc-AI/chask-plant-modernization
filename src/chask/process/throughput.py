"""Bottleneck and throughput analysis: production per available hour, capacity utilization.

Assumptions (named constants — see ``docs/energy-analysis.md``):
    - MONTHLY_OPERATING_HOURS: 720 h/month (24 h × 30 days nominal)
    - POST_CAPACITY_MULTIPLIER: 1.5 — installed capacity post-intervention
      is 1.5× the pre-intervention installed capacity (engineering report).
    - Operational hours = MONTHLY_OPERATING_HOURS − tiempo_inactividad_horas.
"""

import pandas as pd

from chask.config import INTERVENTION_CUTOFF, MONTHLY_OPERATING_HOURS, POST_CAPACITY_MULTIPLIER

STEADY_STATE_START: str = "2021-12-31"
TRANSITION_START: str = "2021-09-30"


def production_per_available_hour(df: pd.DataFrame) -> pd.DataFrame:
    """Compute monthly production per available (non-downtime) operating hour.

    Args:
        df: Monthly enriched DataFrame with ``produccion_kg``,
            ``tiempo_inactividad_horas``, and ``period`` columns.

    Returns:
        Copy of ``df`` with added columns:
        ``operational_hours`` and ``kg_per_op_hour``.
    """
    out = df.copy()
    out["operational_hours"] = MONTHLY_OPERATING_HOURS - out["tiempo_inactividad_horas"]
    out["kg_per_op_hour"] = out["produccion_kg"] / out["operational_hours"].clip(lower=1.0)
    return out


def capacity_utilization(df: pd.DataFrame) -> pd.DataFrame:
    """Compute capacity utilization relative to pre- and post-intervention capacity.

    Installed capacity post-intervention is ``POST_CAPACITY_MULTIPLIER × pre_capacity``.
    Pre-capacity is estimated as the maximum monthly production in the pre period.

    Args:
        df: Monthly enriched DataFrame.

    Returns:
        Copy of ``df`` with added columns:
        ``capacity_pre_kg_mo`` (constant), ``capacity_post_kg_mo`` (constant),
        ``utilization_pre_pct`` (vs pre capacity),
        ``utilization_post_pct`` (vs post installed capacity).
    """
    cutoff = pd.Timestamp(INTERVENTION_CUTOFF)
    pre_max = df[df["fecha"] <= cutoff]["produccion_kg"].max()
    post_capacity = pre_max * POST_CAPACITY_MULTIPLIER

    out = df.copy()
    out["capacity_pre_kg_mo"] = pre_max
    out["capacity_post_kg_mo"] = post_capacity
    out["utilization_pre_pct"] = out["produccion_kg"] / pre_max * 100.0
    out["utilization_post_pct"] = out["produccion_kg"] / post_capacity * 100.0
    return out


def throughput_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Return a period-by-period summary of throughput metrics.

    Periods: ``pre``, ``transition`` (Sep–Nov 2021), ``steady_state``.

    Args:
        df: Monthly enriched DataFrame.

    Returns:
        DataFrame with index = period label and columns:
        ``n_months``, ``mean_prod_kg``, ``mean_op_hours``,
        ``mean_kg_per_op_hour``, ``productivity_vs_pre_pct``,
        ``mean_utilization_pre_pct``.
    """
    cutoff = pd.Timestamp(INTERVENTION_CUTOFF)
    ss_start = pd.Timestamp(STEADY_STATE_START)

    enriched = production_per_available_hour(capacity_utilization(df))

    slices = {
        "pre": enriched[enriched["fecha"] <= cutoff],
        "transition": enriched[(enriched["fecha"] > cutoff) & (enriched["fecha"] < ss_start)],
        "steady_state": enriched[enriched["fecha"] >= ss_start],
    }

    pre_prod_h = slices["pre"]["kg_per_op_hour"].mean()
    rows = []
    for label, sub in slices.items():
        if len(sub) == 0:
            continue
        prod_h = sub["kg_per_op_hour"].mean()
        rows.append(
            {
                "period": label,
                "n_months": len(sub),
                "mean_prod_kg": round(sub["produccion_kg"].mean(), 1),
                "mean_op_hours": round(sub["operational_hours"].mean(), 1),
                "mean_kg_per_op_hour": round(prod_h, 3),
                "productivity_vs_pre_pct": round((prod_h - pre_prod_h) / pre_prod_h * 100, 1),
                "mean_utilization_pre_pct": round(sub["utilization_pre_pct"].mean(), 1),
            }
        )
    return pd.DataFrame(rows).set_index("period")
