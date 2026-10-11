"""Step 7: Figure 2 of the manuscript (somatic anxiety), and the time-course panels reused by Figure 1.

  Fig2  (a) STICSA somatic totals before and after the film, (b) item-level responses (as fig2_sticsa from
        03_figures.py), (c, d) STICSA change against whole-film mean arousal and valence (registered H5a, H5b).
        The statistics are in the caption (journal rule: no titles or statistics inside figures).
  time_course_panel() draws panels b and c of Figure 1 (12_overview_figure.py).

Confirmatory sample, primary analysis sample. Run:  uv run python analysis/07_manuscript_figure.py
Writes manuscript/figures/Fig2 (.pdf, and .png at 600 dpi; 165 mm wide) and a run record.
(The Brief Article's two-panel time-course figure, figure1, was replaced by Figure 1 of 12_overview_figure.py.)
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
        ax.plot(seconds, person, color=colour, lw=0.25, alpha=faintness, zorder=1, rasterized=True)  # keeps PDFs light
    mean, half_width = mean_and_ci(ratings[confirmatory])
    ax.fill_between(seconds, mean - half_width, mean + half_width, color=colour, alpha=0.3, lw=0, zorder=2)
    ax.plot(seconds, mean, color=colour, lw=1.6, zorder=3, label=f"Confirmatory (n = {len(confirmatory)})")
    ax.plot(seconds, ratings[exploratory].mean(axis=0), color=plot_style.TEXT, lw=0.9, ls="--", zorder=4,
            label=f"Exploratory (n = {len(exploratory)})")
    ax.set_ylim(0, 100)
    ax.set_ylabel(f"{rating.capitalize()} (0–100)")


def main():
    record = run_record.make_record("07_manuscript_figure.py", "confirmatory", seed=None,
                                    inputs=[*sorted(study_data.DATA.glob("*.csv")), RESULTS / "hypothesis_tests.csv"])
    plot_style.use()
    participants, valence, arousal = study_data.load()
    measures = hypotheses.participant_measures(participants, valence, arousal)
    primary = study_data.analysis_samples(participants[participants["sample"] == "confirmatory"])["primary"]
    OUT.mkdir(parents=True, exist_ok=True)

    # Figure 2: STICSA (reuses the figure function from 03_figures.py)
    figures_03 = load_figure_script()
    tests = pd.read_csv(RESULTS / "hypothesis_tests.csv").query("analysis_sample == 'primary'")
    tests = tests.set_index("hypothesis", drop=False)
    h5_rows = [tests.loc["H5a"], tests.loc["H5b"]]
    items = participants.loc[primary.index, [c for c in participants.columns if c.startswith("sticsa_") and "_item" in c]]
    figures_03.sticsa(measures.loc[primary.index], items, tests.loc["H1"], "manuscript", OUT, h5_rows=h5_rows,
                      path=OUT / "Fig2")
    run_record.save_record(record, OUT)


if __name__ == "__main__":
    main()
