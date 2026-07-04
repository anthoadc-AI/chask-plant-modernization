"""Energy page — intensity trend, savings, motor reconciliation, load profile."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from chask.config import ANALYTICS_DIR, INTERVENTION_CUTOFF
from chask.energy.kpis import annualized_savings, energy_intensity_rolling, monthly_savings
from chask.energy.load_profile import peak_day_of_week, weekly_load_profile
from chask.energy.motors import motor_savings_detail, reconciliation, total_motor_savings_kwh_mo
from chask.pipeline.ingest import load_raw
from chask.pipeline.transform import to_analytics
from chask.pipeline.validate import validate

sys.path.insert(0, str(Path(__file__).parent.parent))
from _components import render_footer  # noqa: E402


@st.cache_data
def _load() -> pd.DataFrame:
    return to_analytics(validate(load_raw()))


@st.cache_data
def _load_daily() -> pd.DataFrame:
    return pd.read_csv(ANALYTICS_DIR / "daily_synthetic.csv", parse_dates=["fecha"])


st.title("Energy Efficiency Analysis")

df = _load()
cutoff = pd.Timestamp(INTERVENTION_CUTOFF)

# --- 1. Energy intensity trend ---
st.subheader("1. Energy Intensity — Monthly & 3-Month Rolling Average")
rolled = energy_intensity_rolling(df)

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=df["fecha"],
        y=df["intensity_kwh_kg"],
        mode="markers",
        name="Monthly",
        marker={"color": "#607D8B", "size": 6},
        opacity=0.7,
    )
)
fig.add_trace(
    go.Scatter(
        x=rolled["fecha"],
        y=rolled["intensity_rolling"],
        mode="lines",
        name="3-month rolling avg",
        line={"color": "#E91E63", "width": 2},
    )
)
fig.add_vline(
    x=cutoff.timestamp() * 1000,
    line_dash="dash",
    line_color="#9C27B0",
    annotation_text="Intervention",
)
ss_start = pd.Timestamp("2021-11-30")
fig.add_vline(
    x=ss_start.timestamp() * 1000,
    line_dash="dot",
    line_color="#009688",
    annotation_text="SS start",
)
fig.update_layout(
    xaxis_title="Month",
    yaxis_title="kWh/kg",
    legend={"orientation": "h", "y": -0.2},
    height=350,
    margin={"t": 30},
)
st.plotly_chart(fig, use_container_width=True)

# --- 2. Annualized savings ---
st.subheader("2. Annualized Energy Savings")
sav = annualized_savings(df)

col1, col2, col3 = st.columns(3)
col1.metric("SS mean consumption", f"{sav['ss_mean_kwh_mo']:,.0f} kWh/mo")
col2.metric(
    "Annual savings (SS vs pre)",
    f"{sav['ss_savings_kwh_yr']:,.0f} kWh/yr",
    f"${sav['ss_savings_usd_yr']:,.0f}/yr",
)
col3.metric("CO₂ avoided (SS)", f"{sav['ss_co2_avoided_kg_yr']:,.0f} kgCO₂/yr")

st.caption(
    f"Baseline: {sav['baseline_kwh_mo']:,.0f} kWh/mo (pre mean, n=20). "
    f"Post mean: {sav['post_mean_kwh_mo']:,.0f} kWh/mo. "
    f"Steady-state mean (Dec 2021–May 2022): {sav['ss_mean_kwh_mo']:,.0f} kWh/mo."
)

# Monthly savings bar chart
saved = monthly_savings(df)
fig2 = px.bar(
    saved,
    x="fecha",
    y="savings_kwh",
    color=saved["savings_kwh"].apply(lambda v: "Savings" if v >= 0 else "Excess"),
    color_discrete_map={"Savings": "#4CAF50", "Excess": "#F44336"},
    labels={"savings_kwh": "kWh saved vs baseline", "fecha": "Month", "color": ""},
    title="Monthly energy savings vs. pre-intervention baseline",
)
fig2.add_hline(y=0, line_color="black", line_width=1)
fig2.update_layout(height=300, margin={"t": 40}, showlegend=True)
st.plotly_chart(fig2, use_container_width=True)

# --- 3. Motor fleet savings ---
st.subheader("3. Motor Fleet Replacement Savings (Theoretical)")
detail = motor_savings_detail()
st.dataframe(
    detail.rename(
        columns={
            "name": "Equipment",
            "power_kw": "kW",
            "count": "n",
            "eff_old": "η old",
            "eff_new": "η new",
            "hours_per_month": "h/mo",
            "savings_kwh_mo": "kWh/mo (unit)",
            "savings_kwh_mo_total": "kWh/mo (total)",
        }
    ),
    use_container_width=True,
    hide_index=True,
)
st.caption(
    f"Fleet total theoretical savings: **{total_motor_savings_kwh_mo():,.0f} kWh/mo** "
    "(formula: P_shaft × h/mo × (1/η_old − 1/η_new))"
)

# --- 4. Reconciliation ---
st.subheader("4. Reconciliation: Theoretical vs. Observed Savings")
observed_mo = sav["baseline_kwh_mo"] - sav["ss_mean_kwh_mo"]
rec = reconciliation(observed_mo)

c1, c2, c3 = st.columns(3)
c1.metric("Motor fleet (theoretical)", f"{rec['theoretical_motor_kwh_mo']:,.0f} kWh/mo")
c2.metric("Residual (observed − theoretical)", f"{rec['residual_kwh_mo']:,.0f} kWh/mo")
c3.metric("Observed SS savings", f"{rec['observed_kwh_mo']:,.0f} kWh/mo")

fig3 = px.pie(
    values=[rec["motor_share_pct"], rec["residual_share_pct"]],
    names=["Motor fleet (IE3 replacement)", "Residual (non-motor improvements)"],
    color_discrete_sequence=["#2196F3", "#FF9800"],
    title=f"Share of observed savings ({rec['observed_kwh_mo']:,.0f} kWh/mo)",
)
fig3.update_traces(textinfo="percent+label")
fig3.update_layout(height=320, margin={"t": 40})
st.plotly_chart(fig3, use_container_width=True)

st.info(
    f"**Reconciliation note** — {rec['residual_allocation_note']} "
    f"The motor calculation (independently derived) explains "
    f"~{rec['motor_share_pct']:.0f}% of observed savings. "
    f"The remaining ~{rec['residual_share_pct']:.0f}% residual is *consistent* with "
    "field-diagnostic findings (connections, phantom load, automation demand shaping), "
    "but those items were not separately metered."
)

# --- 5. Weekly load profile (synthetic daily) ---
st.subheader("5. Weekly Load Profile")
st.warning(
    "⚠️ **SYNTHETIC DATA — demonstration only.** "
    "The daily dataset (`daily_synthetic.csv`) is model-generated, calibrated to monthly "
    "aggregates. It is NOT real measurements and must NOT be used for financial reporting "
    "or statistical inference."
)
daily_df = _load_daily()
profile = weekly_load_profile(daily_df)
peak = peak_day_of_week(daily_df)

fig4 = px.bar(
    profile,
    x="day_label",
    y="mean_kwh",
    error_y="std_kwh",
    labels={"day_label": "Day of week", "mean_kwh": "Mean daily energy (kWh)"},
    title=f"Weekly load profile — synthetic daily data (peak: {peak['day_label']})",
    color_discrete_sequence=["#2196F3"],
)
fig4.update_layout(height=300, margin={"t": 40})
st.plotly_chart(fig4, use_container_width=True)

render_footer()
