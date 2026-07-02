"""CLI entry point for Phase 2 analysis: figures + statistical summary.

Usage::

    python -m chask.analysis.run
    # or via Makefile:
    make analysis
"""

from chask.analysis.stats import full_statistical_summary
from chask.analysis.viz import generate_all_figures
from chask.pipeline.ingest import load_raw
from chask.pipeline.transform import to_analytics
from chask.pipeline.validate import validate


def main() -> None:
    df = to_analytics(validate(load_raw()))
    print("=== Statistical summary ===")
    summary = full_statistical_summary(df)
    print(summary.to_string(index=False))
    print()
    generate_all_figures(df)


if __name__ == "__main__":
    main()
