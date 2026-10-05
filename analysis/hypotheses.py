"""The registered tests H1-H6, exactly as in docs/preregistration.md (Statistical models, Inference criteria).

Each test returns one result row (a dictionary) per hypothesis, with the same columns, so that all results end up in
one table. Inference: two-sided alpha = .05 after Holm correction within each family; a directional hypothesis is
supported only if the effect is significant in the predicted direction. H3 is supported if the lower bound of the
95% CI of r is above .50.
"""
import numpy as np
import pandas as pd

from analysis import stats_tools, study_data

ALPHA = 0.05
H3_LOWEST_ACCEPTABLE_R = 0.50
STICSA_ITEMS = ["01", "02", "06", "07", "08", "12", "14", "15", "18", "20", "21"]

# H2: within-participant contrasts of segment means. Each compares `later` with `earlier`; `sign` is the predicted
# direction of later - earlier.
CONTRASTS = [
    {"hypothesis": "H2a", "rating": "arousal", "later": "rise", "earlier": "baseline", "sign": +1},
    {"hypothesis": "H2b", "rating": "arousal", "later": "plateau", "earlier": "baseline", "sign": +1},
    {"hypothesis": "H2c", "rating": "arousal", "later": "return", "earlier": "plateau", "sign": -1},
    {"hypothesis": "H2d", "rating": "valence", "later": "plateau", "earlier": "baseline", "sign": -1},
]

# H4-H6: Spearman correlations across participants, with the predicted sign.
CORRELATIONS = [
    {"hypothesis": "H4a", "x": "height_fear", "y": "arousal_plateau", "sign": +1},
    {"hypothesis": "H4b", "x": "height_fear", "y": "valence_plateau", "sign": -1},
    {"hypothesis": "H4c", "x": "height_fear", "y": "sticsa_change", "sign": +1},
    {"hypothesis": "H5a", "x": "sticsa_change", "y": "arousal_whole_film", "sign": +1},
    {"hypothesis": "H5b", "x": "sticsa_change", "y": "valence_whole_film", "sign": -1},
    {"hypothesis": "H6a", "x": "anxiety_overall", "y": "sticsa_change", "sign": +1},
    {"hypothesis": "H6b", "x": "anxiety_overall", "y": "arousal_plateau", "sign": +1},
]


def direction_word(sign):
    return "positive" if sign > 0 else "negative"


# ------------------------------------------------------------------------------------ participant measures

def sticsa_total(participants, when):
    """Sum of the 11 STICSA somatic items; missing unless all 11 items are answered."""
    items = participants[[f"sticsa_{when}_item{item}" for item in STICSA_ITEMS]]
    return items.sum(axis=1).where(items.notna().all(axis=1))


def participant_measures(participants, valence, arousal):
    """One row per participant with every quantity the tests use.

    `valence` and `arousal` have one row per participant (same order as `participants`) and one column per second.
    The STICSA totals are recomputed from the items and checked against the exported totals.
    """
    measures = pd.DataFrame({"participant": participants["participant"].to_numpy()}, index=participants.index)

    for when in ("pre", "post"):
        total = sticsa_total(participants, when)
        exported = participants[f"sticsa_{when}"]
        disagree = ~((total == exported) | (total.isna() & exported.isna()))
        if disagree.any():
            raise ValueError(f"STICSA {when} total in the data does not equal the sum of its items for "
                             f"{list(participants.loc[disagree, 'participant'])}.")
        measures[f"sticsa_{when}"] = total
    measures["sticsa_change"] = measures["sticsa_post"] - measures["sticsa_pre"]

    measures["height_fear"] = participants["height_fear"].to_numpy()
    measures["anxiety_overall"] = participants["anxiety_overall"].to_numpy()

    for name, ratings in (("valence", valence), ("arousal", arousal)):
        ratings = np.asarray(ratings, float)
        segments = pd.DataFrame([study_data.segment_means(row) for row in ratings], index=participants.index)
        for segment in study_data.SEGMENTS:
            measures[f"{name}_{segment}"] = segments[segment]
        measures[f"{name}_whole_film"] = [study_data.whole_film_mean(row) for row in ratings]
    return measures


# ------------------------------------------------------------------------------------ H1

