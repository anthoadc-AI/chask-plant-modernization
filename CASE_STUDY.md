# Case Study: Panificadora Chask Plant Modernization

**Project**: Plant Expansion and Resource Optimization  
**Client**: Panificadora Chask, Punata, Cochabamba, Bolivia  
**Executing firm**: INGEDAV S.R.L.  
**Project director**: Anthony Dávila, Energy Projects Engineer & Director  
**Period**: December 21, 2020 – June 4, 2022  
**Investment**: USD 85,000

---

## Context

Panificadora Chask is an industrial bakery operating in Punata, a mid-sized town in the
Cochabamba valley of Bolivia. The company had been running for several years using a mix
of manual, semi-automatic, and artisanal equipment — much of it original to the facility
or patched together over time. By late 2020, the business had stabilized around
~14,000 kg/month of production and roughly USD 21,000/month in revenue, but the owners
recognized that the operation was hitting a ceiling: they were losing sales to competitors
with higher capacity and their equipment costs were eating into margins.

INGEDAV S.R.L. was engaged in December 2020 to conduct a full energy and production audit
and, if warranted, execute a plant modernization program.

---

## Challenge

The diagnostic phase (Phase 1) revealed four interconnected problems:

**Energy waste.** The plant was consuming approximately 55,000 kWh/month per the
engineering-report baseline (the reconstructed dataset pre-period mean is 51,827 kWh/month;
both figures reflect the same operational reality measured at different reference points) —
abnormally high for its production volume. The culprit was a fleet of electric motors older than
five years, running at IE1 efficiency levels (75–82%), well below the IE3 premium class
(88–93%) now standard in industrial applications. Degraded windings, poor connections in
the distribution panel, and motors running under light or no load compounded the losses.

**Unreliable machinery.** Equipment failures averaged 8.1 events/month, generating
26.9 hours of downtime. Each failure disrupted the production schedule and triggered
costly reactive maintenance. The bottlenecks were concentrated in the kneading and
laminating stages, which were also the slowest and most manual parts of the process.

**Capacity constraint.** The plant could not grow output without replacing the
production-line equipment. Manual kneading and laminating limited throughput and
introduced quality inconsistencies that periodically required rework.

**Margin pressure.** Gross margin was running at ~21.4%, driven down by the combination
of high energy costs and production inefficiencies.

---

## Approach

The project was structured in four phases across 17.5 months:

### Phase 1 — Evaluation & Diagnosis (Dec 2020 – Mar 2021)

I began with a 30-day real-time electrical monitoring period, installing portable
energy analyzers at each circuit breaker. This revealed the energy intensity breakdown
by equipment group and flagged specific faults: high-resistance connections in the
main distribution panel, two motors running at near-no-load during off-shift hours,
and a ventilation fan running continuously when the oven was idle.

Simultaneously, I conducted production flow mapping and cycle-time measurements to
identify the throughput bottlenecks and quantify the output ceiling under the current
equipment configuration.

The diagnosis report presented three scenarios to the client: do-nothing (continue
with increasing maintenance costs), partial upgrade (motor replacement only), and full
modernization (new equipment + motors + EMS + electrical system). The client approved
the full program.

### Phase 2 — Design & Planning (Apr 2021 – Jun 2021)

Using SolidWorks CAD, I designed the new plant layout, which included an expanded
production area to accommodate the new machinery. I specified IE3-class motors for all
production equipment and designed an Energy Management System (EMS) to provide
continuous monitoring of consumption by circuit.

The electrical upgrade design addressed all faults identified in Phase 1: rewiring of
faulty connections, installation of power factor correction capacitors, and new
distribution boards with proper circuit labeling.

### Phase 3 — Implementation & Installation (Jul 2021 – Aug 2021)

INGEDAV's shop fabricated the new industrial kneader, laminator, and mixers
in-house — a decision that reduced procurement risk and kept costs within budget.
Manufacturing new equipment to specification is the core of what INGEDAV does;
importing equivalent machinery would have cost more and taken longer.

Equipment installation, the EMS go-live, and the electrical system modernization
were all completed by the end of August 2021. The new machinery was fully operational
on schedule.

### Phase 4 — Training & Monitoring (Sep 2021 – Jun 2022)

The final phase covered operator training on all new equipment and the EMS interface,
establishment of a formal preventive maintenance program with written inspection
intervals, and nine months of post-intervention monitoring to measure outcomes.

---

## Data & Methods

### Dataset

The original monthly production and energy records from this engagement are
confidential client property. For this portfolio, I constructed a **documented
reconstruction**: 29 monthly observations (January 2020 – May 2022) generated by a
reproducible Python script (`src/chask/datagen/monthly_reconstruction.py`, seed=42),
calibrated to the engineering report's documented averages and known anomaly months.

This approach is honest and transparent. Using real data would violate client
confidentiality. Fabricating data without disclosure would be dishonest. A documented
reconstruction with a fixed seed is reproducible, auditable, and clearly labeled at
every point in the codebase and documentation. See the
[data dictionary](docs/data-dictionary.md) for the full methodology.

### Statistical Analysis

All inference runs on the 29-observation monthly dataset. I tested all 7 headline
metrics using Mann-Whitney U tests (for non-normal distributions) or Welch's t-tests
(where both groups passed Shapiro-Wilk normality), with α = 0.05. All 7 reached
statistical significance with large Cohen's d effect sizes — the intervention effect
is substantial relative to the pre-period variability.

