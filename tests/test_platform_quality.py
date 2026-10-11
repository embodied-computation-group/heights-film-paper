"""Tests for analysis/platform_quality.py (descriptive summaries of how the rating platform performed).

Run:  uv run pytest
"""
import pandas as pd
import pytest

from analysis import platform_quality as pq


def made_up_sessions():
    """Five completed sessions with known answers; two are excluded by registered rules."""
    return pd.DataFrame({
        "registered_exclusion": [None, None, None, "disrupted viewing", "erratic input"],
        "film_coverage": [1.0, 0.99, 1.0, 0.96, 1.0],
        "buffering_s": [0.0, 0.0, 4.0, 40.0, 0.0],
        "interrupted_s": [0.0, 10.0, 0.0, 0.0, 0.0],
        "bouts_per_min": [2.0, 4.0, 0.5, 3.0, 6.0],
        "longest_gap_s": [30.0, 200.0, 50.0, 20.0, 10.0],  # session 2: long gap only; session 3: few bouts only
        "attention_failed": [0, 1, 0, 0, 2],
        "input_device": ["Mouse", "Trackpad / touchpad", "Mouse", "Mouse", "Other"],
        "full_attention": ["Yes", "Mostly", "Yes", "No", "Yes"],
    })


def test_retention_counts_usable_among_completed_sessions():
    result = pq.retention(made_up_sessions())
    assert result["completed"] == 5
    assert result["usable"] == 3
    assert result["percent_usable"] == pytest.approx(60.0)
    assert result["excluded_by_rule"] == {"disrupted viewing": 1, "erratic input": 1}


def test_delivery_summarises_coverage_buffering_and_interruptions():
    result = pq.delivery(made_up_sessions())
    assert result["coverage_median"] == pytest.approx(1.0)
    assert result["coverage_min"] == pytest.approx(0.96)
    assert result["n_any_buffering"] == 2
    assert result["n_any_interruption"] == 1
    assert result["buffering_max_s"] == pytest.approx(40.0)
    assert result["interrupted_max_s"] == pytest.approx(10.0)


def test_rating_behaviour_uses_median_and_quartiles_and_counts_sparse_raters():
    result = pq.rating_behaviour(made_up_sessions())
    assert result["bouts_median"] == pytest.approx(3.0)
    assert result["bouts_q1"] == pytest.approx(2.0)
    assert result["bouts_q3"] == pytest.approx(4.0)
    assert result["gap_median_s"] == pytest.approx(30.0)
    # sparse rater = fewer than 1 bout per minute OR a gap of more than 180 s (the registered sensitivity rule)
    assert result["n_sparse"] == 2


def test_counts_of_categorical_answers():
    sessions = made_up_sessions()
    assert pq.counts(sessions, "input_device") == {"Mouse": 3, "Trackpad / touchpad": 1, "Other": 1}
    assert pq.attention_checks(sessions) == {"failed_none": 3, "failed_one": 1, "failed_both": 1}
