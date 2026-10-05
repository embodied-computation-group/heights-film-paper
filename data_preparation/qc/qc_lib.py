"""Quality-control library: parse result files and compute per-session QC metrics and flags.

Scope: checking data quality (attention, engagement, AI/automation signals). Time-series analysis,
group means and fMRI regressors belong in the separate analysis repository; the parsing here
(`load_session`) documents how to read the raw format (see docs/data.md).

A result file is newline-delimited JSON as written by task/js/experiment.js (JATOS result data, or the
NDJSON downloaded in local mode). Rating data are rebuilt from `chunk` lines, which survive reloads;
questionnaires come from `trial` lines (also reload-safe) and the `final` line when present.
"""
from __future__ import annotations

import difflib
import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

FILM_DURATION_S = 808.9

# Exploratory vs confirmatory samples (docs/preregistration.md). Exploratory = pilot + main-run cohort 1; every
# later Prolific study is confirmatory. Exploratory scripts default to the exploratory sample so confirmatory data
# are not looked at before the registered analysis; pass --confirmatory or --all explicitly to change that.
EXPLORATORY_STUDIES = {
    "6ac1d73ab02248cd4974b96c",  # pilot, Study 1 (anxiety)
    "6ac1d740c40e9350758dd8b4",  # pilot, Study 2 (affect2d)
    "6ac1ee01e5ff2d1969d03f93",  # main run cohort 1
}


def scope_filter(rep, argv=None):
    """Restrict a qc_report DataFrame to the requested sample: exploratory (default), --confirmatory or --all."""
    import sys as _sys
    argv = _sys.argv if argv is None else argv
    if "--all" in argv:
        return rep
    if "prolific_study_id" not in rep:
        raise SystemExit("qc_report.csv lacks prolific_study_id - rerun qc/review.py")
    expl = rep["prolific_study_id"].isin(EXPLORATORY_STUDIES)
    real = rep["prolific_study_id"].fillna("").str.fullmatch(r"[0-9a-f]{24}")  # drops local/test sessions
    return rep[real & ~expl] if "--confirmatory" in argv else rep[expl]

# ---------------------------------------------------------------- thresholds (advisory) ---
T = {
    "teleport_px": 250,  # single raw mouse event larger than this ...
    "teleport_isolation_ms": 100,  # ... with no other mouse event within this time either side = "teleport"
    "stalled_s_review": 30,  # total buffering time during the film
    "teleport_count_review": 3,
    "identical_run_review": 30,  # consecutive identical (dx, dy) mouse deltas ...
    "identical_min_px": 3,  # ... counting only steps of at least this size (slow hands give runs of 1-2 px steps)
    "big_step_frac_review": 0.10,  # > this fraction of film mouse steps > teleport_px: erratic input. Cause unknown
                                   # (cohort 1 case practised normally, so not simply an incompatible device)
    "pure_axis_review": 0.98,  # fraction of moving events with an exactly-zero off-axis component
    "pure_axis_min_events": 200,
    "coverage_min": 0.95,  # fraction of the film with playing samples
    "interruptions_review": 3,
    "interrupted_s_review": 60,
    "no_input_s_review": 180,  # longest stretch of film without any rating input
    "away_s_review": 120,  # total time the window was unfocused/hidden
    "practice_mae_review": 15,  # after the repeat; 2D threshold is 20
    "practice_err2d_review": 20,
    "quadrant_min": 3,  # of 6
    "text_keys_per_char_reject": 0.2,  # typed far fewer keys than characters -> text was inserted
    "text_min_chars_for_key_check": 200,
    "typing_cpm_review": 700,  # characters per minute over the whole text page
    "ai_markers_review": 2,
    "duplicate_text_ratio": 0.8,
}

# Phrases/characters that are common in LLM output and rare in quick participant prose. Advisory only:
# a hit is a reason to read the text, never evidence by itself.
AI_MARKERS = [
    r"\bdelve\b", r"\btapestry\b", r"\bnavigat(e|ing) the\b", r"\btestament to\b", r"\bin conclusion\b",
    r"\boverall,", r"\bit'?s worth noting\b", r"\bas an ai\b", r"\blanguage model\b", r"\bvisceral\b",
    r"\bpalpable\b", r"\bjuxtapos", r"\bunderscore[sd]?\b", r"\ba sense of (awe|unease|vertigo)\b",
    r"\bheightened sense\b", r"\bmultifaceted\b", r"—",
]


