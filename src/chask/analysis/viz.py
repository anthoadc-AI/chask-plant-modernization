"""Static (matplotlib) and interactive (Plotly) figure generation.

All figures are saved to ``reports/figures/``. Matplotlib uses the Agg
backend so figures render in headless / CI environments without a display.

Run with::

    python -m chask.analysis.viz
"""

from __future__ import annotations

import pathlib

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px  # noqa: F401
import plotly.graph_objects as go

matplotlib.use("Agg")

from chask.config import INTERVENTION_CUTOFF  # noqa: E402

# ---------------------------------------------------------------------------
# Style constants
# ---------------------------------------------------------------------------

PALETTE = {
    "pre": "#2196F3",
    "post": "#4CAF50",
    "anomaly_zscore": "#FF9800",
    "anomaly_if": "#F44336",
    "cutoff": "#9C27B0",
    "steady_state": "#009688",
    "neutral": "#607D8B",
}
FIGSIZE = (12, 5)
DPI = 120

_CUTOFF = pd.Timestamp(INTERVENTION_CUTOFF)
_SS_START = pd.Timestamp("2021-12-31")
# Plotly add_vline requires numeric (Unix ms) for datetime x-axes on newer versions
_CUTOFF_MS = int(_CUTOFF.timestamp() * 1000)

_REPORTS_DIR = pathlib.Path(__file__).resolve().parents[3] / "reports" / "figures"


def _save(fig: plt.Figure, name: str, out_dir: pathlib.Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / f"{name}.png", dpi=DPI, bbox_inches="tight")
    plt.close(fig)


def _save_plotly(fig: go.Figure, name: str, out_dir: pathlib.Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(out_dir / f"{name}.html"), include_plotlyjs="cdn")


def plot_time_series(df: pd.DataFrame, out_dir: pathlib.Path = _REPORTS_DIR) -> None:
    """Time series of energy consumption and production with pre/post zones.

    Args:
        df: Monthly enriched DataFrame.
        out_dir: Directory for output files.
    """
    fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

    for ax, col, label, unit in zip(
        axes,
        ["consumo_kwh", "produccion_kg"],
        ["Energy consumption", "Production"],
        ["kWh / month", "kg / month"],
    ):
        pre = df[df["period"] == "pre"]
        post = df[df["period"] == "post"]
        ax.plot(pre["fecha"], pre[col], "o-", color=PALETTE["pre"], label="Pre", lw=2)
        ax.plot(post["fecha"], post[col], "s-", color=PALETTE["post"], label="Post", lw=2)
        ax.axvline(_CUTOFF, color=PALETTE["cutoff"], ls="--", lw=1.5, label="Intervention cutoff")
        ax.axvspan(df["fecha"].min(), _CUTOFF, alpha=0.06, color=PALETTE["pre"])
        ax.axvspan(_CUTOFF, df["fecha"].max(), alpha=0.06, color=PALETTE["post"])
        ax.set_ylabel(f"{label} ({unit})", fontsize=10)
        ax.legend(fontsize=9)
        ax.grid(alpha=0.3)

    axes[-1].set_xlabel("Month", fontsize=10)
    fig.suptitle("Monthly operational time series — Panificadora Chask", fontsize=12)
    plt.tight_layout()
    _save(fig, "01_time_series", out_dir)

    # Plotly interactive version (energy only)
    pfig = go.Figure()
    for period, color in [("pre", PALETTE["pre"]), ("post", PALETTE["post"])]:
        sub = df[df["period"] == period]
        pfig.add_trace(
            go.Scatter(
                x=sub["fecha"],
                y=sub["consumo_kwh"],
                mode="lines+markers",
                name=period.capitalize(),
                line={"color": color, "width": 2},
            )
        )
    pfig.add_vline(
        x=_CUTOFF_MS,
        line_dash="dash",
        line_color=PALETTE["cutoff"],
        annotation_text="Intervention cutoff",
    )
    pfig.update_layout(
        title="Energy consumption — Monthly (interactive)",
        xaxis_title="Month",
        yaxis_title="kWh / month",
        template="plotly_white",
    )
    _save_plotly(pfig, "01_time_series_interactive", out_dir)


