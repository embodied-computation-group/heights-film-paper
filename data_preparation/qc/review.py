"""Fetch results and write a quality-control review.

Usage (from the repo root):
  python qc/review.py                 # fetch JATOS results + Prolific submissions, then review
  python qc/review.py --no-fetch      # review what is already in data/raw
  python qc/review.py --raw tests/out --no-fetch   # review local test runs

Outputs (gitignored; contain Prolific IDs):
  data/raw/jatos_<studyResultId>.ndjson      one file per JATOS study result
  data/raw/prolific_<studyId>.json           Prolific submissions (status, time taken)
  qc/out/qc_report.csv                       one row per session: metrics, verdict, reasons
  qc/out/texts.md                            all free-text answers + feedback, for reading
  qc/out/plots/<pid>_<study>.png             rating trajectory, raw mouse steps, input density
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from qc_lib import FILM_DURATION_S, T, add_duplicate_text_flags, flags, load_session, session_metrics  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
STUDY_UUID = "c4dff945-fbea-45df-9984-2856a87ed904"
PROLIFIC_STUDIES = {
    "pilot_anxiety": "6ac1d73ab02248cd4974b96c",
    "pilot_affect2d": "6ac1d740c40e9350758dd8b4",
    "main_c1": "6ac1ee01e5ff2d1969d03f93",
    "main_c2": "6ac1ee0266279905720bd031",
    "main_c3": "6ac1ee022838bc6b37c30c18",
    "main_c4": "6ac21b0a039963bf6d587ce4",
    "main_c5": "6ac23d7e47e222d973a7d77b",
}


def load_env() -> dict:
    env = {}
    for line in (ROOT / "secrets.env").read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


# ------------------------------------------------------------------------------- fetch ---
def fetch_jatos(raw: Path, env: dict) -> int:
    s = requests.Session()
    s.headers["Authorization"] = f"Bearer {env['JATOS_TOKEN']}"
    s.cookies.set_policy(http.cookiejar.DefaultCookiePolicy(allowed_domains=[]))  # JATOS ignores the token with a cookie
    base = env["JATOS_URL"].rstrip("/") + "/jatos/api/v1"
    md = s.post(f"{base}/results/metadata", json={"studyUuids": [STUDY_UUID]}, timeout=60).json()["data"]
    results = [r for st in md for r in st["studyResults"]]
    for r in results:
        d = s.post(f"{base}/results/data", params={"asPlainText": "true"}, json={"studyResultIds": [r["id"]]}, timeout=120)
        d.raise_for_status()
        (raw / f"jatos_{r['id']}.ndjson").write_text(d.text, encoding="utf8")
        (raw / f"jatos_{r['id']}.meta.json").write_text(json.dumps(r, indent=1), encoding="utf8")
    return len(results)


def fetch_prolific(raw: Path, env: dict) -> pd.DataFrame:
    cli = shutil.which("prolific") or str(ROOT / "bin" / ("prolific.exe" if os.name == "nt" else "prolific"))
    penv = dict(os.environ, PROLIFIC_TOKEN=env.get("PROLIFIC_TOKEN", ""))
    rows = []
    for study, sid in PROLIFIC_STUDIES.items():
        out = subprocess.run([cli, "submission", "list", "-s", sid, "-j"], capture_output=True, text=True,
                             encoding="utf8", env=penv, timeout=120)
        try:
            data = json.loads(out.stdout)
        except json.JSONDecodeError:
            print(f"  could not read Prolific submissions for {study}: {out.stderr.strip()[:200]}")
            continue
        (raw / f"prolific_{sid}.json").write_text(json.dumps(data, indent=1), encoding="utf8")
        subs = data.get("results", data) if isinstance(data, dict) else data
        for x in subs or []:
            rows.append({"prolific_pid": x.get("participant_id") or x.get("participant"),
                         "prolific_status": x.get("status"), "prolific_time_taken_s": x.get("time_taken"),
                         "prolific_submission_id": x.get("id"), "prolific_study": study})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------------- plots ---
def save_fig(fig, path: Path) -> None:
    """Save; if the file is locked (e.g. open in an image viewer on Windows) use a new name instead."""
    try:
        fig.savefig(path, dpi=90)
    except OSError:
        alt = path.with_name(f"{path.stem}_{pd.Timestamp.now():%H%M%S}{path.suffix}")
        fig.savefig(alt, dpi=90)
        print(f"  {path.name} is locked (open elsewhere?) - saved as {alt.name}")
    plt.close(fig)


def plot_session(s, r: dict, out: Path) -> None:
    fs, fi, fe = s.film_samples, s.film_inputs, s.film_events
    fig, ax = plt.subplots(3, 1, figsize=(12, 8), sharex=True, gridspec_kw={"height_ratios": [3, 2, 1]})
    if not fs.empty:
        if s.is2d:
            ax[0].plot(fs["t_stim"], fs["value_x"], lw=1, label="valence (x)")
            ax[0].plot(fs["t_stim"], fs["value_y"], lw=1, label="arousal (y)")
            ax[0].legend(loc="upper right", fontsize=8)
        else:
            ax[0].plot(fs["t_stim"], fs["value"], lw=1, color="C3", label="anxiety")
        notplay = fs[fs["playing"] == 0]
        ax[0].scatter(notplay["t_stim"], np.full(len(notplay), -4), s=2, color="grey", label="not playing")
    if not fe.empty and "e" in fe:
        for _, e in fe[fe["e"].isin(["interrupt", "stall"])].iterrows():
            ax[0].axvline(e["t_stim"], color="red" if e["e"] == "interrupt" else "orange", lw=0.8, alpha=0.7)
    ax[0].set_ylim(-8, 104)
    ax[0].set_ylabel("rating (0-100)")
    ax[0].set_title(f"{r['prolific_pid']}  |  {r['study']}  |  {r['verdict']}", fontsize=10, loc="left")

    mouse = fi[fi["src"] == "m"] if not fi.empty else fi
    if not mouse.empty:
        steps = np.hypot(mouse["dx"].astype(float), mouse["dy"].astype(float))
        ax[1].scatter(mouse["t_stim"], np.maximum(steps, 0.5), s=2, alpha=0.5)
        ax[1].axhline(T["teleport_px"], color="red", lw=0.8, ls="--")
        ax[1].set_yscale("log")
    ax[1].set_ylabel("raw mouse step (px)")

    if not fi.empty:
        bins = np.arange(0, FILM_DURATION_S + 5, 5)
        ax[2].hist(fi["t_stim"].astype(float), bins=bins, color="C0")
    ax[2].set_ylabel("inputs / 5 s")
    ax[2].set_xlabel("film time (s)")
    ax[2].set_xlim(0, FILM_DURATION_S)
    reasons = r["reject_reasons"] + r["review_reasons"]
    if reasons:
        fig.text(0.01, 0.005, "; ".join(reasons)[:220], fontsize=8, color="darkred")
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    save_fig(fig, out)


def plot_overview(sessions, rows, out: Path) -> None:
    """Quick sanity overview per study: every participant's trajectory + mean (not an analysis)."""
    grid = np.arange(0, FILM_DURATION_S, 0.5)
    for study, cols in (("anxiety", ["value"]), ("affect2d", ["value_x", "value_y"])):
        ss = [(s, r) for s, r in zip(sessions, rows) if r["study"] == study and not s.film_samples.empty]
        if not ss:
            continue
        fig, axes = plt.subplots(len(cols), 1, figsize=(12, 3.2 * len(cols)), squeeze=False)
        for ax, col in zip(axes[:, 0], cols):
            curves = []
            for s, r in ss:
                d = s.film_samples[s.film_samples["playing"] == 1].sort_values("t_stim")
                if d.empty or col not in d:
                    continue
                y = np.interp(grid, d["t_stim"].astype(float), d[col].astype(float), left=np.nan, right=np.nan)
                curves.append(y)
                ax.plot(grid, y, lw=0.7, alpha=0.5, label=f"{r['prolific_pid'][:8]} ({r['verdict']})")
            if curves:
                with np.errstate(all="ignore"):
                    ax.plot(grid, np.nanmean(np.vstack(curves), axis=0), color="k", lw=2, label="mean")
            ax.set_ylabel(col)
            ax.set_ylim(-2, 102)
            ax.set_xlim(0, FILM_DURATION_S)
            ax.legend(fontsize=7, loc="upper right", ncol=2)
        axes[-1, 0].set_xlabel("film time (s)")
        axes[0, 0].set_title(f"{study}: n={len(ss)}", loc="left", fontsize=10)
        fig.tight_layout()
        save_fig(fig, out / f"overview_{study}.png")


