# Preregistration log (deviations and data access)

Plan fixed in commit `a654b2b` (tag `prereg-draft-v1`, 2026-10-04 09:43 CEST). OSF submission pending.
Participant codes in this log were replaced on 2026-10-05 by neutral labels (R1-R5 = the five participants
rejected on Prolific) so that no entry can be linked to a Prolific account.
Entries are appended in time order; copy them into the OSF "foreknowledge" text / deviation report.

- **2026-10-04, ~14:00 CEST - QC tooling change (no change to the registered plan).** The QC flag for untyped
  free text now distinguishes probable dictation (no paste/drop attempts, no time away) from inserted text; the
  task now logs text input types. The registered exclusion rule 3 ("free text not typed") is **unchanged and
  applied as written**.
- **2026-10-04 13:27 RDT - first viewing of confirmatory data.** Micah Allen viewed a descriptive plot of the confirmatory
  group-mean valence and arousal time series with 95% CI (`qc/plot_group_timeseries.py --confirmatory`),
  exclusions applied exactly as registered. No registered hypothesis, segment edge, threshold or exclusion rule
  was changed. Cohort 4 still had a few participants active at this time.
- **2026-10-04 - scope clarified (Micah).** The registration is a working draft: the confirmatory core
  (H1–H5, segments, exclusions, sampling) is frozen; further analyses (LLM prompts, text, time series) will be
  developed on the exploratory sample and added before being applied to confirmatory data.
- **2026-10-04 - Prolific rejections (payment decisions, by Micah).** Rule for rejection (behaviour only, no
  rating-based criteria): >= 3 blocked paste/drop attempts on the free-text page, or > 10 min outside the study
  window while writing, or text inserted without typing after blocked paste/drop attempts. Rejected: R1 (text
  inserted after 14 paste/drop attempts; already a registered hard exclusion), R2, R3 (repeated paste
  attempts + time away), R4, R5 (> 10 min away while writing). All other completions approved.
  Analysis treatment of the four rejected sessions whose data otherwise pass the registered rules is to be decided
  (see note in README/notes) and reported.
- **2026-10-04 - additional cohort 5 drafted (no data yet).** Registered stopping rule was met with cohorts 2-4
  (123 usable under registered rules). Micah requested one more cohort of 20 (Prolific 6ac23d7e47e222d973a7d77b) to
  offset the 4 rejected participants who pass the registered rules. Proposed handling (to be confirmed before
  publication): primary confirmatory analysis on the registered sample (cohorts 2-4); cohort 5 used only in
  sensitivity/robustness analyses and reported as additional data collected after the stopping rule was met.
- **2026-10-04 - data collection closed (Micah).** Stopped under the registered stopping rule: cohorts 2-4 give
  123 usable participants under the registered exclusion rules (>= 120). Cohort 5 (6ac23d7e47e222d973a7d77b) was only
  drafted and **not launched** (budget exhausted). Primary analysis: registered rules as written (n = 123). Any
  post-hoc exclusions (e.g. the 4 rejected participants who pass the registered rules -> n = 119) will be reported
  as deviations with reasons.
- **2026-10-04 13:55 - submission version prepared (not yet registered).** `docs/preregistration.md`/`.pdf` updated
  for OSF submission: title/status, explanation-of-foreknowledge chronology (plan fixed at `a654b2b`; only counts/QC
  flags seen during collection; one descriptive confirmatory group-curve plot; rejection handling; no H1-H5 analysis
  run), and sampling/stopping status at submission. The pre-selected foreknowledge checkbox line was removed at
  Micah's request (the option is chosen on the OSF form itself). Hypotheses, segment edges, exclusion rules and
  analysis plan unchanged. **No confirmatory analysis is run until the OSF registration exists.**
- **2026-10-04 - rejection reversed for R5 (Micah).** Participant explained the > 10 min away while writing
  (keyboard broke) and offered to return the study. Rejection reversed (UNREJECT -> awaiting review); a return is to
  be requested so the submission ends as returned, unpaid. R2's rejection stands. Payment-status change only:
  the session's data, exclusion status under the registered rules and the planned sensitivity analysis
  (4 rejected-but-rule-passing participants, n = 119) are unchanged.
