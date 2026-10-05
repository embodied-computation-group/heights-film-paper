"""Loading the study data and the quantities defined in the preregistration (docs/preregistration.md).

The data in data/processed/ were exported by the rating-study tooling repository (vmp_film_rating,
qc/export_dataset.py). See data/processed/README.md for what every column means.
"""
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data" / "processed"

FILM_SECONDS = 808  # one value per second of film time, 0-807 s

# Fixed segment edges (seconds of film time), as registered.
SEGMENTS = {
    "baseline": (0, 262),
    "rise": (262, 470),
    "plateau": (470, 692),
    "return": (692, 808),
}


def load(folder=DATA):
    """Read the participant table and the two 1 Hz rating tables.

    Returns (participants, valence, arousal). `valence` and `arousal` are numpy arrays with one row per
    participant, in the same order as `participants`, and one column per second of film time.
    """
    folder = Path(folder)
    participants = pd.read_csv(folder / "participants.csv")
    valence_table = pd.read_csv(folder / "ratings_valence_1hz.csv")
    arousal_table = pd.read_csv(folder / "ratings_arousal_1hz.csv")

    for name, table in (("valence", valence_table), ("arousal", arousal_table)):
        if list(table["participant"]) != list(participants["participant"]):
            raise ValueError(f"The {name} table does not list the same participants in the same order.")

    valence = valence_table.drop(columns="participant").to_numpy(float)
    arousal = arousal_table.drop(columns="participant").to_numpy(float)
    return participants, valence, arousal


def segment_means(series):
    """Mean rating in each of the four registered segments."""
    series = np.asarray(series, float)
    if len(series) != FILM_SECONDS:
        raise ValueError(f"Expected {FILM_SECONDS} one-second values, got {len(series)}.")
    return {name: float(series[start:end].mean()) for name, (start, end) in SEGMENTS.items()}


def whole_film_mean(series):
    """Mean rating over the whole film (0-808 s)."""
    return float(np.mean(series))


def analysis_samples(participants):
    """The participant groups used in the analysis.

    primary              everyone who passes the registered hard exclusions
    stricter_engagement  sensitivity analysis 1: also drop sparse raters (< 1 rating bout per minute or a
                         stretch of more than 180 s without input), anyone who failed one attention check, and
                         anyone who said they did not watch attentively (answer "No"; "Mostly" is kept)
    without_rejected     sensitivity analysis 2: also drop the registered rejection set (the submissions rejected
                         on Prolific on 2026-10-04 for behaviour on the free-text page, including one rejection
                         later reversed for payment only; see docs/prereg_log.md)
    """
    included = participants["registered_exclusion"].isna() | (participants["registered_exclusion"] == "")
    primary = participants[included]

    sparse = (primary["bouts_per_min"] < 1) | (primary["longest_gap_s"] > 180)
    one_check_failed = primary["attention_failed"] >= 1
    not_attentive = primary["full_attention"] == "No"
    stricter = primary[~(sparse | one_check_failed | not_attentive)]

    without_rejected = primary[~primary["in_rejection_set"].astype(bool)]

    return {"primary": primary, "stricter_engagement": stricter, "without_rejected": without_rejected}


def is_usable(participants):
    """True for participants who pass the registered hard exclusions."""
    return participants["registered_exclusion"].isna() | (participants["registered_exclusion"] == "")


def h3_groups(participants, analysis_sample, sample):
    """The two groups whose group-mean curves H3 correlates.

    Confirmatory run: the analysis sample (cohorts 2-4) against the usable exploratory sample (pilot + cohort 1),
    as registered. Development runs on the exploratory sample have no independent second sample, so H3 is tried
    out on a STAND-IN: cohort 1 against the pilot, within the same analysis sample.
    """
    if sample == "confirmatory":
        exploratory = participants[participants["sample"] == "exploratory"]
        return analysis_sample, exploratory[is_usable(exploratory)]
    return (analysis_sample[analysis_sample["cohort"] != "pilot"],
            analysis_sample[analysis_sample["cohort"] == "pilot"])
