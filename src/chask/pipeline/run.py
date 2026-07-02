"""Pipeline orchestrator: raw → staging → analytics.

Run with::

    python -m chask.pipeline.run
"""

from chask.config import ANALYTICS_DIR, STAGING_DIR
from chask.pipeline.ingest import load_raw
from chask.pipeline.transform import to_analytics, to_staging
from chask.pipeline.validate import validate


def run_pipeline() -> dict:
    """Execute the full ingest → validate → transform pipeline.

    Returns:
        Summary dict with ``rows``, ``checks``, and ``files`` keys.
    """
    df_raw = load_raw()
    df_validated = validate(df_raw)
    to_staging(df_validated)
    df_enriched = to_analytics(df_validated)

    staging_path = STAGING_DIR / "monthly_validated.csv"
    analytics_path = ANALYTICS_DIR / "monthly_enriched.csv"

    summary = {
        "rows": len(df_enriched),
        "checks": "passed",
        "files": [str(staging_path), str(analytics_path)],
    }
    return summary


def _print_summary(summary: dict) -> None:
    print("=" * 60)
    print("Pipeline summary")
    print("=" * 60)
    print(f"  Rows processed : {summary['rows']}")
    print(f"  Schema checks  : {summary['checks']}")
    print("  Files written  :")
    for f in summary["files"]:
        print(f"    {f}")
    print("=" * 60)


if __name__ == "__main__":
    result = run_pipeline()
    _print_summary(result)