- **2026-10-04 - submission version revised after Micah's read-through (not yet registered).** Added **H6**
  (post-film overall anxiety correlates with STICSA change and plateau arousal; Spearman, Holm within H6), stated as
  a late addition after the descriptive group-curve plot and before any hypothesis test. Free-text narrative section
  reduced to a commitment to a separate report with a registered addendum before confirmatory use. Exploratory age
  and sex analyses (incl. interactions with segment/time) made explicit. Consent screening on fear of heights noted
  (range restriction for H4). Data/code release changed from OSF to GitHub and/or Zenodo (OSF projects become
  read-only from 2027-02-19). Study design rewritten as prose; list formatting fixed; reversed rejection noted.
  H1–H5, segment edges, exclusion rules and sampling unchanged. No confirmatory analysis run.
- **2026-10-04 - foreknowledge text shortened (Micah).** The OSF "Explanation of foreknowledge" field is reduced to
  one line (single descriptive plot of the confirmatory group-mean time series; no analysis decision contingent on
  it). The detailed chronology remains in this log. Confirmatory/exploratory sample definition moved to the
  hypotheses section; the rejected-participant sensitivity analysis moved to Data inclusion and exclusion.
- **2026-10-04 16:35 CEST - registered on OSF (Micah).** https://osf.io/s2yvb, OSF Preregistration template (v4),
  embargoed until 2027-01-01. Content filled via the OSF API from `docs/preregistration.md` at `dcc4adb`; the
  foreknowledge level was set to "Authors' limited observation of the data could not influence their analysis
  decisions". OSF stored `<`/`>` in the text answers HTML-escaped (`&lt;`/`&gt;`); content otherwise identical.
  No confirmatory analysis had been run at registration.
- **2026-10-04 - sample counts at export (after registration; no hypothesis test run).** Final data download and
  `qc/export_dataset.py`: confirmatory 130 completions, **124 usable** under the registered rules (registration
  status text said 129/123: one participant completed after the QC snapshot used for that count; complete
  data, passes all rules, included as registered). Exploratory: 23 completions, **21 usable** under the registered
  rules; the fixed segment edges were estimated on n = 22 with the QC rules in use at the time (one cohort-1
  participant with disrupted viewing included); edges unchanged. Both reported as notes in the paper.
- **2026-10-04 - repository split.** Analysis, results and paper moved to heights-film-paper (private), which
  continues this log from here. This repo keeps the tooling and the registered preregistration files.
- **2026-10-04 - analysis pipeline built and run on the exploratory sample only (no confirmatory data analysed).**
  `analysis/01_sample.py`, `02_confirmatory.py`, `03_figures.py` implement H1-H6 and the registered descriptive
  analyses as written. Implementation choices where the registration is silent, for Micah's review:
  (a) segment-edge re-estimation uses 1000 participant-bootstrap rounds (registration gives no number; the
  original `qc/segment_film.py` defaulted to 300); edges re-estimated for the primary sample only;
  (b) H1 is a single test (no Holm), with the Wilcoxon p reported alongside; H3 has no p-value, decided by the CI
  lower bound only; (c) all bootstraps use seed 20261004; Spearman CIs are percentile intervals;
  (d) on the exploratory sample H3 is replaced by a labelled stand-in (cohort 1 vs pilot) because there is no
  second sample. Port check: the segmentation code reproduces the registered edges 262/470/692 s exactly on the
  22 exploratory participants used at the time. With the 21 now usable, the first edge re-estimates at 207 s
  (bootstrap 95% CI 139-275), i.e. weakly identified; registered edges unchanged.
- **2026-10-04 - open questions found while building (not yet resolved; no change made).**
  (1) Sensitivity sample "rejected on Prolific": the export flags 3 rejected-but-rule-passing confirmatory
  participants, giving n = 121; this log (entries above) defines the set as 4 participants, keeping R5 after the
  rejection was reversed (expected n = 120 with 124 usable). Needs a re-export with a flag for the registered
  set, or a decision. (2) "Self-report not watching attentively": the code drops `full_attention == "No"` only;
  5 completers answered "Mostly". Needs a decision before the confirmatory run.
- **2026-10-04 - open questions settled (Micah); no confirmatory data analysed.** (1) The rejected-participant
  sensitivity analysis drops the registered set of 4 rejected-but-rule-passing confirmatory participants,
  including R5: the reversal was a payment decision only and does not mean the data must be analysed.
  Implemented as a fixed list in vmp_film_rating `qc/export_dataset.py` (new column `in_rejection_set`; matches 4
  rule-passing confirmatory participants plus the one already hard-excluded); data re-exported from the existing
  QC report, all other columns and both rating tables unchanged (checked). Sensitivity n = 120 of 124.
  (2) "Self-report not watching attentively" follows the registration literally: answer "No" to the attentiveness
  question; "Mostly" is not excluded. Any broader definition would be an exploratory sensitivity analysis.
  (3) Segment-edge re-estimation: 1000 participant-bootstrap rounds (accepted). (4) Draft plot style accepted.
