# qc/ – data-quality checks

Quick, practical checks for incoming data: is each session complete, attentive, and human? Full analysis
(time-series plotting, group means, fMRI regressors, summaries) belongs in the separate analysis repository;
`qc_lib.load_session` plus [raw_data_format.md](../../materials/rating_task/raw_data_format.md) document how to read the raw format there.

```bash
python qc/review.py              # fetch JATOS results + Prolific submissions into data/raw/, then review
python qc/review.py --no-fetch   # re-review what is already downloaded
python qc/pilot_summary.py       # descriptive summary: timing, usability, questionnaires, time series
python qc/plot_sticsa.py         # pre vs post STICSA somatic (totals + per item)
python qc/plot_affect_grid.py    # 2D grid: smoothed occupancy + extreme points; mean path; per-segment maps (after segment_film.py)
python qc/plot_group_timeseries.py  # 2D arm: group mean + 95% CI (exploratory default; --confirmatory)
python qc/segment_film.py        # exploratory: film segments from group-mean arousal (piecewise-linear DP, BIC, bootstrap CIs)
python tests/test_qc.py          # synthetic human-vs-scripted check of the flags
```
Outputs (gitignored, contain Prolific IDs): `qc/out/qc_report.csv`, `qc/out/texts.md`,
`qc/out/plots/<pid>_<study>_*.png` (rating trajectory with interruptions/stalls, raw mouse step sizes on a log
scale with the teleport line, input density), `qc/out/overview_<study>.png` (all trajectories + mean, sanity only).

## Verdicts (advisory – you decide)
**REJECT-ELIGIBLE** – objective evidence the participant broke the study terms (Prolific requires clear evidence;
the task is off-platform, so the evidence is ours – keep the plot/report row when rejecting):
- failed both attention checks
- script-generated input events during the film (`isTrusted == false`)
- free text not typed: far fewer keystrokes than characters (paste is blocked, so text must have been injected)

**REVIEW** – look at the plot / text before deciding; usually exclusion (pay) rather than rejection:
- automation patterns: repeated mouse jumps > 250 px ("teleporting"); long runs of identical mouse steps
  (constant-velocity scripting); no off-axis jitter (perfectly vertical moves – human hands always wobble)
- text: implausibly fast typing, LLM-style phrasing markers, near-duplicate of another participant, paste attempts
- engagement: one failed attention check, film coverage < 95%, many/long interruptions, long stretch with no
  rating input, lots of time away from the window, poor practice/quadrant performance, seen the film before,
  self-reported inattention, page reloads, incomplete session

Thresholds are in `qc_lib.T`; LLM phrasing markers in `qc_lib.AI_MARKERS` (a hit is a reason to read, not proof).
Note: browser-automation tools that drive a real browser produce "trusted" events; judge those by the movement
patterns in the plot (straight lines, identical steps, jumps, ratings that never react to the film).
