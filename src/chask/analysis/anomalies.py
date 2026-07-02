"""Anomaly detection: univariate Z-score and multivariate Isolation Forest.

Works on both the real monthly dataset (n=29) and the synthetic daily dataset
(n=882). When used on the synthetic daily dataset, results are for demonstration
only and must not be used for statistical inference (the daily values are derived
from the monthly aggregates; using them for inference would inflate sample size
artificially).
"""

import pandas as pd
from sklearn.ensemble import IsolationForest  # noqa: F401

from chask.config import RANDOM_SEED

OPERATIONAL_COLS = [
    "consumo_kwh",
    "produccion_kg",
    "fallas_maquina",
    "tiempo_inactividad_horas",
    "intensity_kwh_kg",
]

ZSCORE_THRESHOLD = 2.0


def detect_zscore(
    df: pd.DataFrame,
    columns: list[str] | None = None,
    threshold: float = ZSCORE_THRESHOLD,
) -> pd.DataFrame:
    """Detect anomalies using per-column Z-score (univariate).

    A row is flagged if any column's |Z-score| exceeds ``threshold``.

    Args:
        df: Input DataFrame (monthly real or daily synthetic).
        columns: Columns to include. Defaults to :data:`OPERATIONAL_COLS`
            (only those present in ``df``).
        threshold: Z-score magnitude threshold (default 2.0).

    Returns:
        Copy of ``df`` with added columns:
        ``z_{col}`` for each tested column, ``zscore_anomaly`` (bool),
        and ``zscore_max_z`` (maximum |Z| across columns per row).
    """
    cols = [c for c in (columns or OPERATIONAL_COLS) if c in df.columns]
    out = df.copy()
    z_cols = []
    for col in cols:
        z = (df[col] - df[col].mean()) / df[col].std(ddof=1)
        out[f"z_{col}"] = z
        z_cols.append(f"z_{col}")

    out["zscore_max_z"] = out[z_cols].abs().max(axis=1)
    out["zscore_anomaly"] = out["zscore_max_z"] > threshold
    return out


def detect_isolation_forest(
    df: pd.DataFrame,
    columns: list[str] | None = None,
    contamination: float = 0.1,
    n_estimators: int = 200,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """Detect anomalies using Isolation Forest (multivariate).

    Args:
        df: Input DataFrame.
        columns: Feature columns. Defaults to :data:`OPERATIONAL_COLS`
            (only those present in ``df``).
        contamination: Expected proportion of outliers (default 0.10).
        n_estimators: Number of trees in the forest (default 200).
        seed: Random seed for reproducibility.

    Returns:
        Copy of ``df`` with added columns:
        ``if_score`` (anomaly score, lower = more anomalous) and
        ``if_anomaly`` (bool, True = anomaly).
    """
    cols = [c for c in (columns or OPERATIONAL_COLS) if c in df.columns]
    X = df[cols].values  # noqa: N806
    clf = IsolationForest(
        contamination=contamination,
        n_estimators=n_estimators,
        random_state=seed,
    )
    clf.fit(X)
    out = df.copy()
    out["if_score"] = clf.score_samples(X)
    out["if_anomaly"] = clf.predict(X) == -1
    return out


def combined_anomalies(
    df: pd.DataFrame,
    columns: list[str] | None = None,
    threshold: float = ZSCORE_THRESHOLD,
    contamination: float = 0.1,
    n_estimators: int = 200,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """Run both Z-score and Isolation Forest and return a combined result.

    Args:
        df: Input DataFrame.
        columns: Feature columns. Defaults to :data:`OPERATIONAL_COLS`.
        threshold: Z-score threshold.
        contamination: IF contamination rate.
        n_estimators: IF number of trees.
        seed: Random seed.

    Returns:
        DataFrame with all Z-score and IF columns, plus
        ``any_anomaly`` (True if either method flags the row).
    """
    out = detect_zscore(df, columns=columns, threshold=threshold)
    out = detect_isolation_forest(
        out,
        columns=columns,
        contamination=contamination,
        n_estimators=n_estimators,
        seed=seed,
    )
    out["any_anomaly"] = out["zscore_anomaly"] | out["if_anomaly"]
    return out
