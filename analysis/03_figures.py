"""Step 3: figures for the registered analyses (primary sample). Run after 02_confirmatory.py.

Run:  uv run python analysis/03_figures.py                 (exploratory sample, the default)
      uv run python analysis/03_figures.py --sample confirmatory

Writes to results/<sample>/figures/:
  fig1_time_course      group-mean arousal and valence over the film (participants faint, mean with 95% CI)
  fig2_sticsa           STICSA somatic total before and after the film (H1)
  fig3_segment_means    segment means per participant and group (H2)
  fig4_replication      group curves of the two samples overlaid (H3; a stand-in on the exploratory sample)
  fig5_correlations     scatter plots for H4-H6
Intervals are 95% confidence intervals of the mean (t distribution) unless stated otherwise.
"""
import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # so `analysis` can be imported
from analysis import hypotheses, plot_style, run_record, stats_tools, study_data  # noqa: E402

RESULTS = Path(__file__).resolve().parent.parent / "results"
RNG_JITTER = np.random.default_rng(0)  # only moves points sideways so they do not hide each other

LABELS = {
    "height_fear": "Everyday fear of heights (1–7)",
    "anxiety_overall": "Post-film overall anxiety (1–7)",
    "sticsa_change": "STICSA change (points)",
    "arousal_plateau": "Plateau arousal (0–100)",
    "valence_plateau": "Plateau valence (0–100)",
    "arousal_whole_film": "Whole-film arousal (0–100)",
    "valence_whole_film": "Whole-film valence (0–100)",
}


def mean_and_ci(values, axis=0):
    """Mean and the half-width of its 95% confidence interval (t distribution)."""
    values = np.asarray(values, float)
    n = values.shape[axis]
    sem = values.std(axis=axis, ddof=1) / np.sqrt(n)
    return values.mean(axis=axis), stats.t.ppf(0.975, n - 1) * sem


def sample_note(fig, sample):
    """Mark development figures (exploratory sample), so they cannot be mistaken for results. Confirmatory and
    manuscript figures carry no note: they go into the paper and its Online Resource, where the caption says it."""
    if sample != "exploratory":
        return
    fig.text(0.995, 0.005, "EXPLORATORY SAMPLE – development run", ha="right", va="bottom",
             color=plot_style.TEXT_SOFT)


# --------------------------------------------------------------------------------------- figures
# Journal rules (2026-10-11): no titles or statistics inside the figures (they go into the captions), lowercase panel
# letters, text 8-10 pt at the printed width (plot_style.FULL_WIDTH).

def time_course(valence, arousal, rows, sample, out):
    fig, axes = plt.subplots(2, 1, figsize=(plot_style.FULL_WIDTH, 4.6), sharex=True, layout="constrained")
    seconds = np.arange(study_data.FILM_SECONDS)
    for ax, rating, ratings in ((axes[0], "arousal", arousal), (axes[1], "valence", valence)):
        colour = plot_style.RATING_COLOURS[rating]
        plot_style.shade_segments(ax, label=ax is axes[0])
        faintness = min(plot_style.PARTICIPANT_ALPHA, 6 / len(rows))  # fainter lines when there are many people
        for person in ratings[rows]:
            ax.plot(seconds, person, color=colour, lw=0.3, alpha=faintness, zorder=1, rasterized=True)
        mean, half_width = mean_and_ci(ratings[rows])
        ax.fill_between(seconds, mean - half_width, mean + half_width, color=colour, alpha=0.3, lw=0, zorder=2)
        ax.plot(seconds, mean, color=colour, lw=1.8, zorder=3)
        ax.set_ylim(0, 100)
        ax.set_ylabel(plot_style.RATING_LABELS[rating])
    axes[1].axhline(50, color=plot_style.GRID, lw=0.8, zorder=1)
    plot_style.minutes_axis(axes[1])
    sample_note(fig, sample)
    plot_style.save(fig, out / "fig1_time_course")


STICSA_ITEM_LABELS = {"01": "Heartbeat", "02": "Tense", "06": "Dizzy", "07": "Weak", "08": "Shaky",
                      "12": "Face hot", "14": "Stiff limbs", "15": "Dry throat", "18": "Breathing",
                      "20": "Butterflies", "21": "Clammy palms"}
STICSA_ANSWERS = {1: "Not at all", 2: "A little", 3: "Moderately", 4: "Very much so"}


