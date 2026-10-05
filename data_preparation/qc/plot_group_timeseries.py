"""Group time series of the valence x arousal arm: mean with 95% CI ribbon (descriptive).

  python qc/plot_group_timeseries.py                 # exploratory sample (pilot Study 2 + cohort 1)
  python qc/plot_group_timeseries.py --confirmatory  # confirmatory sample (cohort 2 onwards)

Sessions: completed affect2d, after the preregistered hard exclusions (docs/preregistration.md, rules 1-7, applied
exactly as written). Ratings resampled to 1 Hz of film time. Ribbon = mean +/- t(.975, n-1) * SEM per second.
The fixed segment edges (262, 470, 692 s) are marked. Writes qc/out/group_timeseries_<sample>.png.
The 1D anxiety arm is not included (separate plot if that arm is run).
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from qc_lib import FILM_DURATION_S, load_session, prereg_hard_exclusion, scope_filter  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW, OUT = ROOT / "data" / "raw", ROOT / "qc" / "out"
T = np.arange(0, np.floor(FILM_DURATION_S), 1.0)
EDGES = [262, 470, 692]
NAMES = ["baseline", "rise", "plateau", "return"]
C_AR, C_VA, INK, INK2 = "#eb6834", "#2a78d6", "#0b0b0b", "#52514e"


def main() -> None:
    sample = "confirmatory" if "--confirmatory" in sys.argv else ("all" if "--all" in sys.argv else "exploratory")
    rep = scope_filter(pd.read_csv(OUT / "qc_report.csv"))
    rep = rep[(rep["completed"] == True) & (rep["study"] == "affect2d")].copy()  # noqa: E712
    rep["hard"] = rep.apply(prereg_hard_exclusion, axis=1)
    keep = set(rep.loc[rep["hard"] == "", "prolific_pid"])
    n_excl = int((rep["hard"] != "").sum())
    V, A = [], []
    for p in sorted(RAW.glob("*.ndjson")):
        s = load_session(p)
        if not (s.meta and s.pid in keep and s.is2d) or s.film_samples.empty:
            continue
        d = s.film_samples[s.film_samples["playing"] == 1].sort_values("t_stim")
        t = d["t_stim"].astype(float)
        V.append(np.interp(T, t, d["value_x"].astype(float)))
        A.append(np.interp(T, t, d["value_y"].astype(float)))
    V, A = np.vstack(V), np.vstack(A)
    n = len(A)
    tcrit = stats.t.ppf(0.975, n - 1)

    fig, axes = plt.subplots(2, 1, figsize=(13, 7.2), sharex=True, facecolor="white")
    for ax, M, col, lab, sub in ((axes[0], A, C_AR, "Arousal", "low → high activation"),
                                 (axes[1], V, C_VA, "Valence", "unpleasant → pleasant")):
        m = M.mean(0)
        half = tcrit * M.std(0, ddof=1) / np.sqrt(n)
        ax.fill_between(T, m - half, m + half, color=col, alpha=0.25, lw=0, label="95% CI")
        ax.plot(T, m, color=col, lw=1.8, label=f"group mean (n = {n})")
        for e in EDGES:
            ax.axvline(e, color=INK2, lw=0.9, ls="--", zorder=1)
        if lab == "Valence":
            ax.axhline(50, color="#c8c7c2", lw=1, zorder=0)
        ax.set_ylim(0, 100)
        ax.set_ylabel(f"{lab}\n({sub})")
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        ax.legend(loc="upper left", fontsize=9, frameon=False)
    bounds = [0, *EDGES, T.max()]
    for i, nm in enumerate(NAMES):
        axes[0].text((bounds[i] + bounds[i + 1]) / 2, 101, nm, ha="center", va="bottom", fontsize=9, color=INK2)
    axes[1].set_xticks(range(0, int(T.max()) + 1, 60), [str(s // 60) for s in range(0, int(T.max()) + 1, 60)])
    axes[1].set_xlim(0, T.max())
    axes[1].set_xlabel("film time (min)")
    fig.suptitle(f"Valence × arousal arm – {sample} sample: group mean with 95% CI "
                 f"(n = {n}; {n_excl} excluded by preregistered rules; dashed = fixed segment edges)",
                 x=0.01, ha="left", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    out = OUT / f"group_timeseries_{sample}.png"
    try:
        fig.savefig(out, dpi=120, facecolor="white")
    except OSError:
        out = out.with_name(f"{out.stem}_{pd.Timestamp.now():%H%M%S}{out.suffix}")
        fig.savefig(out, dpi=120, facecolor="white")
    print("wrote", out, f"(n = {n}, excluded {n_excl})")


if __name__ == "__main__":
    main()
