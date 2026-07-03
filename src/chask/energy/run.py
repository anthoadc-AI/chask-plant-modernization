"""CLI entry point for Phase 3 energy and process analysis.

Usage::

    python -m chask.energy.run
    # or via Makefile:
    make energy
"""

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

matplotlib.use("Agg")

import pathlib  # noqa: E402

from chask.energy.kpis import annualized_savings, energy_intensity_rolling, monthly_savings
from chask.energy.motors import reconciliation
from chask.energy.roi import compute_roi_scenarios, payback_curves
from chask.pipeline.ingest import load_raw
from chask.pipeline.transform import to_analytics
from chask.pipeline.validate import validate
from chask.process.reliability import failure_trends, reliability_summary
from chask.process.throughput import throughput_summary

_REPORTS_DIR = pathlib.Path(__file__).resolve().parents[3] / "reports" / "figures"
_PALETTE = {"pre": "#2196F3", "post": "#4CAF50", "ss": "#009688", "neutral": "#607D8B"}


def _plot_energy_intensity(df: pd.DataFrame, out_dir: pathlib.Path) -> None:
    rolled = energy_intensity_rolling(df)
    fig, ax = plt.subplots(figsize=(13, 5))
    ax.plot(
        df["fecha"],
        df["intensity_kwh_kg"],
        "o",
        color=_PALETTE["neutral"],
        alpha=0.6,
        ms=5,
        label="Monthly",
    )
    ax.plot(
        rolled["fecha"],
        rolled["intensity_rolling"],
        "-",
        color="#E91E63",
        lw=2,
        label="3-month rolling avg",
    )
    ax.axvline(
        pd.Timestamp("2021-08-31"),
        color=_PALETTE["pre"],
        ls="--",
        lw=1.5,
        label="Intervention cutoff",
    )
    ax.axvline(
        pd.Timestamp("2021-11-30"),
        color=_PALETTE["ss"],
        ls=":",
        lw=1.2,
        label="Steady-state start (Dec 2021)",
    )
    ax.set_xlabel("Month")
    ax.set_ylabel("Energy intensity (kWh/kg)")
    ax.set_title("Energy intensity — monthly and 3-month rolling average", fontsize=12)
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / "07_energy_intensity.png", dpi=120, bbox_inches="tight")
    plt.close(fig)


def _plot_savings(df: pd.DataFrame, out_dir: pathlib.Path) -> None:
    saved = monthly_savings(df)
    fig, axes = plt.subplots(2, 1, figsize=(13, 8), sharex=True)
    ax1, ax2 = axes
    colors = [_PALETTE["post"] if v >= 0 else "#F44336" for v in saved["savings_kwh"]]
    ax1.bar(saved["fecha"], saved["savings_kwh"], color=colors, width=20)
    ax1.axhline(0, color="black", lw=0.8)
    ax1.set_ylabel("kWh saved vs baseline")
    ax1.set_title("Monthly energy savings vs. pre-intervention baseline", fontsize=12)
    ax1.grid(alpha=0.3, axis="y")
    ax2.bar(saved["fecha"], saved["co2_avoided_kg"], color=_PALETTE["ss"], width=20)
    ax2.set_ylabel("kgCO₂ avoided")
    ax2.set_title("CO₂ emissions avoided (Bolivia SIN factor: 0.40 kgCO₂/kWh)", fontsize=11)
    ax2.grid(alpha=0.3, axis="y")
    plt.tight_layout()
    fig.savefig(out_dir / "08_energy_savings.png", dpi=120, bbox_inches="tight")
    plt.close(fig)


def _plot_payback_curves(df: pd.DataFrame, out_dir: pathlib.Path) -> None:
    curves = payback_curves(df)
    from chask.config import TOTAL_INVESTMENT_USD

    fig, ax = plt.subplots(figsize=(11, 6))
    palette = {"Conservative": "#F44336", "Base": "#FF9800", "Optimistic": "#4CAF50"}
    for scenario in ["Conservative", "Base", "Optimistic"]:
        ax.plot(
            curves["year"], curves[scenario], "-o", lw=2, color=palette[scenario], label=scenario
        )
    ax.axhline(0, color="black", lw=1.0, ls="--")
    ax.set_xlabel("Year")
    ax.set_ylabel("Cumulative discounted cash flow (USD)")
    ax.set_title(
        f"ROI payback curves — USD {TOTAL_INVESTMENT_USD:,.0f} investment (10% discount rate)",
        fontsize=12,
    )
    ax.legend(fontsize=10)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.grid(alpha=0.3)
    plt.tight_layout()
    fig.savefig(out_dir / "09_roi_payback_curves.png", dpi=120, bbox_inches="tight")
    plt.close(fig)


def _plot_mtbf(df: pd.DataFrame, out_dir: pathlib.Path) -> None:
    from chask.process.reliability import mtbf_monthly

    enriched = mtbf_monthly(df)
    fig, ax = plt.subplots(figsize=(13, 5))
    colors = [_PALETTE["pre"] if p == "pre" else _PALETTE["post"] for p in enriched["period"]]
    ax.bar(enriched["fecha"], enriched["mtbf_h"], color=colors, width=20, alpha=0.7)
    ax.axvline(
        pd.Timestamp("2021-08-31"), color="black", ls="--", lw=1.5, label="Intervention cutoff"
    )
    ax.set_xlabel("Month")
    ax.set_ylabel("MTBF (h)")
    ax.set_title("Approx. monthly MTBF — machine failures", fontsize=12)
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3, axis="y")
    plt.tight_layout()
    fig.savefig(out_dir / "10_mtbf.png", dpi=120, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    df = to_analytics(validate(load_raw()))
    out = _REPORTS_DIR

    print("=== Energy KPIs ===")
    savings = annualized_savings(df)
    for k, v in savings.items():
        print(f"  {k}: {v}")

    print()
    print("=== Motor reconciliation ===")
    observed_mo = savings["baseline_kwh_mo"] - savings["ss_mean_kwh_mo"]
    rec = reconciliation(observed_mo)
    for k, v in rec.items():
        print(f"  {k}: {v}")

    print()
    print("=== Throughput summary ===")
    print(throughput_summary(df).to_string())

    print()
    print("=== Reliability summary ===")
    rel = reliability_summary(df)
    for k, v in rel.items():
        print(f"  {k}: {v}")

    print()
    print("=== Failure trends ===")
    print(failure_trends(df).to_string())

    print()
    print("=== ROI scenarios ===")
    roi = compute_roi_scenarios(df)
    print(roi.to_string(index=False))

    print()
    print("Generating Phase 3 figures …")
    _plot_energy_intensity(df, out)
    print("  [1/4] energy_intensity")
    _plot_savings(df, out)
    print("  [2/4] energy_savings")
    _plot_payback_curves(df, out)
    print("  [3/4] roi_payback_curves")
    _plot_mtbf(df, out)
    print("  [4/4] mtbf")


if __name__ == "__main__":
    main()
