"""Step 7: the two figures of the Brief Article (Cognition and Emotion allows two tables/figures in total).

  Figure 2  somatic anxiety: (A) STICSA somatic totals before and after the film, (B) item-level responses
            (the same figure as fig2_sticsa from 03_figures.py, without the sample note)
  Figure 1  continuous ratings: group-mean arousal and valence over the film (confirmatory sample, 95% CI;
            participants as faint lines), with the exploratory sample's group mean overlaid (dashed)

Confirmatory sample, primary analysis sample. Run:  uv run python analysis/07_manuscript_figure.py
Writes manuscript/figures/figure1 and figure2 (.pdf and .png at 600 dpi) and a run record.
"""
import importlib.util
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

ANALYSIS = Path(__file__).resolve().parent
sys.path.insert(0, str(ANALYSIS.parent))  # so `analysis` can be imported
from analysis import hypotheses, plot_style, run_record, study_data  # noqa: E402

OUT = ANALYSIS.parent / "manuscript" / "figures"
RESULTS = ANALYSIS.parent / "results" / "confirmatory"
DPI = 600  # journal production: 300 dpi colour minimum


def load_figure_script():
    """03_figures.py starts with a digit, so it is loaded by file path to reuse its STICSA figure."""
    spec = importlib.util.spec_from_file_location("figures_03", ANALYSIS / "03_figures.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def mean_and_ci(values):
    values = np.asarray(values, float)
    n = values.shape[0]
    return values.mean(axis=0), stats.t.ppf(0.975, n - 1) * values.std(axis=0, ddof=1) / np.sqrt(n)


def time_course_panel(ax, ratings, confirmatory, exploratory, rating, show_segment_names):
    seconds = np.arange(study_data.FILM_SECONDS)
    colour = plot_style.RATING_COLOURS[rating]
    plot_style.shade_segments(ax, label=show_segment_names)
    faintness = min(plot_style.PARTICIPANT_ALPHA, 6 / len(confirmatory))
    for person in ratings[confirmatory]:
        ax.plot(seconds, person, color=colour, lw=0.25, alpha=faintness, zorder=1)
    mean, half_width = mean_and_ci(ratings[confirmatory])
    ax.fill_between(seconds, mean - half_width, mean + half_width, color=colour, alpha=0.3, lw=0, zorder=2)
    ax.plot(seconds, mean, color=colour, lw=1.6, zorder=3, label=f"Confirmatory (n = {len(confirmatory)})")
    ax.plot(seconds, ratings[exploratory].mean(axis=0), color=plot_style.TEXT, lw=0.9, ls="--", zorder=4,
            label=f"Exploratory (n = {len(exploratory)})")
    ax.set_ylim(0, 100)
    ax.set_ylabel(f"{rating.capitalize()} (0–100)", fontsize=8)


def time_course_figure(valence, arousal, confirmatory, exploratory):
    fig, axes = plt.subplots(2, 1, figsize=(6.9, 4.8), sharex=True)
    time_course_panel(axes[0], arousal, confirmatory, exploratory, "arousal", show_segment_names=True)
    time_course_panel(axes[1], valence, confirmatory, exploratory, "valence", show_segment_names=False)
    axes[1].axhline(50, color=plot_style.GRID, lw=0.8, zorder=1)
    plot_style.minutes_axis(axes[1])
    axes[0].legend(loc="lower right", fontsize=7, handlelength=2.2)
    for ax, letter in zip(axes, "AB"):
        ax.text(-0.08, 1.03, letter, transform=ax.transAxes, fontsize=11, fontweight="bold", va="bottom")
    fig.tight_layout()
    return fig


def main():
    record = run_record.make_record("07_manuscript_figure.py", "confirmatory", seed=None,
                                    inputs=[*sorted(study_data.DATA.glob("*.csv")), RESULTS / "hypothesis_tests.csv"])
    plot_style.use()
    plt.rcParams["savefig.dpi"] = DPI
    participants, valence, arousal = study_data.load()
    measures = hypotheses.participant_measures(participants, valence, arousal)
    primary = study_data.analysis_samples(participants[participants["sample"] == "confirmatory"])["primary"]
    exploratory = participants.index[(participants["sample"] == "exploratory") & study_data.is_usable(participants)]
    OUT.mkdir(parents=True, exist_ok=True)

    # Figure 2: STICSA (reuses the figure function from 03_figures.py)
    figures_03 = load_figure_script()
    h1 = pd.read_csv(RESULTS / "hypothesis_tests.csv").query("analysis_sample == 'primary' and hypothesis == 'H1'")
    items = participants.loc[primary.index, [c for c in participants.columns if c.startswith("sticsa_") and "_item" in c]]
    figures_03.sticsa(measures.loc[primary.index], items, h1.iloc[0], "manuscript", OUT)
    for suffix in (".pdf", ".png"):
        (OUT / f"fig2_sticsa{suffix}").replace(OUT / f"figure2{suffix}")

    # Figure 1: time course
    fig = time_course_figure(valence, arousal, primary.index, exploratory)
    for suffix in (".pdf", ".png"):
        fig.savefig(OUT / f"figure1{suffix}", dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    run_record.save_record(record, OUT)
    print("wrote", OUT / "figure1.pdf (time course) and", OUT / "figure2.pdf (STICSA)")


if __name__ == "__main__":
    main()
