"""Step 4 (EXPLORATORY, descriptive): where on the affect grid people were in each film phase.

Not a registered test. The preregistration lists "affect-grid occupancy per segment" under exploratory analyses.

Run:  uv run python analysis/04_affect_grid.py                 (exploratory sample, the default)
      uv run python analysis/04_affect_grid.py --sample confirmatory

One panel per registered segment (baseline, rise, plateau, return), primary sample:
  - blue map: share of the segment's viewing time in each part of the grid (smoothed; participants count equally;
    same colour scale in all panels)
  - crimson dots: each participant's mean valence and arousal in the segment
  - open circle: group mean with 95% CI in both directions
Writes results/<sample>/figures/fig6_affect_grid_by_phase(.png/.pdf) and a run record.
"""
import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import PowerNorm
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # so `analysis` can be imported
from analysis import affect_grid, plot_style, run_record, study_data  # noqa: E402

RESULTS = Path(__file__).resolve().parent.parent / "results"


def half_width_95(values):
    """Half-width of the 95% confidence interval of the mean (t distribution)."""
    return stats.t.ppf(0.975, len(values) - 1) * np.std(values, ddof=1) / np.sqrt(len(values))


def mm_ss(seconds):
    return f"{seconds // 60}:{seconds % 60:02d}"


def style_grid(ax, show_arousal_labels):
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_aspect("equal")
    ax.axhline(50, color=plot_style.GRID, lw=0.8, zorder=1)
    ax.axvline(50, color=plot_style.GRID, lw=0.8, zorder=1)
    ax.set_xticks([0, 50, 100], ["Unpleasant", "Neutral", "Pleasant"])
    ax.get_xticklabels()[0].set_horizontalalignment("left")
    ax.get_xticklabels()[-1].set_horizontalalignment("right")
    ax.set_xlabel("Valence")
    if show_arousal_labels:
        ax.set_yticks([0, 50, 100], ["Low", "", "High"])
        ax.set_ylabel("Arousal")
    else:
        ax.set_yticks([0, 50, 100], ["", "", ""])


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sample", choices=["exploratory", "confirmatory"], default="exploratory")
    args = parser.parse_args()

    out = RESULTS / args.sample
    record = run_record.make_record("04_affect_grid.py", args.sample, seed=None,
                                    inputs=sorted(study_data.DATA.glob("*.csv")),
                                    settings={"bins": affect_grid.BINS, "smoothing_units": affect_grid.SMOOTHING_UNITS,
                                              "exploratory": True})
    plot_style.use()

    participants, valence, arousal = study_data.load()
    rows = study_data.analysis_samples(participants[participants["sample"] == args.sample])["primary"].index

    # One occupancy map and one set of participant means per segment.
    maps, means = {}, {}
    for name, (start, end) in study_data.SEGMENTS.items():
        segment_valence, segment_arousal = valence[rows, start:end], arousal[rows, start:end]
        maps[name] = affect_grid.occupancy(segment_valence, segment_arousal)
        means[name] = (segment_valence.mean(axis=1), segment_arousal.mean(axis=1))
    highest = max(grid.max() for grid in maps.values())

    fig, axes = plt.subplots(1, 4, figsize=(10.5, 3.0))
    for i, (ax, name) in enumerate(zip(axes, study_data.SEGMENTS)):
        image = ax.imshow(maps[name].T, origin="lower", extent=[0, 100, 0, 100], cmap="Blues",
                          norm=PowerNorm(gamma=0.6, vmin=0, vmax=highest), interpolation="bilinear", zorder=0)
        person_valence, person_arousal = means[name]
        ax.scatter(person_valence, person_arousal, s=9, color=plot_style.AROUSAL, alpha=0.7, edgecolor="white",
                   linewidth=0.4, zorder=3, label="participant mean" if i == 0 else None)
        ax.errorbar(person_valence.mean(), person_arousal.mean(), xerr=half_width_95(person_valence),
                    yerr=half_width_95(person_arousal), fmt="o", color=plot_style.TEXT, mfc="white", mew=1.6, ms=7,
                    capsize=3, lw=1.4, zorder=4, label="group mean ± 95% CI" if i == 0 else None)
        start, end = study_data.SEGMENTS[name]
        style_grid(ax, show_arousal_labels=i == 0)
        ax.set_title(f"{i + 1} {name}  {mm_ss(start)}–{mm_ss(end)}", loc="left", fontsize=9)

    axes[0].legend(loc="lower left", fontsize=6.5, frameon=True, framealpha=0.9, edgecolor="none")
    fig.subplots_adjust(left=0.06, right=0.89, top=0.86, bottom=0.15, wspace=0.08)
    colour_bar = fig.colorbar(image, cax=fig.add_axes([0.905, 0.2, 0.01, 0.55]))
    colour_bar.set_label("% of segment time per 2×2 cell\n(smoothed; participants weighted equally)", fontsize=7)
    colour_bar.ax.tick_params(labelsize=7)
    fig.suptitle(f"Affect grid by film phase (n = {len(rows)}; registered segments; shared colour scale) – "
                 "exploratory, descriptive", x=0.01, ha="left", fontsize=9.5)
    note = ("EXPLORATORY SAMPLE – development run" if args.sample == "exploratory" else "Confirmatory sample")
    fig.text(0.995, 0.005, note, ha="right", va="bottom", fontsize=7, color=plot_style.TEXT_SOFT)
    plot_style.save(fig, out / "figures" / "fig6_affect_grid_by_phase")
    run_record.save_record(record, out)


if __name__ == "__main__":
    main()
