"""Tests for chask.config."""

from pathlib import Path

from chask import config


def test_raw_dir_is_path():
    assert isinstance(config.RAW_DIR, Path)


def test_staging_dir_is_path():
    assert isinstance(config.STAGING_DIR, Path)


def test_analytics_dir_is_path():
    assert isinstance(config.ANALYTICS_DIR, Path)


def test_intervention_cutoff_value():
    assert config.INTERVENTION_CUTOFF == "2021-08-31"


def test_random_seed_value():
    assert config.RANDOM_SEED == 42


def test_columns_list():
    assert "fecha" in config.COLUMNS
    assert "produccion_kg" in config.COLUMNS
    assert "consumo_kwh" in config.COLUMNS
    assert len(config.COLUMNS) == 8


def test_repo_root_contains_pyproject():
    repo_root = config.RAW_DIR.parents[1]
    assert (repo_root / "pyproject.toml").exists()
