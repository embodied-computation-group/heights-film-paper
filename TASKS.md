# Tasks

## Done (2026-10-04)
- Repository set up; de-identified data exported from vmp_film_rating (`qc/export_dataset.py`, commit `6a7a34b`).
- Tested helpers: `analysis/stats_tools.py` (paired test with dz and exact CI, Wilcoxon, Holm, Spearman with
  bootstrap CI, circular block bootstrap correlation, split-half reliability) and `analysis/study_data.py`
  (loading, registered segment means, whole-film mean, primary and sensitivity samples).
- Tested `analysis/hypotheses.py` (H1–H6 as registered), `analysis/segmentation.py` (port of the registered
  segmentation; reproduces 262/470/692 s on the original 22 exploratory participants) and `analysis/run_record.py`
  (run records; refuses a confirmatory run from a dirty tree or a second time). Fixed a crash in the dz CI for
  large effects. 47 tests pass.
- Scripts `01_sample.py`, `02_confirmatory.py`, `03_figures.py`, run on the **exploratory sample only**; outputs in
  `results/exploratory/`. Draft `analysis/plot_style.py`.

## Next
1. Decisions settled 2026-10-04 (see prereg_log): registered rejection set of 4 (n = 120), "No" only for
   not attentive, 1000 edge-bootstrap rounds, draft plot style accepted.
2. Data re-exported with `in_rejection_set`; exploratory run repeated from a clean commit.
3. **Confirmatory run: done 2026-10-04** from `63d042d` (results/confirmatory/, prereg_log entry). Next: fresh-session
   review of the confirmatory code and results; write up results. Figures can be
   redrawn freely (the run-once guard covers only the registered tests, 02_confirmatory.py).
4. Exploratory (labelled as such): done - affect grid by film phase (`04_affect_grid.py`, fig6). To do: age and sex effects and interactions with segment/time; ISC; trajectory features;
   HRF-convolved regressors for the fMRI sample (sex-reweighted group mean).
5. Release: see the Submission section below.
6. Manuscript outline. Free-text narratives are a separate paper (registered addendum required first).

## Submission (Cognition and Emotion, Brief Article)

Final manuscript and supplement: `manuscript/manuscript.tex`, `manuscript/supplement.tex` (the brief-report revision
of 2026-10-05; earlier drafts and revision folders are in the private history only).

Settled with Micah on 2026-10-05: sole author (ORCID 0000-0001-9399-4179); no acknowledgements or competing
interests; Lundbeckfonden (R272-2017-4345) and ERC (ERC-2020-StG-948788) funding; singular AI declaration; ethics
exemption letter filed at `docs/Undtagelsesbrev_v2 (English).pdf`; OSF registration public (embargo lifted);
participant codes redacted from the logs; public repositories created from a fresh history (full history in the
private heights-film-paper-private); the platform published as online-affect-rating (tag `v1.0-heights-film`).

Still open before submission:
1. **Zenodo:** connect heights-film-paper to Zenodo, make a release, and replace `\confirm{Zenodo DOI}` in the
   Data Availability Statement.
2. **Film permission:** request sent to the creator on 2026-10-05 (`docs/permission_email_draft.md`). If granted,
   add the film to the archive and change "is not redistributed" in the Data Availability Statement.
3. **Pseudonym key:** delete `data/pseudonym_key.csv` (and `data/rejection_set.txt` once no re-export is needed)
   in the tooling repo after the release.
4. **MindProbe:** take down the JATOS study (its public link is still live).

Later: make online-affect-rating configurable (questionnaires, film and questions in one config file).
