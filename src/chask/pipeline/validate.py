"""Pandera schema validation for the monthly operational dataset."""

import pandas as pd
import pandera.pandas as pa


def _all_month_end(series: pd.Series) -> pd.Series:
    return series == series.dt.to_period("M").dt.to_timestamp("M")


def _monthly_continuous(df: pd.DataFrame) -> bool:
    periods = df["fecha"].dt.to_period("M").sort_values()
    expected = pd.period_range(periods.iloc[0], periods.iloc[-1], freq="M")
    return set(periods) == set(expected)


MONTHLY_SCHEMA = pa.DataFrameSchema(
    columns={
        "fecha": pa.Column(
            pa.DateTime,
            checks=pa.Check(_all_month_end, element_wise=False, error="dates must be end-of-month"),
            unique=True,
            nullable=False,
        ),
        "produccion_kg": pa.Column(float, checks=pa.Check.gt(0), nullable=False),
        "consumo_kwh": pa.Column(float, checks=pa.Check.gt(0), nullable=False),
        "fallas_maquina": pa.Column(int, checks=pa.Check.ge(0), nullable=False),
        "mantenimiento": pa.Column(int, checks=pa.Check.ge(0), nullable=False),
        "ventas_usd": pa.Column(float, checks=pa.Check.gt(0), nullable=False),
        "costos_usd": pa.Column(float, checks=pa.Check.gt(0), nullable=False),
        "tiempo_inactividad_horas": pa.Column(float, checks=pa.Check.ge(0), nullable=False),
    },
    checks=[
        pa.Check(lambda df: len(df) == 29, error="dataset must have exactly 29 rows"),
        pa.Check(
            _monthly_continuous,
            error="dates must form a continuous monthly series (no gaps)",
        ),
    ],
    coerce=True,
)


def validate(df: pd.DataFrame) -> pd.DataFrame:
    """Validate the monthly dataset against the expected schema.

    Args:
        df: Raw monthly DataFrame returned by :func:`~chask.pipeline.ingest.load_raw`.

    Returns:
        The validated (and coerced) DataFrame if all checks pass.

    Raises:
        pandera.errors.SchemaError: If any validation check fails.
    """
    return MONTHLY_SCHEMA.validate(df)
