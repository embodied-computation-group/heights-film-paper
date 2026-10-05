"""Detect the film's segments from the group-mean ratings (exploratory; move to the analysis repo later).

Model: piecewise-LINEAR segmentation (each segment its own line, so a ramp is one segment), solved exactly by
dynamic programming on the 1 Hz group-mean series, minimum segment length MIN_SEG s.
  - primary: group-mean arousal, K = 3 breakpoints (4 segments: baseline / rise / plateau / return)
  - comparison: joint fit on z-scored arousal + valence
  - model choice: BIC for K = 0..6
  - uncertainty: bootstrap over participants (resample, re-average, re-detect) -> 95% interval per edge

Run after qc/review.py:  python qc/segment_film.py [--k 3] [--boot 300]
Writes qc/out/film_segments.png, film_segments_by_participant.png, film_segments.csv, segment_means.csv
Sessions: completed affect2d, not REJECT-ELIGIBLE, excluding erratic input / incomplete film coverage.
"""
from __future__ import annotations

import argparse
import sys
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
T = np.arange(0, np.floor(FILM_DURATION_S), 1.0)
MIN_SEG = 30
SEG_NAMES = ["baseline", "rise", "plateau", "return"]
SEG_COLORS = ["#f0efec", "#fbe3d6", "#f6c6ae", "#e6eef9"]  # subtle shading only
C_AR, C_VA = "#eb6834", "#2a78d6"  # arousal / valence (validated categorical slots 2 / 1)
INK, INK2 = "#0b0b0b", "#52514e"


# ----------------------------------------------------------------------------------- data ---
def load_matrix() -> tuple[np.ndarray, np.ndarray, list[str]]:
    rep = pd.read_csv(OUT / "qc_report.csv")
    rep = scope_filter(rep)  # exploratory sample unless --confirmatory / --all
    ok = rep[(rep["completed"] == True) & (rep["study"] == "affect2d") & (rep["verdict"] != "REJECT-ELIGIBLE")]  # noqa: E712
    ok = ok[~ok["review_reasons"].fillna("").str.contains("erratic input") & (ok["coverage"] >= 0.95)]
    keep = set(ok["prolific_pid"])
    V, A, pids = [], [], []
    for p in sorted(RAW.glob("*.ndjson")):
        s = load_session(p)
        if not (s.meta and s.pid in keep and s.is2d) or s.film_samples.empty:
            continue
        d = s.film_samples[s.film_samples["playing"] == 1].sort_values("t_stim")
        t = d["t_stim"].astype(float)
        V.append(np.interp(T, t, d["value_x"].astype(float)))
        A.append(np.interp(T, t, d["value_y"].astype(float)))
        pids.append(s.pid)
    return np.vstack(V), np.vstack(A), pids


# --------------------------------------------------------------------- segmentation (DP) ---
def seg_cost_matrix(Y: np.ndarray) -> np.ndarray:
    """C[i, j] = SSE of a separate least-squares line per column of Y over samples i..j-1 (j exclusive)."""
    n = Y.shape[0]
    x = np.arange(n, dtype=float)
    cs = lambda a: np.concatenate([[0.0], np.cumsum(a)])  # noqa: E731
    Sx, Sxx = cs(x), cs(x * x)
    i, j = np.meshgrid(np.arange(n + 1), np.arange(n + 1), indexing="ij")
    m = (j - i).astype(float)
    sx, sxx = Sx[j] - Sx[i], Sxx[j] - Sxx[i]
    with np.errstate(divide="ignore", invalid="ignore"):
        varx = sxx - sx * sx / m
        C = np.zeros_like(m)
        for k in range(Y.shape[1]):
            y = Y[:, k]
            Sy, Syy, Sxy = cs(y), cs(y * y), cs(x * y)
            sy, syy, sxy = Sy[j] - Sy[i], Syy[j] - Syy[i], Sxy[j] - Sxy[i]
            vary = syy - sy * sy / m
            cov = sxy - sx * sy / m
            C += np.where(varx > 0, vary - cov * cov / varx, vary)
    C[(j - i) < MIN_SEG] = np.inf
    return C


def segment(Y: np.ndarray, K: int, C: np.ndarray | None = None) -> tuple[list[int], float]:
    """Exact optimal K breakpoints (K+1 segments). Returns breakpoint indices and total cost."""
    if Y.ndim == 1:
        Y = Y[:, None]
    n = Y.shape[0]
    C = seg_cost_matrix(Y) if C is None else C
    D = C[0].copy()  # D[j]: best cost of [0, j) with current number of segments
    back = []
    for _ in range(K):
        tot = D[:, None] + C  # split at i, last segment [i, j)
        arg = np.argmin(tot, axis=0)
        D = tot[arg, np.arange(n + 1)]
        back.append(arg)
    bps, j = [], n
    for arg in reversed(back):
        j = int(arg[j])
        bps.append(j)
    return sorted(bps), float(D[n])


