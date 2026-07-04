"""Statistics page — hypothesis tests, ITS analysis, Cohen's d."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from chask.analysis.stats import full_statistical_summary, its_analysis
from chask.config import INTERVENTION_CUTOFF
from chask.pipeline.ingest import load_raw
from chask.pipeline.transform import to_analytics
from chask.pipeline.validate import validate

sys.path.insert(0, str(Path(__file__).parent.parent))
from _components import render_footer  # noqa: E402

_EFFECT_EMOJI = {"large": "●●●", "medium": "●●○", "small": "●○○", "negligible": "○○○"}


@st.cache_data
def _load() -> pd.DataFrame:
    return to_analytics(validate(load_raw()))


@st.cache_data
def _summary(df: pd.DataFrame) -> pd.DataFrame:
    return full_statistical_summary(df)


st.title("Statistical Analysis")
st.caption(
    "All inference runs exclusively on the **real monthly dataset (n=29)**. "
    "The synthetic daily dataset was never used for hypothesis testing."
)

df = _load()
summ = _summary(df)

# --- Hypothesis test table ---
st.subheader("1. Two-Sample Hypothesis Tests (Pre vs. Post)")

display = summ[
    [
        "variable",
        "test_used",
        "stat",
        "p_value",
        "significant",
        "cohens_d",
        "effect_size",
        "pre_mean",
        "post_mean",
        "pct_change",
    ]
].copy()
display.columns = [
    "Variable",
    "Test",
    "Statistic",
    "p-value",
    "Significant",
    "Cohen's d",
    "Effect size",
    "Pre mean",
    "Post mean",
    "% change",
]


def _color_significant(val: bool) -> str:
    return "background-color: #C8E6C9" if val else "background-color: #FFCDD2"


styled = display.style.map(_color_significant, subset=["Significant"]).format(
    {
        "Statistic": "{:.3f}",
        "p-value": "{:.4f}",
        "Cohen's d": "{:.3f}",
        "Pre mean": "{:.2f}",
        "Post mean": "{:.2f}",
        "% change": "{:.1f}%",
    }
)
st.dataframe(styled, use_container_width=True, hide_index=True)

st.markdown(
    "All 7 metrics are statistically significant (α=0.05) with **large effect sizes** "
    "(|Cohen's d| ≥ 0.8 for all variables). This means the post-intervention differences "
    "are very unlikely to be due to chance, and the magnitude of change is practically meaningful. "
    "Caveat: n=9 post-period months — results should be interpreted alongside domain context."
)

# --- ITS chart selector ---
st.subheader("2. Interrupted Time Series (ITS) Analysis")
st.caption("Segmented OLS regression: level change + slope change at the intervention cutoff.")

_ITS_VARS = [
    "consumo_kwh",
    "intensity_kwh_kg",
    "gross_margin_pct",
    "fallas_maquina",
    "produccion_kg",
]
_VAR_LABELS = {
    "consumo_kwh": "Energy consumption (kWh)",
    "intensity_kwh_kg": "Energy intensity (kWh/kg)",
    "gross_margin_pct": "Gross margin (%)",
    "fallas_maquina": "Machine failures",
    "produccion_kg": "Production (kg)",
}

selected = st.selectbox(
    "Select variable for ITS chart",
    options=_ITS_VARS,
    format_func=lambda v: _VAR_LABELS[v],
)

cutoff_ts = pd.Timestamp(INTERVENTION_CUTOFF)

its = its_analysis(df, selected)
its_df = its["its_df"]

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=its_df["fecha"],
        y=its_df[selected],
        mode="markers",
        name="Observed",
        marker={"color": "#607D8B", "size": 7},
    )
)
fig.add_trace(
    go.Scatter(
        x=its_df["fecha"],
        y=its["fitted"],
        mode="lines",
        name="ITS fitted",
        line={"color": "#E91E63", "width": 2},
    )
)
fig.add_vline(
    x=cutoff_ts.timestamp() * 1000,
    line_dash="dash",
    line_color="#9C27B0",
    annotation_text="Intervention",
)
fig.update_layout(
    xaxis_title="Month",
    yaxis_title=_VAR_LABELS[selected],
    legend={"orientation": "h", "y": -0.2},
    height=380,
    margin={"t": 30},
)
st.plotly_chart(fig, use_container_width=True)

coef = its["coefficients"]
pval = its["p_values"]
r2 = its["r_squared"]
coef_keys = list(coef.keys())

st.markdown(
    f"**R² = {r2:.3f}** &nbsp;|&nbsp; Model: `{selected} ~ time + intervention + time_post`"
)
coef_df = pd.DataFrame(
    {
        "Coefficient": coef_keys,
        "Estimate": [coef[k] for k in coef_keys],
        "p-value": [pval.get(k, float("nan")) for k in coef_keys],
    }
)
coef_df["Significant"] = coef_df["p-value"] < 0.05
st.dataframe(
    coef_df.style.map(_color_significant, subset=["Significant"]).format(
        {"Estimate": "{:.3f}", "p-value": "{:.4f}"}
    ),
    use_container_width=True,
    hide_index=True,
)

render_footer()