- **2026-10-04 - confirmatory run (Micah: "go").** `01_sample.py`, `02_confirmatory.py`, `03_figures.py` with
  `--sample confirmatory`, each run once from clean commit `63d042d` (run records in `results/confirmatory/`, all
  `uncommitted_changes: false`; seed 20261004; 5000 bootstrap resamples, 1000 split-half splits, 1000 edge
  bootstraps). n = 124 primary, 96 stricter engagement, 120 without the rejection set; H3 reference = the 21 usable
  exploratory participants. Primary-sample outcome under the registered inference criteria: H1, H2a-d, H3 (both
  dimensions), H4b, H5a, H5b, H6a, H6b supported; **H4a and H4c not supported** (H4c uncorrected p = .049, Holm
  p = .098). Same pattern in both sensitivity samples. Descriptive: split-half reliability .992 (arousal), .979
  (valence); re-estimated edges 262 s [133, 271], 467 s [317, 475], 660 s [631, 690] vs registered 262/470/692 s.
  No hypothesis, edge, exclusion or test was changed after seeing these results.
- **2026-10-04 - exploratory figure: affect grid by film phase (Micah's request).** `analysis/04_affect_grid.py`
  (port of vmp_film_rating `qc/plot_affect_grid.py` per-segment maps): occupancy per registered segment,
  participant means, group mean ± 95% CI. Listed as exploratory in the registration ("affect-grid occupancy per
  segment"); descriptive only, no test. Drawn on the exploratory sample, then on the confirmatory sample.
- **2026-10-04 - exploratory age and sex analyses specified (before running them on the confirmatory sample).**
  Listed in the registration under "Other planned analysis"; not registered tests, p values uncorrected.
  `analysis/06_age_sex.py` (+ tested `analysis/demographics.py`), primary sample with age and sex available (Prolific
  sex field, female/male; Prolific withholds demographics for rejected submissions): (1) STICSA change ~ sex + age
  (OLS), plus Welch t (sex) and Spearman (age); (2) per rating, segment means ~ segment x (sex + age): main result a
  random-intercept mixed model with likelihood-ratio tests of segment x sex and segment x age (3 df); clustered-by-
  participant OLS with Wald F tests reported next to it as a check; if the mixed model does not converge it is
  reported as missing, not replaced (it did not converge in the 21-person exploratory sample); (3) female - male
  difference per segment (Welch CI) and age-segment Spearman correlations; (4) figures: time course by sex, STICSA
  change and segment means by sex and age. The registration's "mixed models over the 1 Hz series" example was not
  implemented (segment-level models instead).
- **2026-10-04 - age/sex analyses run on the confirmatory sample; one implementation fix.** First run reported the
  mixed models as "did not converge". Diagnosis: the L-BFGS optimiser I had chosen raised a singular-matrix error,
  while BFGS, Powell and Nelder-Mead all converged to the same solution (random-intercept variance 82, residual 171,
  identical log-likelihood). Fixed by trying optimisers in turn and keeping the first converged fit (the model and
  the decision rule are unchanged); rerun. Mixed-model LR tests and the clustered OLS check agree: no evidence that
  the time course differs by sex or age (all p >= .10), and no sex or age effect on the STICSA change.
  Also: STICSA-by-age panel redrawn with jitter (whole-number values overlapped).
- **2026-10-05 - exploratory item-level STICSA analysis (Micah's request, after the confirmatory results were known).**
  `analysis/10_sticsa_items.py` (+ tested `analysis/sticsa_items.py`): per item, mean change, share increased, dz with
  exact CI, Wilcoxon signed-rank test, Holm across the 11 items; run on the exploratory sample first, then the
  confirmatory sample. Post hoc and exploratory; reported as such (Supplementary Table S6). Result (confirmatory): all
  items increased (Holm p < .001), dz 0.52-1.17, largest for a fast heartbeat.
- **2026-10-05 - participant codes redacted for public release (Micah).** The short Prolific-derived codes for the
  five rejected participants and one late completer were replaced in this log by R1-R5 and "one participant". The
  data files were always pseudonymised (P001, ...). The public repository will be created without the earlier git
  history, and the pseudonym key in vmp_film_rating will be deleted after release so the published data are
  anonymous. No analysis, data value or result changed.
