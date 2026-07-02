"""Reproducible reconstruction of the Panificadora Chask monthly operational dataset.

The original operational records from Panificadora Chask are confidential client data
and are not included in this repository. This module generates a monthly dataset
calibrated to the documented project outcomes from the INGEDAV S.R.L. engineering
closure report (2022) and the company profile document.

All rows are synthetically constructed from the design parameters below. The output
is explicitly labeled as a reconstruction in the filename, data dictionary, and README.

Design parameters approved by project director Anthony Davila.

Run with::

    python -m chask.datagen.monthly_reconstruction
"""

import numpy as np
import pandas as pd

from chask.config import RANDOM_SEED, RAW_DIR

# ---------------------------------------------------------------------------
# Design constants (documented project parameters from field report)
# ---------------------------------------------------------------------------

# Documented pre-intervention baseline energy consumption (kWh/month)
BASELINE_KWH: float = 55_000.0

# Documented steady-state energy consumption after full implementation (-27%)
STEADY_STATE_KWH: float = 40_150.0

# Implicit product price (USD per kg of bakery output)
PRICE_PER_KG: float = 1.53

# Cost structure: fixed overhead + variable per-unit + energy cost
FIXED_COST_USD: float = 7_000.0  # monthly fixed overhead (USD)
VAR_COST_PER_KG: float = 0.42  # variable cost per kg (materials + labor)
ENERGY_TARIFF: float = 0.068  # electricity tariff (USD / kWh)

# Noise levels (standard deviations for multiplicative normal noise)
_KWH_NOISE: float = 0.018
_PROD_NOISE: float = 0.025
_PRICE_NOISE: float = 0.028
_COST_NOISE: float = 0.018

# Output filename
RECONSTRUCTED_FILENAME: str = "monthly_reconstructed.csv"


def _month_end_dates() -> pd.DatetimeIndex:
    starts = pd.date_range("2020-01-01", periods=29, freq="MS")
    return starts + pd.offsets.MonthEnd(0)


# ---------------------------------------------------------------------------
# Target vectors — deterministic baselines per month
# ---------------------------------------------------------------------------

# Energy (kWh/month): baseline → Phase 3 decline → commissioning → steady state
_KWH_TARGETS = np.array(
    [
        # Jan–Aug 2020: near-baseline (Phase 1 diagnostics, no major changes yet)
        55_100,
        54_200,
        55_300,
        54_100,
        55_200,
        53_900,
        54_100,
        53_200,
        # Sep–Dec 2020: modest improvement as Phase 1 findings implemented
        52_800,
        52_600,
        51_900,
        51_800,
        # Jan–Apr 2021: continued gradual decline (Phase 2 design complete, early fixes)
        51_200,
        50_800,
        50_100,
        50_300,
        # May–Aug 2021: Phase 3 progressive removal of inefficient machinery
        49_100,
        48_200,
        47_300,
        46_100,
        # Sep–Nov 2021: commissioning transient (Sep elevated due to failures)
        47_200,
        44_800,
        42_600,
        # Dec 2021–May 2022: steady state (~-27 % vs 55,000 baseline)
        40_100,
        39_800,
        40_200,
        39_900,
        40_100,
        40_000,
    ],
    dtype=float,
)

# Machine failures (count / month) — deterministic integers
# Anomaly months: Apr 2020 (idx 3, =12), Oct 2020 (idx 9, =10), Mar 2021 (idx 14, =11)
# Commissioning spike: Sep–Oct 2021 (idx 20–21: 10, 9)
_FALLAS_TARGETS = np.array(
    [
        8,
        7,
        9,
        12,
        7,
        8,
        7,
        6,  # Jan–Aug 2020  (Apr = 12: anomaly)
        8,
        10,
        7,
        8,  # Sep–Dec 2020  (Oct = 10: anomaly)
        9,
        7,
        11,
        7,  # Jan–Apr 2021  (Mar = 11: anomaly)
        7,
        8,
        8,
        7,  # May–Aug 2021
        10,
        9,
        6,  # Sep–Nov 2021  (commissioning spike)
        3,
        2,
        2,
        3,
        2,
        2,  # Dec 2021–May 2022 (steady state)
    ],
    dtype=int,
)

# Downtime (hours / month) — correlated with failures
_INACT_TARGETS = np.array(
    [
        25,
        22,
        30,
        48,
        20,
        25,
        22,
        18,  # Jan–Aug 2020  (Apr = 48)
        28,
        42,
        22,
        26,  # Sep–Dec 2020  (Oct = 42)
        32,
        22,
        45,
        20,  # Jan–Apr 2021  (Mar = 45)
        22,
        26,
        25,
        22,  # May–Aug 2021
        35,
        32,
        20,  # Sep–Nov 2021  (commissioning)
        10,
        9,
        8,
        9,
        8,
        10,  # Dec 2021–May 2022 (steady state)
    ],
    dtype=float,
)

# Production (kg / month): stable pre with dips on high-failure months,
# commissioning dip in Sep 2021, then +22 % growth to steady state
_PROD_TARGETS = np.array(
    [
        13_800,
        14_100,
        13_500,
        11_500,
        14_200,
        13_800,
        14_100,
        14_500,
        13_500,
        12_000,
        14_200,
        13_800,
        13_200,
        14_100,
        11_800,
        14_200,
        14_100,
        13_800,
        13_700,
        14_100,
        13_200,
        13_800,
        14_500,
        15_200,
        15_500,
        15_800,
        16_200,
        16_500,
        16_800,
    ],
    dtype=float,
)

