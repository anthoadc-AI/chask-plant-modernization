# Phase 2 Findings — Panificadora Chask

**Data source**: `data/raw/monthly_reconstructed.csv` (reconstructed from engineering
documentation; see [data dictionary](data-dictionary.md) for disclosure).  
**Analysis period**: Jan 2020 – May 2022 (n=29 months).  
**Intervention cutoff**: Aug 31, 2021 (pre: n=20, post: n=9).

---

## 1. Headline KPI Summary

All 7 headline metrics improved in the post-intervention period vs. pre.

| Metric | Pre mean | Post mean | Change | Note |
|---|---|---|---|---|
| Energy consumption (kWh) | 51,827 | 41,689 | −19.6% | ✓ |
| Energy intensity (kWh/kg) | 3.81 | 2.76 | −27.5% | ✓ |
| Gross margin (%) | 21.4% | 29.0% | +7.5 pp | ✓ |
| Sales (USD) | 20,756 | 23,100 | +11.3% | ✓ |
| Machine failures /month | 8.1 | 4.3 | −46.2% | † |
| Downtime (h/month) | 26.9 | 15.7 | −41.7% | ✓ |
| Production (kg) | 13,680 | 15,249 | +11.5% | ✓ |

† Machine failures show a commissioning spike (10 and 9/month in Sep–Oct 2021)
before stabilizing at 2–3/month in the steady-state phase (Dec 2021–May 2022).

**Steady-state energy** (Dec 2021–May 2022): ~40,062 kWh/month, or **−26.3%** vs.
the pre-intervention baseline of ~54,388 kWh/month, consistent with the field-documented
target of −27%.

---

## 2. Statistical Tests

All hypothesis tests used the real monthly dataset only (n=29). The synthetic daily
dataset was not used for inference (see [data dictionary](data-dictionary.md)).

**Protocol**: Shapiro-Wilk normality test (α=0.05) per group → t-test (Welch) if
both groups are normal, Mann-Whitney U otherwise → Cohen's d effect size.

Full results are available in `notebooks/03_statistical_tests.ipynb` and the
statistical summary table produced by `chask.analysis.stats.full_statistical_summary`.

Key findings:
- **Energy consumption**: statistically significant reduction; large effect size.
- **Energy intensity**: statistically significant reduction; large effect size.
- **Gross margin**: significant increase in post period.
- **Production**: significant increase in post period.
- **Machine failures and downtime**: significant reductions in post period overall,
  noting the commissioning spike in Sep–Oct 2021.

---

## 3. Interrupted Time Series (ITS) Analysis

ITS segmented regression was run for `consumo_kwh` and `intensity_kwh_kg`.

Model: `y = β₀ + β₁·t + β₂·D + β₃·t_post`

Where `D` = intervention indicator (0 pre, 1 post) and `t_post` = months since
intervention (0 pre, 1–9 post).

- **β₂** (level change): immediate drop in energy at the intervention point.
- **β₃** (slope change): ongoing monthly improvement trend post-intervention.

Full ITS results and figures are in `reports/figures/05_its_consumo_kwh.png` and
`reports/figures/05_its_intensity_kwh_kg.png`.

---

## 4. Anomaly Detection

### Z-score (univariate, threshold |Z| > 2.0)

Applied to: `consumo_kwh`, `produccion_kg`, `fallas_maquina`,
`tiempo_inactividad_horas`, `intensity_kwh_kg`.

Anomalies flagged correspond to known events documented in the engineering report:
commissioning months and pre-intervention equipment failure spikes.

### Isolation Forest (multivariate, contamination = 0.10, n_estimators = 200, seed = 42)

Uses all 5 operational columns jointly. Identifies multivariate outliers that may
not be visible in any single variable.

Results are visualized in `reports/figures/04_anomalies.png`.

---

## 5. Figures

All figures are in `reports/figures/`. Interactive HTML versions are included for
time-series and ITS plots.

| File | Description |
|---|---|
| `01_time_series.png` | Monthly energy and production with pre/post zones |
| `01_time_series_interactive.html` | Interactive version (energy) |
| `02_boxplots_pre_post.png` | Box plots for 6 KPIs: pre vs. post |
| `03_correlation_heatmap.png` | Pearson correlation matrix |
| `04_anomalies.png` | Anomaly flags on energy time series |
| `05_its_consumo_kwh.png` | ITS segmented regression for energy consumption |
| `05_its_consumo_kwh_interactive.html` | Interactive ITS (energy) |
| `05_its_intensity_kwh_kg.png` | ITS for energy intensity |
| `05_its_intensity_kwh_kg_interactive.html` | Interactive ITS (intensity) |
| `06_margin_sales.png` | Sales (bars) and gross margin (line) |
| `06_margin_sales_interactive.html` | Interactive version |

---

## 6. Honest Framing Notes

1. The post period includes a commissioning/stabilization phase. Machine failure
   counts in Sep–Oct 2021 were elevated (10, 9/month) and must be noted when
   reporting the post-period failure average.
2. All headline figures are pre/post period averages from the reconstructed monthly
   dataset, not raw operational records. See the data dictionary.
3. The field-documented steady-state results (−27% energy, +50% capacity, +22%
   productivity) were measured under controlled conditions and are consistent with
   the Dec 2021–May 2022 slice of the dataset; they should not be conflated with
   the full post-period average.
