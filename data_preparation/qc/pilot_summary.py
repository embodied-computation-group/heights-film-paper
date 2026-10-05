"""Descriptive summary of collected sessions (pilot sanity check, not the analysis).

Run after qc/review.py (uses data/raw and qc/out/qc_report.csv):
  python qc/pilot_summary.py
Writes qc/out/summary.md and qc/out/summary_timeseries.png.
"""
from __future__ import annotations

import sys
from itertools import combinations
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from qc_lib import FILM_DURATION_S, load_session, scope_filter  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW, OUT = ROOT / "data" / "raw", ROOT / "qc" / "out"
GRID = np.arange(0, np.floor(FILM_DURATION_S), 1.0)  # 1 Hz film-time grid


def resample(s, col: str) -> np.ndarray:
    d = s.film_samples[s.film_samples["playing"] == 1].sort_values("t_stim")
    if d.empty:
        return np.full(GRID.size, np.nan)
    return np.interp(GRID, d["t_stim"].astype(float), d[col].astype(float), left=np.nan, right=np.nan)


def pairwise_r(curves: list[np.ndarray]) -> tuple[float, list[float]]:
    rs = []
    for a, b in combinations(curves, 2):
        m = ~np.isnan(a) & ~np.isnan(b)
        if m.sum() > 10 and a[m].std() > 0 and b[m].std() > 0:
            rs.append(float(np.corrcoef(a[m], b[m])[0, 1]))
    return (float(np.mean(rs)) if rs else float("nan")), rs


def loo_r(curves: list[np.ndarray]) -> list[float]:
    out = []
    for i, c in enumerate(curves):
        others = np.nanmean(np.vstack([x for j, x in enumerate(curves) if j != i]), axis=0)
        m = ~np.isnan(c) & ~np.isnan(others)
        out.append(float(np.corrcoef(c[m], others[m])[0, 1]) if m.sum() > 10 and c[m].std() > 0 and others[m].std() > 0 else float("nan"))
    return out


def main() -> None:
    rep = pd.read_csv(OUT / "qc_report.csv")
    rep = scope_filter(rep)  # exploratory sample unless --confirmatory / --all
    done = rep[(rep["completed"] == True) & (rep["verdict"] != "REJECT-ELIGIBLE")]  # noqa: E712
    sessions = {}
    for p in sorted(RAW.glob("*.ndjson")):
        s = load_session(p)
        if s.meta and s.pid in set(done["prolific_pid"]):
            sessions[s.pid] = s

    md = ["# Summary of completed sessions (descriptive)\n"]
    md.append(f"Completed, non-rejected sessions: {len(done)} "
              f"({', '.join(f'{k}: {v}' for k, v in done['study'].value_counts().items())})\n")

    # timing + usability + questionnaires (Likert indices 0-6 shown as 1-7)
    t = done.assign(minutes=(done["prolific_time_taken_s"] / 60).round(1))
    cols = {"minutes": "minutes", "q_distracting": "distracting (1-7)", "q_difficult": "difficult (1-7)",
            "q_anxiety_overall": "overall anxious (1-7)", "q_concern_safety": "concern for safety (1-7)",
            "q_body_intensity": "bodily sensations (1-7)", "sticsa_pre": "STICSA pre", "sticsa_post": "STICSA post",
            "sticsa_change": "STICSA change"}
    tab = t[["study"] + [c for c in cols if c in t]].copy()
    for c in ("q_distracting", "q_difficult", "q_anxiety_overall", "q_concern_safety", "q_body_intensity"):
        if c in tab:
            tab[c] = tab[c] + 1
    agg = tab.groupby("study").agg(["mean", "min", "max"]).round(1)
    md.append("## Timing, usability, questionnaires (mean [min-max])\n")
    md.append("| measure | " + " | ".join(agg.index) + " |\n|---|" + "---|" * len(agg.index))
    for c in [c for c in cols if c in tab]:
        md.append(f"| {cols[c]} | " + " | ".join(
            f"{agg.loc[st, (c, 'mean')]} [{agg.loc[st, (c, 'min')]}-{agg.loc[st, (c, 'max')]}]" for st in agg.index) + " |")
    md.append(f"\nOverall median completion time: {t['minutes'].median():.1f} min.\n")

    # bodily sensations
    body = {}
    for s in sessions.values():
        for tr in s.trial("post_body"):
            for opt in (tr.get("response") or {}).get("body_sensations", []):
                body[opt] = body.get(opt, 0) + 1
    if body:
        md.append("## Bodily sensations reported (count of participants)\n")
        md += [f"- {k}: {v}" for k, v in sorted(body.items(), key=lambda kv: -kv[1])]
        md.append("")

    # time series
    series = {"anxiety": [], "valence": [], "arousal": []}
    for s in sessions.values():
        if s.dimension == "anxiety":
            series["anxiety"].append(resample(s, "value"))
        elif s.dimension == "affect2d":
            series["valence"].append(resample(s, "value_x"))
            series["arousal"].append(resample(s, "value_y"))
    md.append("## Rating time series (1 Hz, film time)\n")
    md.append("| series | n | mean pairwise r | leave-one-out r (each rater vs mean of others) |\n|---|---|---|---|")
    means = {}
    for k, cs in series.items():
        if not cs:
            continue
        means[k] = np.nanmean(np.vstack(cs), axis=0)
        mr, _ = pairwise_r(cs)
        md.append(f"| {k} | {len(cs)} | {mr:.2f} | {', '.join(f'{x:.2f}' for x in loo_r(cs))} |")
    md.append("")
    if len(means) > 1:
        md.append("Correlation between group-mean curves (1 Hz; autocorrelated, descriptive only):\n")
        for a, b in combinations(means, 2):
            m = ~np.isnan(means[a]) & ~np.isnan(means[b])
            md.append(f"- {a} vs {b}: r = {np.corrcoef(means[a][m], means[b][m])[0, 1]:.2f}")
        md.append("")

    fig, axes = plt.subplots(len(means), 1, figsize=(12, 2.8 * len(means)), sharex=True, squeeze=False)
    colors = {"anxiety": "C3", "valence": "C0", "arousal": "C1"}
    for ax, (k, mu) in zip(axes[:, 0], means.items()):
        for c in series[k]:
            ax.plot(GRID, c, color=colors[k], lw=0.6, alpha=0.4)
        ax.plot(GRID, mu, color=colors[k], lw=2.2, label=f"{k} mean (n={len(series[k])})")
        ax.set_ylim(-2, 102)
        ax.set_ylabel(k)
        ax.legend(loc="upper left", fontsize=8)
    axes[-1, 0].set_xlabel("film time (s)")
    axes[-1, 0].set_xlim(0, FILM_DURATION_S)
    fig.suptitle("All completed sessions: individual (thin) and mean (thick) continuous ratings", fontsize=10)
    fig.tight_layout()
    out = OUT / "summary_timeseries.png"
    try:
        fig.savefig(out, dpi=100)
    except OSError:  # open in a viewer (Windows lock): save under a new name
        out = out.with_name(f"{out.stem}_{pd.Timestamp.now():%H%M%S}{out.suffix}")
        fig.savefig(out, dpi=100)
    print("wrote", out)
    plt.close(fig)
    md.append("![time series](summary_timeseries.png)\n")
    (OUT / "summary.md").write_text("\n".join(md), encoding="utf8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
