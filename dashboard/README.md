# Panificadora Chask — Streamlit Dashboard

Interactive portfolio dashboard for the Panificadora Chask plant modernization project.

## Local Run

From the **project root** (not from `dashboard/`):

```bash
streamlit run dashboard/app.py
```

The app adds `src/` to `sys.path` automatically so the `chask` package is importable
without a separate pip install. Alternatively, install editable first:

```bash
pip install -e ".[dev]"
streamlit run dashboard/app.py
```

## Pages

| Page | Contents |
|---|---|
| Overview | 7 headline KPI cards, energy time series, findings table |
| Energy | Intensity trend, annualized savings, motor reconciliation, load profile |
| Statistics | Hypothesis tests, ITS charts, Cohen's d |
| Reliability & Process | MTBF, failure trends, throughput, downtime cost |
| ROI Scenarios | Interactive tariff/discount sliders, payback curves |
| Project Management | Charter, Gantt, risk register, cost baseline |

## Streamlit Community Cloud Deployment

1. Fork or push the repository to `anthoadc-AI/chask-plant-modernization` on GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in.
3. Click **New app** → select the repository.
4. Set **Main file path** to `dashboard/app.py`.
5. Streamlit Cloud will use `dashboard/requirements.txt` automatically if it is in the
   app directory; otherwise point it to the root `requirements.txt`.
6. Click **Deploy**.

> **Note**: The app adds `src/` to `sys.path` at startup so the `chask` package is
> importable without being pip-installed from PyPI. All data files in `data/` are
> read at runtime relative to the project root.

## Data Disclosure

All analytical figures are derived from `data/analytics/monthly_enriched.csv`,
a documented reconstruction of the real project dataset. See
[docs/data-dictionary.md](../docs/data-dictionary.md) for full disclosure.
