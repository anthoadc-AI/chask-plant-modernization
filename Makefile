.PHONY: install lint format test pipeline datagen

install:
	pip install -e ".[dev]"

lint:
	ruff check src tests
	ruff format --check src tests

format:
	ruff check --fix src tests
	ruff format src tests

test:
	pytest

pipeline:
	python -m chask.pipeline.run

datagen:
	python -m chask.datagen.synthetic