# Planned maintenance events (count / month)
_MAINT_TARGETS = np.array(
    [
        3,
        2,
        3,
        4,
        2,
        3,
        2,
        2,
        3,
        4,
        2,
        3,
        3,
        2,
        4,
        2,
        2,
        3,
        3,
        2,
        4,
        5,
        3,
        2,
        1,
        1,
        2,
        1,
        1,
    ],
    dtype=int,
)


def generate_monthly(seed: int = RANDOM_SEED) -> pd.DataFrame:
    """Generate the reconstructed monthly dataset (29 rows, Jan 2020 – May 2022).

    Values are deterministic baselines with small multiplicative noise added via
    ``seed`` to produce month-to-month variability. Two calls with the same seed
    return identical output.

    Args:
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with the same 8 columns as the raw monthly schema:
        ``fecha``, ``produccion_kg``, ``consumo_kwh``, ``fallas_maquina``,
        ``mantenimiento``, ``ventas_usd``, ``costos_usd``,
        ``tiempo_inactividad_horas``.
    """
    rng = np.random.default_rng(seed)
    dates = _month_end_dates()

    kwh = _KWH_TARGETS * (1.0 + rng.normal(0.0, _KWH_NOISE, 29))
    prod = np.clip(_PROD_TARGETS * (1.0 + rng.normal(0.0, _PROD_NOISE, 29)), 1.0, None)
    inact = np.clip(_INACT_TARGETS * (1.0 + rng.normal(0.0, 0.04, 29)), 0.5, None)

    price_multiplier = 1.0 + rng.normal(0.0, _PRICE_NOISE, 29)
    ventas = prod * PRICE_PER_KG * price_multiplier

    cost_multiplier = 1.0 + rng.normal(0.0, _COST_NOISE, 29)
    costos = (FIXED_COST_USD + VAR_COST_PER_KG * prod + ENERGY_TARIFF * kwh) * cost_multiplier

    return pd.DataFrame(
        {
            "fecha": dates,
            "produccion_kg": np.round(prod).astype(float),
            "consumo_kwh": np.round(kwh, 2),
            "fallas_maquina": _FALLAS_TARGETS.copy(),
            "mantenimiento": _MAINT_TARGETS.copy(),
            "ventas_usd": np.round(ventas).astype(float),
            "costos_usd": np.round(costos).astype(float),
            "tiempo_inactividad_horas": np.round(inact, 1),
        }
    )


def write_monthly(seed: int = RANDOM_SEED) -> str:
    """Generate and write the reconstructed monthly CSV to ``data/raw/``.

    Args:
        seed: Random seed passed to :func:`generate_monthly`.

    Returns:
        Path to the written CSV as a string.
    """
    df = generate_monthly(seed)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out = RAW_DIR / RECONSTRUCTED_FILENAME
    df.to_csv(out, index=False, date_format="%Y-%m-%d")
    return str(out)


def _print_summary(df: pd.DataFrame) -> None:
    cutoff = pd.Timestamp("2021-08-31")
    pre = df[df["fecha"] <= cutoff]
    post = df[df["fecha"] > cutoff]
    ss = df[df["fecha"] >= pd.Timestamp("2021-12-31")]  # steady state: Dec 2021–May 2022

    cols = {
        "consumo_kwh": "Energy (kWh)",
        "produccion_kg": "Production (kg)",
        "fallas_maquina": "Failures /month",
        "tiempo_inactividad_horas": "Downtime (h)",
        "ventas_usd": "Sales (USD)",
    }
    margin_pre = ((pre["ventas_usd"] - pre["costos_usd"]) / pre["ventas_usd"] * 100).mean()
    margin_post = ((post["ventas_usd"] - post["costos_usd"]) / post["ventas_usd"] * 100).mean()

    print("=" * 70)
    print("Reconstructed monthly dataset — pre/post summary")
    print("=" * 70)
    print(f"{'Metric':<28} {'Pre (n=20)':>12} {'Post (n=9)':>12} {'Change':>10}")
    print("-" * 70)
    for col, label in cols.items():
        pm = pre[col].mean()
        pom = post[col].mean()
        pct = (pom - pm) / pm * 100
        print(f"{label:<28} {pm:>12.1f} {pom:>12.1f} {pct:>+9.1f}%")
    print(
        f"{'Gross margin (%)':<28} {margin_pre:>12.1f} {margin_post:>12.1f} "
        f"{margin_post - margin_pre:>+9.1f} pp"
    )
    print("-" * 70)
    baseline = _KWH_TARGETS[:8].mean()  # Jan–Aug 2020 average as baseline
    ss_mean = ss["consumo_kwh"].mean()
    print(f"Energy baseline (Jan–Aug 2020): {baseline:,.0f} kWh")
    print(
        f"Energy steady state (Dec'21–May'22): {ss_mean:,.0f} kWh  "
        f"({(ss_mean - baseline) / baseline * 100:+.1f}% vs baseline)"
    )
    print("=" * 70)


if __name__ == "__main__":
    path = write_monthly()
    df = pd.read_csv(path, parse_dates=["fecha"])
    print(f"Written: {path}  ({len(df)} rows)")
    print()
    _print_summary(df)
