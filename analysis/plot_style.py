"""One plot style for the whole study. DRAFT - to be agreed with Micah before the figures are final.

Colours run cool to hot: valence is blue (cool), arousal is crimson (hot); the four film segments are shaded from
pale blue (baseline) through lilac (rise) to pale rose (plateau) and pale teal (return). No orange or black.
The valence/arousal pair passes a colour-vision-deficiency check (dataviz validator: protan dE 22, normal dE 31).
Where two curves of the same rating are compared, they differ by line style, not by an extra colour.
"""
import matplotlib

matplotlib.use("Agg")  # draw to files, no window needed
import matplotlib.pyplot as plt  # noqa: E402

from analysis import study_data  # noqa: E402

VALENCE = "#2a6fd6"   # cool
AROUSAL = "#c8324a"   # hot
RATING_COLOURS = {"valence": VALENCE, "arousal": AROUSAL}

# Before / after the film: cool / hot. STICSA item responses 1-4 run cool to hot (more anxiety = hotter); this
# 4-step palette comes from the exploratory STICSA figure in vmp_film_rating (validated there: adjacent CVD dE >= 14.9).
BEFORE, AFTER = "#6da7ec", "#ef8a85"
STICSA_RESPONSE_COLOURS = {1: "#1c5cab", 2: "#6da7ec", 3: "#ef8a85", 4: "#c62f2f"}

# Groups by sex (exploratory figures): purple / teal, also told apart by line style. Validated with the dataviz
# checker: CVD dE 14.1, normal-vision dE 25.0.
SEX_COLOURS = {"Female": "#8a4fc7", "Male": "#00897b"}
SEX_LINES = {"Female": "-", "Male": "--"}

SEGMENT_SHADES ={"baseline": "#e9f0fb", "rise": "#f0eaf8", "plateau": "#fbe7ea", "return": "#e5f3f1"}

TEXT = "#2b2d33"         # dark grey, not black
TEXT_SOFT = "#5f636d"
GRID = "#d9dbe0"
PARTICIPANT_ALPHA = 0.18  # thin, faint lines/points for single participants

RATING_LABELS = {
    "valence": "Valence (0 unpleasant – 100 pleasant)",
    "arousal": "Arousal (0 low – 100 high)",
}


def use():
    """Apply the study style to all following figures."""
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.labelsize": 9,
        "axes.edgecolor": TEXT_SOFT,
        "axes.labelcolor": TEXT,
        "axes.titlecolor": TEXT,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "xtick.color": TEXT_SOFT,
        "ytick.color": TEXT_SOFT,
        "xtick.labelcolor": TEXT,
        "ytick.labelcolor": TEXT,
        "text.color": TEXT,
        "legend.frameon": False,
        "lines.linewidth": 1.6,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "savefig.dpi": 300,
    })


def shade_segments(ax, label=True):
    """Shade the four registered segments and (optionally) name them along the top of the axes."""
    for name, (start, end) in study_data.SEGMENTS.items():
        ax.axvspan(start, end, color=SEGMENT_SHADES[name], lw=0, zorder=0)
        if label:
            ax.text((start + end) / 2, 1.01, name, transform=ax.get_xaxis_transform(), ha="center", va="bottom",
                    fontsize=8, color=TEXT_SOFT)


def minutes_axis(ax):
    """Film time on the x-axis in minutes (data are in seconds)."""
    ax.set_xlim(0, study_data.FILM_SECONDS)
    ticks = range(0, study_data.FILM_SECONDS + 1, 120)
    ax.set_xticks(list(ticks), [str(t // 60) for t in ticks])
    ax.set_xlabel("Film time (min)")


def save(fig, path):
    """Save as PNG (for viewing) and PDF (for the paper)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path.with_suffix(".png"), bbox_inches="tight")
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    print("wrote", path.with_suffix(".png"))
