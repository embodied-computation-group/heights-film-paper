"""Tests for analysis/sticsa_items.py (EXPLORATORY: change in each STICSA somatic item), on made-up data.

Run:  uv run pytest
"""
import numpy as np
import pandas as pd
import pytest

from analysis import sticsa_items

ITEMS = ["01", "02", "06", "07", "08", "12", "14", "15", "18", "20", "21"]


def made_up_answers(n=60, seed=0):
    """Item 20 rises by about 2 points, item 15 by about 1, all others stay the same (late in the item order, so
    the ranking test fails if items are not sorted)."""
    rng = np.random.default_rng(seed)
    table = {}
    for item in ITEMS:
        before = rng.integers(1, 3, n)
        rise = {"20": 2, "15": 1}.get(item, 0)
        after = np.clip(before + rise + rng.integers(-1, 2, n) * (rise > 0), 1, 4)
        table[f"sticsa_pre_item{item}"] = before
        table[f"sticsa_post_item{item}"] = after if rise else before
    return pd.DataFrame(table)


def test_items_are_ranked_from_largest_to_smallest_change():
    result = sticsa_items.item_changes(made_up_answers())

    assert list(result["item"][:2]) == ["20", "15"]
    assert list(result["rank"]) == list(range(1, 12))


def test_unchanged_items_have_zero_change_and_no_test_result():
    result = sticsa_items.item_changes(made_up_answers()).set_index("item")

    assert result.loc["06", "mean_change"] == 0
    assert result.loc["06", "share_increased"] == 0
    assert np.isnan(result.loc["06", "p_holm"])  # no differences at all: nothing to test


def test_holm_correction_is_across_the_items_that_could_be_tested():
    result = sticsa_items.item_changes(made_up_answers())
    tested = result.dropna(subset=["p"])

    from analysis import stats_tools
    assert list(tested["p_holm"]) == pytest.approx(stats_tools.holm(list(tested["p"])), rel=1e-9, abs=0)


def test_share_increased_counts_people_whose_answer_went_up():
    answers = pd.DataFrame({f"sticsa_pre_item{i}": [1, 1, 2, 3] for i in ITEMS}
                           | {f"sticsa_post_item{i}": [2, 1, 1, 4] for i in ITEMS})

    result = sticsa_items.item_changes(answers)

    assert (result["share_increased"] == 0.5).all()
