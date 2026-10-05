"""Export the de-identified dataset that the analysis repository (heights_film_paper) starts from.

Run after qc/review.py (which downloads the data and writes qc/out/qc_report.csv):

    python qc/export_dataset.py                      # writes data/export/
    python qc/export_dataset.py --out ../heights_film_paper/data

What is written (one row per participant who completed the valence x arousal arm, pilot and all cohorts):

    participants.csv      sample, cohort, questionnaires, STICSA, demographics, data-quality measures, and the
                          preregistered exclusion decision
    ratings_arousal_1hz.csv, ratings_valence_1hz.csv
                          one row per participant, one column per second of film time (0-807 s), 0-100
    README.md             what every column means

De-identification: Prolific IDs are replaced by pseudonyms (P001, P002, ...). The key linking the two stays in
data/pseudonym_key.csv in this repository (git-ignored, never shared). Free-text answers are not exported.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from qc_lib import EXPLORATORY_STUDIES, FILM_DURATION_S, load_session, prereg_hard_exclusion  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
QC_REPORT = ROOT / "qc" / "out" / "qc_report.csv"
KEY_FILE = ROOT / "data" / "pseudonym_key.csv"

N_SECONDS = int(np.floor(FILM_DURATION_S))  # 808 one-second bins: 0 ... 807 s
BOUT_GAP_S = 2.0  # inputs more than 2 s apart start a new "rating bout" (as in qc/engagement.py)

# The registered sensitivity analysis drops the submissions rejected on Prolific on 2026-10-04 for behaviour on the
# free-text page (docs/prereg_log.md). Fixed list of Prolific ID prefixes, because the current Prolific status no
# longer shows it for R5: that rejection was reversed for payment only, and it stays in the set (Micah,
# 2026-10-04). The prefixes identify people, so they are kept next to the raw data in a git-ignored file, one
# prefix per line (removed from the published code on 2026-10-05).
REJECTION_SET_FILE = ROOT / "data" / "rejection_set.txt"


def read_rejection_set(path: Path = REJECTION_SET_FILE) -> tuple[str, ...]:
    """The registered rejection set: one Prolific ID prefix per line of a private file."""
    return tuple(line.strip() for line in path.read_text().splitlines() if line.strip())

COHORT_NAMES = {
    "pilot_affect2d": "pilot",
    "main_c1": "cohort 1",
    "main_c2": "cohort 2",
    "main_c3": "cohort 3",
    "main_c4": "cohort 4",
}


# ---------------------------------------------------------------- small building blocks (tested)

def resample_to_1hz(samples: pd.DataFrame, n_seconds: int = N_SECONDS) -> tuple[np.ndarray, np.ndarray]:
    """Valence and arousal at every whole second of film time, by linear interpolation.

    Only samples taken while the film was playing are used (ratings made during a pause are ignored).
    """
    playing = samples[samples["playing"] == 1].sort_values("t_stim")
    film_time = playing["t_stim"].astype(float)
    seconds = np.arange(n_seconds, dtype=float)
    valence = np.interp(seconds, film_time, playing["value_x"].astype(float))
    arousal = np.interp(seconds, film_time, playing["value_y"].astype(float))
    return valence, arousal


def rating_bouts(input_times: np.ndarray, film_length_s: float) -> tuple[float, float]:
    """Number of rating bouts per minute, and the longest stretch of film without any input (seconds)."""
    times = np.sort(np.asarray(input_times, float))
    if times.size == 0:
        return 0.0, float(film_length_s)
    starts_new_bout = np.concatenate([[True], np.diff(times) > BOUT_GAP_S])
    bouts_per_minute = starts_new_bout.sum() / (film_length_s / 60)
    gaps = np.diff(np.concatenate([[0.0], times, [film_length_s]]))
    return float(bouts_per_minute), float(gaps.max())


def seven_point_scale(stored: pd.Series) -> pd.Series:
    """jsPsych stores the position of the chosen option (0-6); the questionnaire scale is 1-7."""
    return pd.to_numeric(stored, errors="coerce") + 1


def assign_pseudonyms(prolific_ids: list[str], existing: dict[str, str]) -> dict[str, str]:
    """Keep existing pseudonyms; give new people the next free number (P001, P002, ...)."""
    mapping = dict(existing)
    next_number = len(mapping) + 1
    for pid in prolific_ids:
        if pid not in mapping:
            mapping[pid] = f"P{next_number:03d}"
            next_number += 1
    return mapping


def in_rejection_set(prolific_ids: list[str], prefixes: tuple[str, ...] | None = None) -> np.ndarray:
    """True for the participants in the registered rejection set. Each prefix must match exactly one ID."""
    if prefixes is None:
        prefixes = read_rejection_set()
    ids = list(prolific_ids)
    for prefix in prefixes:
        matches = [i for i in ids if i.startswith(prefix)]
        if len(matches) != 1:
            raise ValueError(f"Rejection-set prefix {prefix} matches {len(matches)} participants (expected 1).")
    return np.array([any(i.startswith(prefix) for prefix in prefixes) for i in ids])


def check_deidentified(table: pd.DataFrame, known_ids: list[str]) -> None:
    """Stop with an error if any Prolific ID appears anywhere in the table."""
    text = table.astype(str).to_numpy().ravel()
    leaked = {pid for pid in known_ids if any(pid in cell for cell in text)}
    if leaked:
        raise ValueError(f"{len(leaked)} Prolific ID(s) found in an export table - not writing it.")


# ---------------------------------------------------------------- reading one participant

def questionnaire_answers(session) -> dict:
    """Fear of heights (before the film), STICSA items, and the bodily-sensation checklist."""
    answers = {}
    for trial in session.trials:
        response = trial.get("response")
        if isinstance(response, dict) and "height_fear" in response:
            answers["height_fear"] = response["height_fear"]  # stored 0-6, converted to 1-7 below
    for timepoint in ("pre", "post"):
        sticsa = session.trial("sticsa", timepoint=timepoint)
        if sticsa:
            for item in sticsa[-1]["items"]:  # responses 1-4; "item" is the STICSA item number
                answers[f"sticsa_{timepoint}_item{item['item']:02d}"] = item["response"]
    body = session.trial("post_body")
    if body:
        ticked = (body[-1].get("response") or {}).get("body_sensations") or []
        answers["body_sensations"] = "; ".join(ticked)
    return answers


def load_demographics() -> pd.DataFrame:
    """Age and sex from the Prolific demographic exports (withheld by Prolific for rejected/returned people)."""
    frames = [pd.read_csv(f) for f in sorted((RAW / "demographics").glob("prolific_demographics_*.csv"))]
    demo = pd.concat(frames)[["Participant id", "Age", "Sex"]]
    demo = demo.rename(columns={"Participant id": "prolific_pid", "Age": "age", "Sex": "sex"})
    demo["age"] = pd.to_numeric(demo["age"], errors="coerce")
    demo.loc[~demo["sex"].isin(["Female", "Male"]), "sex"] = np.nan
    return demo.drop_duplicates("prolific_pid")


# ---------------------------------------------------------------- main

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default=str(ROOT / "data" / "export"))
    out = Path(parser.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)

    # 1. Who completed the valence x arousal arm (pilot + cohorts 1-4)?
    report = pd.read_csv(QC_REPORT)
    report = report[(report["completed"] == True) & (report["study"] == "affect2d")]  # noqa: E712
    report = report[report["prolific_study"].isin(COHORT_NAMES)]
    completed = report.set_index("prolific_pid")
    print(f"completed sessions: {len(completed)}")

    # 2. Read each participant's raw file: 1 Hz ratings, rating bouts, questionnaire items.
    rows, valence_rows, arousal_rows = [], {}, {}
    for path in sorted(RAW.glob("jatos_*.ndjson")):
        session = load_session(path)
        if not session.meta or session.pid not in completed.index or session.film_samples.empty:
            continue
        pid = session.pid
        valence_rows[pid], arousal_rows[pid] = resample_to_1hz(session.film_samples)
        bouts_per_min, longest_gap = rating_bouts(session.film_inputs["t_stim"].astype(float), N_SECONDS - 1)
        rows.append({"prolific_pid": pid, "bouts_per_min": round(bouts_per_min, 2),
                     "longest_gap_s": round(longest_gap, 1), **questionnaire_answers(session)})
    raw_measures = pd.DataFrame(rows).set_index("prolific_pid")

    # 3. Combine with the QC report (STICSA totals, post-film questions, data quality) and demographics.
    qc = completed.join(raw_measures, how="inner")
    qc["registered_exclusion"] = qc.apply(prereg_hard_exclusion, axis=1)
    demographics = load_demographics().set_index("prolific_pid")
    qc = qc.join(demographics, how="left")

    # 4. Pseudonyms (the key stays in this repository only).
    existing = pd.read_csv(KEY_FILE, dtype=str) if KEY_FILE.exists() else pd.DataFrame(columns=["prolific_pid", "participant"])
    key = assign_pseudonyms(sorted(qc.index), dict(zip(existing["prolific_pid"], existing["participant"])))
    pd.DataFrame({"prolific_pid": list(key), "participant": list(key.values())}).to_csv(KEY_FILE, index=False)

    # 5. The participant table.
    sticsa_items = sorted(c for c in qc.columns if c.startswith("sticsa_") and "_item" in c)
    participants = pd.DataFrame({
        "participant": [key[p] for p in qc.index],
        "sample": np.where(qc["prolific_study_id"].isin(EXPLORATORY_STUDIES), "exploratory", "confirmatory"),
        "cohort": qc["prolific_study"].map(COHORT_NAMES).to_numpy(),
        "age": qc["age"].to_numpy(),
        "sex": qc["sex"].to_numpy(),
        "height_fear": seven_point_scale(qc["height_fear"]).to_numpy(),
        "sticsa_pre": qc["sticsa_pre"].to_numpy(),
        "sticsa_post": qc["sticsa_post"].to_numpy(),
        "anxiety_overall": seven_point_scale(qc["q_anxiety_overall"]).to_numpy(),
        "concern_safety": seven_point_scale(qc["q_concern_safety"]).to_numpy(),
        "body_intensity": seven_point_scale(qc["q_body_intensity"]).to_numpy(),
        "body_sensations": qc["body_sensations"].to_numpy(),
        "distracting": seven_point_scale(qc["q_distracting"]).to_numpy(),
        "difficult": seven_point_scale(qc["q_difficult"]).to_numpy(),
        "seen_before": qc["q_seen_before"].to_numpy(),
        "full_attention": qc["q_full_attention"].to_numpy(),
        "input_device": qc["q_input_device"].to_numpy(),
        "attention_failed": qc["att_failed"].to_numpy(),
        "film_coverage": qc["coverage"].to_numpy(),
        "buffering_s": qc["stalled_s"].to_numpy(),
        "interrupted_s": qc["interrupted_s"].to_numpy(),
        "bouts_per_min": qc["bouts_per_min"].to_numpy(),
        "longest_gap_s": qc["longest_gap_s"].to_numpy(),
        "rejected_on_prolific": (qc["prolific_status"] == "REJECTED").to_numpy(),
        "in_rejection_set": in_rejection_set(list(qc.index)),
        "registered_exclusion": qc["registered_exclusion"].to_numpy(),
        **{c: qc[c].to_numpy() for c in sticsa_items},
    }).sort_values("participant")

    seconds = [f"s{t:03d}" for t in range(N_SECONDS)]
    ratings = {}
    for name, series in (("valence", valence_rows), ("arousal", arousal_rows)):
        table = pd.DataFrame([np.round(series[p], 2) for p in qc.index], columns=seconds)
        table.insert(0, "participant", [key[p] for p in qc.index])
        ratings[name] = table.sort_values("participant")

    # 6. Safety check, then write.
    for table in (participants, *ratings.values()):
        check_deidentified(table, known_ids=list(key))
    participants.to_csv(out / "participants.csv", index=False)
    for name, table in ratings.items():
        table.to_csv(out / f"ratings_{name}_1hz.csv", index=False)
    (out / "README.md").write_text(DATA_README, encoding="utf8")

    usable = participants["registered_exclusion"].fillna("") == ""
    summary = participants.assign(usable=usable).groupby("sample")["usable"].agg(["size", "sum"])
    print(summary.rename(columns={"size": "completed", "sum": "usable (registered rules)"}).to_string())
    print(f"wrote {out}")


DATA_README = """# Heights film rating study – de-identified data

