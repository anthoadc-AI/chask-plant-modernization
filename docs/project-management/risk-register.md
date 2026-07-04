# Risk Register — Panificadora Chask

**Project**: Plant Expansion and Resource Optimization  
**Executing firm**: INGEDAV S.R.L. | **Director**: Anthony Dávila  
**Period**: December 2020 – June 2022

Scale: Probability and Impact rated 1 (Low) – 3 (High). Risk Score = Probability × Impact.

---

## Risk Register

| ID | Risk Description | Category | Probability | Impact | Score | Mitigation | Status |
|---|---|---|---|---|---|---|---|
| R-01 | Extended commissioning period for new machinery causes higher-than-expected failure counts and downtime in early post-intervention months | Operational | 3 | 2 | 6 | Build a stabilization buffer of 2–3 months into the post-intervention monitoring plan; communicate to client that early metrics reflect commissioning, not steady-state | **Materialized** |
| R-02 | Supply delays for machinery components (motors, bearings, structural steel) extend Phase 3 timeline | Supply chain | 2 | 3 | 6 | Identify alternative local suppliers; place orders with lead-time buffer; manufacture non-critical components in-house at INGEDAV | Partially mitigated |
| R-03 | Client staff resistance to adopting new machinery and EMS practices | Human | 2 | 2 | 4 | Involve operators early in Phase 1 diagnostics; design training program (Phase 4) with hands-on sessions; appoint an internal champion | Mitigated |
| R-04 | Electrical system upgrade reveals hidden infrastructure faults (overloaded circuits, substandard wiring) increasing scope | Technical | 2 | 2 | 4 | Include a contingency allowance in the cost baseline; conduct 30-day monitoring before finalizing electrical design | Mitigated |
| R-05 | Production downtime during equipment installation causes revenue loss for the client | Financial | 2 | 3 | 6 | Schedule installation in phases to maintain partial production; plan weekend/overnight work windows for critical changeovers | Partially mitigated |
| R-06 | New machinery does not achieve design performance targets (+50% capacity, -27% energy) due to calibration issues | Technical | 1 | 3 | 3 | Conduct factory acceptance testing at INGEDAV before delivery; include commissioning and calibration period in Phase 3 scope | Mitigated |
| R-07 | Budget overrun due to unforeseen civil works for plant area expansion | Financial | 2 | 2 | 4 | Conduct detailed site survey in Phase 1; include 5% contingency in cost baseline for civil works | Mitigated |
| R-08 | EMS data quality issues (sensor drift, connectivity loss) affect post-intervention monitoring | Technical | 1 | 2 | 2 | Select industrial-grade sensors with redundancy; establish manual backup recording protocol | Mitigated |
| R-09 | Key INGEDAV technical personnel unavailable during critical Phase 3 installation window | Resource | 1 | 3 | 3 | Cross-train two technicians on all critical installation tasks; maintain contingency labor contracts | Mitigated |
| R-10 | Inadequate preventive maintenance after project closure causes equipment degradation and regression of efficiency gains | Operational | 2 | 3 | 6 | Deliver written maintenance manual with inspection intervals; train a dedicated internal maintenance lead; recommend 12-month follow-up inspection by INGEDAV | Pending (long-term) |

---

## Risk Summary

| Score Range | Count | Risks |
|---|---|---|
| High (6–9) | 4 | R-01, R-02, R-05, R-10 |
| Medium (3–5) | 4 | R-03, R-04, R-06, R-07, R-09 |
| Low (1–2) | 2 | R-08 |

---

## Materialized Risks — Post-mortem Notes

**R-01 — Extended commissioning (materialized)**  
The monthly dataset confirms that machine failures increased from 7.3/month (pre) to
10.2/month (post), and downtime increased slightly from 28.3 to 29.1 h/month. These
metrics reflect the commissioning and stabilization phase of new industrial machinery
during September 2021 – May 2022, not a permanent operational regression. The
engineering report documents steady-state performance after calibration: -27% energy
consumption and +50% production capacity. This distinction is critical for honest
reporting and is documented in CLAUDE.md.

**R-05 — Production downtime during installation (partially materialized)**  
Production volume decreased 4.9% in the post-intervention period (13,881 → 13,207 kg/month
average), consistent with planned downtime during Phase 3 equipment changeover. This is
expected in the context of a phased installation and does not indicate a permanent
production loss.