@dataclass
class Session:
    path: Path
    meta: list[dict] = field(default_factory=list)
    trials: list[dict] = field(default_factory=list)  # questionnaire etc. (deduplicated)
    final: dict | None = None
    film_samples: pd.DataFrame | None = None
    film_inputs: pd.DataFrame | None = None
    film_events: pd.DataFrame | None = None
    practice: list[dict] = field(default_factory=list)  # practice trial dicts (scalars only)

    @property
    def m(self) -> dict:
        return self.meta[-1] if self.meta else {}

    @property
    def pid(self) -> str:
        return self.m.get("prolific_pid") or "?"

    @property
    def dimension(self) -> str:
        return self.m.get("dimension") or "?"

    @property
    def is2d(self) -> bool:
        return self.dimension == "affect2d"

    def trial(self, task: str, **kw) -> list[dict]:
        out = [t for t in self.trials if t.get("task") == task]
        for k, v in kw.items():
            out = [t for t in out if t.get(k) == v]
        return out


def _rows_to_df(rows: list[list], cols: list[str]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=cols)
    n = len(cols)
    return pd.DataFrame([(list(r) + [None] * n)[:n] for r in rows], columns=cols)


def load_session(path: str | Path) -> Session:
    path = Path(path)
    s = Session(path)
    chunks = []
    trial_lines = []
    for line in path.read_text(encoding="utf8").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        typ = obj.get("type")
        if typ == "meta":
            s.meta.append(obj)
        elif typ == "chunk":
            chunks.append(obj)
        elif typ == "trial":
            trial_lines.append(obj["trial"])
        elif typ == "final":
            s.final = obj

    # Questionnaire/other trials: `trial` lines (all page loads) + final data of the last load, deduplicated.
    seen = set()
    final_trials = (s.final or {}).get("data", [])
    for t in trial_lines + [t for t in final_trials if t.get("task") not in ("film", "practice")]:
        key = (t.get("task"), t.get("time_elapsed"), t.get("trial_index"), json.dumps(t.get("response"), sort_keys=True, default=str))
        if key in seen:
            continue
        seen.add(key)
        s.trials.append(t)
    s.practice = [{k: v for k, v in t.items() if k not in ("samples", "inputs", "events")}
                  for t in final_trials if t.get("task") == "practice"]

    # Film rating data from chunks (tags "film", "film_resume_<n>").
    is2d = s.is2d
    vcols = ["value_x", "value_y"] if is2d else ["value"]
    scols = ["t_stim", "t_frame", "t_wall", *vcols, "playing"]
    icols = ["t_stim", "t_wall", *vcols, "src", "dx", "dy"]
    samp, inp, ev = [], [], []
    for c in sorted(chunks, key=lambda c: (c.get("t", ""), c.get("chunk", 0))):
        tag = c.get("tag", "")
        if not tag.startswith("film"):
            continue
        for row in c.get("samples", []):
            if len(row) == len(scols) - 1:  # files from before t_frame was recorded
                row = [row[0], None, *row[1:]]
            samp.append([*row, tag])
        inp += [[*r, tag] for r in c.get("inputs", [])]
        ev += [{**e, "segment": tag} for e in c.get("events", [])]
    s.film_samples = _rows_to_df([r[:-1] for r in samp], scols).assign(segment=[r[-1] for r in samp]) if samp else _rows_to_df([], scols)
    s.film_inputs = _rows_to_df([r[:-1] for r in inp], icols).assign(segment=[r[-1] for r in inp]) if inp else _rows_to_df([], icols)
    s.film_events = pd.DataFrame(ev)
    return s


