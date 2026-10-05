"""Affect-grid summary of the valence x arousal study (descriptive).

Run after qc/review.py:  python qc/plot_affect_grid.py
Writes qc/out/affect_grid.png:
  left  - occupancy heatmap: share of viewing time spent in each region of the grid (each participant resampled to
          1 Hz and weighted equally), with every participant's most extreme point (furthest from neutral) marked
  right - the group-mean path through the grid over the film, coloured by film time, minute markers labelled
Also writes qc/out/affect_grid_segments.png (needs qc/out/film_segments.csv from qc/segment_film.py): one smoothed
occupancy map per film segment on a shared colour scale, each participant's mean (valence, arousal) in the segment as
a dot, group mean +/- SEM as an open marker.
Occupancy is a smoothed density: 50x50 bins (2 rating units) + Gaussian smoothing (sigma 4 units, reflecting at the
scale edges), each participant weighted equally (1 Hz samples are strongly autocorrelated, so samples are not
independent observations; equal participant weighting keeps long dwellers from dominating).
Sessions: completed, not REJECT-ELIGIBLE, affect2d only. --exclude-review also drops REVIEW verdicts.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.collections import LineCollection
from matplotlib.colors import PowerNorm
from scipy.ndimage import gaussian_filter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from qc_lib import FILM_DURATION_S, load_session, scope_filter  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW, OUT = ROOT / "data" / "raw", ROOT / "qc" / "out"
GRID_T = np.arange(0, np.floor(FILM_DURATION_S), 1.0)
INK, INK2, GRID = "#0b0b0b", "#52514e", "#d9d8d4"


def resampled(s) -> tuple[np.ndarray, np.ndarray]:
    d = s.film_samples[s.film_samples["playing"] == 1].sort_values("t_stim")
    t = d["t_stim"].astype(float)
    x = np.interp(GRID_T, t, d["value_x"].astype(float), left=np.nan, right=np.nan)
    y = np.interp(GRID_T, t, d["value_y"].astype(float), left=np.nan, right=np.nan)
    return x, y


BINS, SIGMA_UNITS = 50, 4.0


def occupancy(xs: list[np.ndarray], ys: list[np.ndarray]) -> np.ndarray:
    """Smoothed occupancy (% of participant-weighted time per 2x2-unit cell), each participant weighted equally."""
    H = np.zeros((BINS, BINS))
    for x, y in zip(xs, ys):
        ok = np.isfinite(x) & np.isfinite(y)
        if ok.sum() == 0:
            continue
        h, _, _ = np.histogram2d(x[ok], y[ok], bins=BINS, range=[[0, 100], [0, 100]])
        H += h / h.sum()
    H = gaussian_filter(H, sigma=SIGMA_UNITS / (100 / BINS), mode="reflect")
    return 100 * H / H.sum()


def save(fig, out: Path) -> Path:
    try:
        fig.savefig(out, dpi=120, facecolor="white")
    except OSError:  # open in a viewer (Windows lock)
        out = out.with_name(f"{out.stem}_{pd.Timestamp.now():%H%M%S}{out.suffix}")
        fig.savefig(out, dpi=120, facecolor="white")
    plt.close(fig)
    return out


def style_grid(ax, title: str) -> None:
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_aspect("equal")
    ax.axhline(50, color=GRID, lw=1, zorder=1)
    ax.axvline(50, color=GRID, lw=1, zorder=1)
    ax.set_xticks([0, 50, 100], ["Unpleasant", "Neutral", "Pleasant"])
    lab = ax.get_xticklabels()
    lab[0].set_horizontalalignment("left")
    lab[-1].set_horizontalalignment("right")
    ax.set_yticks([0, 50, 100], ["Low", "", "High"])
    ax.set_xlabel("Valence")
    ax.set_ylabel("Arousal (activation)")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.set_title(title, loc="left", fontsize=12, color=INK)


def main() -> None:
    exclude_review = "--exclude-review" in sys.argv
    rep = pd.read_csv(OUT / "qc_report.csv")
    rep = scope_filter(rep)  # exploratory sample unless --confirmatory / --all
    ok = rep[(rep["completed"] == True) & (rep["study"] == "affect2d")]  # noqa: E712
    ok = ok[ok["verdict"] == "OK"] if exclude_review else ok[ok["verdict"] != "REJECT-ELIGIBLE"]
    keep = set(ok["prolific_pid"])
    xs, ys = [], []
    for p in sorted(RAW.glob("*.ndjson")):
        s = load_session(p)
        if s.meta and s.pid in keep and s.is2d and not s.film_samples.empty:
            x, y = resampled(s)
            xs.append(x)
            ys.append(y)
    n = len(xs)
    if not n:
        print("no completed affect2d sessions")
        return
    X, Y = np.vstack(xs), np.vstack(ys)

    plt.rcParams.update({"font.size": 11, "axes.edgecolor": INK2, "axes.labelcolor": INK2,
                         "xtick.color": INK2, "ytick.color": INK2})
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(13, 6.2), facecolor="white")

    # --- occupancy heatmap: each participant contributes equally (1 Hz samples, weights 1/n_valid) ----------------
    H = occupancy(xs, ys)
    im = ax.imshow(H.T, origin="lower", extent=[0, 100, 0, 100], cmap="Blues",
                   norm=PowerNorm(gamma=0.6, vmin=0, vmax=H.max()), interpolation="bilinear", zorder=0)
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
    cb.set_label("% of viewing time per 2×2 cell (smoothed; participants weighted equally)")
    # each participant's most extreme point (furthest from neutral)
    d = np.hypot(X - 50, Y - 50)
    idx = np.nanargmax(d, axis=1)
    ex, ey = X[np.arange(n), idx], Y[np.arange(n), idx]
    ax.scatter(ex, ey, s=46, facecolor="white", edgecolor="#eb6834", linewidth=2, zorder=3,
               label="each participant's most extreme point")
    style_grid(ax, f"Where people were during the film (n = {n})")
    ax.legend(loc="lower left", fontsize=9, frameon=True, framealpha=0.9)

    # --- group-mean path, coloured by film time ---------------------------------------------------------------
    mx = pd.Series(np.nanmean(X, axis=0)).rolling(15, center=True, min_periods=1).mean().to_numpy()
    my = pd.Series(np.nanmean(Y, axis=0)).rolling(15, center=True, min_periods=1).mean().to_numpy()
    pts = np.column_stack([mx, my]).reshape(-1, 1, 2)
    segs = np.concatenate([pts[:-1], pts[1:]], axis=1)
    lc = LineCollection(segs, cmap="Oranges", norm=plt.Normalize(-120, GRID_T.max()), linewidth=3, zorder=2)
    lc.set_array(GRID_T[:-1])
    bx.add_collection(lc)
    for m in range(0, int(GRID_T.max()) + 1, 60):
        bx.scatter(mx[m], my[m], s=28, color="white", edgecolor=INK, linewidth=1.2, zorder=3)
        bx.annotate(f"{m // 60}", (mx[m], my[m]), xytext=(5, 4), textcoords="offset points", fontsize=8, color=INK2)
    bx.scatter(mx[0], my[0], s=60, marker="s", color=INK, zorder=4, label="start")
    bx.scatter(mx[-1], my[-1], s=80, marker="*", color=INK, zorder=4, label="end")
    cb2 = fig.colorbar(lc, ax=bx, fraction=0.046, pad=0.03)
    cb2.set_label("film time (min)")
    cb2.ax.set_ylim(0, GRID_T.max())
    cb2.set_ticks(range(0, int(GRID_T.max()) + 1, 120), labels=[str(m // 60) for m in range(0, int(GRID_T.max()) + 1, 120)])
    style_grid(bx, "Group-mean path through the film (15 s smoothing)")
    bx.legend(loc="lower left", fontsize=9, frameon=True, framealpha=0.9)
    bx.text(0.99, 0.01, "numbers = minutes", transform=bx.transAxes, ha="right", va="bottom", fontsize=8, color=INK2)

    note = ("Completed valence × arousal sessions" + (" with QC verdict OK" if exclude_review else
            " (not reject-eligible)") + "; ratings resampled to 1 Hz of film time. Descriptive.")
    fig.text(0.01, 0.01, note, fontsize=8, color=INK2)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    out = save(fig, OUT / ("affect_grid_ok_only.png" if exclude_review else "affect_grid.png"))
    print("wrote", out, f"(n = {n})")
    if not exclude_review:
        plot_segments(xs, ys)


def plot_segments(xs: list[np.ndarray], ys: list[np.ndarray]) -> None:
    segf = OUT / "film_segments.csv"
    if not segf.exists():
        print("no film_segments.csv - run qc/segment_film.py first for the per-segment maps")
        return
    edges_s = pd.read_csv(segf)["arousal_s"].astype(int).tolist()
    edges = [0, *edges_s, len(GRID_T)]
    names = ["baseline", "rise", "plateau", "return"] if len(edges) == 5 else [f"segment {i + 1}" for i in range(len(edges) - 1)]
    maps, pts = [], []
    for a, b in zip(edges[:-1], edges[1:]):
        sx, sy = [x[a:b] for x in xs], [y[a:b] for y in ys]
        maps.append(occupancy(sx, sy))
        pts.append((np.array([np.nanmean(v) for v in sx]), np.array([np.nanmean(v) for v in sy])))
    vmax = max(m.max() for m in maps)
    fig, axes = plt.subplots(1, len(maps), figsize=(4.2 * len(maps) + 1, 4.9), facecolor="white",
                             gridspec_kw={"wspace": 0.08})
    for i, (ax, H, (px, py)) in enumerate(zip(axes, maps, pts)):
        im = ax.imshow(H.T, origin="lower", extent=[0, 100, 0, 100], cmap="Blues",
                       norm=PowerNorm(gamma=0.6, vmin=0, vmax=vmax), interpolation="bilinear", zorder=0)
        ax.scatter(px, py, s=22, color="#eb6834", edgecolor="white", linewidth=0.8, zorder=3,
                   label="participant mean" if i == 0 else None)
        mx, my = px.mean(), py.mean()
        ex, ey = px.std(ddof=1) / np.sqrt(len(px)), py.std(ddof=1) / np.sqrt(len(py))
        ax.errorbar(mx, my, xerr=ex, yerr=ey, fmt="o", color=INK, markerfacecolor="white", markeredgewidth=2,
                    markersize=9, capsize=4, lw=1.6, zorder=4, label="group mean ± SEM" if i == 0 else None)
        a, b = edges[i], edges[i + 1]
        style_grid(ax, f"{i + 1} {names[i]}  {a // 60}:{a % 60:02d}–{b // 60}:{b % 60:02d}")
        if i:
            ax.set_ylabel("")
            ax.set_yticklabels([])
    axes[0].legend(loc="lower left", fontsize=8, frameon=True, framealpha=0.9)
    fig.subplots_adjust(left=0.05, right=0.88, top=0.86, bottom=0.12)
    cb = fig.colorbar(im, cax=fig.add_axes([0.9, 0.16, 0.01, 0.66]))
    cb.set_label("% of segment time per 2×2 cell\n(smoothed; participants weighted equally)")
    fig.suptitle(f"Affect-grid occupancy per film segment (n = {len(xs)}; shared colour scale)", x=0.01, ha="left",
                 fontsize=12, y=0.98)
    out = save(fig, OUT / "affect_grid_segments.png")
    print("wrote", out)


if __name__ == "__main__":
    main()
