"""Tests for analysis/segmentation.py (piecewise-linear segmentation of the group-mean rating).

Run:  uv run pytest
"""
import numpy as np
import pytest

from analysis import segmentation, study_data


def made_up_film(edges=(262, 470, 692), n=808, noise=0.0, seed=0):
    """A flat baseline, a linear rise, a flat plateau and a linear return, with breakpoints at `edges`.

    Each segment starts with a small step, so the true breakpoints are the only best answer. (Where two lines meet
    exactly, the meeting point fits both lines and the edge could be found one second either way.)
    """
    t = np.arange(n, dtype=float)
    first, second, third = edges
    series = np.where(t < first, 30.0, 0.0)
    series += np.where((t >= first) & (t < second), 35 + 30 * (t - first) / (second - first), 0.0)
    series += np.where((t >= second) & (t < third), 72.0, 0.0)
    series += np.where(t >= third, 66 - 30 * (t - third) / (n - third), 0.0)
    return series + np.random.default_rng(seed).normal(0, noise, n)


def test_segmentation_finds_known_breakpoints_without_noise():
    edges = segmentation.find_breakpoints(made_up_film(), n_breakpoints=3)

    assert edges == [262, 470, 692]


def test_segmentation_finds_known_breakpoints_with_some_noise():
    edges = segmentation.find_breakpoints(made_up_film(noise=2.0, seed=4), n_breakpoints=3)

    assert np.allclose(edges, [262, 470, 692], atol=5)


def test_segmentation_finds_a_single_step():
    series = np.concatenate([np.zeros(100), np.full(100, 10.0)])

    assert segmentation.find_breakpoints(series, n_breakpoints=1) == [100]


def test_no_segment_is_shorter_than_the_registered_minimum_of_30_seconds():
    # A blip of 25 s would be its own segment if the minimum length were shorter than 30 s.
    series = np.zeros(300)
    series[150:175] = 50.0

    edges = segmentation.find_breakpoints(series, n_breakpoints=2)

    boundaries = [0, *edges, 300]
    assert min(np.diff(boundaries)) >= 30


def test_line_cost_is_zero_for_a_straight_line_and_matches_a_direct_fit():
    rng = np.random.default_rng(2)
    wobbly = rng.normal(size=60)
    costs = segmentation.line_costs(wobbly, min_length=5)

    x = np.arange(10, 40)
    residuals = wobbly[10:40] - np.polyval(np.polyfit(x, wobbly[10:40], 1), x)
    assert costs[10, 40] == pytest.approx(np.sum(residuals ** 2))

    straight = segmentation.line_costs(3 + 0.5 * np.arange(60.0), min_length=5)
    assert straight[0, 60] == pytest.approx(0.0, abs=1e-6)


def test_bootstrap_interval_covers_the_true_edges():
    rng = np.random.default_rng(7)
    ratings = np.array([made_up_film(noise=0) + rng.normal(0, 15, 808) for _ in range(20)])

    result = segmentation.bootstrap_breakpoints(ratings, n_breakpoints=3, n_boot=40, seed=1)

    for true_edge, low, high in zip([262, 470, 692], result["ci_low"], result["ci_high"]):
        assert low <= true_edge <= high


def test_bootstrap_is_reproducible_with_the_same_seed():
    rng = np.random.default_rng(3)
    ratings = np.array([made_up_film() + rng.normal(0, 10, 808) for _ in range(8)])

    first = segmentation.bootstrap_breakpoints(ratings, n_breakpoints=3, n_boot=10, seed=5)
    second = segmentation.bootstrap_breakpoints(ratings, n_breakpoints=3, n_boot=10, seed=5)

    assert first == second


def test_the_port_reproduces_the_registered_edges_on_the_exploratory_data():
    # The registered edges (262, 470, 692 s) were estimated on the 22 exploratory participants who passed the QC
    # rules in use at the time: everyone except the one with erratic input. Exploratory data only.
    participants, valence, arousal = study_data.load()
    used = (participants["sample"] == "exploratory") & (participants["registered_exclusion"] != "erratic input")
    assert used.sum() == 22

    edges = segmentation.find_breakpoints(arousal[used.to_numpy()].mean(axis=0), n_breakpoints=3)

    assert edges == [262, 470, 692]
