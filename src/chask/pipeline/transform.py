"""Produce staging and analytics layers from the validated monthly dataset."""

import pandas as pd

from chask.config import ANALYTICS_DIR, INTERVENTION_CUTOFF, STAGING_DIR


def to_staging(df: pd.DataFrame) -> pd.DataFrame:
    """Write the validated dataset to the staging layer and return it.

    Args:
        df: Validated monthly DataFrame.

    Returns:
        The same DataFrame (unchanged), after writing to ``STAGING_DIR``.
    """
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    out = STAGING_DIR / "monthly_validated.csv"
    df.to_csv(out, index=False, date_format="%Y-%m-%d")
    return df


def to_analytics(df: pd.DataFrame) -> pd.DataFrame:
    """Enrich the staging dataset with derived features and write to analytics layer.

    Derived columns:

    - ``intensity_kwh_kg``: energy intensity (kWh per kg of production).
    - ``gross_margin_pct``: gross margin percentage.
    - ``profit_usd``: absolute profit in USD.
    - ``cost_per_kg``: production cost per kg.
    - ``period``: ``"pre"`` if on or before the intervention cutoff, ``"post"`` after.

    Args:
        df: Validated monthly DataFrame (from staging layer).

    Returns:
        Enriched DataFrame with derived columns added.
    """
    cutoff = pd.Timestamp(INTERVENTION_CUTOFF)
    enriched = df.copy()
    enriched["intensity_kwh_kg"] = enriched["consumo_kwh"] / enriched["produccion_kg"]
    enriched["gross_margin_pct"] = (
        (enriched["ventas_usd"] - enriched["costos_usd"]) / enriched["ventas_usd"] * 100
    )
    enriched["profit_usd"] = enriched["ventas_usd"] - enriched["costos_usd"]
    enriched["cost_per_kg"] = enriched["costos_usd"] / enriched["produccion_kg"]
    enriched["period"] = enriched["fecha"].apply(lambda d: "pre" if d <= cutoff else "post")

    ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)
    out = ANALYTICS_DIR / "monthly_enriched.csv"
    enriched.to_csv(out, index=False, date_format="%Y-%m-%d")
    return enriched
