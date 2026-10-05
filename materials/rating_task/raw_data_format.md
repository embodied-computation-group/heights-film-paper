# Data format

Each JATOS study result holds **newline-delimited JSON** (one object per line), appended as the session runs.
Locally (no JATOS) the same lines are downloaded as `vmp_local_<ms>.ndjson` at the end.

| `type` | When | Contents |
|---|---|---|
| `meta` | each page load | IDs (`prolific_pid`, `prolific_study_id`, `prolific_session_id`, `jatos_study_result_id`), `dimension` (`anxiety`/`affect2d`), `study` (1/2), `input_mode`, `user_agent`, `screen`, `config_version`, `n_loads`, `resumed_film_from`, `skipped_to_questions` |
| `chunk` | every 30 s during practice and film, and at the end of each | `tag`, `chunk` index, and the new `samples`, `inputs`, `events` rows since the last chunk (row format, see below) – a crash backup |
| `trial` | as each non-rating trial finishes | `trial`: that trial's data (consent, questionnaires, STICSA, texts…) – survives reloads |
| `final` | end of session (also on exclusion / no consent) | `summary`, `integrity`, `data` (all jsPsych trials of this page load) |

A reloaded session has several `meta` lines and, for the film, trials tagged `film` and `film_resume_<n>`.

Fetch results: JATOS GUI, or `POST /jatos/api/v1/results/data` (see `scripts/deploy_jatos.py` for auth).

## Rating trials (`task` = `practice` or `film`)
Column-wise arrays (`samples`, `inputs`) – each key is a list of equal length.

### `samples` (20 Hz timer)
| column | meaning |
|---|---|
| `t_stim` | stimulus clock (s): `video.currentTime` for the film; for practice, a clock that only runs while unpaused |
| `t_frame` | film only: media time (s) of the last frame actually presented (`requestVideoFrameCallback`); null if unsupported |
| `t_wall` | ms since the trial started (performance clock) |
| `value` | Study 1: rating 0–100 |
| `value_x`, `value_y` | Study 2: valence 0–100 (50 = neutral), arousal 0–100 |
| `playing` | 1 if the stimulus was advancing (film: not paused, not ended, not stalled) |
| `target` / `target_x`, `target_y` | practice only: target position |

Use `t_stim` (or `t_frame`) for alignment to the film/fMRI; drop rows with `playing == 0` or treat them as gaps.

### `inputs` (every input event – the raw, unsmoothed trajectory)
| column | meaning |
|---|---|
| `t_stim`, `t_wall` | as above |
| `value` or `value_x`, `value_y` | value(s) after the event (clamped 0–100) |
| `src` | `m` mouse, `k` key, `s` slider |
| `dx`, `dy` | raw mouse movement in px (unclamped; `movementX/Y`, screen y down), 0 for keys |

### `events`
`{e, t_stim, t_wall, ...}` with `e` in: `can_play` (with `duration`), `arming`, `start` (with `initial_value`),
`playing`, `pause`, `stall` / `stall_end` (buffering), `interrupt` (with `reason`: `hidden`, `fs_exit`,
`pointer_unlock`, `play_rejected`), `resume`, `hidden`/`visible`, `blur`/`focus`, `fs_enter`/`fs_exit`,
`lock`/`unlock`, `seek_blocked`, `video_error`, `ended`, `end`.

### Per-trial scalars
`tag`, `mode` (video/practice), `input_mode`, `axes`, `joystick_px_full_scale`, `start_time`,
`initial_value`, `stimulus_duration`, `n_interruptions`, `interrupted_ms`, `n_stalls`, `stalled_ms`,
`wall_duration_ms`, `n_untrusted_events` (script-generated input events), `max_mouse_step_px` (largest raw mouse
movement in one event), `practice_mae` (practice: 1D mean absolute error or 2D mean Euclidean distance,
excluding 1.5 s after the start and after each step change), `practice_run`, `practice_passed`.

## Other trials (by `task`)
| task | fields |
|---|---|
| `consent` | `consent` (bool), `consent_statements` |
| `browser_check` | jsPsych browser-check fields (browser, mobile, width, height, …) |
| `attention` | `n_checks`, `n_failed`, `attention` ({`attention_1`: bool} / {`attention_2`: bool}); pre-film page also has `pre_film` (`height_fear` 0–6), usability page has `usability` (`distracting`, `difficult` 0–6) |
| `quadrant_practice` (Study 2) | `scenario`, `expected_valence`, `expected_arousal`, `x`, `y`, `correct`, `rt`, `trajectory` [[ms, x, y], …] |
| `post_feelings` | `response`: `anxiety_overall`, `concern_safety`, `body_intensity` (0–6) |
| `post_body` | `response.body_sensations`: list of ticked options |
| `post_mc` | `response`: `seen_before`, `full_attention`, `input_device` |
| `sticsa` | `timepoint` (`pre`/`post`), `items` [{`item` (original STICSA number), `text`, `response` 1–4 or null}], `n_answered`, `total` (11–44, null unless all 11 answered), `onset`, `completion` (ISO timestamps), `duration_ms`; post also `pre_total`, `change` (post − pre or null); raw form values in `response` (`sticsa_<n>`) |
| `final_text` | `text`, `n_words`, `n_chars`, `n_keys` (keystrokes), `away_ms` (time unfocused while writing) |
| `feedback` | `response.feedback` |

Likert responses are 0-based indices (0 = leftmost label).

## `summary` (in the `final` line)
`attention_checks_failed` / `_total`, `practice_mae_last`, `quadrant_correct` / `_total`,
`film_interruptions`, `film_stalled_ms`, `film_untrusted_events`, `film_max_mouse_step_px`, `sticsa_pre_total`, `sticsa_post_total`, `sticsa_change`, `final_text_words`, `final_text_keystrokes`, `final_text_away_ms`,
`paste_blocked`, `drop_blocked`, `copy_blocked`, `n_window_blur`, `n_page_hidden`, `away_ms_total`.

## `integrity` (in the `final` line)
Counters as in the summary plus `events`: `{e, t (s since page load), task}` for every blur/focus,
hidden/visible, and blocked paste/drop/copy across the whole session (capped at 2000).
