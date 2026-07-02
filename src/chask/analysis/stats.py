"""Statistical hypothesis testing and Interrupted Time Series (ITS) analysis.

IMPORTANT — inference scope:
    All hypothesis tests and the ITS regression are executed exclusively on the
    **real monthly dataset (n=29)**. The synthetic daily dataset (n=882) is derived
    from monthly aggregates; using it for inference would artificially inflate the
    sample size and invalidate p-values and confidence intervals.
"""

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

from chask.config import INTERVENTION_CUTOFF

_TEST_COLS = [
    "consumo_kwh",
    "intensity_kwh_kg",
    "gross_margin_pct",
    "ventas_usd",
    "fallas_maquina",
    "tiempo_inactividad_horas",
    "produccion_kg",
]

_ALPHA = 0.05


def normality_test(series: pd.Series) -> dict:
    """Run Shapiro-Wilk normality test on a series.

    Args:
        series: Numeric series to test.

    Returns:
        Dict with keys ``stat``, ``p_value``, ``is_normal`` (at α=0.05).
    """
    stat, p = stats.shapiro(series.dropna())
    return {"stat": float(stat), "p_value": float(p), "is_normal": float(p) > _ALPHA}


def hypothesis_test(pre: pd.Series, post: pd.Series) -> dict:
    """Select and run the appropriate two-sample test based on normality.

    Uses Student's t-test when both groups pass Shapiro-Wilk (p > 0.05),
    otherwise Mann-Whitney U (non-parametric).

    Args:
        pre: Pre-intervention observations.
        post: Post-intervention observations.

    Returns:
        Dict with keys ``test``, ``stat``, ``p_value``, ``significant``.
    """
    norm_pre = normality_test(pre)
    norm_post = normality_test(post)
    both_normal = norm_pre["is_normal"] and norm_post["is_normal"]

    if both_normal:
        stat, p = stats.ttest_ind(pre.dropna(), post.dropna(), equal_var=False)
        test_name = "t-test (Welch)"
    else:
        stat, p = stats.mannwhitneyu(pre.dropna(), post.dropna(), alternative="two-sided")
        test_name = "Mann-Whitney U"

    return {
        "test": test_name,
        "stat": float(stat),
        "p_value": float(p),
        "significant": float(p) < _ALPHA,
    }


def cohens_d(pre: pd.Series, post: pd.Series) -> dict:
    """Compute Cohen's d effect size with interpretation.

    Uses pooled standard deviation (Hedges-style pooling).

    Args:
        pre: Pre-intervention observations.
        post: Post-intervention observations.

    Returns:
        Dict with keys ``d``, ``interpretation`` (negligible/small/medium/large).
    """
    n1, n2 = len(pre.dropna()), len(post.dropna())
    pooled_std = np.sqrt(
        ((n1 - 1) * pre.std(ddof=1) ** 2 + (n2 - 1) * post.std(ddof=1) ** 2) / (n1 + n2 - 2)
    )
    d = (post.mean() - pre.mean()) / pooled_std if pooled_std > 0 else 0.0
    abs_d = abs(d)
    if abs_d < 0.2:
        interp = "negligible"
    elif abs_d < 0.5:
        interp = "small"
    elif abs_d < 0.8:
        interp = "medium"
    else:
        interp = "large"
    return {"d": float(d), "interpretation": interp}


def full_statistical_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Run the full statistical protocol for each key variable.

    Protocol per variable:
    1. Shapiro-Wilk on pre and post groups.
    2. t-test or Mann-Whitney U based on normality.
    3. Cohen's d with interpretation.

    Args:
        df: Monthly enriched DataFrame with ``period`` column.

    Returns:
        DataFrame with one row per variable and columns:
        ``variable``, ``normality_pre_p``, ``normality_post_p``,
        ``test_used``, ``stat``, ``p_value``, ``significant``,
        ``cohens_d``, ``effect_size``, ``pre_mean``, ``post_mean``, ``pct_change``.
    """
    pre = df[df["period"] == "pre"]
    post = df[df["period"] == "post"]
    rows = []
    for col in _TEST_COLS:
        if col not in df.columns:
            continue
        np_res = normality_test(pre[col])
        npost_res = normality_test(post[col])
        ht = hypothesis_test(pre[col], post[col])
        cd = cohens_d(pre[col], post[col])
        pm, pom = pre[col].mean(), post[col].mean()
        rows.append(
            {
                "variable": col,
                "normality_pre_p": round(np_res["p_value"], 4),
                "normality_post_p": round(npost_res["p_value"], 4),
                "test_used": ht["test"],
                "stat": round(ht["stat"], 4),
                "p_value": round(ht["p_value"], 4),
                "significant": ht["significant"],
                "cohens_d": round(cd["d"], 3),
                "effect_size": cd["interpretation"],
                "pre_mean": round(pm, 3),
                "post_mean": round(pom, 3),
                "pct_change": round((pom - pm) / pm * 100, 2),
            }
        )
    return pd.DataFrame(rows)


def its_analysis(df: pd.DataFrame, outcome_col: str) -> dict:
    """Interrupted Time Series (segmented regression) analysis via OLS.

    Model specification::

        y = β0 + β1·t + β2·D + β3·t_post + ε

    Where:
    - ``t`` = time index (1 … 29).
    - ``D`` = intervention indicator (0 = pre, 1 = post).
    - ``t_post`` = months since intervention (0 pre, 1 … 9 post).
    - ``β1`` = pre-intervention slope (monthly trend before cutoff).
    - ``β2`` = immediate level change at intervention.
    - ``β3`` = change in slope post-intervention.

    Args:
        df: Monthly enriched DataFrame sorted by ``fecha``.
        outcome_col: Column to use as the dependent variable.

    Returns:
        Dict with ``coefficients``, ``p_values``, ``r_squared``,
        ``n_pre``, ``n_post``, and ``fitted`` (series of fitted values).
    """
    cutoff = pd.Timestamp(INTERVENTION_CUTOFF)
    its = df.sort_values("fecha").copy()
    its["t"] = range(1, len(its) + 1)
    its["D"] = (its["fecha"] > cutoff).astype(int)
    its["t_post"] = (its["t"] - 20).clip(lower=0) * its["D"]

    formula = f"{outcome_col} ~ t + D + t_post"
    model = smf.ols(formula, data=its).fit()

    return {
        "outcome": outcome_col,
        "n_pre": int((its["D"] == 0).sum()),
        "n_post": int((its["D"] == 1).sum()),
        "coefficients": model.params.to_dict(),
        "p_values": model.pvalues.to_dict(),
        "r_squared": float(model.rsquared),
        "adj_r_squared": float(model.rsquared_adj),
        "fitted": model.fittedvalues,
        "its_df": its,
        "model": model,
    }
