"""Exploratory data analysis: descriptive statistics, correlation, headline findings.

All analysis in this module operates on the real monthly dataset (n=29).
"""

import pandas as pd

from chask.config import INTERVENTION_CUTOFF

_NUMERIC_COLS = [
    "produccion_kg",
    "consumo_kwh",
    "fallas_maquina",
    "tiempo_inactividad_horas",
    "ventas_usd",
    "costos_usd",
    "intensity_kwh_kg",
    "gross_margin_pct",
    "profit_usd",
    "cost_per_kg",
]


def descriptive_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Compute descriptive statistics segmented by pre/post period.

    Args:
        df: Monthly enriched DataFrame (must contain a ``period`` column).

    Returns:
        DataFrame with index = statistic name, columns = (metric, period) MultiIndex.
    """
    cols = [c for c in _NUMERIC_COLS if c in df.columns]
    pre = df[df["period"] == "pre"][cols]
    post = df[df["period"] == "post"][cols]

    stats_pre = pre.agg(["mean", "median", "std", "min", "max"])
    stats_post = post.agg(["mean", "median", "std", "min", "max"])

    stats_pre.columns = pd.MultiIndex.from_product([stats_pre.columns, ["pre"]])
    stats_post.columns = pd.MultiIndex.from_product([stats_post.columns, ["post"]])

    return pd.concat([stats_pre, stats_post], axis=1).sort_index(axis=1)


def correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Compute the Pearson correlation matrix for operational variables.

    Args:
        df: Monthly enriched DataFrame.

    Returns:
        Square correlation DataFrame.
    """
    cols = [c for c in _NUMERIC_COLS if c in df.columns]
    return df[cols].corr(method="pearson")


def headline_findings(df: pd.DataFrame) -> pd.DataFrame:
    """Return the 7-metric headline table calibrated to the CLAUDE.md ground truth.

    Computes pre/post means for each key metric and derives the direction
    (improved / worsened) and magnitude of change.

    Args:
        df: Monthly enriched DataFrame with ``period`` and derived columns.

    Returns:
        DataFrame with columns: ``metric``, ``pre_mean``, ``post_mean``,
        ``change``, ``change_unit``, ``direction``.
    """
    cutoff = pd.Timestamp(INTERVENTION_CUTOFF)
    pre = df[df["fecha"] <= cutoff]
    post = df[df["fecha"] > cutoff]

    def _pct(col: str) -> tuple[float, float, float, str, str]:
        pm = pre[col].mean()
        pom = post[col].mean()
        pct = (pom - pm) / pm * 100
        direction = "improved" if pct < 0 else "worsened"
        return pm, pom, pct, f"{pct:+.1f}%", direction

    def _pp(col: str) -> tuple[float, float, float, str, str]:
        pm = pre[col].mean()
        pom = post[col].mean()
        delta = pom - pm
        direction = "improved" if delta > 0 else "worsened"
        return pm, pom, delta, f"{delta:+.1f} pp", direction

    def _higher_better(col: str) -> tuple[float, float, float, str, str]:
        pm = pre[col].mean()
        pom = post[col].mean()
        pct = (pom - pm) / pm * 100
        direction = "improved" if pct > 0 else "worsened"
        return pm, pom, pct, f"{pct:+.1f}%", direction

    rows = []

    pm, pom, ch, cu, di = _pct("consumo_kwh")
    rows.append(("Energy consumption (kWh)", pm, pom, cu, di))

    pm, pom, ch, cu, di = _pct("intensity_kwh_kg")
    rows.append(("Energy intensity (kWh/kg)", pm, pom, cu, di))

    pm, pom, ch, cu, di = _pp("gross_margin_pct")
    rows.append(("Gross margin (%)", pm, pom, cu, di))

    pm, pom, ch, cu, di = _higher_better("ventas_usd")
    rows.append(("Sales (USD)", pm, pom, cu, di))

    pm, pom, ch, cu, di = _pct("fallas_maquina")
    rows.append(("Machine failures /month", pm, pom, cu, di))

    pm, pom, ch, cu, di = _pct("tiempo_inactividad_horas")
    rows.append(("Downtime (h/month)", pm, pom, cu, di))

    pm, pom, ch, cu, di = _higher_better("produccion_kg")
    rows.append(("Production (kg)", pm, pom, cu, di))

    return pd.DataFrame(rows, columns=["metric", "pre_mean", "post_mean", "change", "direction"])
