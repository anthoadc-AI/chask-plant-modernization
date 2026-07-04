# Energy Efficiency & Process Optimization — Technical Summary

**Project**: Panificadora Chask plant modernization  
**Package**: `chask` v1.0.0  
**Phase**: 3 — Energy efficiency and process optimization  
**Data source**: `data/raw/monthly_reconstructed.csv` (reconstructed; see data dictionary)

---

## 1. Master Assumptions Table

All quantitative results in Phase 3 depend on the following assumptions.
A reviewer can audit every number by checking the constant named in the
**Source** column against the code.

| Parameter | Value | Unit | Source (code constant) | Notes |
|---|---|---|---|---|
| Energy tariff | 0.065 | USD/kWh | `config.ENERGY_TARIFF_USD_KWH` | Bolivia ENDE industrial rate, ~2021 (approximate) |
| Emission factor | 0.40 | kgCO₂/kWh | `config.EMISSION_FACTOR_KG_CO2_KWH` | Bolivia SIN grid; IEA 2020 / CNDC data (approximate) |
| Monthly operating hours | 720 | h/month | `config.MONTHLY_OPERATING_HOURS` | 24 h/day × 30 days nominal |
| Post capacity multiplier | 1.5 | × | `config.POST_CAPACITY_MULTIPLIER` | Engineering report: +50% installed capacity |
| Discount rate | 10% | % p.a. | `config.DISCOUNT_RATE` | Standard project finance assumption |
| Total investment | 85,000 | USD | `config.TOTAL_INVESTMENT_USD` | Documented project budget |
| Capacity ramp | 3 | years | `roi.CAPACITY_RAMP_YEARS` | Years to fully utilize +50% capacity (assumption) |
| NPV projection | 5 | years | `roi.PROJECTION_YEARS` | Standard mid-term evaluation horizon |
| Steady-state start | Dec 2021 | — | `kpis.STEADY_STATE_START` | Post commissioning; derived from failure trend analysis |
| Z-score threshold | 1.5 | σ | `load_profile.BASE_ANOMALY_ZSCORE` | For monthly base-load anomaly detection (synthetic daily) |

---

## 2. Motor Inventory (Plausible Reconstruction)

The exact motor asset register is confidential client property.
The inventory below is a plausible reconstruction for a medium Bolivian
industrial bakery producing ~14,000 kg/month.

Savings formula (per motor group):
```
savings_kwh_mo = P_shaft_kW × hours_per_month × (1/η_old − 1/η_new)
```

Old motors: IE1-class, >5 years service, degraded windings (η = 0.75–0.82).
New motors: IE3-class premium efficiency (per IEC 60034-30-1, 2–15 kW band).

| Equipment | kW | Count | η old | η new | h/mo | Savings/unit kWh | Total kWh/mo |
|---|---|---|---|---|---|---|---|
| Amasadora espiral 1 | 11.0 | 2 | 0.780 | 0.921 | 360 | 776 | 1,552 |
| Amasadora espiral 2 | 7.5 | 1 | 0.770 | 0.912 | 320 | 487 | 487 |
| Laminadora | 5.5 | 2 | 0.750 | 0.900 | 300 | 367 | 733 |
| Batidora industrial | 3.7 | 3 | 0.760 | 0.895 | 280 | 206 | 617 |
| Ventilación auxiliar | 2.2 | 4 | 0.800 | 0.900 | 720 | 220 | 880 |
| Transporte interno | 1.5 | 3 | 0.780 | 0.885 | 480 | 109 | 328 |
| Soplante horno rot. | 15.0 | 2 | 0.820 | 0.930 | 600 | 1,298 | 2,596 |
| **Fleet total** | | | | | | | **7,193** |

---

## 3. Reconciliation: Theoretical vs. Observed Savings

The motor-fleet calculation (row 1) is the **only independently derived figure**.
The residual three items are an **estimated allocation of the residual** based on
field-diagnostic findings. Individual components were not separately metered.

| Item | kWh/month (central) | Range | Basis |
|---|---|---|---|
| Motor fleet replacement (**theoretical**) | 7,193 | — | Computed from `motors.py` formula |
| ↳ Defective connections | ~2,000 | 1,800–2,200 | High-resistance connections in panel (diagnostic) |
| ↳ Phantom / idle load | ~1,500 | 1,200–1,800 | Motors energized off-shift (diagnostic) |
| ↳ Automation / demand shaping | ~1,074 | 800–1,300 | PLC-controlled peak reduction (diagnostic) |
| **Observed SS savings** (pre − SS mean) | **11,765** | — | Dataset: 51,827 − 40,062 kWh/mo |
| **Residual** (observed − theoretical) | **~4,572** | — | Attributed to field-diagnostic items above |