Exported by `qc/export_dataset.py` in the rating-study tooling repository (vmp_film_rating). One row per participant
who completed the valence × arousal arm (pilot, cohorts 1–4). Prolific IDs are replaced by pseudonyms (P001, …).
Free-text answers are not included.

## participants.csv

| column | meaning |
|---|---|
| participant | pseudonym |
| sample | `exploratory` (pilot + cohort 1) or `confirmatory` (cohorts 2–4), as preregistered |
| cohort | recruitment cohort |
| age, sex | Prolific profile data; empty where Prolific withholds it (rejected submissions) |
| height_fear | "In everyday life, how afraid are you of heights?" 1 (not at all) – 7 (extremely), before the film |
| sticsa_pre, sticsa_post | STICSA state somatic total (11 items, 1–4 each, range 11–44), just before / just after the film |
| sticsa_pre_itemNN, sticsa_post_itemNN | the 11 item responses (1–4), in the order shown |
| anxiety_overall | "Overall, how tense or anxious did you feel while watching the film?" 1–7 |
| concern_safety | "How concerned did you feel for the safety of the people in the film?" 1–7 |
| body_intensity | strength of bodily sensations while watching, 1–7 |
| body_sensations | ticked bodily sensations, separated by "; " |
| distracting, difficult | how much rating distracted from the film / how difficult the mouse control was, 1–7 |
| seen_before, full_attention, input_device | self-reports after the film |
| attention_failed | number of failed attention checks (0–2) |
| film_coverage | share of film seconds with rating samples while playing |
| buffering_s, interrupted_s | seconds of buffering / interruptions (tab switch, leaving full screen) during the film |
| bouts_per_min, longest_gap_s | rating bouts per minute (inputs > 2 s apart start a new bout); longest stretch without input |
| rejected_on_prolific | current Prolific status is REJECTED (payment decision only) |
| in_rejection_set | in the registered sensitivity set: rejected on 2026-10-04 for behaviour on the free-text page, including one rejection later reversed for payment only (see prereg_log) |
| registered_exclusion | empty = included; otherwise the preregistered hard-exclusion rule(s) that apply |

## ratings_valence_1hz.csv, ratings_arousal_1hz.csv

One row per participant, columns `s000` … `s807` = film time in seconds. Values 0–100 (valence: 0 unpleasant,
50 neutral, 100 pleasant; arousal: 0 low, 100 high activation), linearly interpolated from the 20 Hz samples taken
while the film was playing.
"""


if __name__ == "__main__":
    main()
