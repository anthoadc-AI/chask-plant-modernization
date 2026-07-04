"""Smoke tests for the Streamlit dashboard.

Tests that all 6 pages load without exception and that headline_findings()
produces data consistent with the CLAUDE.md ground truth.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from streamlit.testing.v1 import AppTest

from chask.analysis.eda import headline_findings
from chask.pipeline.ingest import load_raw
from chask.pipeline.transform import to_analytics
from chask.pipeline.validate import validate

_PAGES = [
    "dashboard/pages/overview.py",
    "dashboard/pages/energy.py",
    "dashboard/pages/statistics.py",
    "dashboard/pages/reliability_process.py",
    "dashboard/pages/roi_scenarios.py",
    "dashboard/pages/project_management.py",
]


@pytest.mark.parametrize("page_path", _PAGES)
def test_page_runs_without_exception(page_path: str) -> None:
    """Each dashboard page must start and render without raising an exception."""
    at = AppTest.from_file(page_path, default_timeout=60)
    at.run()
    assert not at.exception, f"Page {page_path} raised: {at.exception}"


class TestHeadlineFindings:
    """Verify headline_findings() produces data matching CLAUDE.md ground truth."""

    def test_returns_seven_rows(self) -> None:
        df = to_analytics(validate(load_raw()))
        hf = headline_findings(df)
        assert len(hf) == 7

    def test_all_directions_improved(self) -> None:
        df = to_analytics(validate(load_raw()))
        hf = headline_findings(df)
        non_improved = hf[hf["direction"] != "improved"]
        assert non_improved.empty, f"Non-improved rows:\n{non_improved}"

    def test_energy_pre_mean_matches_ground_truth(self) -> None:
        df = to_analytics(validate(load_raw()))
        hf = headline_findings(df)
        row = hf[hf["metric"].str.contains("Energy consumption")].iloc[0]
        assert abs(row["pre_mean"] - 51_826.5) < 200

    def test_energy_post_mean_matches_ground_truth(self) -> None:
        df = to_analytics(validate(load_raw()))
        hf = headline_findings(df)
        row = hf[hf["metric"].str.contains("Energy consumption")].iloc[0]
        assert abs(row["post_mean"] - 41_689.0) < 200

    def test_has_required_columns(self) -> None:
        df = to_analytics(validate(load_raw()))
        hf = headline_findings(df)
        for col in ("metric", "pre_mean", "post_mean", "change", "direction"):
            assert col in hf.columns


class TestDeltaFormat:
    """Verify that no rendered st.metric delta contains more than one decimal."""

    _BAD_DECIMAL = re.compile(r"\d+\.\d{2,}")

    @pytest.mark.parametrize("page_path", _PAGES)
    def test_no_delta_has_excess_decimals(self, page_path: str) -> None:
        at = AppTest.from_file(page_path, default_timeout=60)
        at.run()
        assert not at.exception, f"Page {page_path} raised: {at.exception}"
        for m in at.metric:
            delta = m.delta or ""
            assert not self._BAD_DECIMAL.search(delta), (
                f"Delta {delta!r} on page {page_path} has more than one decimal place"
            )
