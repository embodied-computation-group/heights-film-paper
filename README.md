# Heights film: continuous valence and arousal ratings

Analysis for the online validation study of a first-person heights film as an induction of somatic anxiety and
a reproducible affective time course. Participants (Prolific) watched the muted 13.5-minute film while rating
valence and arousal continuously on a 2D affect grid, and filled in the STICSA somatic scale before and after.

- **Archive:** [doi:10.5281/zenodo.23151387](https://doi.org/10.5281/zenodo.23151387) (Zenodo; this DOI always
  points to the latest version; v1.0.0, the submission version, is 10.5281/zenodo.23151388).
- **Preregistration:** [osf.io/s2yvb](https://osf.io/s2yvb), registered 2026-10-04 (public).
  Text in [docs/preregistration.md](docs/preregistration.md); decisions and deviations in
  [docs/prereg_log.md](docs/prereg_log.md).
- **Rating task:** the exact task and study settings used are in [materials/rating_task/](materials/rating_task/).
  The general tool is [online-affect-rating](https://github.com/embodied-computation-group/online-affect-rating)
  (tag `v1.0-heights-film` = the version used here).
- **Data preparation:** the scripts that turned the raw results into `data/processed/` are in
  [data_preparation/](data_preparation/) (a record; the raw data contain Prolific IDs and are not shared).

## What you need

- [uv](https://docs.astral.sh/uv/) (installs the right Python and packages for you).

```bash
uv sync --locked      # set up the environment from uv.lock
uv run pytest         # check that everything works
```

## Data

`data/processed/` holds the de-identified data: one row per participant who completed the study (pilot and
cohorts 1–4), with pseudonyms instead of Prolific IDs and no free text. Column definitions are in
[data/processed/README.md](data/processed/README.md).

- **Exploratory sample:** pilot + cohort 1 (23 completed, 21 usable under the registered rules). Used to fix the
  segment edges and plan the study.
- **Confirmatory sample:** cohorts 2–4 (130 completed, 124 usable). Used only for the registered tests.

## Running the analysis

Three steps, run in order. Each writes its tables, figures and a run record to `results/<sample>/`:

```bash
uv run python analysis/01_sample.py         # sample, exclusions, age/sex/device
uv run python analysis/02_confirmatory.py   # H1-H6 + registered descriptives (about 1 min)
uv run python analysis/03_figures.py        # figures
```

The default is the exploratory sample (for development); `--sample confirmatory` uses the confirmatory sample. The
registered tests (`02_confirmatory.py`) were run once on the confirmatory sample (2026-10-04) and the script refuses
a second run. Figures and descriptive tables can be redrawn at any time.

```bash
uv run python analysis/04_affect_grid.py    # exploratory figure: affect grid by film phase
uv run python analysis/05_report_numbers.py # numbers and tables for the results report
cd manuscript && latexmk -pdf results.tex   # APA results report (manuscript/results.pdf)
```

## Repository layout

```text
analysis/          # the analysis: small, readable scripts and tested helper functions
data/processed/    # participant data (pseudonyms, no Prolific IDs or free text)
data_preparation/  # the scripts that made data/processed/ from the raw results (a record)
materials/         # the rating task and study settings exactly as used
docs/              # preregistration and its log
results/           # tables and figures written by the scripts
tests/             # tests, run with `uv run pytest`
TASKS.md           # what is being worked on next
VERIFICATION.md    # the checks behind each result
AI_ASSISTANCE.md   # how AI coding tools were used (for the paper's disclosure)
```

## Licence and history

Code: MIT (see `LICENSE`). Data in `data/processed/`: CC BY 4.0. The film is a third-party video and is not
included. This public repository starts from a single commit made on 2026-10-05; the commit hashes cited in run
records and in `docs/prereg_log.md` (e.g. the confirmatory run from `63d042d`) refer to the full development
history, which is kept in a private repository and is available on request.
