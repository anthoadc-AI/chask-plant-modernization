"""Central configuration: project paths, dataset constants, and global settings."""

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = _REPO_ROOT / "data" / "raw"
STAGING_DIR = _REPO_ROOT / "data" / "staging"
ANALYTICS_DIR = _REPO_ROOT / "data" / "analytics"

RAW_DATASET = "monthly_reconstructed.csv"

INTERVENTION_CUTOFF = "2021-08-31"

RANDOM_SEED = 42

# --- Energy analysis assumptions ---
# Bolivia ENDE industrial tariff, circa 2021 (assumption — update if rate changes)
ENERGY_TARIFF_USD_KWH: float = 0.065
# Bolivia SIN grid emission factor (approximate; IEA 2020 / CNDC data)
EMISSION_FACTOR_KG_CO2_KWH: float = 0.40
# Nominal monthly operating hours (24 h/day × 30 days)
MONTHLY_OPERATING_HOURS: float = 720.0
# Post-intervention installed capacity multiplier (engineering report)
POST_CAPACITY_MULTIPLIER: float = 1.5
# ROI analysis discount rate (assumption)
DISCOUNT_RATE: float = 0.10
# Total project investment (USD)
TOTAL_INVESTMENT_USD: float = 85_000.0

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
