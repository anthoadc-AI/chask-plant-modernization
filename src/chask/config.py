"""Central configuration: project paths, dataset constants, and global settings."""

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = _REPO_ROOT / "data" / "raw"
STAGING_DIR = _REPO_ROOT / "data" / "staging"
ANALYTICS_DIR = _REPO_ROOT / "data" / "analytics"

RAW_DATASET = "dataset_panificadora.csv"

INTERVENTION_CUTOFF = "2021-08-31"

RANDOM_SEED = 42

COLUMNS: list[str] = [
    "fecha",
    "produccion_kg",
    "consumo_kwh",
    "fallas_maquina",
    "mantenimiento",
    "ventas_usd",
    "costos_usd",
    "tiempo_inactividad_horas",
]
