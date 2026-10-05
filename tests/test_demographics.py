"""Tests for analysis/demographics.py (EXPLORATORY age and sex analyses), on made-up data with known answers.

Run:  uv run pytest
"""
import numpy as np
import pandas as pd
import pytest
from scipy import stats

from analysis import demographics

SEGMENTS = ["baseline", "rise", "plateau", "return"]


def made_up_segment_means(n=120, plateau_sex_difference=10.0, seed=0):
    """Segment means where women rate the plateau `plateau_sex_difference` points higher; age has no effect."""
    rng = np.random.default_rng(seed)
    people = pd.DataFrame({"participant": [f"P{i:03d}" for i in range(n)],
                           "sex": np.where(np.arange(n) % 2 == 0, "Female", "Male"),
                           "age": rng.uniform(18, 70, n)})
    person_level = rng.normal(0, 8, n)  # stable differences between people
    rows = []
    for segment, level in zip(SEGMENTS, [40, 65, 80, 55]):
        extra = np.where((people["sex"] == "Female") & (segment == "plateau"), plateau_sex_difference, 0.0)
        values = level + person_level + extra + rng.normal(0, 6, n)
        rows.append(pd.DataFrame({"participant": people["participant"], "segment": segment, "value": values,
                                  "sex": people["sex"], "age": people["age"]}))
    return pd.concat(rows, ignore_index=True)


def test_mixed_model_finds_a_sex_by_segment_interaction_and_no_age_interaction():
    result = demographics.segment_moderation(made_up_segment_means())

    assert result["sex_x_segment"]["p"] < 0.001
    assert result["sex_x_segment"]["df"] == 3
    assert result["age_x_segment"]["p"] > 0.05
    assert result["n_participants"] == 120


def test_no_interaction_when_there_is_none():
    result = demographics.segment_moderation(made_up_segment_means(plateau_sex_difference=0.0, seed=3))

    assert result["sex_x_segment"]["p"] > 0.05


def test_sex_difference_per_segment_recovers_the_built_in_difference():
    long = made_up_segment_means(plateau_sex_difference=10.0, seed=1)

    table = demographics.sex_difference_by_segment(long).set_index("segment")

    assert table.loc["plateau", "difference"] == pytest.approx(10.0, abs=3.0)  # female - male
    assert table.loc["plateau", "ci_low"] < table.loc["plateau", "difference"] < table.loc["plateau", "ci_high"]
    assert abs(table.loc["baseline", "difference"]) < 5
    plateau = long[long["segment"] == "plateau"]
    expected = stats.ttest_ind(plateau.loc[plateau["sex"] == "Female", "value"],
                               plateau.loc[plateau["sex"] == "Male", "value"], equal_var=False)
    assert table.loc["plateau", "p"] == pytest.approx(expected.pvalue)


def test_people_without_age_or_sex_are_left_out():
    long = made_up_segment_means(n=40)
    long.loc[long["participant"] == "P000", "sex"] = np.nan
    long.loc[long["participant"] == "P001", "age"] = np.nan

    result = demographics.segment_moderation(long)

    assert result["n_participants"] == 38


def test_sticsa_change_regression_recovers_known_effects():
    rng = np.random.default_rng(2)
    n = 200
    people = pd.DataFrame({"sex": np.where(np.arange(n) % 2 == 0, "Female", "Male"), "age": rng.uniform(18, 70, n)})
    # Women +3 points; each 10 years of age -1 point.
    people["sticsa_change"] = (5 + 3 * (people["sex"] == "Female") - 0.1 * (people["age"] - 40)
                               + rng.normal(0, 2, n))

    result = demographics.sticsa_change_model(people)

    assert result["female_minus_male"]["estimate"] == pytest.approx(3.0, abs=0.8)
    assert result["per_10_years"]["estimate"] == pytest.approx(-1.0, abs=0.3)
    assert result["n"] == n


def test_mixed_model_agrees_with_the_clustered_fit_on_clear_data():
    result = demographics.segment_moderation(made_up_segment_means())

    mixed = result["mixed_model"]
    assert mixed["converged"]
    assert mixed["sex_x_segment"]["p"] < 0.001
    assert mixed["age_x_segment"]["p"] > 0.05
    assert mixed["random_intercept_variance"] > 0
