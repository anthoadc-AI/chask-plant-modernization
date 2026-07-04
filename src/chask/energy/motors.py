"""Motor replacement savings model for the Panificadora Chask fleet.

Assumptions (documented; see ``docs/energy-analysis.md``):
- Power ratings are rated *mechanical output* (shaft power, kW).
  Electrical input = mechanical output / efficiency.
- Old motors: IE1-class wound rotors, >5 years service, degraded windings.
  Efficiency range 0.75–0.82.
- New motors: IE3-class premium efficiency.
  Efficiency range 0.885–0.930 (per IEC 60034-30-1, 2-15 kW band).
- Monthly operating hours estimated from production schedule
  (two shifts, 6 days/week; soplantes/ventilación continuous).
- Inventory is a plausible reconstruction for a medium bolivian industrial
  bakery producing ~14,000 kg/month; exact asset register is confidential.

Savings formula per motor:
    savings_kwh_mo = P_mec_kW × h/mo × (1/η_old − 1/η_new)

Reconciliation note:
    The theoretical motor savings (~7,200 kWh/mo) account for ~61% of the
    observed reduction.  The remaining ~39% is a *residual* attributed to
    non-motor improvements identified in the field diagnostic (high-resistance
    connections, phantom load, demand-shaping automation).  These three items
    were NOT separately metered; the breakdown below is an estimated allocation
    of the residual consistent with the diagnostic findings.
"""

from __future__ import annotations

import pandas as pd

# ---------------------------------------------------------------------------
# Motor inventory — all physical constants must be named and documented
# ---------------------------------------------------------------------------


def _m(name: str, kw: float, n: int, e_old: float, e_new: float, h: int) -> dict:
    return {
        "name": name,
        "power_kw": kw,
        "count": n,
        "eff_old": e_old,
        "eff_new": e_new,
        "hours_per_month": h,
    }


MOTOR_INVENTORY: list[dict] = [
    # name                       kW    n  η_old  η_new   h/mo
    _m("Amasadora espiral 1", 11.0, 2, 0.780, 0.921, 360),
    _m("Amasadora espiral 2", 7.5, 1, 0.770, 0.912, 320),
    _m("Laminadora", 5.5, 2, 0.750, 0.900, 300),
    _m("Batidora industrial", 3.7, 3, 0.760, 0.895, 280),
    _m("Ventilacion auxiliar", 2.2, 4, 0.800, 0.900, 720),
    _m("Transporte interno", 1.5, 3, 0.780, 0.885, 480),
    _m("Soplante horno rot.", 15.0, 2, 0.820, 0.930, 600),
]

# Estimated allocation of the non-motor residual.
# These figures are indicative; individual components were NOT separately metered.
# They reflect the field-diagnostic categories and must be presented with ranges.
# Central values sum to approximately the observed residual (~4,570 kWh/mo).
NON_MOTOR_RESIDUAL_ALLOCATION: dict[str, float] = {
    "defective_connections_kwh_mo": 2_000.0,  # range: 1,800–2,200
    "phantom_load_kwh_mo": 1_500.0,  # range: 1,200–1,800
    "automation_peak_reduction_kwh_mo": 1_074.0,  # range:   800–1,300
}

# Keep legacy alias so callers that import the old name still work
NON_MOTOR_SAVINGS_BREAKDOWN = NON_MOTOR_RESIDUAL_ALLOCATION

_RESIDUAL_ALLOCATION_NOTE: str = (
    "Allocation is indicative; individual components were not separately metered. "
    "Ranges: connections 1,800–2,200 kWh/mo, phantom load 1,200–1,800 kWh/mo, "
    "automation 800–1,300 kWh/mo."
)


def motor_savings_detail(
    inventory: list[dict] | None = None,
) -> pd.DataFrame:
    """Compute monthly kWh savings per motor group from efficiency improvement.

    Args:
        inventory: List of motor dicts. Defaults to :data:`MOTOR_INVENTORY`.

    Returns:
        DataFrame with one row per motor group and columns:
        ``name``, ``power_kw``, ``count``, ``eff_old``, ``eff_new``,
        ``hours_per_month``, ``savings_kwh_mo`` (per unit),
        ``savings_kwh_mo_total`` (× count).
    """
    inv = inventory or MOTOR_INVENTORY
    rows = []
    for m in inv:
        savings_unit = (
            m["power_kw"] * m["hours_per_month"] * (1.0 / m["eff_old"] - 1.0 / m["eff_new"])
        )
        rows.append(
            {
                "name": m["name"],
                "power_kw": m["power_kw"],
                "count": m["count"],
                "eff_old": m["eff_old"],
                "eff_new": m["eff_new"],
                "hours_per_month": m["hours_per_month"],
                "savings_kwh_mo": round(savings_unit, 1),
                "savings_kwh_mo_total": round(savings_unit * m["count"], 1),
            }
        )
    return pd.DataFrame(rows)


def total_motor_savings_kwh_mo(inventory: list[dict] | None = None) -> float:
    """Return aggregate monthly kWh savings from motor fleet replacement.

    Args:
        inventory: Motor inventory. Defaults to :data:`MOTOR_INVENTORY`.

    Returns:
        Total theoretical monthly savings in kWh.
    """
    df = motor_savings_detail(inventory)
    return float(df["savings_kwh_mo_total"].sum())


def reconciliation(
    observed_savings_kwh_mo: float,
    inventory: list[dict] | None = None,
    non_motor: dict | None = None,  # accepted but not used to compute residual
) -> dict:
    """Compare theoretical motor savings vs. observed dataset savings.

    Only the motor-fleet calculation is independently derived.  The residual
    (observed − theoretical) is consistent with non-motor improvements found
    in the field diagnostic, but those items were not separately metered.

    Args:
        observed_savings_kwh_mo: Mean monthly kWh reduction (pre − SS mean).
        inventory: Motor inventory. Defaults to :data:`MOTOR_INVENTORY`.
        non_motor: Accepted for API compatibility; not used to compute residual.

    Returns:
        Dict with ``theoretical_motor_kwh_mo``, ``observed_kwh_mo``,
        ``residual_kwh_mo``, ``motor_share_pct``, ``residual_share_pct``,
        and ``residual_allocation_note``.
    """
    theoretical = total_motor_savings_kwh_mo(inventory)
    residual = observed_savings_kwh_mo - theoretical

    return {
        "theoretical_motor_kwh_mo": round(theoretical, 1),
        "observed_kwh_mo": round(observed_savings_kwh_mo, 1),
        "residual_kwh_mo": round(residual, 1),
        "motor_share_pct": round(theoretical / observed_savings_kwh_mo * 100, 1),
        "residual_share_pct": round(residual / observed_savings_kwh_mo * 100, 1),
        "residual_allocation_note": _RESIDUAL_ALLOCATION_NOTE,
    }