> ⚠️ **Allocation is indicative; individual components were not separately metered.**
> The motor calculation explains ~61% of the observed reduction. The remaining
> ~39% residual is *consistent* with the field-diagnostic findings — it is not
> a separately verified quantity.

The observed savings are pre mean (51,827 kWh/mo) − steady-state mean (40,062 kWh/mo).
Motor replacement accounts for ~61% of the reduction; the residual ~39% is consistent
with connections, phantom load, and automation improvements per the engineering report.

---

## 4. Energy KPIs

| Metric | Value |
|---|---|
| Pre-intervention mean | 51,827 kWh/mo |
| Post-intervention mean | 41,689 kWh/mo (−19.6%) |
| Steady-state mean (Dec 2021–May 2022) | 40,062 kWh/mo (−26.3% vs. baseline) |
| Annual energy savings (SS) | 141,177 kWh/yr |
| Annual savings in USD (SS, tariff 0.065) | $9,177/yr |
| Annual CO₂ avoided (SS, factor 0.40) | 56,471 kgCO₂/yr |

---

## 5. Process Optimization

### Throughput by Period

| Period | n | Mean prod (kg) | Op. hours | kg/op-hour | vs. Pre |
|---|---|---|---|---|---|
| Pre | 20 | 13,680 | 693 | 19.7 | — |
| Transition (Sep–Nov 2021) | 3 | 13,950 | 691 | 20.2 | +2.4% |
| Steady-state (Dec 2021–May 2022) | 6 | 15,899 | 711 | 22.4 | **+13.3%** |

The steady-state productivity improvement (+13.3%) is consistent with the
engineering report's documented +22% (note: the report figure may refer to
specific controlled measurements vs. the monthly average used here).

### Reliability

| Period | Mean failures/mo | MTBF (h) | Downtime cost/mo |
|---|---|---|---|
| Pre | 8.05 | 88.7 h | $165 |
| Transition | 8.33 | 87.2 h | — |
| Steady-state | 2.33 | 316.1 h | $96 |

MTBF improved by **+256%** at steady state vs. pre.
Transition shows elevated failures (commissioning spike), consistent with the
documented Sep–Oct 2021 spike in the dataset.

---

## 6. ROI Analysis

Investment: USD 85,000 · Discount rate: 10% · Horizon: 5 years

| Scenario | Annual benefit | Payback | NPV (5yr) |
|---|---|---|---|
| **Conservative** (energy + downtime only) | $11,230 | 7.6 yr | **−$42,430** |
| **Base** (+ observed production growth) | $19,490 | 4.4 yr | **−$11,116** |
| **Optimistic** (+ full capacity ramp, 3yr) | $28,741* | 1.8 yr | **+$69,618** |

*Year-1 benefit; rises to ~$47,100/yr at full capacity.

### Honest Interpretation

1. **Energy savings alone do not justify the investment** at a 10% discount rate
   over 5 years. The conservative NPV is −$42,430.
2. **Including the observed production growth**, the base NPV reaches −$11,116 —
   barely negative. With a longer horizon or lower discount rate it crosses positive.
3. **The full financial case requires capacity utilization**: the +50% installed
   capacity, progressively utilized over 3 years, yields NPV = +$69,618. The
   post-intervention dataset already shows 15,249 kg/mo (+11.5% vs. pre), confirming
   partial materialization.
4. **The dataset post-period is only 9 months** (including commissioning). The
   optimistic scenario is a projection, not an observed outcome.

Figures: `reports/figures/09_roi_payback_curves.png`

---

## 7. Load Profile (Synthetic Data — Demonstration Only)

⚠️ **This section uses `daily_synthetic.csv`** — model-generated data, NOT real
measurements. Results are illustrative only.

The weekly load profile derived from the synthetic dataset shows higher energy
consumption on Fridays and Saturdays, consistent with the production weight
assumptions used to generate the synthetic data. This reflects typical bakery
operations (pre-weekend baking demand).

See `notebooks/05_energy_and_process.ipynb` for load profile plots.
