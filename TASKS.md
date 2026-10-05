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

**Submitted 2026-10-05** (3,549 words abstract to references; 22 references). Awaiting the editor.

Final manuscript and supplement: `manuscript/manuscript.tex`, `manuscript/supplement.tex` (the brief-report revision
of 2026-10-05; earlier drafts and revision folders are in the private history only).

Settled with Micah on 2026-10-05: sole author (ORCID 0000-0001-9399-4179); no acknowledgements or competing
interests; Lundbeckfonden (R272-2017-4345) and ERC (ERC-2020-StG-948788) funding; singular AI declaration; ethics
exemption letter filed at `docs/Undtagelsesbrev_v2 (English).pdf`; OSF registration public (embargo lifted);
participant codes redacted from the logs; public repositories created from a fresh history (full history in the
private heights-film-paper-private); the platform published as online-affect-rating (tag `v1.0-heights-film`).

Done 2026-10-05: Zenodo archives of releases v1.0.0 (10.5281/zenodo.23151388) and v1.0.1 (10.5281/zenodo.23152896;
submission version, with the revised Discussion). The manuscript cites the concept DOI 10.5281/zenodo.23151387, which always resolves
to the latest version, so it stays correct in every release. If anything changes before acceptance, make a new
GitHub release.

PsyArXiv preprint szv9e_v1 (manuscript + supplement) submitted 2026-10-05, pending moderation. On acceptance of
the paper, add the published article's DOI to the preprint (Taylor & Francis requirement).

Open:
1. **Film permission:** request sent to the creator on 2026-10-05 (`docs/permission_email_draft.md`). If granted,
   add the film to a new release and change "is not redistributed" in the Data Availability Statement.
2. **Data retention and anonymity (decide, possibly with the AU data office):** the tooling repo keeps the raw
   results (`data/raw/`, with Prolific IDs) and the pseudonym key. Deleting only the key does not anonymise the
   published data, because each row can be matched to its raw file by its values. Options: keep raw data under the
   research-integrity retention period and describe the release as pseudonymised (de-identified), or strip IDs from
   the raw data after the retention decision. Until then the key and `data/rejection_set.txt` stay. At revision,
   word the Data Availability Statement to match ("pseudonymised" while raw data are kept; it now says "anonymised").
3. **MindProbe:** take down the JATOS study link (deleting the study would also delete the raw results there).
4. **PsyArXiv:** check that moderation accepts the preprint (OSF emails); on acceptance of the paper, add its DOI.

Later: make online-affect-rating configurable (questionnaires, film and questions in one config file).
