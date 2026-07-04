# Panificadora Chask — Plant Modernization

**Portfolio repository** documenting a real industrial consulting engagement:
the plant modernization and energy optimization of **Panificadora Chask**,
an industrial bakery in Punata, Cochabamba, Bolivia.

- **Client**: Panificadora Chask
- **Executing firm**: INGEDAV S.R.L. (Ingeniería, Diseño y Automatización)
- **Project Director**: Anthony Dávila
- **Period**: December 21, 2020 – June 4, 2022
- **Intervention cutoff**: August 2021 (new machinery fully operational)
- **Total investment**: USD 85,000
- **GitHub**: [anthoadc-AI/chask-plant-modernization](https://github.com/anthoadc-AI/chask-plant-modernization)

---

## Project Outcomes — Headline Metrics

All 7 headline metrics improved after the August 2021 intervention.

| Metric | Pre (n=20) | Post (n=9) | Change |
|---|---|---|---|
| Energy consumption (kWh/mo) | 51,827 | 41,689 | **−19.6%** |
| Energy intensity (kWh/kg) | 3.81 | 2.76 | **−27.5%** |
| Gross margin (%) | 21.4% | 29.0% | **+7.5 pp** |
| Sales (USD/mo) | 20,756 | 23,100 | **+11.3%** |
| Machine failures/month | 8.1 | 4.3 | **−46.2%** |
| Downtime (h/month) | 26.9 | 15.7 | **−41.7%** |
| Production (kg/mo) | 13,680 | 15,249 | **+11.5%** |

> **Honest framing**: Sep–Oct 2021 show a commissioning spike in failures (10, 9 vs
> pre mean 8.1). Steady-state (Dec 2021–May 2022) results are even better:
> energy ~40,062 kWh/mo (−22.7% vs pre-period mean of 51,827 kWh; −26.3% vs engineering-report baseline of ~54,388 kWh).

---

## Dataset Disclosure

!!! warning "Documented Reconstruction"
    The monthly dataset (29 observations, Jan 2020 – May 2022) is a **documented
    reconstruction** calibrated to the engineering report metrics. Original client
    records are confidential. The reconstruction is reproducible with a fixed seed
    (`seed=42`). See the [Data Dictionary](data-dictionary.md) for full details.

---

## Repository Structure

```
chask-plant-modernization/
├── data/               # Raw, staging, analytics datasets
├── docs/               # Documentation (this site)
├── notebooks/          # Jupyter notebooks
├── project-management/ # PM artefacts (charter, WBS, schedule, risks, cost)
+-- reports/figures/    # Generated figures (PNG + interactive HTML)
├── src/chask/          # Python package — all analysis logic
└── tests/              # pytest unit tests
```

## Competencies Demonstrated

- **Project Management**: charter, WBS, Gantt, risk register, cost baseline
- **Data Engineering**: reproducible pipeline, schema validation, synthetic data generation
- **Data Science**: EDA, anomaly detection, hypothesis testing, interrupted time series
- **Energy Efficiency**: motor savings model, reconciliation, CO₂ avoidance, ROI
- **Software Engineering**: `src`-layout Python package, CI/CD, MkDocs site, Streamlit dashboard
