"""Pre vs post STICSA somatic subscale (descriptive).

Run after qc/review.py:  python qc/plot_sticsa.py
Writes
  qc/out/sticsa_pre_post.png  left: paired totals per participant coloured by study; right: change per item
  qc/out/sticsa_items_stacked.png  lab figure style (cf. HauntedHearts Fig. 2): A pre/post boxplots of the
      total with paired lines; B item-level stacked proportions of responses 1-4, faceted Pre / Post
Options: --study anxiety|affect2d restricts to one study (default: all).
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from qc_lib import load_session, scope_filter  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW, OUT = ROOT / "data" / "raw", ROOT / "qc" / "out"
# Reference categorical palette (validated: CVD dE 24.7, normal dE 33.6, contrast >= 3:1 on #fcfcfb)
COLORS = {"anxiety": "#2a78d6", "affect2d": "#eb6834"}
LABELS = {"anxiety": "Study 1 · anxiety", "affect2d": "Study 2 · valence × arousal"}
INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"


SHORT = {1: "Heartbeat", 2: "Tense", 6: "Dizzy", 7: "Weak", 8: "Shaky", 12: "Face hot", 14: "Stiff limbs",
         15: "Dry throat", 18: "Breathing", 20: "Butterflies", 21: "Clammy palms"}
# Responses cool -> hot (more anxiety = hotter): diverging blue <-> red arms, two steps each, no neutral midpoint
# (4 levels). Validated: adjacent CVD dE >= 14.9, normal-vision dE >= 20.6; light steps < 3:1 contrast are
# relieved by the labelled legend. Pre / Post boxes: cool / hot.
RESP_COLORS = {1: "#1c5cab", 2: "#6da7ec", 3: "#ef8a85", 4: "#c62f2f"}
TIME_COLORS = {"Pre": "#6da7ec", "Post": "#ef8a85"}


def plot_stacked(df: pd.DataFrame, it: pd.DataFrame, out: Path, title_note: str) -> None:
    plt.rcParams.update({"font.size": 12, "axes.edgecolor": "#222222", "axes.labelcolor": "#111111",
                         "xtick.color": "#111111", "ytick.color": "#111111"})
    fig = plt.figure(figsize=(14, 7), facecolor="white")
    gs = fig.add_gridspec(2, 3, width_ratios=[0.8, 0.5, 2.2], height_ratios=[1, 1], wspace=0.05, hspace=0.08)
    ax = fig.add_subplot(gs[:, 0])
    # A: boxplots of totals with paired lines
    for _, r in df.iterrows():
        ax.plot([0.15, 0.85], [r["pre"], r["post"]], color="#c8c8c8", lw=1.2, zorder=1)
        ax.scatter([0.15, 0.85], [r["pre"], r["post"]], s=22, facecolor="white", edgecolor="#333333", lw=0.8, zorder=3)
    bp = ax.boxplot([df["pre"], df["post"]], positions=[-0.15, 1.15], widths=0.18, patch_artist=True,
                    medianprops={"color": "#222222", "lw": 2}, whiskerprops={"color": "#333333"},
                    capprops={"color": "#333333"}, flierprops={"marker": ""})
    for patch, t in zip(bp["boxes"], ("Pre", "Post")):
        patch.set_facecolor(TIME_COLORS[t])
        patch.set_edgecolor("#333333")
    # mean +/- SEM across participants, drawn over the paired lines
    n = len(df)
    means = [df["pre"].mean(), df["post"].mean()]
    sems = [df["pre"].std(ddof=1) / np.sqrt(n), df["post"].std(ddof=1) / np.sqrt(n)] if n > 1 else [0, 0]
    ax.errorbar([0.15, 0.85], means, yerr=sems, color="#111111", lw=2.6, capsize=6, capthick=2,
                marker="o", markersize=8, markerfacecolor="white", markeredgecolor="#111111", markeredgewidth=2,
                zorder=5)
    ax.set_xticks([0.5], ["Somatic Anxiety"])
    ax.set_xlim(-0.4, 1.4)
    ax.set_ylim(10, 45)
    ax.set_ylabel("STICSA somatic total (11–44)")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.set_title("Somatic Anxiety", loc="left", fontsize=15, fontweight="bold", pad=58)
    handles = [plt.Rectangle((0, 0), 1, 1, facecolor=TIME_COLORS[t], edgecolor="#333333") for t in ("Pre", "Post")]
    handles.append(plt.Line2D([0], [0], color="#111111", lw=2.6, marker="o", markersize=7, markerfacecolor="white",
                              markeredgecolor="#111111", markeredgewidth=2))
    ax.legend(handles, ["Pre", "Post", "Mean ± SEM"], title="Time", ncol=3, loc="lower left", bbox_to_anchor=(0, 1.0),
              frameon=False, fontsize=11, title_fontsize=12, alignment="left")
    fig.text(0.02, 0.94, "A", fontsize=16, fontweight="bold")

    # B: stacked proportions per item, Pre and Post facets
    items_order = [n for n in SHORT if n in set(it["item"])]
    for row, tp in enumerate(("pre", "post")):
        bx = fig.add_subplot(gs[row, 2])
        sub = it[it["timepoint"] == tp]
        props = (sub.groupby("item")["response"].value_counts(normalize=True).unstack(fill_value=0)
                 .reindex(index=items_order, columns=[1, 2, 3, 4], fill_value=0))
        y = np.arange(len(items_order))[::-1]
        left = np.zeros(len(items_order))
        for k in (1, 2, 3, 4):
            anchors = {1: "Not at all", 2: "A little", 3: "Moderately", 4: "Very much so"}
            bx.barh(y, props[k].to_numpy(), left=left, height=0.86, color=RESP_COLORS[k], label=f"{k} {anchors[k]}",
                    edgecolor="white", linewidth=1.5)
            left += props[k].to_numpy()
        bx.set_yticks(y, [SHORT[n] for n in items_order])
        bx.set_xlim(0, 1)
        bx.set_ylim(-0.6, len(items_order) - 0.4)
        for side in ("top", "right"):
            bx.spines[side].set_visible(False)
        if row == 0:
            bx.set_xticks([])
            bx.spines["bottom"].set_visible(False)
            bx.set_title("Item-Level Responses", loc="left", fontsize=15, fontweight="bold", pad=58)
            bx.legend(title="Rating", ncol=4, loc="lower left", bbox_to_anchor=(0, 1.0), frameon=False,
                      fontsize=11, title_fontsize=12, alignment="left", handlelength=1.2)
        else:
            bx.set_xticks([0, 0.25, 0.5, 0.75, 1], ["0%", "25%", "50%", "75%", "100%"])
            bx.set_xlabel("Proportion of Responses")
        strip = bx.inset_axes([1.01, 0, 0.04, 1])
        strip.set_facecolor("#d0d0d0")
        strip.set_xticks([])
        strip.set_yticks([])
        for sp in strip.spines.values():
            sp.set_visible(False)
        strip.text(0.5, 0.5, tp.capitalize(), rotation=270, ha="center", va="center", fontsize=13)
    fig.text(0.385, 0.94, "B", fontsize=16, fontweight="bold")
    fig.text(0.01, 0.005, title_note, fontsize=9, color="#555555")
    fig.subplots_adjust(left=0.06, right=0.95, top=0.8, bottom=0.1)
    try:
        fig.savefig(out, dpi=120, facecolor="white")
    except OSError:  # file open in a viewer (Windows locks it): save under a new name
        out = out.with_name(f"{out.stem}_{pd.Timestamp.now():%H%M%S}{out.suffix}")
        fig.savefig(out, dpi=120, facecolor="white")
    print("wrote", out)
    plt.close(fig)


def main() -> None:
    study_filter = sys.argv[sys.argv.index("--study") + 1] if "--study" in sys.argv else None
    rep = pd.read_csv(OUT / "qc_report.csv")
    rep = scope_filter(rep)  # exploratory sample unless --confirmatory / --all
    keep = set(rep.loc[(rep["completed"] == True) & (rep["verdict"] != "REJECT-ELIGIBLE"), "prolific_pid"])  # noqa: E712
    rows, items, long_items = [], [], []
    for p in sorted(RAW.glob("*.ndjson")):
        s = load_session(p)
        if not s.meta or s.pid not in keep or (study_filter and s.dimension != study_filter):
            continue
        pre, post = s.trial("sticsa", timepoint="pre"), s.trial("sticsa", timepoint="post")
        if not pre or not post or pre[-1]["total"] is None or post[-1]["total"] is None:
            continue
        rows.append({"pid": s.pid, "study": s.dimension, "pre": pre[-1]["total"], "post": post[-1]["total"]})
        for a, b in zip(pre[-1]["items"], post[-1]["items"]):
            items.append({"pid": s.pid, "study": s.dimension, "item": a["item"], "text": a["text"],
                          "change": b["response"] - a["response"]})
            long_items.append({"pid": s.pid, "item": a["item"], "timepoint": "pre", "response": a["response"]})
            long_items.append({"pid": s.pid, "item": b["item"], "timepoint": "post", "response": b["response"]})
    df, it = pd.DataFrame(rows), pd.DataFrame(items)
    if df.empty:
        print("no complete pre/post STICSA pairs")
        return

    plt.rcParams.update({"font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                         "xtick.color": INK2, "ytick.color": INK2, "text.color": INK})
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(12, 5.6), gridspec_kw={"width_ratios": [1, 1.6]}, facecolor=SURFACE)
    for a in (ax, bx):
        a.set_facecolor(SURFACE)
        for side in ("top", "right"):
            a.spines[side].set_visible(False)

    # --- left: paired slope plot -----------------------------------------------------------
    rng = np.random.default_rng(0)
    for study, g in df.groupby("study"):
        c = COLORS.get(study, INK2)
        for _, r in g.iterrows():
            j = rng.uniform(-0.03, 0.03)
            ax.plot([0 + j, 1 + j], [r["pre"], r["post"]], color=c, lw=1.2, alpha=0.55, zorder=2)
            ax.scatter([0 + j, 1 + j], [r["pre"], r["post"]], s=40, color=c, edgecolor=SURFACE, linewidth=2, zorder=3)
        m = g[["pre", "post"]].mean()
        ax.plot([0, 1], [m["pre"], m["post"]], color=c, lw=3, zorder=4, solid_capstyle="round",
                label=f"{LABELS.get(study, study)} (n={len(g)})")
        ax.annotate(f"mean +{m['post'] - m['pre']:.1f}", (1, m["post"]), xytext=(10, 0), textcoords="offset points",
                    va="center", fontsize=9, color=INK2)
    ax.set_xticks([0, 1], ["Before film", "After film"])
    ax.set_xlim(-0.25, 1.45)
    ax.set_ylim(10, 45)
    ax.axhline(11, color=GRID, lw=1, zorder=1)
    ax.set_ylabel("STICSA somatic total (11–44)")
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", frameon=False, fontsize=9)
    ax.set_title("Somatic anxiety before vs after the film", loc="left", fontsize=11, color=INK)

    # --- right: item-level change ------------------------------------------------------------
    order = it.groupby(["item", "text"])["change"].mean().reset_index().sort_values("change")
    ypos = {r["item"]: i for i, r in enumerate(order.to_dict("records"))}
    bx.barh(range(len(order)), order["change"], height=0.55, color=GRID, zorder=1)
    for study, g in it.groupby("study"):
        off = -0.13 if study == "anxiety" else 0.13
        y = g["item"].map(ypos) + off + rng.uniform(-0.05, 0.05, len(g))
        bx.scatter(g["change"], y, s=26, color=COLORS.get(study, INK2), edgecolor=SURFACE, linewidth=1.5, zorder=3,
                   label=LABELS.get(study, study))
    bx.set_yticks(range(len(order)), [f"{t}  ({n})" for n, t in zip(order["item"], order["text"])], fontsize=9)
    bx.axvline(0, color=INK2, lw=1, zorder=2)
    bx.set_xlim(-3.3, 3.3)
    bx.set_xticks(range(-3, 4))
    bx.set_xlabel("Change after − before (response points, 1–4 scale)")
    bx.grid(axis="x", color=GRID, lw=0.8)
    bx.set_axisbelow(True)
    bx.set_title("Change per item (bar = mean, dots = participants)", loc="left", fontsize=11, color=INK)
    bx.legend(loc="lower right", frameon=False, fontsize=9)

    fig.text(0.01, 0.01, f"n = {len(df)} completed sessions; descriptive only. Item numbers are original STICSA numbers.",
             fontsize=8, color=INK2)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    out = OUT / "sticsa_pre_post.png"
    fig.savefig(out, dpi=110, facecolor=SURFACE)
    suffix = f"_{study_filter}" if study_filter else ""
    note = (f"n = {len(df)} completed sessions" + (f" ({study_filter})" if study_filter else " (both studies pooled)")
            + "; STICSA state form, somatic subscale; descriptive.")
    plot_stacked(df, pd.DataFrame(long_items), OUT / f"sticsa_items_stacked{suffix}.png", note)
    print(df.assign(change=df["post"] - df["pre"]).to_string(index=False))
    print("wrote", out)


if __name__ == "__main__":
    main()
