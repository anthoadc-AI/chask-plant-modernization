"""Overview page — headline KPI cards, intervention time series, findings table."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from chask.analysis.eda import headline_findings
from chask.config import INTERVENTION_CUTOFF
from chask.pipeline.ingest import load_raw
from chask.pipeline.transform import to_analytics
from chask.pipeline.validate import validate

sys.path.insert(0, str(Path(__file__).parent.parent))
from _components import format_delta, kpi_card, render_footer  # noqa: E402


@st.cache_data
def _load() -> pd.DataFrame:
    return to_analytics(validate(load_raw()))


def _format_value(metric: str, post_mean: float) -> str:
    """Return a display-friendly string for a post-intervention mean."""
    m = metric.lower()
    if "kwh/kg" in m:
        return f"{post_mean:.2f} kWh/kg"
    if "kwh" in m:
        return f"{post_mean:,.0f} kWh"
    if "margin" in m:
        return f"{post_mean:.1f}%"
    if "sales" in m or "usd" in m:
        return f"${post_mean:,.0f}"
    if "failure" in m or "fallas" in m:
        return f"{post_mean:.1f}/mo"
    if "downtime" in m:
        return f"{post_mean:.1f} h"
    if "production" in m or "kg" in m:
        return f"{post_mean:,.0f} kg"
    return f"{post_mean:.2f}"


def _delta_color(direction: str) -> str:
    return "normal" if direction == "improved" else "inverse"


st.title("Panificadora Chask — Plant Modernization")
st.caption(
    "Panificadora Chask · INGEDAV S.R.L. · Punata, Cochabamba, Bolivia"
    " · Dec 2020 – Jun 2022 · Project Director: Anthony Dávila"
)

df = _load()
hf = headline_findings(df)

# --- KPI Cards (7 metrics in two rows) ---
st.subheader("Post-Intervention Headline KPIs (all 7 metrics improved)")
row1_cols = st.columns(4)
row2_cols = st.columns(3)
all_cols = row1_cols + row2_cols

for col, (_, row) in zip(all_cols, hf.iterrows()):
    kpi_card(
        col,
        title=row["metric"],
        value_str=_format_value(row["metric"], row["post_mean"]),
        delta_str=format_delta(row["change"]),
        delta_color=_delta_color(row["direction"]),
    )

st.markdown(
    "> All 7 headline metrics improved after the Aug 2021 intervention. "
    "Sep–Oct 2021 show a commissioning spike in failures; "
    "steady-state (Dec 2021–May 2022) results are even better."
)

# --- Time series: energy consumption ---
st.subheader("Monthly Energy Consumption")

pre = df[df["period"] == "pre"]
post = df[df["period"] == "post"]
cutoff = pd.Timestamp(INTERVENTION_CUTOFF)

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=pre["fecha"],
        y=pre["consumo_kwh"],
        mode="lines+markers",
        name="Pre-intervention",
        line={"color": "#2196F3"},
        marker={"size": 6},
    )
)
fig.add_trace(
    go.Scatter(
        x=post["fecha"],
        y=post["consumo_kwh"],
        mode="lines+markers",
        name="Post-intervention",
        line={"color": "#4CAF50"},
        marker={"size": 6},
    )
)
fig.add_vline(
    x=cutoff.timestamp() * 1000,
    line_dash="dash",
    line_color="#9C27B0",
    annotation_text="Intervention cutoff (Aug 2021)",
    annotation_position="top right",
)
fig.update_layout(
    xaxis_title="Month",
    yaxis_title="kWh",
    yaxis_tickformat=",.0f",
    legend={"orientation": "h", "y": -0.2},
    margin={"t": 30, "b": 0},
    height=350,
)
st.plotly_chart(fig, use_container_width=True)

# --- Headline findings table ---
st.subheader("Headline Findings")
st.dataframe(
    hf[["metric", "pre_mean", "post_mean", "change", "direction"]].rename(
        columns={
            "metric": "Metric",
            "pre_mean": "Pre mean",
            "post_mean": "Post mean",
            "change": "Change",
            "direction": "Direction",
        }
    ),
    use_container_width=True,
    hide_index=True,
)

render_footer()