def sticsa(measures, items, h1, sample, out, h5_rows=None, path=None):
    """a: STICSA somatic totals before and after the film; b: answers to each item before and after.
    With `h5_rows` (the H5a and H5b result rows; manuscript figure), a second row adds c and d: STICSA change against
    whole-film mean arousal and valence. The statistics are given in the caption, not in the figure.

    Layout from the exploratory STICSA figure in vmp_film_rating (qc/plot_sticsa.py, sticsa_items_stacked.png).
    `items` holds the item columns (sticsa_pre_itemNN, sticsa_post_itemNN) of the same participants.
    `path`: where to save as a journal figure (plot_style.save_print); by default results/<sample>/figures.
    """
    complete = measures[["sticsa_pre", "sticsa_post"]].dropna()
    # The layout of the original figure (narrow spacer column between a and b), drawn at the printed width.
    if h5_rows is None:
        fig = plt.figure(figsize=(plot_style.FULL_WIDTH, 3.4))
        grid = fig.add_gridspec(2, 3, width_ratios=[0.85, 0.62, 2.2], hspace=0.12, wspace=0.05,
                                left=0.09, right=0.95, top=0.88, bottom=0.14)
    else:
        fig = plt.figure(figsize=(plot_style.FULL_WIDTH, 6.0))
        outer = fig.add_gridspec(2, 1, height_ratios=[4.6, 3.4], hspace=0.32, left=0.09, right=0.95, top=0.93,
                                 bottom=0.08)
        grid = outer[0].subgridspec(2, 3, width_ratios=[0.85, 0.62, 2.2], hspace=0.12, wspace=0.05)

    # a: boxplots at the sides, paired lines and mean +/- 95% CI in the middle
    ax = fig.add_subplot(grid[:, 0])
    faintness = min(0.5, 25 / len(complete))  # fainter lines when there are many people
    for pre, post in complete.to_numpy():
        ax.plot([0.15, 0.85], [pre, post], color="#9ea2ab", lw=0.6, alpha=faintness, zorder=1)
    boxes = ax.boxplot([complete["sticsa_pre"], complete["sticsa_post"]], positions=[-0.15, 1.15], widths=0.2,
                       patch_artist=True, medianprops={"color": plot_style.TEXT, "lw": 1.6},
                       whiskerprops={"color": plot_style.TEXT_SOFT}, capprops={"color": plot_style.TEXT_SOFT},
                       flierprops={"marker": ""})
    for patch, colour in zip(boxes["boxes"], (plot_style.BEFORE, plot_style.AFTER)):
        patch.set_facecolor(colour)
        patch.set_edgecolor(plot_style.TEXT_SOFT)
    means, half_widths = zip(*(mean_and_ci(complete[c]) for c in ("sticsa_pre", "sticsa_post")))
    ax.errorbar([0.15, 0.85], means, yerr=half_widths, color=plot_style.TEXT, lw=2, capsize=4, marker="o", ms=6,
                mfc="white", mew=1.6, zorder=5)
    ax.set_xticks([-0.15, 1.15], ["Before\nfilm", "After\nfilm"])
    ax.set_xlim(-0.4, 1.4)
    ax.set_ylim(10, 45)  # a little room around the scale limits (11-44)
    ax.set_ylabel("STICSA somatic total (11–44)")
    plot_style.panel_letter(ax, "a", x=-0.4, y=1.03)

    # b: share of each answer per item, before (top) and after (bottom) the film
    order = list(STICSA_ITEM_LABELS)
    for row, when in enumerate(("pre", "post")):
        bx = fig.add_subplot(grid[row, 2])
        answers = items[[f"sticsa_{when}_item{item}" for item in order]]
        shares = pd.DataFrame({k: (answers == k).mean().to_numpy() for k in STICSA_ANSWERS}, index=order)
        y = np.arange(len(order))[::-1]
        left = np.zeros(len(order))
        for answer, label in STICSA_ANSWERS.items():
            bx.barh(y, shares[answer], left=left, height=0.85, color=plot_style.STICSA_RESPONSE_COLOURS[answer],
                    edgecolor="white", linewidth=1, label=f"{answer} {label}")
            left += shares[answer].to_numpy()
        bx.set_yticks(y, [STICSA_ITEM_LABELS[item] for item in order])
        bx.set_xlim(0, 1)
        bx.set_ylim(-0.6, len(order) - 0.4)
        bx.text(1.01, 0.5, "Before film" if when == "pre" else "After film", transform=bx.transAxes,
                rotation=270, ha="left", va="center")
        if row == 0:
            bx.set_xticks([])
            bx.spines["bottom"].set_visible(False)
            # Legend across the width of panel b, as in the original figure (kept within the panel's x limits).
            bx.legend(ncol=4, loc="lower left", bbox_to_anchor=(0, 1.0, 1, 0.1), mode="expand", handlelength=1.0,
                      handletextpad=0.4, columnspacing=0.6, borderaxespad=0.2)
            plot_style.panel_letter(bx, "b", x=-0.3, y=1.06)  # level with "a" (panel b rows are half as tall)
        else:
            bx.set_xticks([0, 0.25, 0.5, 0.75, 1], ["0%", "25%", "50%", "75%", "100%"])
            bx.set_xlabel("Share of participants")

    # c, d: STICSA change against whole-film mean ratings (registered H5a, H5b)
    if h5_rows is not None:
        lower = outer[1].subgridspec(1, 2, wspace=0.28)
        for i, (row, letter) in enumerate(zip(h5_rows, "cd")):
            spec = next(s for s in hypotheses.CORRELATIONS if s["hypothesis"] == row["hypothesis"])
            cx = fig.add_subplot(lower[0, i])
            scatter_with_fit(cx, measures, spec, jitter=0.25)
            plot_style.panel_letter(cx, letter, x=-0.22)
    sample_note(fig, sample)
    if path is None:
        plot_style.save(fig, out / "fig2_sticsa")
    else:
        plot_style.save_print(fig, path)