An Interrupted Time Series (ITS) segmented OLS regression on energy consumption
confirmed a structural break at the August 2021 cutoff: the level-change coefficient
is statistically significant, and the model explains a substantial share of the
time-series variance.

Anomaly detection (Z-score threshold |Z| > 2.0, and Isolation Forest with 10%
contamination) flagged the pre-period months with the highest energy spikes as
outliers, consistent with the field diagnostic finding of intermittent phantom loads.

---

## Results

### Post-period averages (n=9, Sep 2021 – May 2022)

| Metric | Pre | Post | Change |
|---|---|---|---|
| Energy consumption (kWh/mo) | 51,827 | 41,689 | **−19.6%** |
| Energy intensity (kWh/kg) | 3.81 | 2.76 | **−27.5%** |
| Gross margin | 21.4% | 29.0% | **+7.5 pp** |
| Sales (USD/mo) | 20,756 | 23,100 | **+11.3%** |
| Machine failures/month | 8.1 | 4.3 | **−46.2%** |
| Downtime (h/month) | 26.9 | 15.7 | **−41.7%** |
| Production (kg/mo) | 13,680 | 15,249 | **+11.5%** |

### Steady-state (n=6, Dec 2021 – May 2022)

Once the commissioning period settled, results improved further:

- Energy consumption: **40,062 kWh/mo** (−22.7% vs pre, −26.3% vs the highest
  pre-period months)
- MTBF (mean time between failures): 88.7 h → **316.1 h** (+256%)
- Productivity: 19.7 → 22.4 kg/operational hour (+13.3%)

The engineering report cited −27% energy and +22% productivity; these figures align
with the steady-state slice of the dataset, not the full post-period average. The
distinction matters for honest reporting.

### Motor savings reconciliation

Motor fleet replacement (theoretical, using the IE1→IE3 efficiency gain formula)
accounts for approximately **61%** of the observed energy reduction.
The remaining ~39% residual is consistent with the non-motor improvements identified
in the diagnostic: high-resistance connection repair, phantom-load elimination, and
demand-shaping automation. These items were not separately metered; their individual
breakdown is an estimated allocation, not a verified measurement.

### ROI

The investment was USD 85,000. At the Bolivian industrial electricity tariff
(~USD 0.065/kWh) and a 10% annual discount rate over a 5-year horizon:

| Scenario | What is included | Annual benefit | NPV (5yr) |
|---|---|---|---|
| **Conservative** | Energy savings + downtime cost reduction | $11,230 | **−$42,430** |
| **Base** | + Observed production growth margin | $19,490 | **−$11,116** |
| **Optimistic** | + Full +50% capacity utilization over 3 years | $28,741 | **+$69,618** |

**Interpretation**: At Bolivian electricity prices, energy savings alone do not justify
an USD 85,000 investment over five years. The financial case requires the production
capacity growth that the new equipment enables. The post-intervention dataset (9 months)
already shows partial materialization — production is up 11.5% and gross margin has
improved 7.5 percentage points — but the full case depends on the client continuing to
grow sales volume to fill the expanded capacity.

---

## Lessons Learned

**1. Build a commissioning buffer into the monitoring plan.**  
September and October 2021 showed elevated failure counts (10 and 9 vs. the pre-period
mean of 8.1). This was expected — new machinery requires calibration, and operators
need time to learn it. If I had reported the post-period average without flagging this,
the failure improvement would have appeared modest. Communicating this to the client
upfront prevented confusion and set realistic expectations.

**2. The motor calculation explains only part of the savings.**  
When I first ran the theoretical motor-savings model, it projected ~7,200 kWh/month.
The observed steady-state reduction was ~11,765 kWh/month — roughly 39% larger. The
gap came from non-motor improvements: rewiring bad connections, eliminating phantom
loads, and the automation reducing peak demand. A rigorous field diagnostic, not just
motor replacement, is what moves the needle.

**3. Honest ROI reporting builds credibility.**  
Presenting three scenarios with an honest negative NPV in the conservative case is
uncomfortable — but it is accurate. The investment was justified by the full picture
(capacity growth, quality improvement, operational reliability), not by energy savings
alone. Clients and evaluators trust analyses that acknowledge limitations.

**4. Data confidentiality requires a reproducible reconstruction methodology.**  
Original client records could not be shared. Rather than presenting a sanitized
spreadsheet of uncertain provenance, I built a reproducible reconstruction script
with a fixed seed, calibrated it to the engineering report metrics, and documented
every assumption. This is auditable and honest. The methodology is fully described
in the data dictionary.

---

## Replicability

All analyses in this repository are fully reproducible:

```bash
git clone https://github.com/anthoadc-AI/chask-plant-modernization.git
cd chask-plant-modernization
make install && make pipeline && make test
```

The data pipeline regenerates the staged and analytics datasets from the raw
reconstruction. All 230+ unit tests verify the analytical logic against expected
values. The figures, dashboard, and documentation site are generated programmatically
from the same source data.

No analysis logic is duplicated outside `src/chask/`. The Streamlit dashboard,
MkDocs site, and notebooks all delegate computation to the package.

---

*Anthony Dávila · anthoadc@gmail.com · [linkedin.com/in/anthony-davila-034b921ba](https://linkedin.com/in/anthony-davila-034b921ba)*
