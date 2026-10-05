# Project: heights film validation paper

## Question
Does the heights film (towerClimb, muted, 13:28) reliably induce somatic anxiety and a reproducible affective time
course (baseline → rise → plateau → return), and how do individual differences relate to it? The group time series
will later model fMRI data from an independent sample. This repo = the paper: analysis, results, figures, manuscript.
The rating task, deployment, data download and QC live in the tooling repo (vmp_film_rating), which exports
`data/processed/`.

## Scientific context
- The plan is the OSF preregistration **osf.io/s2yvb** (`docs/preregistration.md`). Hypotheses H1–H6, segment edges,
  exclusion rules, tests, Holm families and inference criteria are fixed. Implement them exactly as written.
- Do not change hypotheses, exclusions, edges or expected test values to make code run. Identify ambiguities and ask.
- Anything not in the preregistration is **exploratory** and must be labelled so in code, outputs and text.
- Record every decision or deviation, dated, in `docs/prereg_log.md`.
- Micah reviews scientific choices; help implement, test and document.

## The confirmatory run
- Develop and check every script on the **exploratory sample** first (`--sample exploratory`, the default).
- Run on the **confirmatory sample** only when Micah says so, once, from a clean committed state, with a run record.
- Known counts (registered rules): confirmatory 124 usable of 130; exploratory 21 of 23. H3 compares the
  confirmatory curve with the exploratory curve of those 21. See prereg_log 2026-10-04 for why these differ from
  the registration's status text (123; edges estimated on 22).

## Environment
- uv: `uv sync --locked`; run scripts with `uv run python analysis/<script>.py`; tests: `uv run pytest`.
- Seeds: pass explicitly (default 20261004); record them in the run record.

## Code style (Micah)
- Plain, friendly, readable scripts that someone with little coding experience can run start to finish.
  No dense or over-engineered code. Short functions with plain comments; one script per analysis step.
- Tests **before** implementation, on small made-up data with known answers. Check that a deliberately introduced
  plausible error makes a test fail.
- One shared plot style for the study (`analysis/plot_style.py`, to be developed with Micah): cool-to-hot colours,
  no orange/black "Halloween" palettes. Show participants as well as group means; label units and intervals.

## Data
- `data/processed/` is participant data (age, sex, questionnaires, ratings; pseudonyms P001..., no Prolific IDs
  or free text), published with the code since 2026-10-05. The raw results and pseudonym key stay in the private
  tooling repo; while they exist the published data are pseudonymised, not anonymous (retention decision open in
  TASKS.md). Never add identifying information (Prolific IDs or prefixes, free text, dates of participation).
- Repositories: work in the public `heights-film-paper` (local `~/vibes/heights-film-paper-public`). The private
  `heights-film-paper-private` holds the full development history; its `main` has been kept identical so far.
  Never push the private history to the public repo.
- Never edit files in `data/processed/`; re-export from the tooling repo instead.
- If an input is missing, report it. Do not invent replacement values.

## Working cycle
- Short plan for a substantial change; small steps; focused commits with the check results in the message.
- Update `TASKS.md` and `VERIFICATION.md` as you go; note AI use in `AI_ASSISTANCE.md`.
- Ask before pushing, publishing or anything outward-facing.
