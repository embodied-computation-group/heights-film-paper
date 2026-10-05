# OSF Preregistration – version for submission (2026-10-04)

Prepared on the OSF Preregistration template (current COS version;
[Markdown mirror](https://gist.github.com/JoKeyser/3506f3087bc68dda89f32f56ed9c283c)). Copy each section into the OSF web form.
Status: **ready for OSF submission – not yet registered.** Data collection is complete; no registered analysis has
been run.

- **Frozen** (fixed in commit `a654b2b`, tag `prereg-draft-v1`, before cohort 3; confirmatory group curves have
  since been viewed descriptively, see `docs/prereg_log.md`): hypotheses H1–H5, segment edges, exclusion rules,
  sampling plan. Changes to these are reported as deviations. H6 was added at submission.
- **Open**: analyses not yet specified (LLM prompt-based ratings and labels, text analyses, further time-series
  analyses) are developed on the exploratory sample only (pilot + cohort 1) and added to this document, with a
  dated entry in the log, **before** they are applied to any confirmatory data.

## Metadata

### Title
Continuous valence and arousal ratings of a first-person heights film: validation of an online emotion- and
somatic-anxiety-induction paradigm

### Description
Online participants (Prolific) watch a muted, ~13.5-min first-person film of people climbing a skyscraper and
continuously report valence and arousal with a mouse-controlled affect grid, with the STICSA somatic subscale
before and after the film. We test whether the film induces somatic anxiety and a reproducible group-level
affective time course with four phases (baseline, rise, plateau, return) identified in exploratory pilot data,
and whether individual differences (everyday fear of heights, somatic-anxiety change) relate to the responses.
The group time series will later be used to model fMRI data from an independent sample who watched the same film.

### Contributors
Micah Allen (micah@cfin.au.dk), Center of Functionally Integrative Neuroscience, Aarhus University.

### License
- [x] CC-By Attribution 4.0 International

### Subject
Social and Behavioral Sciences › Psychology › Cognitive Psychology; Psychology › Biological Psychology;
Psychology › Quantitative Psychology

### Tags
continuous rating; affect grid; valence; arousal; emotion induction; somatic anxiety; STICSA; film; heights;
naturalistic stimuli; fMRI regressors; online experiment

## Overview

### Research questions or hypotheses
All confirmatory tests use only the confirmatory sample (cohorts 2–4) and Study 2 (valence × arousal grid). The
exploratory sample (pilot and cohort 1) was used to set the segment edges, exclusion rules and sample size and is
excluded from all confirmatory tests.
Segment edges are **fixed** at the values estimated in the complete exploratory sample (Study 2, n = 22 usable;
piecewise-linear segmentation of the group-mean arousal, `qc/segment_film.py`): baseline 0–262 s, rise 262–470 s,
plateau 470–692 s, return 692–808 s (film time).

- **H1 – somatic-anxiety induction.** STICSA somatic total (11–44) is higher immediately after the film than
  immediately before it.
- **H2 – affective time course (fixed segments).** Within participants, using segment means of the continuous
  ratings:
  - H2a arousal: rise > baseline; H2b arousal: plateau > baseline; H2c arousal: return < plateau;
  - H2d valence: plateau < baseline.
- **H3 – replication of the group time course.** The confirmatory group-mean arousal and valence time series
  (1 Hz) correlate positively with the exploratory group-mean series, with the lower bound of the 95% CI of each
  correlation above r = .50.
- **H4 – fear of heights.** Everyday fear of heights (pre-film item, 1–7) correlates positively with plateau
  arousal (H4a), negatively with plateau valence (H4b), and positively with the STICSA change, post − pre (H4c).
- **H5 – somatic change and continuous ratings.** STICSA change (post − pre) correlates positively with
  whole-film mean arousal (H5a) and negatively with whole-film mean valence (H5b).
- **H6 – convergence with reported anxiety** (added at submission).
  Post-film overall anxiety ("Overall, how tense or anxious did you feel while watching the film?", 1–7)
  correlates positively with the STICSA change, post − pre (H6a), and with plateau arousal (H6b).

### Explanation of foreknowledge and managing unintended influences
The author viewed a single descriptive plot of the confirmatory group-mean time series; no analysis decision
(hypotheses, segment edges, exclusion rules) was contingent on it.

## Research Design

### Study type
- [x] Non-randomized study (single-group within-subject design; no manipulated between-subject variable)

### Intention for causal interpretation
- [x] Indirect inference on causal relationship(s): the film is interpreted as inducing the measured changes
  (pre/post and time course), without a control film.

### Blinding of experimental treatments
- [x] No blinding is involved.

### Study design
Single-session online within-subject study. After giving consent, participants pass a device check (desktop
computer, browser window at least 1000×600) and answer a question on everyday fear of heights, followed by the first
attention check. The study then switches to full screen. Participants read the instructions and practise the rating
task: 40 s of tracking a moving target on the 2D grid (repeated once if the error exceeds 20 units), then placing six
example states on the affect grid.

Participants complete the **STICSA somatic scale (pre)** and then watch the film (13:28, muted, downloaded in full
before playback). Throughout the film they rate valence and arousal continuously by moving a dot in a small grid in
the corner of the frame with the mouse (pointer locked, sampled at 20 Hz). The **STICSA somatic scale (post)**
follows immediately after the film.

The session ends with the post-film questions (overall anxiety, concern for the people's safety, intensity of bodily
sensations and a checklist of them, distraction, difficulty, the second attention check, whether they had seen the
film before, attentiveness and input device), a required written description of at least 100 words, and an optional
feedback field.
A separate Study 1 (continuous 1D anxiety rating) was piloted (n = 3) and is not part of this registration.

### Randomization
Not applicable (single condition). Sex-balanced recruitment by Prolific quota (see Sampling).

## Sampling

### Data collection procedures
Prolific; filters: fluent English, normal/corrected vision, approval rate ≥ 95%, ≥ 20 previous submissions,
desktop only; requirement stated in the listing and information sheet: physical mouse or trackpad (no
touchscreen, pen tablet or remote desktop). Each cohort is a separate Prolific study of 20 places with a 50/50 quota
on Prolific's sex screener, blocking participants of the pilot and all earlier cohorts. Payment £4.80 (estimated
30 min). The information sheet advised people with a strong fear of heights not to take part, and consent
included the statement "I do not expect this to be seriously distressing for me"; the sample therefore
under-represents the upper range of fear of heights (relevant to H4). Task: jsPsych 8 on JATOS (MindProbe). The film (re-encoded H.264, 1280×720, 25 fps, all frames, no audio)
is downloaded completely before playback; if not downloaded within 5 min of waiting the session ends and the
participant is asked to return the study (not counted as a completion). Ratings are time-stamped against film
playback time; interruptions (tab switch, leaving full screen, pointer release) pause the film.

### Sample size
Confirmatory: **120 usable participants** in Study 2 (after the exclusions below), starting with cohort 2.

*Status at submission:* collection is complete. Cohort 2 (20 completions), cohort 3 (20) and cohort 4 (90; one
Prolific study whose places were increased in steps of 20 about 25 min apart, sex quota 50/50 throughout, instead of
separate 20-place studies, to limit simultaneous video downloads on the host): 129 completions, **123 usable** under
the registered exclusion rules. An additional cohort was drafted but not launched.

### Sample size rationale
Exploratory estimates (n = 21 usable at the time of the power analysis; final exploratory n = 22): STICSA change dz = 0.89 (n = 19 for 95% power); segment contrasts dz = 1.6–2.4
(n ≤ 8). The binding constraint is individual differences: n = 120 gives 80% power for correlations of
r ≈ .25 (two-sided α = .05). It also yields a 95% CI half-width of about ±3.7 (arousal) and ±3.4 (valence) on the
0–100 group-mean time series and expected group-curve reliability (Spearman–Brown) of ≈ .995 / .986.

### Starting and stopping rules
Start: cohort 2. Recruit in cohorts of 20 (sex quota 10/10) and apply the exclusion rules after each cohort;
stop at the end of the first cohort after which ≥ 120 usable participants are available (the final cohort may be
reduced to the number still needed, keeping the quota). Hard cap: 160 completions. If the budget is exhausted
first, analyse the sample available and report the shortfall.

*Status at submission:* the stopping rule was met with cohorts 2–4 (123 usable ≥ 120); collection stopped.
Procedural changes during collection (task wording and analysis plan unaffected): from cohort 4 the free-text
input type was logged, and a fix ensured that a failed (rather than slow) video download also ends in the return
path; one cohort-4 participant was affected by the earlier behaviour (film streamed with heavy buffering) and is
excluded by registered rule 5.

## Variables

### Manipulated variables
None (single film condition).

### Measured variables
- Continuous valence (x, 0–100; 50 = neutral) and arousal (y, 0–100), sampled at 20 Hz with film playback time
  (`t_stim`) and presented-frame time; raw mouse movements and all input events.
- STICSA state somatic subscale (items 1, 2, 6, 7, 8, 12, 14, 15, 18, 20, 21; 1–4), immediately before and after
  the film; instruction "Please indicate how you feel right now, at this moment."
- Everyday fear of heights (1–7, before the film).
- Post-film: overall anxiety, concern for the people's safety, bodily-sensation intensity (1–7); bodily-sensation
  checklist; distraction and difficulty of rating (1–7); seen before; attentiveness; input device.
- Two instructed-response attention checks; free-text description and feedback; data-quality logs (interruptions,
  buffering, window focus, copy/paste attempts, keystrokes); Prolific demographics (age, sex, etc.).

### Indices
- Ratings resampled to 1 Hz of film time (linear interpolation over samples with the film playing).
- Segment mean = mean of the 1 Hz series within the fixed segment window (H2, H4, H5, H6); whole-film mean = mean over
  0–808 s (H5).
- STICSA total = sum of the 11 items (11–44), computed only when all 11 are answered; change = post − pre.
- Group-mean series = mean across usable participants at each second.

## Analysis Plan

### Statistical models
- H1: paired t-test (post vs pre STICSA total); effect size dz with 95% CI; Wilcoxon signed-rank as robustness.
- H2: paired t-tests on segment means (four directional contrasts); dz with 95% CIs; Holm correction across H2a–d.
- H3: Pearson r between the confirmatory and exploratory group-mean series (1 Hz), separately for arousal and
  valence; 95% CI by circular block bootstrap over time (block length 30 s, 5000 resamples).
- H4, H5, H6: Spearman correlations across participants; bootstrap 95% CIs (5000); Holm correction within H4 (three
  tests), within H5 (two tests) and within H6 (two tests).
- Reported descriptively alongside: split-half reliability of the group-mean series (1000 random splits,
  Spearman–Brown), segment edges re-estimated in the confirmatory sample (same piecewise-linear method) with
  participant-bootstrap CIs.

### Transformations
No transformations of ratings beyond 1 Hz resampling and averaging. Spearman correlations are used because of
ordinal predictors and bounded outcomes.

### Inference criteria
Two-sided α = .05 after Holm correction within each hypothesis family; directional hypotheses are supported only
if the effect is significant in the predicted direction. H3 is supported if the lower 95% CI bound of r exceeds
.50 for the given dimension.

### Data inclusion and exclusion
Participants are included if they complete the study (reach the end) in Study 2. **Hard exclusions** (decided
from data-quality logs, blind to hypotheses):

1. failed both attention checks;
2. any script-generated input events during the film;
3. free text not typed (keystrokes < 0.2 × characters for texts ≥ 200 characters);
4. erratic input: > 10% of mouse movement events larger than 250 px;
5. disrupted viewing: > 30 s of buffering or > 60 s of interruptions during the film;
6. film coverage < 95% of seconds with playing samples;
7. had seen the film before (self-report).

**Sensitivity analysis** (all confirmatory tests repeated): additionally excluding sparse raters (< 1 rating bout
per minute or a > 180 s stretch without input) and participants who failed one attention check or self-report not
watching attentively; separately, excluding the participants whose submissions were rejected on Prolific for
behaviour on the free-text page but who pass the registered rules.

### Missing data
STICSA items are required, so totals are complete for all completers; sessions without a valid pre or post total
are excluded from H1, H4c, H5 and H6a only. Rating samples missing during interruptions are bridged by interpolation of
film time; sessions failing rule 5 or 6 are excluded.

### Other planned analysis
All of the following are exploratory and will be labelled as such; predictive models will be evaluated with
out-of-sample cross-validation (participant-level folds) and compared against appropriate null/baseline models.

*Rating time series*

- Data-driven segmentation of the confirmatory group mean (same method as above), and change-point / dynamic
  features of individual trajectories (e.g. peak timing, rise slope, recovery, variability).
- Inter-subject correlation of the ratings, response latency (from the practice tracking task), and affect-grid
  occupancy per segment.
- HRF-convolved regressors for the independent fMRI sample; sex-reweighted group means (e.g. to that sample's
  ~2/3 women).

*Free-text narratives (required ≥100-word description)*

- The free-text descriptions will be analysed and reported separately (e.g. language-model ratings of the
  narratives, related to the measured data). Methods are developed only on the exploratory texts (pilot +
  cohort 1). Before any confirmatory text is analysed, the exact procedure (for language models: prompts, model
  name and version, decoding settings, label definitions, output parsing and human validation) will be registered
  as a time-stamped addendum to this registration; later changes will be reported as deviations.

*Individual differences*

- Relations between STICSA (pre, post, change), everyday fear of heights, post-film questions, bodily sensations
  and rating trajectories beyond H4–H6.
- Age and sex (Prolific demographic data): effects on the STICSA change and on the rating time course, including
  interactions with time (e.g. sex × segment and age × segment on segment means, mixed models over the 1 Hz series),
  and group means by sex.

## Other

### Context and additional information
Code, task and QC pipeline: [github.com/embodied-computation-group/vmp-film-rating](https://github.com/embodied-computation-group/vmp-film-rating) (private until
publication; to be released together with the de-identified data on GitHub and/or Zenodo, with a DOI, and
linked from this registration). The exploratory analyses are in `qc/` (segment_film.py,
plot_affect_grid.py, pilot_summary.py, engagement.py). Data format: docs/data.md. Ethics: survey study under the
Aarhus University standard waiver for non-interventional online studies.
