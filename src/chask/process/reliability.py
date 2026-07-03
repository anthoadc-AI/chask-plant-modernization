"""Reliability metrics: MTBF, failure trend by period, downtime cost estimation.

Assumptions (documented — see ``docs/energy-analysis.md``):
    - MONTHLY_OPERATING_HOURS: 720 h/month nominal (from chask.config).
    - Downtime cost is estimated as lost gross margin per hour of downtime.
      hourly_margin = (monthly_ventas × margin_pct) / operational_hours.
    - MTBF = operational_hours / failure_count per month.
      When fallas_maquina = 0, MTBF is set to MONTHLY_OPERATING_HOURS
      (i.e., no failures in that month → lower-bound MTBF of one month).
"""

import pandas as pd

from chask.config import INTERVENTION_CUTOFF, MONTHLY_OPERATING_HOURS

STEADY_STATE_START: str = "2021-12-31"
TRANSITION_START: str = "2021-09-30"

# Minimum fallas guard: avoid division-by-zero (set MTBF = full month)
_MTBF_NO_FAILURE_H: float = MONTHLY_OPERATING_HOURS


def mtbf_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """Compute approximate MTBF (h) per calendar month.

    MTBF = operating_hours / failures.  When failures = 0, MTBF is set to
    ``MONTHLY_OPERATING_HOURS`` (conservative: at least one full month MTBF).

    Args:
        df: Monthly enriched DataFrame with ``fallas_maquina`` and
            ``tiempo_inactividad_horas``.

    Returns:
        Copy of ``df`` with added column ``mtbf_h``.
    """
    out = df.copy()
    operational = MONTHLY_OPERATING_HOURS - out["tiempo_inactividad_horas"]
    fallas = out["fallas_maquina"].replace(0, _MTBF_NO_FAILURE_H)
    out["mtbf_h"] = operational / fallas
    return out


def failure_trends(df: pd.DataFrame) -> pd.DataFrame:
    """Return failure and MTBF statistics by pre/transition/steady-state period.

    Args:
        df: Monthly enriched DataFrame.

    Returns:
        DataFrame with index = period and columns:
        ``n_months``, ``mean_fallas``, ``mean_downtime_h``,
        ``mean_mtbf_h``, ``fallas_vs_pre_pct``.
    """
    cutoff = pd.Timestamp(INTERVENTION_CUTOFF)
    ss_start = pd.Timestamp(STEADY_STATE_START)

    enriched = mtbf_monthly(df)

    slices = {
        "pre": enriched[enriched["fecha"] <= cutoff],
        "transition": enriched[(enriched["fecha"] > cutoff) & (enriched["fecha"] < ss_start)],
        "steady_state": enriched[enriched["fecha"] >= ss_start],
    }

    pre_mean_fallas = slices["pre"]["fallas_maquina"].mean()
    rows = []
    for label, sub in slices.items():
        if len(sub) == 0:
            continue
        mf = sub["fallas_maquina"].mean()
        rows.append(
            {
                "period": label,
                "n_months": len(sub),
                "mean_fallas": round(mf, 2),
                "mean_downtime_h": round(sub["tiempo_inactividad_horas"].mean(), 2),
                "mean_mtbf_h": round(sub["mtbf_h"].mean(), 1),
                "fallas_vs_pre_pct": round((mf - pre_mean_fallas) / pre_mean_fallas * 100, 1),
            }
        )
    return pd.DataFrame(rows).set_index("period")


def downtime_cost_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """Estimate the monthly cost of production downtime (lost gross margin).

    hourly_margin_usd = (ventas_usd × gross_margin_pct / 100)
                        / (MONTHLY_OPERATING_HOURS − tiempo_inactividad_horas)

    downtime_cost_usd = tiempo_inactividad_horas × hourly_margin_usd

    Args:
        df: Monthly enriched DataFrame with ``ventas_usd``,
            ``gross_margin_pct``, and ``tiempo_inactividad_horas``.

    Returns:
        Copy of ``df`` with added columns:
        ``hourly_margin_usd`` and ``downtime_cost_usd``.
    """
    out = df.copy()
    operational = (MONTHLY_OPERATING_HOURS - out["tiempo_inactividad_horas"]).clip(lower=1.0)
    out["hourly_margin_usd"] = (out["ventas_usd"] * out["gross_margin_pct"] / 100.0) / operational
    out["downtime_cost_usd"] = out["tiempo_inactividad_horas"] * out["hourly_margin_usd"]
    return out


def reliability_summary(df: pd.DataFrame) -> dict:
    """One-dict summary: pre/SS MTBF, total downtime cost saved, MTBF improvement.

    Args:
        df: Monthly enriched DataFrame.

    Returns:
        Dict with pre and steady-state MTBF, downtime cost reduction,
        and MTBF improvement percentage.
    """
    cutoff = pd.Timestamp(INTERVENTION_CUTOFF)
    ss_start = pd.Timestamp(STEADY_STATE_START)

    enriched = downtime_cost_monthly(mtbf_monthly(df))
    pre = enriched[enriched["fecha"] <= cutoff]
    ss = enriched[enriched["fecha"] >= ss_start]

    pre_mtbf = pre["mtbf_h"].mean()
    ss_mtbf = ss["mtbf_h"].mean()
    pre_dtcost_mo = pre["downtime_cost_usd"].mean()
    ss_dtcost_mo = ss["downtime_cost_usd"].mean()

    return {
        "pre_mean_mtbf_h": round(pre_mtbf, 1),
        "ss_mean_mtbf_h": round(ss_mtbf, 1),
        "mtbf_improvement_pct": round((ss_mtbf - pre_mtbf) / pre_mtbf * 100, 1),
        "pre_downtime_cost_usd_mo": round(pre_dtcost_mo, 2),
        "ss_downtime_cost_usd_mo": round(ss_dtcost_mo, 2),
        "downtime_cost_reduction_usd_mo": round(pre_dtcost_mo - ss_dtcost_mo, 2),
        "downtime_cost_reduction_usd_yr": round((pre_dtcost_mo - ss_dtcost_mo) * 12, 2),
    }
