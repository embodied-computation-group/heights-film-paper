"""Tests for analysis/report_format.py (APA-style number formatting for the results report).

Run:  uv run pytest
"""
import math

from analysis import report_format as fmt


def test_p_values_follow_apa_style():
    assert fmt.p(0.0004) == "< .001"
    assert fmt.p(0.0491) == "= .049"
    assert fmt.p(0.355) == "= .355"
    assert fmt.p(0.0005) == "< .001"
    assert fmt.p(0.0010) == "= .001"
    assert fmt.p(1.0) == "= 1.000"


def test_values_bounded_by_one_have_no_leading_zero():
    assert fmt.bounded(0.0837) == ".08"
    assert fmt.bounded(-0.3166) == "-.32"
    assert fmt.bounded(0.99317, digits=3) == ".993"


def test_unbounded_values_keep_the_leading_zero_and_use_a_real_minus_sign():
    assert fmt.number(1.0295) == "1.03"
    assert fmt.number(-0.8849) == "$-$0.88"
    assert fmt.number(6.7903, digits=1) == "6.8"


def test_minus_sign_in_bounded_values_is_typeset_as_a_minus():
    assert fmt.tex(fmt.bounded(-0.3166)) == "$-$.32"


def test_confidence_interval():
    assert fmt.ci(0.8102, 1.2461) == "[0.81, 1.25]"
    assert fmt.ci(-0.0908, 0.2595, between_minus_one_and_one=True) == "[$-$.09, .26]"


def test_missing_values_are_shown_as_a_dash():
    assert fmt.number(math.nan) == "--"
