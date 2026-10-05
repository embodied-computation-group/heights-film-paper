"""Statistical helper functions used by the confirmatory analysis.

Each function does one thing and is tested in tests/test_analysis.py.
"""
import numpy as np
from scipy import stats


def paired_test(before, after):
    """Paired t-test of `after` vs `before`, with Cohen's dz, its 95% CI and a Wilcoxon signed-rank test."""
    before, after = np.asarray(before, float), np.asarray(after, float)
    differences = after - before
    n = len(differences)

    t_test = stats.ttest_rel(after, before)
    dz = differences.mean() / differences.std(ddof=1)
    dz_low, dz_high = dz_confidence_interval(dz, n)
    wilcoxon = stats.wilcoxon(after, before)

    return {
        "n": n,
        "mean_before": before.mean(),
        "mean_after": after.mean(),
        "mean_difference": differences.mean(),
        "t": t_test.statistic,
        "df": n - 1,
        "p": t_test.pvalue,
        "dz": dz,
        "dz_ci_low": dz_low,
        "dz_ci_high": dz_high,
        "wilcoxon_p": wilcoxon.pvalue,
    }


def dz_confidence_interval(dz, n, level=0.95):
    """Exact confidence interval for dz, from the noncentral t distribution.

    The t statistic of a paired test is t = dz * sqrt(n). We look for the noncentrality values that put the
    observed t at the upper and lower tail of the distribution, then convert back to the dz scale.
    """
    from scipy.optimize import brentq

    t_observed = dz * np.sqrt(n)
    df = n - 1
    tail = (1 - level) / 2

    def tail_probability(noncentrality, target):
        return stats.nct.cdf(t_observed, df, noncentrality) - target

    # Search within about 6 standard errors of t. A wider search reaches values where scipy's noncentral t
    # returns NaN (far in the tail, for large t), and the search then fails.
    half_width = 6 * np.sqrt(1 + t_observed ** 2 / (2 * df)) + 1
    search = (t_observed - half_width, t_observed + half_width)
    low = brentq(tail_probability, *search, args=(1 - tail,))
    high = brentq(tail_probability, *search, args=(tail,))
    return low / np.sqrt(n), high / np.sqrt(n)


def holm(p_values):
    """Holm-Bonferroni adjusted p-values, returned in the original order."""
    p = np.asarray(p_values, float)
    m = len(p)
    order = np.argsort(p)

    adjusted = np.empty(m)
    running_max = 0.0
    for rank, index in enumerate(order):
        running_max = max(running_max, (m - rank) * p[index])
        adjusted[index] = min(running_max, 1.0)
    return list(adjusted)


def spearman_with_ci(x, y, n_boot=5000, seed=0):
    """Spearman correlation with a percentile bootstrap 95% CI (participants resampled with replacement).

    Participants with a missing value on either variable are left out.
    """
    x, y = np.asarray(x, float), np.asarray(y, float)
    complete = ~np.isnan(x) & ~np.isnan(y)
    x, y = x[complete], y[complete]
    n = len(x)

    result = stats.spearmanr(x, y)

    rng = np.random.default_rng(seed)
    boot = []
    for _ in range(n_boot):
        pick = rng.integers(0, n, n)
        boot.append(stats.spearmanr(x[pick], y[pick]).statistic)
    ci_low, ci_high = np.nanpercentile(boot, [2.5, 97.5])

    return {"n": n, "rho": result.statistic, "p": result.pvalue, "ci_low": ci_low, "ci_high": ci_high}


def block_bootstrap_correlation(a, b, block_length=30, n_boot=5000, seed=0):
    """Pearson r between two time series, with a circular block bootstrap 95% CI.

    Time series are autocorrelated, so we resample whole blocks of `block_length` seconds (wrapping around the
    end of the film) instead of single seconds. The same blocks are taken from both series.
    """
    a, b = np.asarray(a, float), np.asarray(b, float)
    n = len(a)
    r = np.corrcoef(a, b)[0, 1]

    rng = np.random.default_rng(seed)
    n_blocks = int(np.ceil(n / block_length))
    boot = []
    for _ in range(n_boot):
        starts = rng.integers(0, n, n_blocks)
        index = np.concatenate([(start + np.arange(block_length)) % n for start in starts])[:n]
        boot.append(np.corrcoef(a[index], b[index])[0, 1])
    ci_low, ci_high = np.nanpercentile(boot, [2.5, 97.5])

    return {"r": r, "ci_low": ci_low, "ci_high": ci_high}


def split_half_reliability(ratings, n_splits=1000, seed=0):
    """Reliability of the group-mean time series.

    `ratings` has one row per participant and one column per second. We split the participants randomly into two
    halves, correlate the two half-group means, and correct for halving with the Spearman-Brown formula.
    Returns the mean over `n_splits` random splits.
    """
    ratings = np.asarray(ratings, float)
    n = len(ratings)
    rng = np.random.default_rng(seed)

    values = []
    for _ in range(n_splits):
        order = rng.permutation(n)
        half_1, half_2 = order[: n // 2], order[n // 2:]
        r = np.corrcoef(ratings[half_1].mean(0), ratings[half_2].mean(0))[0, 1]
        values.append(2 * r / (1 + r))
    return float(np.mean(values))


def linear_fit_band(x, y, grid, level=0.95):
    """Least-squares line through (x, y) and its 95% confidence band, evaluated at `grid`.

    Used only to draw a trend line in figures; the registered tests are Spearman correlations.
    """
    x, y, grid = np.asarray(x, float), np.asarray(y, float), np.asarray(grid, float)
    n = len(x)
    slope, intercept = np.polyfit(x, y, 1)
    fit = intercept + slope * grid

    residual_sd = np.sqrt(np.sum((y - (intercept + slope * x)) ** 2) / (n - 2))
    spread_x = np.sum((x - x.mean()) ** 2)
    standard_error = residual_sd * np.sqrt(1 / n + (grid - x.mean()) ** 2 / spread_x)
    half_width = stats.t.ppf(1 - (1 - level) / 2, n - 2) * standard_error
    return fit, fit - half_width, fit + half_width
