"""Tests for analysis/affect_grid.py (where on the valence x arousal grid people spent their time).

Run:  uv run pytest
"""
import numpy as np
import pytest

from analysis import affect_grid


def test_occupancy_adds_up_to_100_percent():
    rng = np.random.default_rng(0)
    valence, arousal = rng.uniform(0, 100, (5, 200)), rng.uniform(0, 100, (5, 200))

    grid = affect_grid.occupancy(valence, arousal)

    assert grid.shape == (affect_grid.BINS, affect_grid.BINS)
    assert grid.sum() == pytest.approx(100.0)


def test_someone_who_never_moves_puts_all_their_time_in_one_place():
    # Valence 10 (unpleasant), arousal 90 (high): the busiest cell is at the upper left.
    grid = affect_grid.occupancy(np.full((1, 100), 10.0), np.full((1, 100), 90.0))

    valence_bin, arousal_bin = np.unravel_index(np.argmax(grid), grid.shape)
    assert valence_bin == 5 and arousal_bin == 45  # 2-unit bins: 10 -> bin 5, 90 -> bin 45


def test_every_participant_counts_equally_however_long_their_series():
    # Two people: one sits at the lower left, one at the upper right. Even if one of them has far more samples
    # (a longer segment of valid data), each gets half of the map.
    lower_left = (np.full(10, 10.0), np.full(10, 10.0))
    upper_right = (np.full(1000, 90.0), np.full(1000, 90.0))

    grid = affect_grid.occupancy([lower_left[0], upper_right[0]], [lower_left[1], upper_right[1]], smooth=False)

    assert grid[:25, :25].sum() == pytest.approx(50.0)
    assert grid[25:, 25:].sum() == pytest.approx(50.0)
