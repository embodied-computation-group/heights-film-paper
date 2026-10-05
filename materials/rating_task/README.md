# The rating task as used in this study

A frozen copy of the browser task and study settings exactly as participants saw them, so the format of the
rating platform used for these data is preserved even as the general tool changes. The general, maintained tool
is [online-affect-rating](https://github.com/embodied-computation-group/online-affect-rating); its tag
`v1.0-heights-film` is the same code.

Copied on 2026-10-05 from commit `13e786a` of the private tooling repository (vmp_film_rating); the task code
there was last changed in `ef3cada` (2026-10-04 13:26 CEST), the version deployed for the end of data collection.

| file | what it is |
|---|---|
| `task/` | the jsPsych 8 task (run on JATOS/MindProbe). `?dim=affect2d` is the valence x arousal arm used in the paper; `?dim=anxiety` is the 1D arm, piloted only |
| `task/js/texts.js` | all participant-facing text: information sheet, consent, instructions, questionnaires, debrief |
| `task/js/config.js` | timing, sampling rate (20 Hz), attention checks, Prolific completion links |
| `prolific/` | Prolific study settings (description, payment, time limit, device) and participant filters |
| `encode_film.sh` | how the film was re-encoded for web delivery (CRF 29 from the main run on) |
| `design.md` | the study design as run |
| `raw_data_format.md` | the format of the raw result files the task writes |
| `img/` | screenshots of the rating screens and the encoding comparison |

The film itself is a third-party video and is not included (see the manuscript's Data Availability Statement).
To try the task locally, serve this folder (e.g. `python -m http.server`) and open
`task/index.html?dim=affect2d&reset=1` with a copy of the film; see the general tool for full instructions.

## Changes to the task during data collection

From the tooling repository's history (commit messages). None changed the rating screen, the affect grid or the
sampling of ratings.

- `079ee57` (2026-10-04 09:02): participants whose connection could not download the film within 5 min were asked to
  return the study (code `VMPSLOWD`); deployed after cohort 1 finished, before cohort 2.
- `ef3cada` (2026-10-04 13:26): a failed film download also ends in that return path; text input types are logged.

Deployment times are not recorded in git; which cohorts ran which version follows the order above.