def fit_lines(y: np.ndarray, bps: list[int]) -> np.ndarray:
    out = np.empty_like(y)
    edges = [0, *bps, len(y)]
    for a, b in zip(edges[:-1], edges[1:]):
        x = np.arange(a, b)
        out[a:b] = np.polyval(np.polyfit(x, y[a:b], 1), x)
    return out


def bic(cost: float, n: int, K: int, dims: int) -> float:
    return n * dims * np.log(cost / (n * dims)) + (2 * (K + 1) * dims + K) * np.log(n * dims)


# ---------------------------------------------------------------------------------- main ---
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--boot", type=int, default=300)
    a = ap.parse_args()
    V, A, pids = load_matrix()
    n_p, n = A.shape
    mA, mV = A.mean(0), V.mean(0)
    print(f"participants: {n_p}")

    # model choice on arousal
    CA = seg_cost_matrix(mA[:, None])
    rows = []
    for K in range(0, 7):
        bps, cost = segment(mA, K, CA)
        rows.append({"K_breakpoints": K, "segments": K + 1, "bic": round(bic(cost, n, K, 1), 1),
                     "breakpoints_s": bps})
    sel = pd.DataFrame(rows)
    print(sel.to_string(index=False))

    bpA, _ = segment(mA, a.k, CA)
    Z = np.column_stack([(mA - mA.mean()) / mA.std(), (mV - mV.mean()) / mV.std()])
    bpJ, _ = segment(Z, a.k)
    print("arousal breakpoints (s):", bpA, "| joint arousal+valence:", bpJ)

    # bootstrap over participants
    rng = np.random.default_rng(1)
    boots = []
    for _ in range(a.boot):
        idx = rng.integers(0, n_p, n_p)
        b, _ = segment(A[idx].mean(0), a.k)
        boots.append(b)
    boots = np.array(boots)
    ci = np.percentile(boots, [2.5, 97.5], axis=0)
    seg_tab = pd.DataFrame({
        "edge": [f"{SEG_NAMES[i]} -> {SEG_NAMES[i + 1]}" if a.k == 3 else f"edge {i + 1}" for i in range(a.k)],
        "arousal_s": bpA, "ci95_low_s": ci[0].round(), "ci95_high_s": ci[1].round(), "joint_av_s": bpJ})
    seg_tab["arousal_mmss"] = [f"{s // 60}:{s % 60:02d}" for s in bpA]
    print(seg_tab.to_string(index=False))
    seg_tab.to_csv(OUT / "film_segments.csv", index=False)

    # per-participant segment means
    edges = [0, *bpA, n]
    names = SEG_NAMES if a.k == 3 else [f"seg{i + 1}" for i in range(a.k + 1)]
    recs = []
    for p, v, ar in zip(pids, V, A):
        for nm, s0, s1 in zip(names, edges[:-1], edges[1:]):
            recs.append({"pid": p, "segment": nm, "start_s": s0, "end_s": s1,
                         "valence": v[s0:s1].mean(), "arousal": ar[s0:s1].mean()})
    sm = pd.DataFrame(recs)
    sm.to_csv(OUT / "segment_means.csv", index=False)
    summ = sm.groupby("segment", sort=False)[["valence", "arousal"]].agg(["mean", "sem"]).round(1)
    print(summ.to_string())

    # ---------------- figure 1: time series with segments --------------------------------------------------
    sem = lambda M: M.std(0, ddof=1) / np.sqrt(M.shape[0])  # noqa: E731
    fig, axes = plt.subplots(2, 1, figsize=(13, 7.5), sharex=True, facecolor="white")
    for ax, M, m, col, lab, bp in ((axes[0], A, mA, C_AR, "Arousal", bpA), (axes[1], V, mV, C_VA, "Valence", bpA)):
        for i, (s0, s1) in enumerate(zip(edges[:-1], edges[1:])):
            ax.axvspan(s0, s1, color=SEG_COLORS[i % 4], zorder=0, lw=0)
            if ax is axes[0]:
                ax.text((s0 + s1) / 2, 103, names[i], ha="center", va="bottom", fontsize=10, color=INK2)
        ax.fill_between(T, m - sem(M), m + sem(M), color=col, alpha=0.25, lw=0, zorder=1)
        ax.plot(T, m, color=col, lw=1.6, zorder=2, label=f"group mean ± SEM (n = {n_p})")
        ax.plot(T, fit_lines(m, bp), color=INK, lw=1.4, ls="--", zorder=3, label="piecewise-linear fit (arousal edges)")
        for k, b in enumerate(bp):
            ax.axvspan(ci[0][k], ci[1][k], color=INK, alpha=0.08, zorder=1, lw=0)
            ax.axvline(b, color=INK, lw=1, zorder=3)
        ax.set_ylim(0, 100)
        ax.set_ylabel(lab + (" (low → high)" if lab == "Arousal" else " (unpleasant → pleasant)"))
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        ax.legend(loc="lower left", fontsize=8, frameon=False)
    axes[1].axhline(50, color="#c8c7c2", lw=1, zorder=1)
    axes[1].set_xlabel("film time (min)")
    axes[1].set_xticks(range(0, int(T.max()) + 1, 60), [str(s // 60) for s in range(0, int(T.max()) + 1, 60)])
    axes[1].set_xlim(0, T.max())
    edge_txt = ", ".join(f"{b // 60}:{b % 60:02d} [{int(lo) // 60}:{int(lo) % 60:02d}–{int(hi) // 60}:{int(hi) % 60:02d}]"
                         for b, lo, hi in zip(bpA, ci[0], ci[1]))
    fig.suptitle(f"Film segments from group-mean arousal: edges at {edge_txt} (95% bootstrap CI, grey bands)",
                 fontsize=10.5, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    _save(fig, OUT / "film_segments.png")

    # ---------------- figure 2: per-segment participant means + grid centroids ------------------------------
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(13, 5.6), facecolor="white", gridspec_kw={"width_ratios": [1.3, 1]})
    rng2 = np.random.default_rng(0)
    for off, var, col in ((-0.15, "arousal", C_AR), (0.15, "valence", C_VA)):
        for i, nm in enumerate(names):
            vals = sm.loc[sm["segment"] == nm, var].to_numpy()
            ax.scatter(i + off + rng2.uniform(-0.05, 0.05, len(vals)), vals, s=18, color=col, alpha=0.45,
                       edgecolor="white", linewidth=0.8, zorder=2)
            ax.errorbar(i + off, vals.mean(), yerr=vals.std(ddof=1) / np.sqrt(len(vals)), fmt="o", color=col,
                        markerfacecolor="white", markeredgewidth=2, markersize=8, capsize=5, lw=2, zorder=3,
                        label=var.capitalize() if i == 0 else None)
    ax.axhline(50, color="#c8c7c2", lw=1, zorder=1)
    ax.set_xticks(range(len(names)), [f"{nm}\n{edges[i] // 60}:{edges[i] % 60:02d}–{edges[i + 1] // 60}:{edges[i + 1] % 60:02d}"
                                      for i, nm in enumerate(names)])
    ax.set_ylim(0, 100)
    ax.set_ylabel("participant mean rating in segment (0–100)")
    ax.legend(loc="upper left", fontsize=9, frameon=False)
    ax.set_title("Mean rating per segment (dots = participants; open = mean ± SEM)", loc="left", fontsize=11)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    # centroids on the grid
    cent = sm.groupby("segment", sort=False)[["valence", "arousal"]]
    mu, se = cent.mean(), cent.sem()
    bx.axhline(50, color="#d9d8d4", lw=1)
    bx.axvline(50, color="#d9d8d4", lw=1)
    xs, ys = mu["valence"].to_numpy(), mu["arousal"].to_numpy()
    for i in range(len(xs) - 1):
        bx.annotate("", (xs[i + 1], ys[i + 1]), (xs[i], ys[i]),
                    arrowprops={"arrowstyle": "->", "color": INK2, "lw": 1.5, "shrinkA": 9, "shrinkB": 9})
    for i, nm in enumerate(mu.index):
        bx.errorbar(xs[i], ys[i], xerr=se.loc[nm, "valence"], yerr=se.loc[nm, "arousal"], fmt="o", color=INK,
                    markerfacecolor="white", markeredgewidth=2, markersize=9, capsize=4, lw=1.4, zorder=3)
        bx.annotate(f"{i + 1} {nm}", (xs[i], ys[i]), xytext=(9, 6), textcoords="offset points", fontsize=10)
    bx.set_xlim(0, 100)
    bx.set_ylim(0, 100)
    bx.set_aspect("equal")
    bx.set_xticks([0, 50, 100], ["Unpleasant", "Neutral", "Pleasant"])
    bx.set_yticks([0, 50, 100], ["Low", "", "High"])
    bx.set_xlabel("Valence")
    bx.set_ylabel("Arousal")
    bx.set_title("Segment centroids on the affect grid (mean ± SEM)", loc="left", fontsize=11)
    for side in ("top", "right"):
        bx.spines[side].set_visible(False)
    fig.tight_layout()
    _save(fig, OUT / "film_segments_by_participant.png")


def _save(fig, out: Path) -> None:
    try:
        fig.savefig(out, dpi=120, facecolor="white")
    except OSError:
        out = out.with_name(f"{out.stem}_{pd.Timestamp.now():%H%M%S}{out.suffix}")
        fig.savefig(out, dpi=120, facecolor="white")
    plt.close(fig)
    print("wrote", out)


if __name__ == "__main__":
    main()
