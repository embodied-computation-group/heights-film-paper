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

# Journal artwork rules (Affective Science): at most 174 mm wide and 234 mm high, lettering 8-12 pt with little
# variation, lowercase panel letters, no titles inside figures. Figures are drawn at their printed size.
MAX_WIDTH_MM, MAX_HEIGHT_MM = 174, 234
FULL_WIDTH = MAX_WIDTH_MM / 25.4  # inches
LETTER_SIZE = 10                  # panel letters (a, b, c), bold
PRINT_DPI = 600                   # combination art (colour, lettering) needs at least 600 dpi

RATING_LABELS = {
    "valence": "Valence (0 unpleasant – 100 pleasant)",
    "arousal": "Arousal (0 low – 100 high)",
}


def use():
    """Apply the study style to all following figures."""
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 8,
        "axes.titlesize": 9,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "pdf.fonttype": 42,  # embed the fonts as TrueType, so text stays text in the PDF
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


def film_time_label(seconds):
    """Film time as minutes:seconds, like a video player (636 -> "10:36")."""
    whole = int(seconds)
    return f"{whole // 60}:{whole % 60:02d}"


def panel_letter(ax, letter, x=-0.1, y=1.02):
    """Bold lowercase panel letter at the top left of a panel (the journal asks for a, b, c)."""
    if letter != letter.lower():
        raise ValueError(f"panel letters must be lowercase, got {letter!r}")
    ax.text(x, y, letter, transform=ax.transAxes, fontsize=LETTER_SIZE, fontweight="bold", va="bottom",
            ha="left")


def save_print(fig, path):
    """Save a journal figure at exactly its drawn size: PDF (vector, fonts embedded) and a 600-dpi PNG.
    Refuses figures larger than the journal allows. No tight cropping, so the size stays as drawn."""
    width, height = (size * 25.4 for size in fig.get_size_inches())
    if width > MAX_WIDTH_MM + 0.01 or height > MAX_HEIGHT_MM + 0.01:
        raise ValueError(f"figure is {width:.0f} x {height:.0f} mm; the journal allows at most "
                         f"{MAX_WIDTH_MM} x {MAX_HEIGHT_MM} mm")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path.with_suffix(".pdf"))
    fig.savefig(path.with_suffix(".png"), dpi=PRINT_DPI)
    plt.close(fig)
    print("wrote", path.with_suffix(".pdf"), f"({width:.0f} x {height:.0f} mm)")


def save(fig, path):
    """Save as PNG (for viewing) and PDF (for the paper)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path.with_suffix(".png"), bbox_inches="tight")
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    print("wrote", path.with_suffix(".png"))