# -------------------------------------------------------------------------------- main ---
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=str(ROOT / "data" / "raw"))
    ap.add_argument("--out", default=str(ROOT / "qc" / "out"))
    ap.add_argument("--no-fetch", action="store_true")
    ap.add_argument("--include-tests", action="store_true", help="keep sessions with PROLIFIC_PID=TESTPID")
    a = ap.parse_args()
    raw, out = Path(a.raw), Path(a.out)
    raw.mkdir(parents=True, exist_ok=True)
    (out / "plots").mkdir(parents=True, exist_ok=True)

    prol = pd.DataFrame()
    if not a.no_fetch:
        env = load_env()
        print(f"fetched {fetch_jatos(raw, env)} JATOS results")
        prol = fetch_prolific(raw, env)
        print(f"fetched {len(prol)} Prolific submissions")

    files = sorted(p for p in raw.glob("*.ndjson"))
    sessions = [load_session(p) for p in files]
    sessions = [s for s in sessions if s.meta and (a.include_tests or s.pid != "TESTPID" or "tests" in str(raw))]
    if not sessions:
        print("no sessions to review")
        return
    rows = [session_metrics(s) for s in sessions]
    add_duplicate_text_flags(rows)
    for r in rows:
        r["verdict"], r["reject_reasons"], r["review_reasons"] = flags(r)
    for s, r in zip(sessions, rows):
        plot_session(s, r, out / "plots" / f"{r['prolific_pid']}_{r['study']}_{r['file'].split('.')[0]}.png")
    plot_overview(sessions, rows, out)

    df = pd.DataFrame(rows)
    df["reject_reasons"] = df["reject_reasons"].map("; ".join)
    df["review_reasons"] = df["review_reasons"].map("; ".join)
    if not prol.empty:
        df = df.merge(prol, on="prolific_pid", how="left")
    front = ["verdict", "prolific_pid", "study", "prolific_status", "completed", "reject_reasons", "review_reasons"]
    df = df[[c for c in front if c in df] + [c for c in df.columns if c not in front and c not in ("text", "feedback")]]
    df.to_csv(out / "qc_report.csv", index=False)

    with open(out / "texts.md", "w", encoding="utf8") as f:
        for r in rows:
            f.write(f"## {r['prolific_pid']} ({r['study']}) - {r['verdict']}\n\n")
            f.write(f"words={r.get('text_words')} keys/char={r.get('text_keys_per_char')} cpm={r.get('text_cpm')} "
                    f"away={r.get('text_away_s')}s markers={r.get('ai_markers') or '-'} "
                    f"max_similarity={r.get('text_max_similarity')}\n\n")
            f.write((r.get("text") or "(no text)") + "\n\n")
            f.write(f"**Feedback:** {r.get('feedback') or '-'}\n\n")

    show = ["verdict", "prolific_pid", "study", "completed", "att_failed", "coverage", "n_teleports",
            "longest_no_input_s", "sticsa_pre", "sticsa_post", "text_words", "text_keys_per_char"]
    with pd.option_context("display.width", 200, "display.max_columns", 30):
        print(df[[c for c in show if c in df]].to_string(index=False))
    for r in rows:
        if r["reject_reasons"] or r["review_reasons"]:
            print(f"\n{r['prolific_pid']} ({r['study']}) {r['verdict']}")
            for x in r["reject_reasons"]:
                print(f"  REJECT-ELIGIBLE: {x}")
            for x in r["review_reasons"]:
                print(f"  review: {x}")
    print(f"\nwrote {out / 'qc_report.csv'}, {out / 'texts.md'}, plots in {out / 'plots'}")


if __name__ == "__main__":
    main()
