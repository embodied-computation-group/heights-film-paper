# Heights film rating study – de-identified data

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
