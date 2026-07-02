# chask-plant-modernization

[![CI](https://github.com/anthoadc-AI/chask-plant-modernization/actions/workflows/ci.yml/badge.svg)](https://github.com/anthoadc-AI/chask-plant-modernization/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://github.com/anthoadc-AI/chask-plant-modernization)

Portfolio-grade repository documenting the real consulting engagement executed by **INGEDAV S.R.L.**
(Anthony Davila, Project Director) for the plant modernization and energy optimization of
**Panificadora Chask**, an industrial bakery in Punata, Cochabamba, Bolivia (Dec 2020 – Jun 2022).

---

## Phase Status

| Phase | Name | Status |
|---|---|---|
| 0 | Foundations & Governance | ✅ Complete |
| 1 | Data Engineering | ✅ Complete |
| 2 | Data Science | ✅ Complete |
| 3 | Energy Efficiency & Process Optimization | 🔲 Pending |
| 4 | Visible Products (Dashboard + Docs Site) | 🔲 Pending |
| 5 | Portfolio Polish | 🔲 Pending |

---

## Repository Structure

```
chask-plant-modernization/
├── .github/              # CI workflow and GitHub templates
├── data/
│   ├── raw/              # Reconstructed monthly dataset (see data dictionary)
│   ├── staging/          # Validated, schema-checked data
│   └── analytics/        # Enriched KPIs + synthetic daily dataset
├── docs/                 # Data dictionary, findings, source documents
├── notebooks/            # Exploratory analysis notebooks (Phase 2)
├── project-management/   # Charter, WBS, schedule, risk register, cost baseline
├── reports/figures/      # Static PNG + interactive HTML figures (Phase 2)
├── src/chask/            # Python package (all reusable logic lives here)
└── tests/                # pytest unit tests (123 tests)
```

> **Data note**: The monthly dataset is a reproducible reconstruction calibrated to
> documented engineering results. Original client records are confidential.
> See [docs/data-dictionary.md](docs/data-dictionary.md).

---

## Installation

```bash
git clone https://github.com/anthoadc-AI/chask-plant-modernization.git
cd chask-plant-modernization
make install
```

Requires Python >= 3.10.

## Development

```bash
make lint    # ruff check + ruff format --check
make format  # ruff check --fix + ruff format
make test     # pytest (123 tests)
make pipeline # run data pipeline (ingest → validate → transform)
make datagen  # regenerate synthetic daily dataset
make figures  # generate all analysis figures (reports/figures/)
make analysis # statistical summary + figures
```
