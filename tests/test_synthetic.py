"""Tests for chask.datagen.synthetic."""

import numpy as np
import pandas as pd
import pytest

from chask.datagen.synthetic import generate_daily
from chask.pipeline.ingest import load_raw


@pytest.fixture(scope="module")
def monthly_df() -> pd.DataFrame:
    return load_raw()


@pytest.fixture(scope="module")
def daily_df(monthly_df: pd.DataFrame) -> pd.DataFrame:
    return generate_daily(monthly_df, seed=42)


def test_row_count(daily_df: pd.DataFrame):
    assert len(daily_df) == 882


def test_is_synthetic_column_all_true(daily_df: pd.DataFrame):
    assert daily_df["is_synthetic"].all()


def test_date_range_start(daily_df: pd.DataFrame):
    assert daily_df["fecha"].iloc[0] == pd.Timestamp("2020-01-01")


def test_date_range_end(daily_df: pd.DataFrame):
    assert daily_df["fecha"].iloc[-1] == pd.Timestamp("2022-05-31")


def test_period_values(daily_df: pd.DataFrame):
    assert set(daily_df["period"].unique()) == {"pre", "post"}


def test_reproducibility(monthly_df: pd.DataFrame):
    df1 = generate_daily(monthly_df, seed=42)
    df2 = generate_daily(monthly_df, seed=42)
    pd.testing.assert_frame_equal(df1, df2)


def test_different_seeds_differ(monthly_df: pd.DataFrame):
    df1 = generate_daily(monthly_df, seed=42)
    df2 = generate_daily(monthly_df, seed=99)
    assert not df1["consumo_kwh"].equals(df2["consumo_kwh"])


def test_calibration_produccion_kg(daily_df: pd.DataFrame, monthly_df: pd.DataFrame):
    daily_df["month"] = daily_df["fecha"].dt.to_period("M")
    monthly_sums = daily_df.groupby("month")["produccion_kg"].sum()
    monthly_df2 = monthly_df.copy()
    monthly_df2["month"] = monthly_df2["fecha"].dt.to_period("M")
    for _, row in monthly_df2.iterrows():
        assert np.isclose(monthly_sums[row["month"]], row["produccion_kg"], rtol=1e-9)


def test_calibration_consumo_kwh(daily_df: pd.DataFrame, monthly_df: pd.DataFrame):
    daily_df["month"] = daily_df["fecha"].dt.to_period("M")
    monthly_sums = daily_df.groupby("month")["consumo_kwh"].sum()
    monthly_df2 = monthly_df.copy()
    monthly_df2["month"] = monthly_df2["fecha"].dt.to_period("M")
    for _, row in monthly_df2.iterrows():
        assert np.isclose(monthly_sums[row["month"]], row["consumo_kwh"], rtol=1e-9)


def test_calibration_ventas_usd(daily_df: pd.DataFrame, monthly_df: pd.DataFrame):
    daily_df["month"] = daily_df["fecha"].dt.to_period("M")
    monthly_sums = daily_df.groupby("month")["ventas_usd"].sum()
    monthly_df2 = monthly_df.copy()
    monthly_df2["month"] = monthly_df2["fecha"].dt.to_period("M")
    for _, row in monthly_df2.iterrows():
        assert np.isclose(monthly_sums[row["month"]], row["ventas_usd"], rtol=1e-9)


def test_calibration_costos_usd(daily_df: pd.DataFrame, monthly_df: pd.DataFrame):
    daily_df["month"] = daily_df["fecha"].dt.to_period("M")
    monthly_sums = daily_df.groupby("month")["costos_usd"].sum()
    monthly_df2 = monthly_df.copy()
    monthly_df2["month"] = monthly_df2["fecha"].dt.to_period("M")
    for _, row in monthly_df2.iterrows():
        assert np.isclose(monthly_sums[row["month"]], row["costos_usd"], rtol=1e-9)


def test_calibration_fallas_maquina(daily_df: pd.DataFrame, monthly_df: pd.DataFrame):
    daily_df["month"] = daily_df["fecha"].dt.to_period("M")
    monthly_sums = daily_df.groupby("month")["fallas_maquina"].sum()
    monthly_df2 = monthly_df.copy()
    monthly_df2["month"] = monthly_df2["fecha"].dt.to_period("M")
    for _, row in monthly_df2.iterrows():
        assert monthly_sums[row["month"]] == int(row["fallas_maquina"])


def test_calibration_tiempo_inactividad(daily_df: pd.DataFrame, monthly_df: pd.DataFrame):
    daily_df["month"] = daily_df["fecha"].dt.to_period("M")
    monthly_sums = daily_df.groupby("month")["tiempo_inactividad_horas"].sum()
    monthly_df2 = monthly_df.copy()
    monthly_df2["month"] = monthly_df2["fecha"].dt.to_period("M")
    for _, row in monthly_df2.iterrows():
        assert np.isclose(monthly_sums[row["month"]], row["tiempo_inactividad_horas"], rtol=1e-9)


def test_produccion_all_positive(daily_df: pd.DataFrame):
    assert (daily_df["produccion_kg"] > 0).all()


def test_consumo_all_positive(daily_df: pd.DataFrame):
    assert (daily_df["consumo_kwh"] > 0).all()


def test_fallas_binary(daily_df: pd.DataFrame):
    assert daily_df["fallas_maquina"].isin([0, 1]).all()
