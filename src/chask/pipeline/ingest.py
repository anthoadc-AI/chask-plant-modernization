"""Load the raw monthly dataset from disk."""

from pathlib import Path

import pandas as pd

from chask.config import COLUMNS, RAW_DATASET, RAW_DIR


def load_raw(path: Path | None = None) -> pd.DataFrame:
    """Load raw monthly dataset with explicit dtypes and date parsing.

    Args:
        path: Override path to the CSV. Defaults to ``RAW_DIR / RAW_DATASET``.

    Returns:
        DataFrame with ``fecha`` parsed as datetime and all expected columns present.

    Raises:
        FileNotFoundError: If the CSV file does not exist at ``path``.
        ValueError: If the CSV is missing one or more expected columns.
    """
    csv_path = path or (RAW_DIR / RAW_DATASET)
    if not Path(csv_path).exists():
        raise FileNotFoundError(f"Raw dataset not found: {csv_path}")

    df = pd.read_csv(
        csv_path,
        parse_dates=["fecha"],
        dtype={
            "produccion_kg": float,
            "consumo_kwh": float,
            "fallas_maquina": int,
            "mantenimiento": int,
            "ventas_usd": float,
            "costos_usd": float,
            "tiempo_inactividad_horas": float,
        },
    )

    missing = set(COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Raw CSV is missing expected columns: {sorted(missing)}")

    return df[COLUMNS]
