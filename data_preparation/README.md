# Data preparation: from raw results to `data/processed/`

These are the scripts that downloaded the raw results, checked data quality and exported the de-identified tables in
`data/processed/`. They are kept here as a record of how the dataset was made. They cannot be rerun from this
repository: the raw results contain Prolific IDs and are not shared.

Copied on 2026-10-05 from commit `13e786a` of the private tooling repository (vmp_film_rating), where they were run.
One change was made for publication: the Prolific ID prefixes of the registered rejection set are no longer written
in `qc/export_dataset.py` but read from a private file next to the raw data (`data/rejection_set.txt`). The tests
use made-up IDs. Participant codes in the logs were replaced by R1-R5 (see `docs/prereg_log.md`).

| script | what it does |
|---|---|
| `qc/review.py` | fetch JATOS results and Prolific submissions; write the QC report |
| `qc/qc_lib.py` | read a session's raw result file; QC measures, flags and the registered hard exclusions |
| `qc/engagement.py` | engagement and compliance check for the continuous ratings |
| `qc/export_dataset.py` | write `participants.csv` and the 1 Hz rating tables, with pseudonyms (P001, ...) |
| `qc/segment_film.py` | exploratory: segment edges from the exploratory sample's group-mean arousal (the registered edges) |
| `qc/pilot_summary.py`, `qc/plot_*.py`, `qc/cohort_status.py` | descriptive checks during collection |

The tests run on made-up data:

```bash
uv run pytest data_preparation/tests
```
