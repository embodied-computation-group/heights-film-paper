"""Step 12: Figure 1 of the Methodology article - the rating screen and the time course in one overview figure.

  (A) the rating screen at 10:36, the scene in which a member of the group is held by one hand over the edge
      (made by 11_task_illustration.py; the dot is the confirmatory group's mean rating at that second)
  (B) arousal and (C) valence over the film: confirmatory participants (faint), confirmatory group mean with 95% CI,
      exploratory group mean (dashed), the four registered segments, and a marker at 10:36 linking back to (A)

Panels B and C are drawn with the same function as the Brief Article's Figure 1 (07_manuscript_figure.py).
Two versions are written: with the film still (figure1_overview) and without it (figure1_overview_nostill), because
showing the still needs the film creator's permission.

Confirmatory sample, primary analysis sample. Run 11_task_illustration.py first, then:
      uv run python analysis/12_overview_figure.py
Writes manuscript/figures/figure1_overview(.pdf/.png), figure1_overview_nostill(.pdf/.png) and a run record.
"""
import importlib.util
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from PIL import Image

ANALYSIS = Path(__file__).resolve().parent
sys.path.insert(0, str(ANALYSIS.parent))  # so `analysis` can be imported
from analysis import plot_style, run_record, study_data  # noqa: E402

OUT = ANALYSIS.parent / "manuscript" / "figures"
DPI = 600


def load_script(filename):
    """Scripts whose names start with a digit are loaded by file path, to reuse their functions."""
    spec = importlib.util.spec_from_file_location(filename.removesuffix(".py"), ANALYSIS / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def mark_moment(ax, second, label):
    """A thin vertical line at the moment shown in panel A, with its film time on top."""
    ax.axvline(second, color=plot_style.TEXT_SOFT, lw=0.8, ls=":", zorder=5)
    if label:
        ax.text(second, 1.01, plot_style.film_time_label(second), transform=ax.get_xaxis_transform(),
                ha="center", va="bottom", fontsize=7, color=plot_style.TEXT, fontweight="bold")


def overview_figure(screen, valence, arousal, confirmatory, exploratory, second, figure_07):
    fig = plt.figure(figsize=(6.9, 8.6))
    grid = fig.add_gridspec(3, 1, height_ratios=[4.2, 2.0, 2.0], hspace=0.28)
    ax_screen = fig.add_subplot(grid[0])
    ax_arousal = fig.add_subplot(grid[1])
    ax_valence = fig.add_subplot(grid[2], sharex=ax_arousal)

    ax_screen.imshow(screen)
    ax_screen.set_axis_off()

    figure_07.time_course_panel(ax_arousal, arousal, confirmatory, exploratory, "arousal", show_segment_names=True)
    figure_07.time_course_panel(ax_valence, valence, confirmatory, exploratory, "valence", show_segment_names=False)
    ax_valence.axhline(50, color=plot_style.GRID, lw=0.8, zorder=1)
    plt.setp(ax_arousal.get_xticklabels(), visible=False)
    plot_style.minutes_axis(ax_valence)
    # The segment names sit on top of the arousal panel; put the 10:36 label just below the top edge instead.
    mark_moment(ax_arousal, second, label=False)
    ax_arousal.text(second + 8, 4, plot_style.film_time_label(second), fontsize=7, color=plot_style.TEXT,
                    fontweight="bold", va="bottom", ha="left")
    mark_moment(ax_valence, second, label=False)
    ax_arousal.legend(loc="lower left", fontsize=7, handlelength=2.2, bbox_to_anchor=(0.0, 0.0))

    for ax, letter, x in ((ax_screen, "A", -0.02), (ax_arousal, "B", -0.08), (ax_valence, "C", -0.08)):
        ax.text(x, 1.02, letter, transform=ax.transAxes, fontsize=11, fontweight="bold", va="bottom")
    return fig


def main():
    figure_07 = load_script("07_manuscript_figure.py")
    task = load_script("11_task_illustration.py")
    screens = {"figure1_overview": OUT / "task_illustration.png",
               "figure1_overview_nostill": OUT / "task_illustration_nostill.png"}
    missing = [str(path) for path in screens.values() if not path.exists()]
    if missing:
        sys.exit(f"Missing {missing}: run analysis/11_task_illustration.py first.")

    record = run_record.make_record("12_overview_figure.py", "confirmatory", seed=None,
                                    inputs=[*sorted(study_data.DATA.glob("*.csv")), *screens.values()],
                                    settings={"second": task.SECOND})
    plot_style.use()
    participants, valence, arousal = study_data.load()
    primary = study_data.analysis_samples(participants[participants["sample"] == "confirmatory"])["primary"].index
    exploratory = participants.index[(participants["sample"] == "exploratory") & study_data.is_usable(participants)]

    for name, screen_path in screens.items():
        fig = overview_figure(Image.open(screen_path), valence, arousal, primary, exploratory, task.SECOND, figure_07)
        for suffix in (".pdf", ".png"):
            fig.savefig(OUT / f"{name}{suffix}", dpi=DPI, bbox_inches="tight")
        plt.close(fig)
        print("wrote", OUT / f"{name}.pdf")
    run_record.save_record(record, OUT)


if __name__ == "__main__":
    main()
