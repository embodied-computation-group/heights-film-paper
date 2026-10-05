"""Tests for analysis/hypotheses.py (the registered tests H1-H6), on small made-up data with known answers.

Run:  uv run pytest
"""
import numpy as np
import pandas as pd
import pytest
from scipy import stats

from analysis import hypotheses, stats_tools

ITEMS = ["01", "02", "06", "07", "08", "12", "14", "15", "18", "20", "21"]


def made_up_participants(n=3):
    """Participants whose STICSA items are all 1 before and all 2 after the film (totals 11 and 22)."""
    table = pd.DataFrame({"participant": [f"P{i:03d}" for i in range(n)],
                          "height_fear": np.arange(n) + 1, "anxiety_overall": np.arange(n) + 2,
                          "sticsa_pre": 11.0, "sticsa_post": 22.0})
    for item in ITEMS:
        table[f"sticsa_pre_item{item}"] = 1
        table[f"sticsa_post_item{item}"] = 2
    return table


# ------------------------------------------------------------------- participant measures

def test_participant_measures_compute_change_segment_and_whole_film_means():
    people = made_up_participants(2)
    film_time = np.arange(808.0)
    arousal = np.vstack([film_time, film_time + 1])
    valence = np.vstack([np.full(808, 40.0), np.full(808, 60.0)])

    measures = hypotheses.participant_measures(people, valence, arousal)

    assert list(measures["sticsa_change"]) == [11.0, 11.0]
    assert list(measures["arousal_plateau"]) == [580.5, 581.5]
    assert list(measures["arousal_baseline"]) == [130.5, 131.5]
    assert list(measures["valence_whole_film"]) == [40.0, 60.0]
    assert list(measures["arousal_whole_film"]) == [403.5, 404.5]


def test_participant_measures_stop_if_the_exported_sticsa_total_disagrees_with_the_items():
    people = made_up_participants(2)
    people.loc[1, "sticsa_post"] = 23.0  # items add up to 22

    with pytest.raises(ValueError, match="STICSA"):
        hypotheses.participant_measures(people, np.zeros((2, 808)), np.zeros((2, 808)))


def test_sticsa_total_is_missing_when_an_item_is_missing():
    people = made_up_participants(2)
    people["sticsa_pre_item06"] = people["sticsa_pre_item06"].astype(float)
    people.loc[0, "sticsa_pre_item06"] = np.nan
    people.loc[0, "sticsa_pre"] = np.nan

    measures = hypotheses.participant_measures(people, np.zeros((2, 808)), np.zeros((2, 808)))

    assert np.isnan(measures.loc[0, "sticsa_change"])
    assert measures.loc[1, "sticsa_change"] == 11.0


# ------------------------------------------------------------------- H1

def test_h1_supported_when_sticsa_rises_after_the_film():
    rng = np.random.default_rng(0)
    pre = rng.normal(15, 3, 50)
    measures = pd.DataFrame({"sticsa_pre": pre, "sticsa_post": pre + rng.normal(3, 2, 50)})

    row = hypotheses.test_h1(measures)

    assert row["hypothesis"] == "H1"
    assert row["supported"]
    assert row["p"] == pytest.approx(stats.ttest_rel(measures["sticsa_post"], measures["sticsa_pre"]).pvalue)
    assert row["estimate"] == pytest.approx(stats_tools.paired_test(pre, measures["sticsa_post"])["dz"])


def test_h1_not_supported_when_sticsa_falls_even_if_significant():
    rng = np.random.default_rng(0)
    pre = rng.normal(15, 3, 50)
    measures = pd.DataFrame({"sticsa_pre": pre, "sticsa_post": pre - rng.normal(3, 2, 50)})

    row = hypotheses.test_h1(measures)

    assert row["p"] < 0.001
    assert not row["supported"]


def test_h1_leaves_out_people_without_a_valid_total():
    measures = pd.DataFrame({"sticsa_pre": [11, 12, np.nan, 14, 15, 13],
                             "sticsa_post": [14, 13, 20, 18, 17, np.nan]})

    assert hypotheses.test_h1(measures)["n"] == 4


# ------------------------------------------------------------------- H2

def made_up_segment_means(n=30, return_level=60.0, seed=1):
    rng = np.random.default_rng(seed)
    noise = lambda: rng.normal(0, 5, n)  # noqa: E731
    return pd.DataFrame({
        "arousal_baseline": 30 + noise(), "arousal_rise": 50 + noise(), "arousal_plateau": 70 + noise(),
        "arousal_return": return_level + noise(),
        "valence_baseline": 55 + noise(), "valence_plateau": 35 + noise(),
    })


