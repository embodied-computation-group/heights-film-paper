"""Step 14: the session workflow of the rating platform (Supplementary Figure S2). No data are used.

A simple box-and-arrow diagram. Top row: the steps of a session, in the order the task runs them. Bottom row: what
is recorded throughout the session, and the quality review afterwards. The contents follow the task code at tag
v1.0-heights-film of online-affect-rating (task/js/experiment.js) and the registered exclusion rules
(docs/preregistration.md).

Run:  uv run python analysis/14_workflow_figure.py
Writes manuscript/figures/figure2_workflow (.pdf and .png).
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # so `analysis` can be imported
from analysis import plot_style  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "manuscript" / "figures"

# Colours, cool to hot, as in the rest of the study: before the film blue, the film purple, after the film rose,
# quality review teal. Each box has a pale fill and a stronger edge.
BEFORE = ("#e9f0fb", "#6da7ec")
FILM = ("#f0eaf8", "#8a4fc7")
AFTER = ("#fbe7ea", "#c8324a")
REVIEW = ("#e5f3f1", "#00897b")
LOGGED = ("#f3f4f6", "#9aa0aa")

# The session, in order: (title, lines of text, colours).
SESSION = [
    ("Consent", ["Information sheet", "Device check"], BEFORE),
    ("Questions", ["Fear of heights", "Attention check"], BEFORE),
    ("Practice", ["Track a moving", "target", "Place six", "situations, with", "feedback"], BEFORE),
    ("Film ready", ["Film downloaded", "in full", "STICSA (before)"], BEFORE),
    ("Rate the film", ["Affect grid over", "the video", "Full screen", "Sampled at 20 Hz"], FILM),
    ("After the film", ["STICSA (after)", "Ratings and", "checklists", "Attention check", "Written account"], AFTER),
]

LOGGED_LINES = [
    "Film pauses if the tab or full screen is left   •   saved every 30 s; resumes after a reload",
    "Mouse, keyboard and text-entry events kept   •   pasting blocked in text fields",
]
REVIEW_LINES = ["Automated flags", "prompt review", "Registered", "exclusion rules"]

BOX_W, GAP = 0.14, 0.028   # box width and the gap (with arrow) between boxes, in axes units
TOP_Y, TOP_H = 0.46, 0.52  # session row
LOW_Y, LOW_H = 0.01, 0.31  # logging and review row


def box(ax, x, y, w, h, title, lines, colours):
    """One rounded box with a bold title and short lines of text."""
    fill, edge = colours
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.015",
                                facecolor=fill, edgecolor=edge, lw=1.3))
    ax.text(x + w / 2, y + h - 0.045, title, ha="center", va="top", fontsize=7.6, fontweight="bold",
            color=plot_style.TEXT)
    for i, line in enumerate(lines):
        ax.text(x + w / 2, y + h - 0.12 - i * 0.064, line, ha="center", va="top", fontsize=6.2,
                color=plot_style.TEXT)


def arrow(ax, start, end):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=10, lw=1.1,
                                 color=plot_style.TEXT_SOFT, shrinkA=0, shrinkB=0))


def main():
    plot_style.use()
    fig, ax = plt.subplots(figsize=(7.0, 2.7))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_axis_off()

    # Top row: the session, left to right.
    xs = [i * (BOX_W + GAP) + 0.01 for i in range(len(SESSION))]
    for i, (title, lines, colours) in enumerate(SESSION):
        box(ax, xs[i], TOP_Y, BOX_W, TOP_H, title, lines, colours)
        if i < len(SESSION) - 1:
            arrow(ax, (xs[i] + BOX_W + 0.004, TOP_Y + TOP_H / 2), (xs[i + 1] - 0.004, TOP_Y + TOP_H / 2))

    # Bottom row: recorded throughout (under the first five steps), then the quality review (under the last).
    log_w = xs[4] + BOX_W - xs[0]
    box(ax, xs[0], LOW_Y, log_w, LOW_H, "Recorded throughout the session", [], LOGGED)
    for i, line in enumerate(LOGGED_LINES):
        ax.text(xs[0] + log_w / 2, LOW_Y + LOW_H - 0.14 - i * 0.07, line, ha="center", va="top", fontsize=6.2,
                color=plot_style.TEXT)
    box(ax, xs[5], LOW_Y, BOX_W, LOW_H, "Quality review", [], REVIEW)
    for i, line in enumerate(REVIEW_LINES):
        ax.text(xs[5] + BOX_W / 2, LOW_Y + LOW_H - 0.12 - i * 0.045, line, ha="center", va="top", fontsize=6.2,
                color=plot_style.TEXT)

    # The session's data and the logged events both go to the quality review.
    arrow(ax, (xs[5] + BOX_W / 2, TOP_Y - 0.004), (xs[5] + BOX_W / 2, LOW_Y + LOW_H + 0.004))
    arrow(ax, (xs[4] + BOX_W + 0.004, LOW_Y + LOW_H / 2), (xs[5] - 0.004, LOW_Y + LOW_H / 2))

    OUT.mkdir(parents=True, exist_ok=True)
    for suffix in (".pdf", ".png"):
        fig.savefig(OUT / f"figure2_workflow{suffix}", dpi=600, bbox_inches="tight")
    plt.close(fig)
    print("wrote", OUT / "figure2_workflow.pdf")


if __name__ == "__main__":
    main()
