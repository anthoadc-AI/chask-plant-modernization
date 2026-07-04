"""Shared UI components for the Panificadora Chask dashboard."""

from __future__ import annotations

import streamlit as st


def format_delta(val: float | str) -> str:
    """Format a delta value for ``st.metric`` — one decimal and ``%`` sign.

    Pre-formatted strings (e.g. ``"+7.5 pp"``, ``"→ $1,200/mo"``) are
    returned unchanged. Raw floats are formatted as ``"+X.X%"``.
    """
    if isinstance(val, str):
        return val
    return f"{val:+.1f}%"


FOOTER_DISCLAIMER: str = (
    "Dataset is a documented reconstruction calibrated to the real project outcomes; "
    "original client records are confidential. "
    "See the [data dictionary]"
    "(https://anthoadc-AI.github.io/chask-plant-modernization/data-dictionary/) "
    "for full disclosure."
)


def render_footer() -> None:
    """Render the persistent dataset disclosure footer."""
    st.markdown("---")
    st.caption(FOOTER_DISCLAIMER)


def kpi_card(
    col: st.delta_generator.DeltaGenerator,
    title: str,
    value_str: str,
    delta_str: str,
    delta_color: str = "normal",
) -> None:
    """Render a KPI metric card inside a Streamlit column.

    Args:
        col: The Streamlit column context to render into.
        title: Metric label displayed above the value.
        value_str: Formatted post-intervention value string.
        delta_str: Change string (e.g. "-19.6%", "+7.5 pp").
        delta_color: "normal" (green=positive), "inverse" (green=negative), or "off".
    """
    col.metric(label=title, value=value_str, delta=delta_str, delta_color=delta_color)