# ------------------------------------------------------------------------------ metrics ---
def _longest_identical_run(dx: np.ndarray, dy: np.ndarray, min_px: float = 0) -> int:
    best = run = 0
    prev = None
    for a, b in zip(dx, dy):
        cur = (a, b)
        big_enough = math.hypot(a, b) >= max(min_px, 1e-9)
        if big_enough and cur == prev:
            run += 1
        else:
            run = 1 if big_enough else 0
        best = max(best, run)
        prev = cur
    return best


def _longest_no_input(inputs: pd.DataFrame, samples: pd.DataFrame) -> float:
    """Longest stretch of film time (s) without any rating input, while the film was playing."""
    if samples.empty:
        return float("nan")
    play = samples.loc[samples["playing"] == 1, "t_stim"]
    if play.empty:
        return float("nan")
    times = np.sort(np.concatenate([[play.min()], inputs["t_stim"].to_numpy(dtype=float), [play.max()]]))
    return float(np.max(np.diff(times))) if len(times) > 1 else float("nan")


def _paired_s(events: pd.DataFrame, start_e: str, end_es: tuple) -> float:
    """Total wall time (s) from each `start_e` event to the next end event, within each segment."""
    if events.empty or "e" not in events:
        return 0.0
    total = 0.0
    for _, seg in events.groupby("segment", sort=False):
        start = None
        for e, t in zip(seg["e"], seg["t_wall"]):
            if e == start_e and start is None:
                start = t
            elif e in end_es and start is not None:
                total += (t - start) / 1000
                start = None
    return total


def _interrupted_s(events: pd.DataFrame) -> float:
    """Total wall time between each `interrupt` and the next `resume` (or segment end), all segments."""
    if events.empty or "e" not in events:
        return 0.0
    total = 0.0
    for _, seg in events.groupby("segment", sort=False):
        start = None
        for e, t in zip(seg["e"], seg["t_wall"]):
            if e == "interrupt" and start is None:
                start = t
            elif e in ("resume", "end") and start is not None:
                total += (t - start) / 1000
                start = None
    return total


def _coverage(samples: pd.DataFrame) -> float:
    if samples.empty:
        return 0.0
    t = samples.loc[samples["playing"] == 1, "t_stim"].to_numpy(dtype=float)
    if t.size == 0:
        return 0.0
    covered = np.unique(np.floor(t)).size  # seconds of film with at least one playing sample
    return min(1.0, covered / math.floor(FILM_DURATION_S))


def ai_marker_hits(text: str) -> list[str]:
    tl = text.lower()
    return [m for m in AI_MARKERS if re.search(m, tl)]


