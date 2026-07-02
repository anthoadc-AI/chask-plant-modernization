"""Generate a calibrated synthetic daily dataset from the real monthly aggregates.

The synthetic dataset is calibrated so that summing daily values back to monthly
totals reproduces the original monthly figures exactly (within floating-point
precision for continuous variables; exactly for discrete event counts).

Run with::

    python -m chask.datagen.synthetic
"""

import numpy as np
import pandas as pd

from chask.config import ANALYTICS_DIR, INTERVENTION_CUTOFF, RANDOM_SEED
from chask.pipeline.ingest import load_raw

# Relative production weight by day of week (Mon=0 … Sun=6) for a bakery.
# Higher on Friday/Saturday (weekend preparation), lower on Sunday (rest day).
_WEEKDAY_WEIGHTS: dict[int, float] = {
    0: 1.00,  # Monday
    1: 1.00,  # Tuesday
    2: 1.00,  # Wednesday
    3: 1.10,  # Thursday
    4: 1.30,  # Friday
    5: 1.40,  # Saturday
    6: 0.60,  # Sunday
}


def _weekday_factors(dates: pd.DatetimeIndex) -> np.ndarray:
    return np.array([_WEEKDAY_WEIGHTS[d.weekday()] for d in dates])


def _distribute(monthly_total: float, weights: np.ndarray) -> np.ndarray:
    """Scale ``weights`` so they sum to ``monthly_total``."""
    return weights / weights.sum() * monthly_total


def _pick_event_days(n: int, k: int, rng: np.random.Generator) -> np.ndarray:
    """Return a binary array of length ``n`` with exactly ``k`` ones."""
    arr = np.zeros(n, dtype=int)
    if k > 0:
        idx = rng.choice(n, size=min(k, n), replace=False)
        arr[idx] = 1
    return arr


def generate_daily(
    monthly_df: pd.DataFrame | None = None,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """Generate a daily synthetic DataFrame calibrated against monthly aggregates.

    Args:
        monthly_df: Monthly dataset (29 rows). If ``None``, loads from disk.
        seed: Random seed for reproducibility.

    Returns:
        Daily DataFrame with 882 rows (Jan 2020 – May 2022) and an
        ``is_synthetic`` column set to ``True`` throughout.
    """
    if monthly_df is None:
        monthly_df = load_raw()

    rng = np.random.default_rng(seed)
    rows: list[dict] = []
    cutoff = pd.Timestamp(INTERVENTION_CUTOFF)

    for _, month in monthly_df.iterrows():
        month_end: pd.Timestamp = month["fecha"]
        month_start = month_end.replace(day=1)
        dates = pd.date_range(month_start, month_end, freq="D")
        n = len(dates)

        base_factors = _weekday_factors(dates)
        noise = rng.lognormal(0.0, 0.15, size=n)
        weights = base_factors * noise

        prod_daily = _distribute(float(month["produccion_kg"]), weights)
        ventas_daily = _distribute(float(month["ventas_usd"]), weights)
        costos_daily = _distribute(float(month["costos_usd"]), weights)
        inact_daily = _distribute(float(month["tiempo_inactividad_horas"]), weights)

        # Failure days drive higher energy consumption.
        fallas = _pick_event_days(n, int(month["fallas_maquina"]), rng)
        maint = _pick_event_days(n, int(month["mantenimiento"]), rng)
        kwh_weights = weights * (1.0 + 0.3 * fallas)
        kwh_daily = _distribute(float(month["consumo_kwh"]), kwh_weights)

        period = "pre" if month_end <= cutoff else "post"

        for i, day in enumerate(dates):
            rows.append(
                {
                    "fecha": day,
                    "produccion_kg": prod_daily[i],
                    "consumo_kwh": kwh_daily[i],
                    "fallas_maquina": fallas[i],
                    "mantenimiento": maint[i],
                    "ventas_usd": ventas_daily[i],
                    "costos_usd": costos_daily[i],
                    "tiempo_inactividad_horas": inact_daily[i],
                    "period": period,
                    "is_synthetic": True,
                }
            )

    return pd.DataFrame(rows)


def write_daily(df: pd.DataFrame | None = None, seed: int = RANDOM_SEED) -> str:
    """Generate and write the daily synthetic CSV to the analytics layer.

    Args:
        df: Pre-loaded monthly DataFrame. If ``None``, loads from disk.
        seed: Random seed passed to :func:`generate_daily`.

    Returns:
        Path to the written CSV as a string.
    """
    daily = generate_daily(monthly_df=df, seed=seed)
    ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)
    out = ANALYTICS_DIR / "daily_synthetic.csv"
    daily.to_csv(out, index=False, date_format="%Y-%m-%d")
    return str(out)


if __name__ == "__main__":
    path = write_daily()
    df = pd.read_csv(path)
    print("=" * 60)
    print("Synthetic daily dataset")
    print("=" * 60)
    print(f"  Rows written   : {len(df)}")
    print(f"  Date range     : {df['fecha'].iloc[0]} to {df['fecha'].iloc[-1]}")
    print(f"  File           : {path}")
    print("=" * 60)
