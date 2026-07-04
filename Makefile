.PHONY: install lint format test pipeline datagen figures analysis energy dashboard docs-serve docs-build

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

figures:
	python -m chask.analysis.viz

analysis:
	python -m chask.analysis.run

energy:
	python -m chask.energy.run

dashboard:
	streamlit run dashboard/app.py

docs-serve:
	mkdocs serve

docs-build:
	mkdocs build --strict
