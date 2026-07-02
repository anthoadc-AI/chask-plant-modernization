"""Tests for chask.pipeline.ingest."""

import textwrap
from pathlib import Path

import pandas as pd
import pytest

from chask.pipeline.ingest import load_raw


def test_load_raw_returns_dataframe():
    df = load_raw()
    assert isinstance(df, pd.DataFrame)


def test_load_raw_row_count():
    df = load_raw()
    assert len(df) == 29


def test_load_raw_columns():
    df = load_raw()
    expected = {
        "fecha",
        "produccion_kg",
        "consumo_kwh",
        "fallas_maquina",
        "mantenimiento",
        "ventas_usd",
        "costos_usd",
        "tiempo_inactividad_horas",
    }
    assert set(df.columns) == expected


def test_load_raw_fecha_is_datetime():
    df = load_raw()
    assert pd.api.types.is_datetime64_any_dtype(df["fecha"])


def test_load_raw_first_date():
    df = load_raw()
    assert df["fecha"].iloc[0] == pd.Timestamp("2020-01-31")


def test_load_raw_last_date():
    df = load_raw()
    assert df["fecha"].iloc[-1] == pd.Timestamp("2022-05-31")


def test_load_raw_missing_file_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="not found"):
        load_raw(path=tmp_path / "nonexistent.csv")


def test_load_raw_missing_column_raises(tmp_path: Path):
    csv = tmp_path / "bad.csv"
    csv.write_text(
        textwrap.dedent("""\
            fecha,produccion_kg
            2020-01-31,14993
        """)
    )
    with pytest.raises(ValueError, match="missing expected columns"):
        load_raw(path=csv)


def test_load_raw_no_nulls():
    df = load_raw()
    assert df.isnull().sum().sum() == 0


def test_load_raw_produccion_positive():
    df = load_raw()
    assert (df["produccion_kg"] > 0).all()


def test_load_raw_consumo_positive():
    df = load_raw()
    assert (df["consumo_kwh"] > 0).all()
