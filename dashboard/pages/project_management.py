"""Project Management page — charter summary, Gantt, risk register, cost baseline."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
from _components import render_footer  # noqa: E402

_ROOT = Path(__file__).parent.parent.parent
_PM_DIR = _ROOT / "project-management"


def _read_pm(filename: str) -> str:
    return (_PM_DIR / filename).read_text(encoding="utf-8")


st.title("Project Management")

# --- Project Charter Summary ---
st.subheader("Project Charter")

charter_data = {
    "Field": [
        "Project title",
        "Client",
        "Executing firm",
        "Project director",
        "Location",
        "Start date",
        "End date",
        "Total investment",
        "Intervention cutoff",
    ],
    "Detail": [
        "Plant Expansion and Resource Optimization — Panificadora Chask",
        "Panificadora Chask",
        "INGEDAV S.R.L. (Ingeniería, Diseño y Automatización)",
        "Anthony Dávila",
        "Av. Juan Manuel Sánchez, Punata, Cochabamba, Bolivia",
        "December 21, 2020",
        "June 4, 2022",
        "USD 85,000",
        "August 2021 (new machinery fully operational)",
    ],
}
st.dataframe(pd.DataFrame(charter_data), use_container_width=True, hide_index=True)

with st.expander("Full project charter"):
    st.markdown(_read_pm("project-charter.md"))

# --- Gantt Chart ---
st.subheader("Project Gantt Chart")

_TASKS: list[dict] = [
    dict(
        Phase="Phase 1 · Evaluation",
        Task="Technical inventory",
        Start="2020-12-21",
        Finish="2021-01-31",
    ),  # noqa: E501
    dict(
        Phase="Phase 1 · Evaluation",
        Task="Electrical monitoring",
        Start="2021-01-15",
        Finish="2021-02-28",
    ),  # noqa: E501
    dict(
        Phase="Phase 1 · Evaluation",
        Task="Flow & time study",
        Start="2021-02-01",
        Finish="2021-02-28",
    ),  # noqa: E501
    dict(
        Phase="Phase 1 · Evaluation",
        Task="Diagnosis report",
        Start="2021-03-01",
        Finish="2021-03-31",
    ),  # noqa: E501
    dict(
        Phase="Phase 2 · Design",
        Task="CAD modeling (SolidWorks)",
        Start="2021-04-01",
        Finish="2021-05-15",
    ),  # noqa: E501
    dict(
        Phase="Phase 2 · Design",
        Task="Machinery specification",
        Start="2021-04-15",
        Finish="2021-05-31",
    ),  # noqa: E501
    dict(
        Phase="Phase 2 · Design",
        Task="Energy efficiency plan",
        Start="2021-05-01",
        Finish="2021-06-15",
    ),  # noqa: E501
    dict(
        Phase="Phase 2 · Design",
        Task="Electrical upgrade design",
        Start="2021-05-15",
        Finish="2021-06-30",
    ),  # noqa: E501
    dict(
        Phase="Phase 3 · Implementation",
        Task="Machinery manufacturing",
        Start="2021-07-01",
        Finish="2021-07-31",
    ),  # noqa: E501
    dict(
        Phase="Phase 3 · Implementation",
        Task="Plant area expansion",
        Start="2021-07-01",
        Finish="2021-08-15",
    ),  # noqa: E501
    dict(
        Phase="Phase 3 · Implementation",
        Task="Equipment installation",
        Start="2021-07-15",
        Finish="2021-08-31",
    ),  # noqa: E501
    dict(
        Phase="Phase 3 · Implementation",
        Task="EMS implementation",
        Start="2021-08-01",
        Finish="2021-08-31",
    ),  # noqa: E501
    dict(
        Phase="Phase 3 · Implementation",
        Task="Electrical modernization",
        Start="2021-08-01",
        Finish="2021-08-31",
    ),  # noqa: E501
    dict(
        Phase="Phase 4 · Training",
        Task="Operator training (machinery)",
        Start="2021-09-01",
        Finish="2021-10-31",
    ),  # noqa: E501
    dict(Phase="Phase 4 · Training", Task="EMS training", Start="2021-09-15", Finish="2021-10-31"),  # noqa: E501
    dict(
        Phase="Phase 4 · Training",
        Task="Preventive maintenance program",
        Start="2021-10-01",
        Finish="2021-12-31",
    ),  # noqa: E501
    dict(
        Phase="Phase 4 · Training",
        Task="Post-intervention monitoring",
        Start="2021-09-01",
        Finish="2022-05-31",
    ),  # noqa: E501
    dict(
        Phase="Phase 4 · Training",
        Task="Project closure report",
        Start="2022-04-01",
        Finish="2022-06-04",
    ),  # noqa: E501
]
gantt_df = pd.DataFrame(_TASKS)
gantt_df["Start"] = pd.to_datetime(gantt_df["Start"])
gantt_df["Finish"] = pd.to_datetime(gantt_df["Finish"])

fig_gantt = px.timeline(
    gantt_df,
    x_start="Start",
    x_end="Finish",
    y="Task",
    color="Phase",
    color_discrete_sequence=["#2196F3", "#4CAF50", "#FF9800", "#9C27B0"],
    title="Panificadora Chask — Plant Modernization Schedule",
)
fig_gantt.update_yaxes(autorange="reversed")
fig_gantt.add_vline(
    x=pd.Timestamp("2021-08-31").timestamp() * 1000,
    line_dash="dash",
    line_color="red",
    annotation_text="Intervention milestone",
    annotation_position="top left",
)
fig_gantt.update_layout(
    height=520, margin={"t": 50, "l": 230}, legend={"orientation": "h", "y": -0.15}
)
st.plotly_chart(fig_gantt, use_container_width=True)

with st.expander("Full schedule details (Mermaid source)"):
    st.markdown(_read_pm("schedule.md"))

# --- Risk Register ---
st.subheader("Risk Register")

risk_text = _read_pm("risk-register.md")
table_match = re.search(r"\| ID \|.*?\n(\|[-|]+\|\n)((?:\|.*\|\n)+)", risk_text, re.DOTALL)
if table_match:
    header_line = re.search(r"(\| ID \|.*?\n)", risk_text).group(1)
    rows_raw = table_match.group(2).strip().split("\n")
    header_cols = [h.strip() for h in header_line.strip("|").split("|")]
    rows_data = []
    for row in rows_raw:
        cells = [c.strip() for c in row.strip("|").split("|")]
        if len(cells) == len(header_cols):
            rows_data.append(dict(zip(header_cols, cells)))
    if rows_data:
        risk_df = pd.DataFrame(rows_data)
        st.dataframe(risk_df, use_container_width=True, hide_index=True)
    else:
        st.markdown(risk_text)
else:
    st.markdown(risk_text)

# --- Cost Baseline ---
st.subheader("Cost Baseline")
with st.expander("View cost breakdown", expanded=True):
    st.markdown(_read_pm("cost-baseline.md"))

with st.expander("WBS"):
    st.markdown(_read_pm("wbs.md"))

render_footer()
