"""End-to-end pipeline integration tests."""

from chask.config import ANALYTICS_DIR, STAGING_DIR
from chask.pipeline.run import run_pipeline


def test_pipeline_runs_without_error():
    summary = run_pipeline()
    assert summary["checks"] == "passed"


def test_pipeline_returns_correct_row_count():
    summary = run_pipeline()
    assert summary["rows"] == 29


def test_pipeline_writes_staging_file():
    run_pipeline()
    assert (STAGING_DIR / "monthly_validated.csv").exists()


def test_pipeline_writes_analytics_file():
    run_pipeline()
    assert (ANALYTICS_DIR / "monthly_enriched.csv").exists()
