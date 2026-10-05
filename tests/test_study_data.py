"""Tests for analysis/study_data.py, on small made-up data where we know the right answer.

Run:  uv run pytest
"""
import numpy as np
import pandas as pd
import pytest

from analysis import study_data


def test_segment_means_use_the_registered_segment_edges():
    # A series that equals 1 in the baseline, 2 in the rise, 3 on the plateau and 4 in the return.
    series = np.concatenate([np.full(262, 1.0), np.full(208, 2.0), np.full(222, 3.0), np.full(116, 4.0)])

    means = study_data.segment_means(series)

    assert means == {"baseline": 1.0, "rise": 2.0, "plateau": 3.0, "return": 4.0}


def test_segment_means_detect_a_shifted_edge():
    # With a rating equal to the film time, each segment mean is the middle of that segment,
    # so moving any edge by even one second changes the result.
    series = np.arange(808.0)

    means = study_data.segment_means(series)

    assert means == {"baseline": 130.5, "rise": 365.5, "plateau": 580.5, "return": 749.5}


def test_whole_film_mean_covers_0_to_808_seconds():
    series = np.arange(808.0)

    assert study_data.whole_film_mean(series) == pytest.approx(series.mean())


def test_segment_means_refuse_a_series_of_the_wrong_length():
    with pytest.raises(ValueError):
        study_data.segment_means(np.zeros(700))


def test_samples_for_the_sensitivity_analyses():
    people = pd.DataFrame({
        "participant": ["ok", "excluded", "sparse", "one_check", "inattentive", "rejected"],
        "registered_exclusion": [np.nan, "film coverage < 95%", np.nan, np.nan, np.nan, np.nan],
        "bouts_per_min": [5, 5, 0.5, 5, 5, 5],
        "longest_gap_s": [20, 20, 20, 20, 20, 20],
        "attention_failed": [0, 0, 0, 1, 0, 0],
        "full_attention": ["Yes", "Yes", "Yes", "Yes", "No", "Yes"],
        # The registered set, not the current Prolific status (one rejection was reversed for payment only).
        "rejected_on_prolific": [False] * 6,
        "in_rejection_set": [False] * 5 + [True],
    })

    samples = study_data.analysis_samples(people)

    assert list(samples["primary"]["participant"]) == ["ok", "sparse", "one_check", "inattentive", "rejected"]
    assert list(samples["stricter_engagement"]["participant"]) == ["ok", "rejected"]
    assert list(samples["without_rejected"]["participant"]) == ["ok", "sparse", "one_check", "inattentive"]


def test_a_long_gap_alone_makes_someone_a_sparse_rater():
    people = pd.DataFrame({
        "participant": ["gap"], "registered_exclusion": [np.nan], "bouts_per_min": [5.0],
        "longest_gap_s": [181.0], "attention_failed": [0], "full_attention": ["Yes"],
        "rejected_on_prolific": [False], "in_rejection_set": [False],
    })

    assert study_data.analysis_samples(people)["stricter_engagement"].empty


def test_load_checks_that_ratings_and_participants_line_up(tmp_path):
    pd.DataFrame({"participant": ["P001", "P002"], "sample": ["confirmatory"] * 2}).to_csv(
        tmp_path / "participants.csv", index=False)
    ratings = pd.DataFrame({"participant": ["P002", "P001"], "s000": [1.0, 2.0]})  # wrong order
    ratings.to_csv(tmp_path / "ratings_valence_1hz.csv", index=False)
    ratings.to_csv(tmp_path / "ratings_arousal_1hz.csv", index=False)

    with pytest.raises(ValueError):
        study_data.load(tmp_path)


def test_h3_reference_is_the_usable_exploratory_sample_for_a_confirmatory_run():
    people = pd.DataFrame({
        "participant": ["e1", "e2", "e_excluded", "c1"],
        "sample": ["exploratory", "exploratory", "exploratory", "confirmatory"],
        "cohort": ["pilot", "cohort 1", "cohort 1", "cohort 2"],
        "registered_exclusion": [np.nan, np.nan, "erratic input", np.nan],
    })

    tested, reference = study_data.h3_groups(people, people[people["sample"] == "confirmatory"], "confirmatory")

    assert list(tested["participant"]) == ["c1"]
    assert list(reference["participant"]) == ["e1", "e2"]


def test_h3_stand_in_on_the_exploratory_sample_compares_cohort_1_with_the_pilot():
    people = pd.DataFrame({
        "participant": ["p1", "k1", "k2"],
        "sample": ["exploratory"] * 3,
        "cohort": ["pilot", "cohort 1", "cohort 1"],
        "registered_exclusion": [np.nan] * 3,
    })

    tested, reference = study_data.h3_groups(people, people, "exploratory")

    assert list(tested["participant"]) == ["k1", "k2"]
    assert list(reference["participant"]) == ["p1"]


def test_mostly_attentive_is_not_counted_as_not_watching_attentively():
    # Registered rule: "self-report not watching attentively" = answered "No" (decision 2026-10-04).
    people = pd.DataFrame({
        "participant": ["yes", "mostly", "no"], "registered_exclusion": [np.nan] * 3, "bouts_per_min": [5.0] * 3,
        "longest_gap_s": [20.0] * 3, "attention_failed": [0] * 3, "full_attention": ["Yes", "Mostly", "No"],
        "rejected_on_prolific": [False] * 3, "in_rejection_set": [False] * 3,
    })

    assert list(study_data.analysis_samples(people)["stricter_engagement"]["participant"]) == ["yes", "mostly"]