def test_h1(measures):
    """H1: STICSA somatic total higher after than before the film (paired t-test, dz, Wilcoxon as robustness)."""
    complete = measures[["sticsa_pre", "sticsa_post"]].dropna()
    result = stats_tools.paired_test(complete["sticsa_pre"], complete["sticsa_post"])
    supported = result["p"] < ALPHA and result["mean_difference"] > 0
    return {
        "hypothesis": "H1", "family": "H1",
        "description": "STICSA somatic total: post > pre",
        "test": "paired t-test", "predicted": "post > pre", "n": result["n"],
        "mean_difference": result["mean_difference"],
        "statistic": result["t"], "df": result["df"],
        "estimate_name": "dz", "estimate": result["dz"],
        "ci_low": result["dz_ci_low"], "ci_high": result["dz_ci_high"],
        "p": result["p"], "p_holm": result["p"],  # single test: no correction
        "wilcoxon_p": result["wilcoxon_p"],
        "supported": bool(supported),
    }


# ------------------------------------------------------------------------------------ H2

def test_h2(measures):
    """H2a-d: paired t-tests on segment means, dz with 95% CI, Holm across the four contrasts."""
    rows = []
    for contrast in CONTRASTS:
        earlier = measures[f"{contrast['rating']}_{contrast['earlier']}"]
        later = measures[f"{contrast['rating']}_{contrast['later']}"]
        result = stats_tools.paired_test(earlier, later)
        symbol = ">" if contrast["sign"] > 0 else "<"
        rows.append({
            "hypothesis": contrast["hypothesis"], "family": "H2",
            "description": f"{contrast['rating']}: {contrast['later']} {symbol} {contrast['earlier']}",
            "test": "paired t-test", "predicted": f"{contrast['later']} {symbol} {contrast['earlier']}",
            "n": result["n"], "mean_difference": result["mean_difference"],
            "statistic": result["t"], "df": result["df"],
            "estimate_name": "dz", "estimate": result["dz"],
            "ci_low": result["dz_ci_low"], "ci_high": result["dz_ci_high"],
            "p": result["p"],
        })

    for row, p_holm, contrast in zip(rows, stats_tools.holm([row["p"] for row in rows]), CONTRASTS):
        row["p_holm"] = p_holm
        row["supported"] = bool(p_holm < ALPHA and np.sign(row["mean_difference"]) == contrast["sign"])
    return rows


# ------------------------------------------------------------------------------------ H3

def test_h3(confirmatory_curves, reference_curves, n_boot=5000, seed=0):
    """H3: Pearson r between two group-mean series, circular block bootstrap CI (30 s blocks); supported if the
    lower CI bound exceeds .50. `*_curves` are dictionaries {"arousal": series, "valence": series}."""
    rows = []
    for rating in ("arousal", "valence"):
        result = stats_tools.block_bootstrap_correlation(confirmatory_curves[rating], reference_curves[rating],
                                                         block_length=30, n_boot=n_boot, seed=seed)
        rows.append({
            "hypothesis": f"H3 {rating}", "family": "H3",
            "description": f"group-mean {rating} series: confirmatory vs exploratory",
            "test": "Pearson r, circular block bootstrap (30 s)", "predicted": "CI lower bound > .50",
            "n": len(confirmatory_curves[rating]),
            "estimate_name": "r", "estimate": result["r"],
            "ci_low": result["ci_low"], "ci_high": result["ci_high"],
            "supported": bool(result["ci_low"] > H3_LOWEST_ACCEPTABLE_R),
        })
    return rows


# ------------------------------------------------------------------------------------ H4-H6

def test_correlations(measures, n_boot=5000, seed=0):
    """H4-H6: Spearman correlations with bootstrap 95% CIs; Holm within H4 (3 tests), H5 (2) and H6 (2)."""
    rows = []
    for spec in CORRELATIONS:
        result = stats_tools.spearman_with_ci(measures[spec["x"]], measures[spec["y"]], n_boot=n_boot, seed=seed)
        rows.append({
            "hypothesis": spec["hypothesis"], "family": spec["hypothesis"][:2],
            "description": f"{spec['x']} vs {spec['y']}",
            "test": "Spearman correlation", "predicted": direction_word(spec["sign"]),
            "n": result["n"], "estimate_name": "rho", "estimate": result["rho"],
            "ci_low": result["ci_low"], "ci_high": result["ci_high"], "p": result["p"],
        })

    for family in ("H4", "H5", "H6"):
        members = [i for i, row in enumerate(rows) if row["family"] == family]
        adjusted = stats_tools.holm([rows[i]["p"] for i in members])
        for i, p_holm in zip(members, adjusted):
            rows[i]["p_holm"] = p_holm
            rows[i]["supported"] = bool(p_holm < ALPHA and np.sign(rows[i]["estimate"]) == CORRELATIONS[i]["sign"])
    return rows