def session_metrics(s: Session) -> dict:
    sm = (s.final or {}).get("summary", {}) or {}
    integ = (s.final or {}).get("integrity", {}) or {}
    r: dict = {
        "file": s.path.name,
        "prolific_pid": s.pid,
        "study": s.dimension,
        "jatos_id": s.m.get("jatos_study_result_id"),
        "prolific_study_id": s.m.get("prolific_study_id"),
        "n_loads": max([m.get("n_loads") or 1 for m in s.meta] or [1]),
        "completed": any(t.get("task") == "end" for t in s.trials),
        "consent": next((t.get("consent") for t in s.trials if t.get("task") == "consent"), None),
    }

    # attention
    att = s.trial("attention")
    r["att_failed"] = sum(t.get("n_failed", 0) for t in att)
    r["att_total"] = sum(t.get("n_checks", 0) for t in att)

    # practice / quadrant
    pm = [p.get("practice_mae") for p in s.practice if p.get("practice_mae") is not None]
    r["practice_runs"] = len(s.practice)
    r["practice_err_last"] = pm[-1] if pm else sm.get("practice_mae_last")
    quad = s.trial("quadrant_practice")
    r["quadrant_correct"] = sum(bool(q.get("correct")) for q in quad) if quad else None

    # film coverage / interruptions
    fs, fi, fe = s.film_samples, s.film_inputs, s.film_events
    r["coverage"] = round(_coverage(fs), 3)
    evn = fe["e"] if not fe.empty and "e" in fe else pd.Series(dtype=str)
    r["n_interruptions"] = int((evn == "interrupt").sum())
    r["n_stalls"] = int((evn == "stall").sum())
    r["stalled_s"] = round(_paired_s(fe, "stall", ("stall_end", "end")), 1)
    r["interrupted_s"] = round(_interrupted_s(fe), 1)
    r["away_s_total"] = round(integ.get("away_ms", sm.get("away_ms_total", 0) or 0) / 1000, 1) if (integ or sm) else None
    r["n_blur"] = integ.get("n_blur", sm.get("n_window_blur"))
    r["n_hidden"] = integ.get("n_hidden", sm.get("n_page_hidden"))

    # rating engagement
    r["n_inputs"] = len(fi)
    r["longest_no_input_s"] = round(_longest_no_input(fi, fs), 1)
    vcol = "value_y" if s.is2d else "value"
    if not fs.empty:
        v = fs.loc[fs["playing"] == 1, vcol].astype(float)
        r["value_sd"] = round(float(v.std()), 2) if len(v) > 1 else None
        r["frac_at_bounds"] = round(float(((v <= 0) | (v >= 100)).mean()), 3) if len(v) else None
        if s.is2d:
            vx = fs.loc[fs["playing"] == 1, "value_x"].astype(float)
            r["valence_sd"] = round(float(vx.std()), 2) if len(vx) > 1 else None

    # mouse automation signals (raw, unclamped deltas)
    mouse = fi[fi["src"] == "m"] if not fi.empty else fi
    dx = mouse["dx"].to_numpy(dtype=float) if not mouse.empty else np.array([])
    dy = mouse["dy"].to_numpy(dtype=float) if not mouse.empty else np.array([])
    steps = np.hypot(dx, dy)
    r["n_mouse_events"] = int(steps.size)
    r["frac_key_inputs"] = round(float((fi["src"] == "k").mean()), 3) if len(fi) else None
    r["max_step_px"] = int(steps.max()) if steps.size else 0
    # Teleport = a large step that is isolated in time. Fast human flicks are large too, but come in dense bursts.
    r["n_big_steps"] = int((steps > T["teleport_px"]).sum())
    if steps.size:
        tw = mouse["t_wall"].to_numpy(dtype=float)
        gap_prev = np.diff(tw, prepend=-np.inf)
        gap_next = np.diff(tw, append=np.inf)
        iso = (gap_prev > T["teleport_isolation_ms"]) & (gap_next > T["teleport_isolation_ms"])
        r["n_teleports"] = int(((steps > T["teleport_px"]) & iso).sum())
    else:
        r["n_teleports"] = 0
    r["identical_run_max"] = _longest_identical_run(dx, dy, T["identical_min_px"])
    r["frac_big_steps"] = round(float((steps > T["teleport_px"]).mean()), 3) if steps.size else None
    if steps.size:
        moving = steps > 0
        off = (dx == 0) if not s.is2d else ((dx == 0) | (dy == 0))
        r["frac_pure_axis"] = round(float(off[moving].mean()), 3) if moving.any() else None
    else:
        r["frac_pure_axis"] = None
    r["untrusted_events"] = sm.get("film_untrusted_events")

    # STICSA
    for tp in ("pre", "post"):
        st = s.trial("sticsa", timepoint=tp)
        r[f"sticsa_{tp}"] = st[-1].get("total") if st else None
        r[f"sticsa_{tp}_straightline"] = (len({i["response"] for i in st[-1]["items"]}) == 1) if st else None
    r["sticsa_change"] = (r["sticsa_post"] - r["sticsa_pre"]) if None not in (r["sticsa_pre"], r["sticsa_post"]) else None

    # post questions
    pf = s.trial("post_feelings")
    if pf:
        r.update({f"q_{k}": v for k, v in (pf[-1].get("response") or {}).items()})
    us = [t for t in s.trials if t.get("usability")]
    if us:
        r.update({f"q_{k}": v for k, v in us[-1]["usability"].items()})
    mc = s.trial("post_mc")
    if mc:
        r.update({f"q_{k}": v for k, v in (mc[-1].get("response") or {}).items()})

    # free text
    ft = s.trial("final_text")
    text = ft[-1].get("text", "") if ft else ""
    r["text"] = text
    r["text_words"] = ft[-1].get("n_words") if ft else None
    r["text_chars"] = ft[-1].get("n_chars", len(text)) if ft else None
    r["text_keys"] = ft[-1].get("n_keys") if ft else None
    r["text_keys_per_char"] = (round(r["text_keys"] / r["text_chars"], 2)
                               if ft and r["text_chars"] and r["text_keys"] is not None else None)
    rt_min = (ft[-1].get("rt") or 0) / 60000 if ft else 0
    r["text_cpm"] = round(r["text_chars"] / rt_min) if ft and rt_min > 0 else None
    r["text_away_s"] = round((ft[-1].get("away_ms") or 0) / 1000, 1) if ft else None
    r["text_input_types"] = json.dumps(ft[-1].get("input_types")) if ft and ft[-1].get("input_types") else ""
    tev = [e for e in integ.get("events", []) if e.get("task") == "final_text"]
    r["text_paste_drop_attempts"] = sum(e.get("e") in ("paste_blocked", "drop_blocked", "insert_blocked") for e in tev)
    r["paste_blocked"] = integ.get("paste_blocked", sm.get("paste_blocked"))
    r["copy_blocked"] = integ.get("copy_blocked", sm.get("copy_blocked"))
    r["ai_markers"] = ";".join(ai_marker_hits(text)) if text else ""
    fb = s.trial("feedback")
    r["feedback"] = ((fb[-1].get("response") or {}).get("feedback") or "") if fb else ""
    return r