def test_h2_contrasts_and_holm_correction():
    measures = made_up_segment_means()

    rows = hypotheses.test_h2(measures)

    assert [row["hypothesis"] for row in rows] == ["H2a", "H2b", "H2c", "H2d"]
    assert all(row["supported"] for row in rows)
    assert [row["p_holm"] for row in rows] == pytest.approx(stats_tools.holm([row["p"] for row in rows]),
                                                             rel=1e-9, abs=0)
    # H2c compares return with plateau (return < plateau), so its mean difference is return - plateau.
    h2c = rows[2]
    expected = (measures["arousal_return"] - measures["arousal_plateau"]).mean()
    assert h2c["mean_difference"] == pytest.approx(expected)


def test_h2c_not_supported_when_arousal_goes_up_after_the_plateau():
    rows = hypotheses.test_h2(made_up_segment_means(return_level=80.0))

    h2c = rows[2]
    assert h2c["p"] < 0.05
    assert not h2c["supported"]


# ------------------------------------------------------------------- H3

def test_h3_supported_for_near_identical_curves_and_not_for_weakly_related_curves():
    rng = np.random.default_rng(0)
    curve = 50 + 20 * np.sin(np.linspace(0, 6, 808))
    confirmatory = {"arousal": curve, "valence": curve}
    reference = {"arousal": curve + rng.normal(0, 1, 808),          # nearly the same
                 "valence": 0.2 * curve + rng.normal(0, 20, 808)}  # only weakly related

    rows = hypotheses.test_h3(confirmatory, reference, n_boot=500, seed=0)

    by_name = {row["hypothesis"]: row for row in rows}
    assert by_name["H3 arousal"]["supported"]
    assert by_name["H3 arousal"]["ci_low"] > 0.5
    assert not by_name["H3 valence"]["supported"]


# ------------------------------------------------------------------- H4-H6

def test_correlation_hypotheses_follow_the_preregistration():
    # (hypothesis, x, y, predicted sign), copied from docs/preregistration.md.
    expected = [
        ("H4a", "height_fear", "arousal_plateau", +1),
        ("H4b", "height_fear", "valence_plateau", -1),
        ("H4c", "height_fear", "sticsa_change", +1),
        ("H5a", "sticsa_change", "arousal_whole_film", +1),
        ("H5b", "sticsa_change", "valence_whole_film", -1),
        ("H6a", "anxiety_overall", "sticsa_change", +1),
        ("H6b", "anxiety_overall", "arousal_plateau", +1),
    ]

    assert [(h["hypothesis"], h["x"], h["y"], h["sign"]) for h in hypotheses.CORRELATIONS] == expected


def made_up_individual_differences(n=80, seed=2):
    rng = np.random.default_rng(seed)
    fear = rng.integers(1, 8, n).astype(float)
    change = fear + rng.normal(0, 3, n)
    return pd.DataFrame({
        "height_fear": fear, "sticsa_change": change, "anxiety_overall": fear + rng.normal(0, 2, n),
        "arousal_plateau": 10 * fear + rng.normal(0, 25, n),
        "valence_plateau": -10 * fear + rng.normal(0, 25, n),
        "arousal_whole_film": 5 * change + rng.normal(0, 20, n),
        "valence_whole_film": -5 * change + rng.normal(0, 20, n),
    })


def test_correlations_with_holm_within_each_family():
    measures = made_up_individual_differences()

    rows = hypotheses.test_correlations(measures, n_boot=200, seed=0)

    assert [row["hypothesis"] for row in rows] == ["H4a", "H4b", "H4c", "H5a", "H5b", "H6a", "H6b"]
    assert all(row["supported"] for row in rows)
    for family in ("H4", "H5", "H6"):
        family_rows = [row for row in rows if row["family"] == family]
        # abs=0: the default absolute tolerance (1e-12) would accept any two very small p-values as equal.
        assert [row["p_holm"] for row in family_rows] == pytest.approx(
            stats_tools.holm([row["p"] for row in family_rows]), rel=1e-9, abs=0)
    h4c = rows[2]
    assert h4c["estimate"] == pytest.approx(stats.spearmanr(measures["height_fear"],
                                                            measures["sticsa_change"]).statistic)


def test_a_correlation_in_the_wrong_direction_is_not_supported():
    measures = made_up_individual_differences()
    measures["valence_plateau"] = -measures["valence_plateau"]  # now positive, but H4b predicts negative

    rows = hypotheses.test_correlations(measures, n_boot=200, seed=0)

    h4b = rows[1]
    assert h4b["estimate"] > 0 and h4b["p_holm"] < 0.05
    assert not h4b["supported"]