def scatter_with_fit(ax, measures, spec, jitter):
    """Participants as points (jittered sideways) and a least-squares line with its 95% band. The band is a visual
    guide; the registered test is Spearman's rho."""
    pair = measures[[spec["x"], spec["y"]]].dropna()
    colour = plot_style.VALENCE if "valence" in spec["y"] else plot_style.AROUSAL
    x = pair[spec["x"]] + RNG_JITTER.uniform(-jitter, jitter, len(pair))
    ax.scatter(x, pair[spec["y"]], s=12, color=colour, alpha=0.55, edgecolor="white", linewidth=0.5)
    line_x = np.linspace(pair[spec["x"]].min(), pair[spec["x"]].max(), 100)
    fit, low, high = stats_tools.linear_fit_band(pair[spec["x"]], pair[spec["y"]], line_x)
    ax.fill_between(line_x, low, high, color=plot_style.TEXT, alpha=0.2, lw=0, zorder=2)
    ax.plot(line_x, fit, color=plot_style.TEXT, lw=1.4, zorder=3)
    if spec["x"] in ("height_fear", "anxiety_overall"):
        ax.set_xticks(range(1, 8))
        ax.set_xlim(0.5, 7.5)
    if spec["y"] != "sticsa_change":
        ax.set_ylim(-3, 103)
    ax.set_xlabel(LABELS[spec["x"]])
    ax.set_ylabel(LABELS[spec["y"]])


def segment_means(measures, h2_rows, sample, out):
    """a: arousal, b: valence; segment means per participant and group mean with 95% CI (H2). The H2 statistics are
    in the tables of the Online Resource, not in the figure."""
    segments = list(study_data.SEGMENTS)
    fig, axes = plt.subplots(1, 2, figsize=(plot_style.FULL_WIDTH, 3.0), sharey=True, layout="constrained")
    for ax, rating, letter in zip(axes, ("arousal", "valence"), "ab"):
        colour = plot_style.RATING_COLOURS[rating]
        values = measures[[f"{rating}_{segment}" for segment in segments]].to_numpy()
        for i, segment in enumerate(segments):
            ax.axvspan(i - 0.5, i + 0.5, color=plot_style.SEGMENT_SHADES[segment], lw=0, zorder=0)
        for person in values:
            ax.plot(range(4), person, color=colour, lw=0.6, alpha=plot_style.PARTICIPANT_ALPHA + 0.1, marker="o",
                    ms=2.5, zorder=1)
        mean, half_width = mean_and_ci(values)
        ax.errorbar(range(4), mean, yerr=half_width, color=colour, fmt="-o", ms=7, mfc="white", mew=1.8, capsize=4,
                    lw=1.8, zorder=3)
        ax.set_xticks(range(4), segments)
        ax.set_xlim(-0.5, 3.5)
        ax.set_ylim(0, 100)
        ax.set_ylabel(f"{rating.capitalize()}, segment mean (0–100)")
        ax.yaxis.set_tick_params(labelleft=True)
        plot_style.panel_letter(ax, letter, x=-0.16)
    axes[1].axhline(50, color=plot_style.GRID, lw=0.8, zorder=0)
    sample_note(fig, sample)
    plot_style.save(fig, out / "fig3_segment_means")