def add_duplicate_text_flags(rows: list[dict]) -> None:
    for i, a in enumerate(rows):
        best, who = 0.0, None
        for j, b in enumerate(rows):
            if i == j or not a.get("text") or not b.get("text"):
                continue
            ratio = difflib.SequenceMatcher(None, a["text"].lower(), b["text"].lower()).ratio()
            if ratio > best:
                best, who = ratio, b.get("prolific_pid")
        a["text_max_similarity"] = round(best, 2)
        a["text_most_similar_to"] = who if best >= T["duplicate_text_ratio"] else ""


def flags(r: dict) -> tuple[str, list[str], list[str]]:
    """Return (verdict, reject_reasons, review_reasons). Verdicts are advisory."""
    rej, rev = [], []
    # Objective evidence (Prolific: rejection needs clear evidence the terms were broken)
    if r.get("att_failed", 0) >= 2:
        rej.append("failed both attention checks")
    if (r.get("untrusted_events") or 0) > 0:
        rej.append(f"{r['untrusted_events']} script-generated input events")
    if (r.get("text_chars") or 0) >= T["text_min_chars_for_key_check"] and r.get("text_keys_per_char") is not None \
            and r["text_keys_per_char"] < T["text_keys_per_char_reject"]:
        msg = f"text not typed ({r['text_keys']} keystrokes for {r['text_chars']} characters)"
        outside = (r.get("text_paste_drop_attempts") or 0) > 0 or (r.get("text_away_s") or 0) > 10
        if outside:  # inserted from elsewhere after blocked paste/drop attempts or time in another window
            rej.append(msg + " after paste/drop attempts or time away")
        else:  # e.g. voice dictation / IME: the participant's own words, no evidence of misconduct
            rev.append(msg + " - no paste attempts or time away: possibly dictation; check input types/text")
    # Patterns that need a human look (automation)
    if r.get("n_teleports", 0) >= T["teleport_count_review"]:
        rev.append(f"{r['n_teleports']} isolated mouse jumps > {T['teleport_px']} px")
    if (r.get("frac_big_steps") or 0) > T["big_step_frac_review"] and r.get("n_mouse_events", 0) >= 50:
        rev.append(f"erratic input: {r['frac_big_steps']:.0%} of mouse steps > {T['teleport_px']} px - inspect the "
                   "rating trace; likely exclusion, not evidence of misconduct")
    if r.get("identical_run_max", 0) >= T["identical_run_review"]:
        rev.append(f"{r['identical_run_max']} identical mouse steps in a row")
    if (r.get("frac_pure_axis") or 0) >= T["pure_axis_review"] and r.get("n_mouse_events", 0) >= T["pure_axis_min_events"]:
        rev.append(f"no off-axis mouse jitter ({r['frac_pure_axis']:.0%} pure-axis moves)")
    if (r.get("text_cpm") or 0) > T["typing_cpm_review"]:
        rev.append(f"very fast text ({r['text_cpm']} chars/min)")
    hits = [h for h in (r.get("ai_markers") or "").split(";") if h]
    if len(hits) >= T["ai_markers_review"]:
        rev.append(f"LLM-style phrasing ({len(hits)} markers)")
    if r.get("text_most_similar_to"):
        rev.append(f"text {r['text_max_similarity']:.0%} similar to {r['text_most_similar_to']}")
    if (r.get("paste_blocked") or 0) > 0 or (r.get("copy_blocked") or 0) > 0:
        rev.append(f"{r.get('copy_blocked') or 0} copy / {r.get('paste_blocked') or 0} paste attempts (blocked)"
                   + (f", {r['text_away_s']:.0f} s away while writing" if (r.get("text_away_s") or 0) > 10 else ""))
    # Engagement / attention (exclusion candidates, not rejection)
    if r.get("att_failed") == 1:
        rev.append("failed 1 attention check")
    if r.get("coverage", 1) < T["coverage_min"]:
        rev.append(f"film coverage {r['coverage']:.0%}")
    if r.get("n_interruptions", 0) > T["interruptions_review"] or (r.get("interrupted_s") or 0) > T["interrupted_s_review"]:
        rev.append(f"{r['n_interruptions']} interruptions ({r.get('interrupted_s')} s)")
    if (r.get("stalled_s") or 0) > T["stalled_s_review"]:
        rev.append(f"film buffered {r['stalled_s']:.0f} s ({r['n_stalls']} stalls)")
    if (r.get("longest_no_input_s") or 0) > T["no_input_s_review"]:
        rev.append(f"no rating input for {r['longest_no_input_s']:.0f} s")
    if (r.get("away_s_total") or 0) > T["away_s_review"]:
        rev.append(f"away from the window {r['away_s_total']:.0f} s")
    thr = T["practice_err2d_review"] if r.get("study") == "affect2d" else T["practice_mae_review"]
    if r.get("practice_err_last") is not None and r["practice_err_last"] > thr:
        rev.append(f"practice error {r['practice_err_last']} after {r['practice_runs']} runs")
    if r.get("quadrant_correct") is not None and r["quadrant_correct"] < T["quadrant_min"]:
        rev.append(f"quadrant practice {r['quadrant_correct']}/6")
    if r.get("q_seen_before") == "Yes":
        rev.append("had seen the film")
    if r.get("q_full_attention") == "No":
        rev.append("reports not watching attentively")
    if r.get("n_loads", 1) > 1:
        rev.append(f"{r['n_loads']} page loads")
    if not r.get("completed"):
        rev.append("did not complete")
    verdict = "REJECT-ELIGIBLE" if rej else ("REVIEW" if rev else "OK")
    return verdict, rej, rev


def prereg_hard_exclusion(r) -> str:
    """Preregistered hard exclusions (docs/preregistration.md, 'Data inclusion and exclusion', rules 1-7), applied
    exactly as written. Returns '' if included, else the reasons. Takes a qc_report row (dict or Series)."""
    g = (lambda k: r.get(k)) if hasattr(r, "get") else (lambda k: getattr(r, k, None))
    num = lambda k: (g(k) if g(k) is not None and g(k) == g(k) else 0)  # noqa: E731  (NaN -> 0)
    w = []
    if num("att_failed") >= 2:
        w.append("both attention checks failed")
    if num("untrusted_events") > 0:
        w.append("script-generated input")
    kpc = g("text_keys_per_char")
    if kpc is not None and kpc == kpc and num("text_chars") >= 200 and kpc < 0.2:
        w.append("free text not typed")
    if num("frac_big_steps") > 0.10:
        w.append("erratic input")
    if num("stalled_s") > 30 or num("interrupted_s") > 60:
        w.append("disrupted viewing")
    if num("coverage") < 0.95:
        w.append("film coverage < 95%")
    if g("q_seen_before") == "Yes":
        w.append("seen the film before")
    return "; ".join(w)
