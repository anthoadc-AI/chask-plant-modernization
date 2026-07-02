"""Tests for chask.pipeline.validate."""

import pandas as pd
import pandera.pandas
import pytest

from chask.pipeline.ingest import load_raw
from chask.pipeline.validate import validate


@pytest.fixture()
def real_df() -> pd.DataFrame:
    return load_raw()


def test_validate_passes_on_real_data(real_df: pd.DataFrame):
    result = validate(real_df)
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 29


def test_validate_coerces_types(real_df: pd.DataFrame):
    result = validate(real_df)
    assert pd.api.types.is_datetime64_any_dtype(result["fecha"])
    assert pd.api.types.is_float_dtype(result["produccion_kg"])


def test_validate_rejects_negative_produccion(real_df: pd.DataFrame):
    bad = real_df.copy()
    bad.loc[bad.index[0], "produccion_kg"] = -1.0
    with pytest.raises(pandera.pandas.errors.SchemaError):
        validate(bad)


def test_validate_rejects_negative_consumo(real_df: pd.DataFrame):
    bad = real_df.copy()
    bad.loc[bad.index[0], "consumo_kwh"] = -100.0
    with pytest.raises(pandera.pandas.errors.SchemaError):
        validate(bad)


def test_validate_rejects_negative_fallas(real_df: pd.DataFrame):
    bad = real_df.copy()
    bad.loc[bad.index[0], "fallas_maquina"] = -1
    with pytest.raises(pandera.pandas.errors.SchemaError):
        validate(bad)


def test_validate_rejects_wrong_row_count(real_df: pd.DataFrame):
    bad = real_df.iloc[:10].copy()
    with pytest.raises(pandera.pandas.errors.SchemaError):
        validate(bad)


def test_validate_rejects_duplicate_dates(real_df: pd.DataFrame):
    bad = pd.concat([real_df, real_df.iloc[[0]]], ignore_index=True)
    # 30 rows — fails both uniqueness and row count
    with pytest.raises(pandera.pandas.errors.SchemaError):
        validate(bad)


def test_validate_rejects_non_month_end_date(real_df: pd.DataFrame):
    bad = real_df.copy()
    bad.loc[bad.index[0], "fecha"] = pd.Timestamp("2020-01-15")
    with pytest.raises(pandera.pandas.errors.SchemaError):
        validate(bad)


def test_validate_rejects_date_gap(real_df: pd.DataFrame):
    # Remove one middle month to create a gap
    bad = real_df.drop(real_df.index[10]).reset_index(drop=True)
    with pytest.raises(pandera.pandas.errors.SchemaError):
        validate(bad)