def plot_boxplots(df: pd.DataFrame, out_dir: pathlib.Path = _REPORTS_DIR) -> None:
    """Box plots of key KPIs split by pre/post period.

    Args:
        df: Monthly enriched DataFrame.
        out_dir: Directory for output files.
    """
    kpis = [
        ("consumo_kwh", "Energy (kWh)"),
        ("intensity_kwh_kg", "Intensity (kWh/kg)"),
        ("gross_margin_pct", "Gross margin (%)"),
        ("fallas_maquina", "Failures /month"),
        ("tiempo_inactividad_horas", "Downtime (h)"),
        ("produccion_kg", "Production (kg)"),
    ]
    kpis = [(c, lbl) for c, lbl in kpis if c in df.columns]

    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    axes = axes.flatten()

    for ax, (col, label) in zip(axes, kpis):
        pre_vals = df[df["period"] == "pre"][col].dropna()
        post_vals = df[df["period"] == "post"][col].dropna()
        bp = ax.boxplot(
            [pre_vals, post_vals],
            tick_labels=["Pre", "Post"],
            patch_artist=True,
            medianprops={"color": "black", "lw": 2},
        )
        bp["boxes"][0].set_facecolor(PALETTE["pre"] + "80")
        bp["boxes"][1].set_facecolor(PALETTE["post"] + "80")
        ax.scatter([1] * len(pre_vals), pre_vals, color=PALETTE["pre"], alpha=0.6, s=30, zorder=3)
        ax.scatter(
            [2] * len(post_vals), post_vals, color=PALETTE["post"], alpha=0.6, s=30, zorder=3
        )
        ax.set_title(label, fontsize=10)
        ax.grid(alpha=0.3, axis="y")

    fig.suptitle("KPI distributions — Pre vs. Post intervention", fontsize=13)
    plt.tight_layout()
    _save(fig, "02_boxplots_pre_post", out_dir)


def plot_correlation_heatmap(df: pd.DataFrame, out_dir: pathlib.Path = _REPORTS_DIR) -> None:
    """Pearson correlation heatmap for operational variables.

    Args:
        df: Monthly enriched DataFrame.
        out_dir: Directory for output files.
    """
    from chask.analysis.eda import correlation_matrix

    corr = correlation_matrix(df)
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(corr.values, cmap="RdYlGn", vmin=-1, vmax=1)
    fig.colorbar(im, ax=ax, shrink=0.8)
    ax.set_xticks(range(len(corr.columns)))
    ax.set_yticks(range(len(corr.index)))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right", fontsize=8)
    ax.set_yticklabels(corr.index, fontsize=8)
    for i in range(len(corr)):
        for j in range(len(corr.columns)):
            ax.text(j, i, f"{corr.values[i, j]:.2f}", ha="center", va="center", fontsize=7)
    ax.set_title("Pearson correlation matrix — operational variables", fontsize=12)
    plt.tight_layout()
    _save(fig, "03_correlation_heatmap", out_dir)


def plot_anomalies(
    df: pd.DataFrame,
    anomaly_df: pd.DataFrame,
    out_dir: pathlib.Path = _REPORTS_DIR,
) -> None:
    """Mark detected anomalies on the energy consumption time series.

    Args:
        df: Monthly enriched DataFrame.
        anomaly_df: Output of :func:`~chask.analysis.anomalies.combined_anomalies`.
        out_dir: Directory for output files.
    """
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.plot(df["fecha"], df["consumo_kwh"], "o-", color=PALETTE["neutral"], lw=1.5, label="Energy")
    _false = pd.Series(False, index=anomaly_df.index)
    z_mask = anomaly_df["zscore_anomaly"] if "zscore_anomaly" in anomaly_df.columns else _false
    if_mask = anomaly_df["if_anomaly"] if "if_anomaly" in anomaly_df.columns else _false
    ax.scatter(
        df.loc[z_mask, "fecha"],
        df.loc[z_mask, "consumo_kwh"],
        marker="^",
        s=100,
        color=PALETTE["anomaly_zscore"],
        label="Z-score anomaly",
        zorder=5,
    )
    ax.scatter(
        df.loc[if_mask, "fecha"],
        df.loc[if_mask, "consumo_kwh"],
        marker="x",
        s=120,
        color=PALETTE["anomaly_if"],
        label="Isolation Forest anomaly",
        zorder=5,
        lw=2,
    )
    ax.axvline(_CUTOFF, color=PALETTE["cutoff"], ls="--", lw=1.5, label="Intervention cutoff")
    ax.set_xlabel("Month")
    ax.set_ylabel("Energy (kWh)")
    ax.set_title("Anomaly detection — Energy consumption", fontsize=12)
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    _save(fig, "04_anomalies", out_dir)