def replication(valence, arousal, tested, reference, h3_rows, sample, out):
    """Development figure (not in the paper): group curves of the two samples overlaid, r with its CI."""
    fig, axes = plt.subplots(2, 1, figsize=(plot_style.FULL_WIDTH, 4.6), sharex=True, layout="constrained")
    seconds = np.arange(study_data.FILM_SECONDS)
    if sample == "confirmatory":
        names = (f"Confirmatory (n = {len(tested)})", f"Exploratory (n = {len(reference)})")
    else:
        names = (f"Cohort 1 (n = {len(tested)})", f"Pilot (n = {len(reference)})")
    for ax, rating, ratings, row in zip(axes, ("arousal", "valence"), (arousal, valence), h3_rows):
        colour = plot_style.RATING_COLOURS[rating]
        plot_style.shade_segments(ax, label=ax is axes[0])
        ax.plot(seconds, ratings[tested.index].mean(axis=0), color=colour, lw=1.8, label=names[0])
        ax.plot(seconds, ratings[reference.index].mean(axis=0), color=colour, lw=1.4, ls="--", label=names[1])
        ax.set_ylim(0, 100)
        ax.set_ylabel(plot_style.RATING_LABELS[rating])
        ax.legend(loc="lower left")
        ax.text(0.99, 0.96, f"r = {no_zero(row['estimate'])} [{no_zero(row['ci_low'])}, {no_zero(row['ci_high'])}]",
                transform=ax.transAxes, ha="right", va="top",
                bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85, "pad": 2})
    plot_style.minutes_axis(axes[1])
    sample_note(fig, sample)
    plot_style.save(fig, out / "fig4_replication")


def no_zero(value):
    """Two decimals without the leading zero, for statistics that cannot exceed 1 (journal style): 0.97 -> .97."""
    return f"{value:.2f}".replace("0.", ".", 1)


def correlations(measures, rows, sample, out):
    """H4-H6, one row per hypothesis family: a-c H4a-c, d-e H5a-b, f-g H6a-b. Statistics are in the caption/table."""
    fig, axes = plt.subplots(3, 3, figsize=(plot_style.FULL_WIDTH, 6.6), layout="constrained")
    positions = {"H4a": (0, 0), "H4b": (0, 1), "H4c": (0, 2), "H5a": (1, 0), "H5b": (1, 1), "H6a": (2, 0),
                 "H6b": (2, 1)}
    for letter, spec in zip("abcdefg", hypotheses.CORRELATIONS):
        ax = axes[positions[spec["hypothesis"]]]
        scatter_with_fit(ax, measures, spec, jitter=0.15)
        plot_style.panel_letter(ax, letter, x=-0.3)
    axes[1, 2].axis("off")
    axes[2, 2].axis("off")
    sample_note(fig, sample)
    plot_style.save(fig, out / "fig5_correlations")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sample", choices=["exploratory", "confirmatory"], default="exploratory")
    args = parser.parse_args()

    out = RESULTS / args.sample
    tests_file = out / "hypothesis_tests.csv"
    if not tests_file.exists():
        sys.exit(f"{tests_file} is missing: run analysis/02_confirmatory.py --sample {args.sample} first.")
    record = run_record.make_record("03_figures.py", args.sample, seed=None,
                                    inputs=[*sorted(study_data.DATA.glob("*.csv")), tests_file])
    plot_style.use()

    participants, valence, arousal = study_data.load()
    measures = hypotheses.participant_measures(participants, valence, arousal)
    primary = study_data.analysis_samples(participants[participants["sample"] == args.sample])["primary"]
    tested, reference = study_data.h3_groups(participants, primary, args.sample)

    results = pd.read_csv(tests_file)
    results = results[results["analysis_sample"] == "primary"].set_index("hypothesis", drop=False)
    h2_rows = [results.loc[h] for h in ("H2a", "H2b", "H2c", "H2d")]
    h3_rows = [results.loc["H3 arousal"], results.loc["H3 valence"]]
    correlation_rows = [results.loc[spec["hypothesis"]] for spec in hypotheses.CORRELATIONS]

    figures = out / "figures"
    group = measures.loc[primary.index]
    time_course(valence, arousal, primary.index, args.sample, figures)
    item_columns = [c for c in participants.columns if c.startswith("sticsa_") and "_item" in c]
    sticsa(group, participants.loc[primary.index, item_columns], results.loc["H1"], args.sample, figures)
    segment_means(group, h2_rows, args.sample, figures)
    replication(valence, arousal, tested, reference, h3_rows, args.sample, figures)
    correlations(group, correlation_rows, args.sample, figures)
    run_record.save_record(record, out)


if __name__ == "__main__":
    main()
