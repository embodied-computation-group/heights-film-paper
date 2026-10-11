"""Descriptive summaries of how the rating platform performed in a sample of completed sessions.

These are descriptive (not preregistered tests). The input is a table with one row per completed session and the
quality columns exported to data/processed/participants.csv (see data/processed/README.md).
"""
import pandas as pd


def is_usable(sessions):
    """True for sessions that pass the registered hard exclusions (empty registered_exclusion)."""
    rule = sessions["registered_exclusion"]
    return rule.isna() | (rule == "")


def retention(sessions):
    """How many completed sessions were usable, and how many each registered rule excluded."""
    usable = is_usable(sessions)
    excluded = sessions.loc[~usable, "registered_exclusion"].value_counts()
    return {
        "completed": len(sessions),
        "usable": int(usable.sum()),
        "percent_usable": 100 * usable.mean(),
        "excluded_by_rule": {rule: int(n) for rule, n in excluded.items()},
    }


def delivery(sessions):
    """Film coverage, buffering and interruptions (seconds) across sessions."""
    return {
        "coverage_median": float(sessions["film_coverage"].median()),
        "coverage_min": float(sessions["film_coverage"].min()),
        "n_any_buffering": int((sessions["buffering_s"] > 0).sum()),
        "buffering_max_s": float(sessions["buffering_s"].max()),
        "n_any_interruption": int((sessions["interrupted_s"] > 0).sum()),
        "interrupted_max_s": float(sessions["interrupted_s"].max()),
    }


def rating_behaviour(sessions):
    """Rating bouts per minute and the longest stretch without input; sparse raters as in the registered rule."""
    bouts = sessions["bouts_per_min"]
    sparse = (bouts < 1) | (sessions["longest_gap_s"] > 180)
    return {
        "bouts_median": float(bouts.median()),
        "bouts_q1": float(bouts.quantile(0.25)),
        "bouts_q3": float(bouts.quantile(0.75)),
        "gap_median_s": float(sessions["longest_gap_s"].median()),
        "n_sparse": int(sparse.sum()),
    }


def counts(sessions, column):
    """How often each answer occurs in a column, most common first."""
    return {answer: int(n) for answer, n in sessions[column].value_counts().items()}


def attention_checks(sessions):
    """Number of sessions that failed none, one or both of the two attention checks."""
    failed = pd.to_numeric(sessions["attention_failed"])
    return {"failed_none": int((failed == 0).sum()), "failed_one": int((failed == 1).sum()),
            "failed_both": int((failed >= 2).sum())}
