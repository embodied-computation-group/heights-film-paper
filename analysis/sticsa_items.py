"""EXPLORATORY: how much each STICSA somatic item changed from before to after the film.

Not a registered test. For each of the 11 items: mean before and after, mean change, share of participants whose
answer went up, Cohen's dz with its 95% CI, and a Wilcoxon signed-rank test (answers are 1-4, so ordinal), with Holm
correction across the items. Items are ranked from the largest to the smallest change (by dz).
"""
import numpy as np
import pandas as pd
from scipy import stats

from analysis import stats_tools

ITEMS = ["01", "02", "06", "07", "08", "12", "14", "15", "18", "20", "21"]
# Short labels (the full STICSA item wording is not reproduced here).
LABELS = {"01": "Heart beats fast", "02": "Muscles tense", "06": "Dizzy", "07": "Muscles weak", "08": "Trembly, shaky",
          "12": "Face hot", "14": "Arms and legs stiff", "15": "Throat dry", "18": "Breathing fast, shallow",
          "20": "Butterflies in stomach", "21": "Palms clammy"}


def item_changes(answers):
    """`answers` has columns sticsa_pre_itemNN and sticsa_post_itemNN (one row per participant)."""
    rows = []
    for item in ITEMS:
        before = answers[f"sticsa_pre_item{item}"].astype(float)
        after = answers[f"sticsa_post_item{item}"].astype(float)
        change = after - before
        row = {"item": item, "label": LABELS[item], "n": len(change), "mean_before": before.mean(),
               "mean_after": after.mean(), "mean_change": change.mean(), "share_increased": (change > 0).mean(),
               "dz": np.nan, "dz_ci_low": np.nan, "dz_ci_high": np.nan, "p": np.nan}
        if (change != 0).any():
            dz = change.mean() / change.std(ddof=1)
            low, high = stats_tools.dz_confidence_interval(dz, len(change))
            row.update({"dz": dz, "dz_ci_low": low, "dz_ci_high": high, "p": stats.wilcoxon(after, before).pvalue})
        rows.append(row)

    table = pd.DataFrame(rows)
    tested = table["p"].notna()
    table["p_holm"] = np.nan
    table.loc[tested, "p_holm"] = stats_tools.holm(list(table.loc[tested, "p"]))
    table = table.sort_values(["dz", "mean_change"], ascending=False, na_position="last").reset_index(drop=True)
    table.insert(0, "rank", range(1, len(table) + 1))
    return table
