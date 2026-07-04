"""Reliability & Process page — MTBF, failures, throughput, downtime."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from chask.config import INTERVENTION_CUTOFF
from chask.pipeline.ingest import load_raw
from chask.pipeline.transform import to_analytics
from chask.pipeline.validate import validate
from chask.process.reliability import (
    downtime_cost_monthly,
    failure_trends,
    mtbf_monthly,
    reliability_summary,
)
from chask.process.throughput import capacity_utilization, throughput_summary

sys.path.insert(0, str(Path(__file__).parent.parent))
from _components import kpi_card, render_footer  # noqa: E402

_PERIOD_COLORS = {"pre": "#2196F3", "post": "#4CAF50"}
_COMMISSIONING_MONTHS = ["2021-09-30", "2021-10-31"]


@st.cache_data
def _load() -> pd.DataFrame:
    return to_analytics(validate(load_raw()))


st.title("Reliability & Process Optimization")

df = _load()
cutoff_ts = pd.Timestamp(INTERVENTION_CUTOFF)

# --- Reliability KPI cards ---
rel = reliability_summary(df)
st.subheader("Reliability Summary")
c1, c2, c3, c4 = st.columns(4)
kpi_card(c1, "Pre MTBF", f"{rel['pre_mean_mtbf_h']:.1f} h", "")
kpi_card(
    c2,
    "Steady-state MTBF",
    f"{rel['ss_mean_mtbf_h']:.1f} h",
    f"+{rel['mtbf_improvement_pct']:.0f}%",
)
kpi_card(
    c3,
    "Downtime cost reduction",
    f"${rel['downtime_cost_reduction_usd_yr']:,.0f}/yr",
    "",
)
kpi_card(
    c4,
    "Pre downtime cost",
    f"${rel['pre_downtime_cost_usd_mo']:,.0f}/mo",
    f"→ ${rel['ss_downtime_cost_usd_mo']:,.0f}/mo",
    delta_color="inverse",
)

# --- MTBF chart ---
st.subheader("1. Monthly MTBF")
st.warning(
    "⚠️ **Commissioning spike**: Sep–Oct 2021 show elevated failures (10, 9) "
    "vs. pre-period mean (8.1). This reflects normal new-machinery commissioning, "
    "not a regression. Steady-state (Dec 2021+) MTBF is substantially higher than pre."
)

mtbf = mtbf_monthly(df)
colors = [_PERIOD_COLORS.get(p, "#FF9800") for p in mtbf["period"]]

fig_mtbf = go.Figure()
fig_mtbf.add_trace(
    go.Bar(
        x=mtbf["fecha"],
        y=mtbf["mtbf_h"],
        marker_color=colors,
        name="MTBF (h)",
        width=20 * 24 * 3600 * 1000,
    )
)
fig_mtbf.add_vline(
    x=cutoff_ts.timestamp() * 1000,
    line_dash="dash",
    line_color="black",
    annotation_text="Intervention",
)
for m in _COMMISSIONING_MONTHS:
    fig_mtbf.add_vline(
        x=pd.Timestamp(m).timestamp() * 1000,
        line_dash="dot",
        line_color="#FF5722",
        line_width=1,
    )
fig_mtbf.update_layout(
    xaxis_title="Month",
    yaxis_title="MTBF (h)",
    height=320,
    margin={"t": 20},
    showlegend=False,
)
st.plotly_chart(fig_mtbf, use_container_width=True)
st.caption("Orange dotted lines mark Sep–Oct 2021 commissioning months.")

# --- Failure trends ---
st.subheader("2. Failure Trends by Period")
ft = failure_trends(df)
st.dataframe(
    ft.rename(
        columns={
            "n_months": "Months",
            "mean_fallas": "Mean failures/mo",
            "mean_downtime_h": "Mean downtime (h)",
            "mean_mtbf_h": "Mean MTBF (h)",
            "fallas_vs_pre_pct": "vs Pre (%)",
        }
    ),
    use_container_width=True,
)

# --- Monthly failures bar chart ---
fig_fail = px.bar(
    df,
    x="fecha",
    y="fallas_maquina",
    color="period",
    color_discrete_map={"pre": "#2196F3", "post": "#4CAF50"},
    labels={"fallas_maquina": "Failures / month", "fecha": "Month", "period": "Period"},
    title="Machine failures per month",
)
fig_fail.add_vline(
    x=cutoff_ts.timestamp() * 1000,
    line_dash="dash",
    line_color="black",
)
fig_fail.update_layout(height=300, margin={"t": 40})
st.plotly_chart(fig_fail, use_container_width=True)

# --- Throughput ---
st.subheader("3. Throughput by Period")
ts = throughput_summary(df)
st.dataframe(
    ts.rename(
        columns={
            "n_months": "Months",
            "mean_prod_kg": "Mean prod (kg)",
            "mean_op_hours": "Op hours",
            "mean_kg_per_op_hour": "kg/op-hour",
            "productivity_vs_pre_pct": "vs Pre (%)",
            "mean_utilization_pre_pct": "Utilization (%)",
        }
    ),
    use_container_width=True,
)

# --- Capacity utilization ---
cu = capacity_utilization(df)
fig_cu = px.bar(
    cu,
    x="fecha",
    y=["utilization_pre_pct"],
    labels={"value": "Utilization (%)", "fecha": "Month"},
    title="Monthly capacity utilization (% of pre-intervention max capacity)",
    color_discrete_sequence=["#2196F3"],
)
fig_cu.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="Pre max")
fig_cu.add_hline(
    y=100 / 1.5,
    line_dash="dot",
    line_color="#9C27B0",
    annotation_text="Post installed capacity",
)
fig_cu.add_vline(
    x=cutoff_ts.timestamp() * 1000,
    line_dash="dash",
    line_color="black",
)
fig_cu.update_layout(height=320, margin={"t": 40}, showlegend=False)
st.plotly_chart(fig_cu, use_container_width=True)

# --- Downtime cost ---
st.subheader("4. Downtime Cost")
dtc = downtime_cost_monthly(df)
fig_dt = px.bar(
    dtc,
    x="fecha",
    y="downtime_cost_usd",
    color="period",
    color_discrete_map={"pre": "#2196F3", "post": "#4CAF50"},
    labels={"downtime_cost_usd": "Downtime cost (USD)", "fecha": "Month"},
    title="Monthly downtime cost (hourly margin × downtime hours)",
)
fig_dt.add_vline(
    x=cutoff_ts.timestamp() * 1000,
    line_dash="dash",
    line_color="black",
)
fig_dt.update_layout(height=300, margin={"t": 40})
st.plotly_chart(fig_dt, use_container_width=True)

render_footer()
