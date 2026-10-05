"""Tests for analysis/stats_tools.py, on small made-up data where we know the right answer.

Run:  uv run pytest
"""
import numpy as np
import pytest
from scipy import stats

from analysis import stats_tools


# ---------------------------------------------------------------- statistics

def test_paired_test_matches_scipy_and_reports_dz():
    rng = np.random.default_rng(1)
    pre = rng.normal(20, 3, 40)
    post = pre + rng.normal(2, 2, 40)

    result = stats_tools.paired_test(pre, post)

    expected = stats.ttest_rel(post, pre)
    differences = post - pre
    assert result["t"] == pytest.approx(expected.statistic)
    assert result["p"] == pytest.approx(expected.pvalue)
    assert result["dz"] == pytest.approx(differences.mean() / differences.std(ddof=1))
    assert result["dz_ci_low"] < result["dz"] < result["dz_ci_high"]
    assert result["wilcoxon_p"] == pytest.approx(stats.wilcoxon(post, pre).pvalue)
    assert result["n"] == 40


def test_dz_confidence_interval_is_close_to_the_normal_approximation_in_large_samples():
    low, high = stats_tools.dz_confidence_interval(dz=0.5, n=10_000)

    assert low == pytest.approx(0.5 - 1.96 / 100, abs=0.002)
    assert high == pytest.approx(0.5 + 1.96 / 100, abs=0.002)


@pytest.mark.parametrize("dz, n", [(1.8, 21), (2.4, 21), (-2.4, 21), (1.0, 124), (0.3, 124)])
def test_dz_confidence_interval_for_large_effects_meets_its_definition(dz, n):
    # Effects as large as the exploratory segment contrasts (dz 1.6-2.4 with n = 21). The exact interval is
    # defined by the observed t sitting at the 97.5th / 2.5th percentile of the noncentral t at the two bounds.
    low, high = stats_tools.dz_confidence_interval(dz=dz, n=n)

    t_observed = dz * np.sqrt(n)
    assert stats.nct.cdf(t_observed, n - 1, low * np.sqrt(n)) == pytest.approx(0.975, abs=1e-6)
    assert stats.nct.cdf(t_observed, n - 1, high * np.sqrt(n)) == pytest.approx(0.025, abs=1e-6)
    assert low < dz < high


def test_holm_correction_on_a_textbook_example():
    adjusted = stats_tools.holm([0.01, 0.04, 0.03])

    assert adjusted == pytest.approx([0.03, 0.06, 0.06])


def test_spearman_with_ci_is_reproducible_and_finds_a_perfect_relation():
    x = np.arange(30.0)
    y = x ** 2  # perfectly monotonic

    first = stats_tools.spearman_with_ci(x, y, n_boot=500, seed=3)
    second = stats_tools.spearman_with_ci(x, y, n_boot=500, seed=3)

    assert first["rho"] == pytest.approx(1.0)
    assert first == second


def test_spearman_with_ci_drops_missing_values():
    x = np.array([1, 2, 3, 4, 5, np.nan, 7, 8])
    y = np.array([2, 1, 4, 3, 6, 5, np.nan, 9])

    result = stats_tools.spearman_with_ci(x, y, n_boot=200, seed=0)

    assert result["n"] == 6


def test_block_bootstrap_correlation_of_identical_series_is_one():
    series = np.sin(np.linspace(0, 20, 800))

    result = stats_tools.block_bootstrap_correlation(series, series, block_length=30, n_boot=200, seed=0)

    assert result["r"] == pytest.approx(1.0)
    assert result["ci_low"] == pytest.approx(1.0)


def test_block_bootstrap_ci_covers_zero_for_unrelated_series():
    rng = np.random.default_rng(5)
    a, b = rng.normal(size=800), rng.normal(size=800)

    result = stats_tools.block_bootstrap_correlation(a, b, block_length=30, n_boot=1000, seed=0)

    assert result["ci_low"] < 0 < result["ci_high"]


def test_split_half_reliability_of_identical_participants_is_one():
    one_person = np.sin(np.linspace(0, 10, 300))
    ratings = np.tile(one_person, (20, 1)) + np.random.default_rng(0).normal(0, 1e-6, (20, 300))

    reliability = stats_tools.split_half_reliability(ratings, n_splits=50, seed=0)

    assert reliability == pytest.approx(1.0, abs=1e-6)


def test_linear_fit_band_matches_scipy_and_contains_the_line():
    rng = np.random.default_rng(4)
    x = rng.integers(1, 8, 60).astype(float)
    y = 2 * x + rng.normal(0, 3, 60)
    grid = np.linspace(1, 7, 25)

    fit, low, high = stats_tools.linear_fit_band(x, y, grid)

    reference = stats.linregress(x, y)
    assert fit == pytest.approx(reference.intercept + reference.slope * grid)
    assert np.all(low < fit) and np.all(fit < high)
    # The band is narrowest near the mean of x.
    widths = high - low
    assert np.argmin(widths) == np.argmin(np.abs(grid - x.mean()))