def plot_its(
    df: pd.DataFrame,
    its_results: dict,
    outcome_col: str = "consumo_kwh",
    out_dir: pathlib.Path = _REPORTS_DIR,
) -> None:
    """ITS segmented regression plot with fitted lines and intervention marker.

    Args:
        df: Monthly enriched DataFrame.
        its_results: Output of :func:`~chask.analysis.stats.its_analysis`.
        outcome_col: Outcome variable name (used for axis label).
        out_dir: Directory for output files.
    """
    its_df = its_results["its_df"]
    fitted = its_results["fitted"]
    coeffs = its_results["coefficients"]

    fig, ax = plt.subplots(figsize=FIGSIZE)
    pre_mask = its_df["D"] == 0
    post_mask = its_df["D"] == 1

    ax.scatter(
        its_df.loc[pre_mask, "fecha"],
        its_df.loc[pre_mask, outcome_col],
        color=PALETTE["pre"],
        s=50,
        label="Pre (observed)",
        zorder=4,
    )
    ax.scatter(
        its_df.loc[post_mask, "fecha"],
        its_df.loc[post_mask, outcome_col],
        color=PALETTE["post"],
        s=50,
        label="Post (observed)",
        zorder=4,
    )
    ax.plot(its_df["fecha"], fitted, color="black", lw=2, label="ITS fitted")

    # Counterfactual (pre trend extended)
    b0, b1 = coeffs["Intercept"], coeffs["t"]
    cf = b0 + b1 * its_df["t"]
    ax.plot(
        its_df["fecha"], cf, color=PALETTE["neutral"], lw=1.5, ls=":", label="Counterfactual trend"
    )

    ax.axvline(_CUTOFF, color=PALETTE["cutoff"], ls="--", lw=1.5, label="Intervention cutoff")
    ax.set_xlabel("Month")
    ax.set_ylabel(outcome_col.replace("_", " ").title())
    r2 = its_results["r_squared"]
    ax.set_title(f"Interrupted Time Series — {outcome_col}  (R²={r2:.3f})", fontsize=12)
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    _save(fig, f"05_its_{outcome_col}", out_dir)

    # Plotly interactive
    pfig = go.Figure()
    pfig.add_trace(
        go.Scatter(
            x=its_df["fecha"],
            y=its_df[outcome_col],
            mode="markers",
            name="Observed",
            marker={"color": [PALETTE["pre"] if v == 0 else PALETTE["post"] for v in its_df["D"]]},
        )
    )
    pfig.add_trace(
        go.Scatter(
            x=its_df["fecha"],
            y=fitted,
            mode="lines",
            name="ITS fitted",
            line={"color": "black", "width": 2},
        )
    )
    pfig.add_trace(
        go.Scatter(
            x=its_df["fecha"],
            y=cf,
            mode="lines",
            name="Counterfactual",
            line={"color": PALETTE["neutral"], "dash": "dot"},
        )
    )
    pfig.add_vline(
        x=_CUTOFF_MS,
        line_dash="dash",
        line_color=PALETTE["cutoff"],
        annotation_text="Intervention",
    )
    pfig.update_layout(
        title=f"ITS — {outcome_col} (interactive)",
        template="plotly_white",
        xaxis_title="Month",
        yaxis_title=outcome_col,
    )
    _save_plotly(pfig, f"05_its_{outcome_col}_interactive", out_dir)


