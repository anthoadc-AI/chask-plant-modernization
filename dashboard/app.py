"""Panificadora Chask — Plant Modernization Dashboard.

Entry point for the multi-page Streamlit application.
Run from the project root: ``streamlit run dashboard/app.py``
"""

import sys
from pathlib import Path

# Allow importing the chask package without a pip editable install
# (needed for Streamlit Community Cloud deployment)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import streamlit as st

st.set_page_config(
    page_title="Panificadora Chask — Plant Modernization",
    layout="wide",
    page_icon="🏭",
    initial_sidebar_state="expanded",
)

_PAGES = st.navigation(
    [
        st.Page("pages/overview.py", title="Overview", icon="🏭"),
        st.Page("pages/energy.py", title="Energy", icon="⚡"),
        st.Page("pages/statistics.py", title="Statistics", icon="📊"),
        st.Page("pages/reliability_process.py", title="Reliability & Process", icon="⚙️"),
        st.Page("pages/roi_scenarios.py", title="ROI Scenarios", icon="💰"),
        st.Page("pages/project_management.py", title="Project Management", icon="📋"),
    ]
)
_PAGES.run()
