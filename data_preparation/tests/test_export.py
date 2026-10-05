"""Tests for qc/export_dataset.py (the de-identified tables handed to the analysis repository).

Run from the project folder:
    python -m pytest tests/test_export.py -v
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "qc"))
import export_dataset  # noqa: E402


def test_resample_to_1hz_follows_film_time_and_skips_paused_samples():
    # 20 Hz samples of a rating that rises by 1 point per second of film time.
    t = np.arange(0, 20, 0.05)
    samples = pd.DataFrame({"t_stim": t, "value_x": 50.0, "value_y": t, "playing": 1})
    # While the film is paused the dot is moved to 99 - these samples must be ignored.
    paused = pd.DataFrame({"t_stim": 10.0, "value_x": 99.0, "value_y": 99.0, "playing": [0] * 40})
    samples = pd.concat([samples, paused])

    valence, arousal = export_dataset.resample_to_1hz(samples, n_seconds=20)

    assert len(arousal) == 20
    assert np.allclose(arousal, np.arange(20))
    assert np.allclose(valence, 50)


def test_rating_bouts_and_longest_gap():
    # Inputs every 0.5 s for 10 s, a 30-s pause, then inputs again: 2 bouts, longest gap 30.5 s.
    times = np.concatenate([np.arange(0, 10, 0.5), np.arange(40, 50, 0.5)])

    bouts_per_minute, longest_gap = export_dataset.rating_bouts(times, film_length_s=60)

    assert bouts_per_minute == pytest.approx(2.0)
    assert longest_gap == pytest.approx(30.5)


def test_pseudonyms_are_stable_and_new_people_are_added_at_the_end():
    existing = {"prolificA": "P001", "prolificB": "P002"}

    mapping = export_dataset.assign_pseudonyms(["prolificB", "prolificC", "prolificA"], existing)

    assert mapping["prolificA"] == "P001"
    assert mapping["prolificB"] == "P002"
    assert mapping["prolificC"] == "P003"


def test_check_deidentified_catches_a_leaked_prolific_id():
    table = pd.DataFrame({"participant": ["P001"], "note": ["5f1a2b3c4d5e6f7a8b9c0d1e"]})

    with pytest.raises(ValueError):
        export_dataset.check_deidentified(table, known_ids=["5f1a2b3c4d5e6f7a8b9c0d1e"])


def test_check_deidentified_accepts_a_clean_table():
    table = pd.DataFrame({"participant": ["P001"], "age": [30]})

    export_dataset.check_deidentified(table, known_ids=["5f1a2b3c4d5e6f7a8b9c0d1e"])


def test_seven_point_answers_are_converted_from_0_6_to_1_7():
    # jsPsych stores the chosen option's position (0-6); the scale is reported as 1-7.
    stored = pd.Series([0, 3, 6, np.nan])

    reported = export_dataset.seven_point_scale(stored)

    assert list(reported[:3]) == [1, 4, 7]
    assert np.isnan(reported[3])


def test_registered_rejection_set_is_matched_by_id_prefix():
    ids = ["aaaa1111aaaaaaaaaaaaaaaa", "bbbb2222bbbbbbbbbbbbbbbb", "5f00000000000000000000aa"]

    flags = export_dataset.in_rejection_set(ids, prefixes=("aaaa1111", "bbbb2222"))

    assert list(flags) == [True, True, False]


def test_registered_rejection_set_stops_if_a_prefix_is_missing_or_ambiguous():
    with pytest.raises(ValueError):
        export_dataset.in_rejection_set(["aaaa1111aaaa"], prefixes=("aaaa1111", "bbbb2222"))  # missing
    with pytest.raises(ValueError):
        export_dataset.in_rejection_set(["aaaa1111aaaa", "aaaa1111bbbb"], prefixes=("aaaa1111",))  # ambiguous


def test_rejection_set_is_read_one_prefix_per_line(tmp_path):
    path = tmp_path / "rejection_set.txt"
    path.write_text("aaaa1111\n\nbbbb2222\n")

    assert export_dataset.read_rejection_set(path) == ("aaaa1111", "bbbb2222")
