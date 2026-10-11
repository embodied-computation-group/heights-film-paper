"""Tests for analysis/plot_style.py helpers.

Run:  uv run pytest
"""
from analysis import plot_style


def test_film_time_label_gives_minutes_and_zero_padded_seconds():
    assert plot_style.film_time_label(636) == "10:36"
    assert plot_style.film_time_label(65) == "1:05"
    assert plot_style.film_time_label(0) == "0:00"
    assert plot_style.film_time_label(808.9) == "13:28"  # partial seconds are dropped, as on a video player