def plot_margin_sales(df: pd.DataFrame, out_dir: pathlib.Path = _REPORTS_DIR) -> None:
    """Dual-axis chart: monthly sales (bars) and gross margin (line).

    Args:
        df: Monthly enriched DataFrame.
        out_dir: Directory for output files.
    """
    fig, ax1 = plt.subplots(figsize=(14, 5))
    ax2 = ax1.twinx()

    colors = [PALETTE["pre"] if p == "pre" else PALETTE["post"] for p in df["period"]]
    ax1.bar(df["fecha"], df["ventas_usd"], color=colors, alpha=0.6, width=20, label="Sales (USD)")
    ax2.plot(
        df["fecha"], df["gross_margin_pct"], "o-", color="#E91E63", lw=2, label="Gross margin (%)"
    )
    ax2.axhline(
        df[df["period"] == "pre"]["gross_margin_pct"].mean(),
        color=PALETTE["pre"],
        ls="--",
        lw=1,
        alpha=0.7,
        label="Pre mean margin",
    )
    ax2.axhline(
        df[df["period"] == "post"]["gross_margin_pct"].mean(),
        color=PALETTE["post"],
        ls="--",
        lw=1,
        alpha=0.7,
        label="Post mean margin",
    )
    ax1.axvline(_CUTOFF, color=PALETTE["cutoff"], ls="--", lw=1.5, label="Cutoff")
    ax1.set_xlabel("Month")
    ax1.set_ylabel("Monthly sales (USD)", color=PALETTE["neutral"])
    ax2.set_ylabel("Gross margin (%)", color="#E91E63")
    ax1.set_title("Sales and gross margin evolution — Panificadora Chask", fontsize=12)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, fontsize=8, loc="upper left")
    fig.tight_layout()
    _save(fig, "06_margin_sales", out_dir)

    # Plotly
    pfig = go.Figure()
    pfig.add_trace(
        go.Bar(
            x=df["fecha"],
            y=df["ventas_usd"],
            name="Sales (USD)",
            marker_color=[PALETTE["pre"] if p == "pre" else PALETTE["post"] for p in df["period"]],
            opacity=0.7,
        )
    )
    pfig.add_trace(
        go.Scatter(
            x=df["fecha"],
            y=df["gross_margin_pct"],
            mode="lines+markers",
            name="Gross margin (%)",
            yaxis="y2",
            line={"color": "#E91E63", "width": 2},
        )
    )
    pfig.add_vline(x=_CUTOFF_MS, line_dash="dash", line_color=PALETTE["cutoff"])
    pfig.update_layout(
        title="Sales and gross margin (interactive)",
        yaxis={"title": "Sales (USD)"},
        yaxis2={"title": "Gross margin (%)", "overlaying": "y", "side": "right"},
        template="plotly_white",
        barmode="overlay",
    )
    _save_plotly(pfig, "06_margin_sales_interactive", out_dir)


def generate_all_figures(df: pd.DataFrame | None = None) -> None:
    """Generate all analysis figures and save to ``reports/figures/``.

    Args:
        df: Monthly enriched DataFrame. If ``None``, loads from disk.
    """
    from chask.analysis.anomalies import combined_anomalies
    from chask.analysis.stats import its_analysis
    from chask.pipeline.ingest import load_raw
    from chask.pipeline.transform import to_analytics
    from chask.pipeline.validate import validate

    if df is None:
        df = to_analytics(validate(load_raw()))

    out = _REPORTS_DIR
    print(f"Generating figures in {out} ...")

    plot_time_series(df, out)
    print("  [1/6] time_series")

    plot_boxplots(df, out)
    print("  [2/6] boxplots")

    plot_correlation_heatmap(df, out)
    print("  [3/6] correlation_heatmap")

    anomaly_df = combined_anomalies(df)
    plot_anomalies(df, anomaly_df, out)
    print("  [4/6] anomalies")

    its_kwh = its_analysis(df, "consumo_kwh")
    plot_its(df, its_kwh, "consumo_kwh", out)
    its_int = its_analysis(df, "intensity_kwh_kg")
    plot_its(df, its_int, "intensity_kwh_kg", out)
    print("  [5/6] its (consumo_kwh + intensity_kwh_kg)")

    plot_margin_sales(df, out)
    print("  [6/6] margin_sales")

    print(f"Done. {len(list(out.glob('*')))} files in {out}")


if __name__ == "__main__":
    generate_all_figures()
