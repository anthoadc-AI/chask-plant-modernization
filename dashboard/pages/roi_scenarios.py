"""ROI Scenarios page — parameterized ROI with interactive tariff/discount sliders."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from chask.config import DISCOUNT_RATE, ENERGY_TARIFF_USD_KWH, TOTAL_INVESTMENT_USD
from chask.energy.roi import compute_roi_scenarios, payback_curves
from chask.pipeline.ingest import load_raw
from chask.pipeline.transform import to_analytics
from chask.pipeline.validate import validate

sys.path.insert(0, str(Path(__file__).parent.parent))
from _components import render_footer  # noqa: E402


@st.cache_data
def _load() -> pd.DataFrame:
    return to_analytics(validate(load_raw()))


st.title("ROI Scenarios")
st.caption(
    f"Investment: USD {TOTAL_INVESTMENT_USD:,.0f} · "
    "Three scenarios: energy savings only, + production growth, + full capacity ramp."
)

df = _load()

# --- Sliders ---
st.subheader("Model Parameters")
st.markdown(
    "Adjust the sliders to explore how the ROI changes with different assumptions. "
    "The model recalculates live — demonstrating that every figure comes from the "
    "`chask` package, not hardcoded values."
)

col_s1, col_s2 = st.columns(2)
with col_s1:
    tariff = st.slider(
        "Energy tariff (USD/kWh)",
        min_value=0.03,
        max_value=0.15,
        value=float(ENERGY_TARIFF_USD_KWH),
        step=0.005,
        format="$%.3f",
        help="Bolivia ENDE industrial tariff ~2021. Adjust to test sensitivity.",
    )
with col_s2:
    discount_pct = st.slider(
        "Discount rate (%)",
        min_value=5,
        max_value=25,
        value=int(DISCOUNT_RATE * 100),
        step=1,
        format="%d%%",
        help="Annual discount rate for NPV calculation.",
    )
discount = discount_pct / 100.0

# --- ROI table ---
st.subheader("ROI Scenarios")
roi_df = compute_roi_scenarios(df, tariff=tariff, discount_rate=discount)

palette = {"Conservative": "#F44336", "Base": "#FF9800", "Optimistic": "#4CAF50"}


def _npv_color(val: float) -> str:
    return "color: #4CAF50" if val > 0 else "color: #F44336"


display = roi_df[["scenario", "annual_benefit_usd", "payback_years", "npv_5yr_usd", "notes"]].copy()
display.columns = ["Scenario", "Annual benefit (USD)", "Payback (years)", "NPV 5yr (USD)", "Notes"]

styled = display.style.format(
    {
        "Annual benefit (USD)": "${:,.0f}",
        "Payback (years)": "{:.1f}",
        "NPV 5yr (USD)": "${:,.0f}",
    }
).map(_npv_color, subset=["NPV 5yr (USD)"])
st.dataframe(styled, use_container_width=True, hide_index=True)

# --- Payback curves ---
st.subheader("Payback Curves")
curves = payback_curves(df, tariff=tariff, discount_rate=discount)

fig = go.Figure()
for scenario, color in palette.items():
    fig.add_trace(
        go.Scatter(
            x=curves["year"],
            y=curves[scenario],
            mode="lines+markers",
            name=scenario,
            line={"color": color, "width": 2},
            marker={"size": 6},
        )
    )
fig.add_hline(y=0, line_color="black", line_width=1, line_dash="dash")
fig.update_layout(
    xaxis_title="Year",
    yaxis_title="Cumulative discounted cash flow (USD)",
    yaxis_tickformat="$,.0f",
    legend={"orientation": "h", "y": -0.2},
    height=380,
    margin={"t": 20},
)
st.plotly_chart(fig, use_container_width=True)

# --- Honest interpretation ---
conservative_npv = roi_df.loc[roi_df["scenario"] == "Conservative", "npv_5yr_usd"].iloc[0]
optimistic_npv = roi_df.loc[roi_df["scenario"] == "Optimistic", "npv_5yr_usd"].iloc[0]

if conservative_npv < 0:
    st.info(
        f"**Conservative scenario NPV = ${conservative_npv:,.0f}** (negative) — "
        f"at the selected tariff (${tariff:.3f}/kWh) and {discount_pct}% discount rate, "
        "energy savings and downtime reduction alone do not recover the investment over 5 years. "
        f"**Optimistic scenario NPV = ${optimistic_npv:,.0f}** — the investment is justified "
        "only when the +50% installed capacity is progressively utilized over 3 years."
    )
else:
    st.success(
        f"At the selected tariff (${tariff:.3f}/kWh) and {discount_pct}% discount rate, "
        f"the Conservative scenario NPV is ${conservative_npv:,.0f} (positive). "
        "Note: at the documented base tariff of $0.065/kWh and 10% discount rate, "
        "the Conservative NPV is negative — see the honest assessment in the Energy page."
    )

st.caption(
    "All model assumptions are named constants in `chask.config` and `chask.energy.roi`. "
    "There are no magic numbers — every figure is traceable to its source."
)

render_footer()
