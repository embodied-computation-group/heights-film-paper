"""Step 5: numbers and tables for the results report (manuscript/results.tex), straight from the data and results.

Run after 01-04 on the confirmatory sample:
      uv run python analysis/05_report_numbers.py

Writes manuscript/generated/:
  numbers.tex             every number quoted in the text, as \\val{key} (the report never types a number by hand)
  table_descriptives.tex  Table 1: descriptive statistics of the primary confirmatory sample
  table_confirmatory.tex  Table 2: the registered tests in the primary sample
  table_sensitivity.tex   the registered tests in the two sensitivity samples
  table_sample.tex        sample characteristics
  table_age_sex.tex       exploratory age and sex analyses
"""
import json
import sys
from pathlib import Path

import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # so `analysis` can be imported
from analysis import hypotheses, run_record, study_data  # noqa: E402
from analysis import report_format as fmt  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results" / "confirmatory"
OUT = ROOT / "manuscript" / "generated"

SAMPLE_NAMES = {"primary": "Primary", "stricter_engagement": "Stricter engagement",
                "without_rejected": "Rejection set removed"}
PREDICTIONS = {
    "H1": "STICSA somatic: post $>$ pre",
    "H2a": "Arousal: rise $>$ baseline",
    "H2b": "Arousal: plateau $>$ baseline",
    "H2c": "Arousal: return $<$ plateau",
    "H2d": "Valence: plateau $<$ baseline",
    "H3 arousal": "Arousal curve replicates",
    "H3 valence": "Valence curve replicates",
    "H4a": "Fear of heights, plateau arousal (+)",
    "H4b": "Fear of heights, plateau valence ($-$)",
    "H4c": "Fear of heights, STICSA change (+)",
    "H5a": "STICSA change, whole-film arousal (+)",
    "H5b": "STICSA change, whole-film valence ($-$)",
    "H6a": "Overall anxiety, STICSA change (+)",
    "H6b": "Overall anxiety, plateau arousal (+)",
}


# ------------------------------------------------------------------------------------------- helpers

def effect_text(row, with_name=True):
    """Effect size with its 95% CI, e.g. 'd_z = 1.03 [0.81, 1.25]' or 'rho = .08 [-.09, .26]'."""
    if row["estimate_name"] == "dz":
        value = f"{fmt.number(row['estimate'])} {fmt.ci(row['ci_low'], row['ci_high'])}"
        name = "$d_z$"
    else:
        digits = 3 if row["estimate_name"] == "r" else 2
        value = (f"{fmt.tex(fmt.bounded(row['estimate'], digits))} "
                 f"{fmt.ci(row['ci_low'], row['ci_high'], between_minus_one_and_one=True, digits=digits)}")
        name = "$r$" if row["estimate_name"] == "r" else "$\\rho$"
    return f"{name} = {value}" if with_name else value


def in_text_report(row):
    """The full APA string for a test, for use in the text."""
    if row["estimate_name"] == "dz":
        return (f"$t$({int(row['df'])}) = {fmt.number(row['statistic'])}, "
                f"$p_\\mathrm{{Holm}}$ {fmt.p(row['p_holm'])}, $d_z$ = {fmt.number(row['estimate'])}, "
                f"95\\% CI {fmt.ci(row['ci_low'], row['ci_high'])}")
    if row["estimate_name"] == "r":
        return f"$r$ = {fmt.bounded(row['estimate'], 3)}, 95\\% CI {fmt.ci(row['ci_low'], row['ci_high'], True, 3)}"
    return (f"$\\rho$ = {fmt.tex(fmt.bounded(row['estimate']))}, 95\\% CI "
            f"{fmt.ci(row['ci_low'], row['ci_high'], True)}, $p$ {fmt.p(row['p'])}, "
            f"$p_\\mathrm{{Holm}}$ {fmt.p(row['p_holm'])}")


def write_values(values, path):
    """Each value becomes \\val{key} in LaTeX; an unknown key stops the LaTeX run with an error."""
    lines = ["% Written by analysis/05_report_numbers.py - do not edit by hand.",
             "\\newcommand{\\val}[1]{\\ifcsname val:#1\\endcsname\\csname val:#1\\endcsname"
             "\\else\\errmessage{Unknown value #1}\\fi}"]
    for key, value in values.items():
        lines.append(f"\\expandafter\\def\\csname val:{key}\\endcsname{{{value}}}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ------------------------------------------------------------------------------------------- sample

def count_and_percent(mask):
    return f"{int(mask.sum())} ({100 * mask.mean():.0f})"


def mean_sd(values, digits=1):
    values = values.dropna()
    return f"{fmt.number(values.mean(), digits)} ({fmt.number(values.std(), digits)})"


def sample_table(columns):
    """Sample characteristics. `columns` = [(heading, measures, participants), ...] for the same people."""
    rows = [
        ("$n$", lambda m, p: str(len(p))),
        ("Age, years, $M$ ($SD$)", lambda m, p: mean_sd(p["age"])),
        ("\\hspace{1em}Range", lambda m, p: f"{p['age'].min():.0f}--{p['age'].max():.0f}"),
        ("Sex, $n$ (\\%)", None),
        ("\\hspace{1em}Female", lambda m, p: count_and_percent(p["sex"] == "Female")),
        ("\\hspace{1em}Male", lambda m, p: count_and_percent(p["sex"] == "Male")),
        ("\\hspace{1em}Not available\\tnote{a}", lambda m, p: count_and_percent(p["sex"].isna())),
        ("Input device, $n$ (\\%)", None),
        ("\\hspace{1em}Mouse", lambda m, p: count_and_percent(p["input_device"] == "Mouse")),
        ("\\hspace{1em}Trackpad", lambda m, p: count_and_percent(p["input_device"] == "Trackpad / touchpad")),
        ("\\hspace{1em}Other", lambda m, p: count_and_percent(p["input_device"] == "Other")),
        ("Everyday fear of heights (1--7), $M$ ($SD$)", lambda m, p: mean_sd(m["height_fear"], 2)),
        ("STICSA somatic, pre-film (11--44), $M$ ($SD$)", lambda m, p: mean_sd(m["sticsa_pre"], 2)),
        ("Failed one attention check, $n$ (\\%)", lambda m, p: count_and_percent(p["attention_failed"] == 1)),
        ("Excluded under registered rules, $n$", lambda m, p: str(int((~study_data.is_usable(p)).sum()))),
    ]
    lines = []
    for label, cell in rows:
        if cell is None:
            lines.append(f"{label} & & & \\\\")
        else:
            lines.append(f"{label} & " + " & ".join(cell(m, p) for _, m, p in columns) + " \\\\")
    header = " & ".join(heading for heading, _, _ in columns)
    return "\n".join([
        "\\begin{table}[tbp]",
        "\\caption{Sample Characteristics}",
        "\\label{tab:sample}",
        "\\begin{threeparttable}",
        "\\small\\linespread{1}\\selectfont",
        "\\begin{tabular}{@{}l*{3}{>{\\centering\\arraybackslash}p{2.6cm}}@{}}",
        "\\toprule",
        f"Characteristic & {header} \\\\",
        "\\midrule",
        *lines,
        "\\bottomrule",
        "\\end{tabular}",
        "\\vspace{4pt}",
        "\\begin{tablenotes}[para,flushleft]",
        "{\\small\\textit{Note.} Exploratory sample: pilot and cohort 1, usable under the registered rules (reference "
        "curve for H3). Confirmatory sample: cohorts 2--4. Age and sex are Prolific profile data; input device is "
        "self-reported. STICSA = State-Trait Inventory for Cognitive and Somatic Anxiety, state somatic subscale. "
        "\\tnote{a}Prolific withholds demographic data for rejected submissions.}",
        "\\end{tablenotes}",
        "\\end{threeparttable}",
        "\\end{table}",
    ])


def sample_values(participants, completers, samples):
    values = {}
    usable = samples["primary"]
    excluded = completers[~study_data.is_usable(completers)]
    values["n_completed"] = len(completers)
    values["n_excluded"] = len(excluded)
    values["n_primary"] = len(usable)
    rules = excluded["registered_exclusion"].str.split("; ").explode().value_counts()
    for rule, key in (("disrupted viewing", "disrupted"), ("free text not typed", "freetext"),
                      ("erratic input", "erratic")):
        values[f"n_excl_{key}"] = int(rules.get(rule, 0))
    for cohort, key in (("cohort 2", "two"), ("cohort 3", "three"), ("cohort 4", "four")):
        values[f"n_cohort_{key}"] = int((usable["cohort"] == cohort).sum())

    ages = usable["age"].dropna()
    values.update({"n_age": len(ages), "age_mean": fmt.number(ages.mean(), 1), "age_sd": fmt.number(ages.std(), 1),
                   "age_min": int(ages.min()), "age_max": int(ages.max()),
                   "n_female": int((usable["sex"] == "Female").sum()), "n_male": int((usable["sex"] == "Male").sum()),
                   "n_sex_missing": int(usable["sex"].isna().sum()),
                   "n_mouse": int((usable["input_device"] == "Mouse").sum()),
                   "n_trackpad": int((usable["input_device"] == "Trackpad / touchpad").sum())})

    # Sensitivity samples: how many people each extra rule removes from the primary sample (rules can overlap).
    sparse = (usable["bouts_per_min"] < 1) | (usable["longest_gap_s"] > 180)
    values.update({"n_stricter": len(samples["stricter_engagement"]),
                   "n_sparse": int(sparse.sum()),
                   "n_one_check": int((usable["attention_failed"] >= 1).sum()),
                   "n_not_attentive": int((usable["full_attention"] == "No").sum()),
                   "n_without_rejected": len(samples["without_rejected"]),
                   "n_rejection_set": int(usable["in_rejection_set"].sum())})

    exploratory = participants[participants["sample"] == "exploratory"]
    values["n_exploratory_completed"] = len(exploratory)
    values["n_exploratory"] = int(study_data.is_usable(exploratory).sum())
    return values


# ------------------------------------------------------------------------------------------- descriptives

DESCRIPTIVE_ROWS = [
    ("Before the film", None, None),
    ("Everyday fear of heights", "height_fear", "1--7"),
    ("STICSA somatic, pre-film", "sticsa_pre", "11--44"),
    ("After the film", None, None),
    ("STICSA somatic, post-film", "sticsa_post", "11--44"),
    ("STICSA somatic change (post $-$ pre)", "sticsa_change", ""),
    ("Overall anxiety while watching", "anxiety_overall", "1--7"),
    ("Concern for the climbers' safety", "concern_safety", "1--7"),
    ("Intensity of bodily sensations", "body_intensity", "1--7"),
    ("Continuous arousal", None, None),
    ("Baseline (0:00--4:22)", "arousal_baseline", "0--100"),
    ("Rise (4:22--7:50)", "arousal_rise", "0--100"),
    ("Plateau (7:50--11:32)", "arousal_plateau", "0--100"),
    ("Return (11:32--13:28)", "arousal_return", "0--100"),
    ("Whole film", "arousal_whole_film", "0--100"),
    ("Continuous valence", None, None),
    ("Baseline (0:00--4:22)", "valence_baseline", "0--100"),
    ("Rise (4:22--7:50)", "valence_rise", "0--100"),
    ("Plateau (7:50--11:32)", "valence_plateau", "0--100"),
    ("Return (11:32--13:28)", "valence_return", "0--100"),
    ("Whole film", "valence_whole_film", "0--100"),
]


def descriptives(group):
    """Table 1 and the matching values for the text."""
    values = {}
    lines = []
    for label, column, scale in DESCRIPTIVE_ROWS:
        if column is None:
            lines.append(f"\\multicolumn{{6}}{{l}}{{\\textit{{{label}}}}} \\\\")
            continue
        x = group[column].dropna()
        lines.append(f"\\hspace{{1em}}{label} & {scale} & {fmt.number(x.mean())} & {fmt.number(x.std())} & "
                     f"{fmt.number(x.median())} & {fmt.number(x.min(), 0 if scale != '0--100' else 1)}--"
                     f"{fmt.number(x.max(), 0 if scale != '0--100' else 1)} \\\\")
        values[f"{column}_mean"] = fmt.number(x.mean())
        values[f"{column}_sd"] = fmt.number(x.std())
        values[f"{column}_median"] = fmt.number(x.median(), 0 if scale != "0--100" else 1)

    table = "\n".join([
        "\\begin{table}[tbp]",
        "\\caption{Descriptive Statistics, Primary Confirmatory Sample}",
        "\\label{tab:descriptives}",
        "\\begin{threeparttable}",
        "\\linespread{1}\\selectfont",
        "\\begin{tabular}{@{}lccccc@{}}",
        "\\toprule",
        "Measure & Scale & $M$ & $SD$ & $Mdn$ & Range \\\\",
        "\\midrule",
        *lines,
        "\\bottomrule",
        "\\end{tabular}",
        "\\vspace{4pt}",
        "\\begin{tablenotes}[para,flushleft]",
        f"{{\\small\\textit{{Note.}} $N$ = {len(group)}. Range is the observed minimum--maximum. Continuous ratings are "
        "participant means of the 1-Hz series within each registered segment (film time in min:s); valence "
        "0 = unpleasant, 50 = neutral, 100 = pleasant; arousal 0 = low, 100 = high. STICSA = State-Trait Inventory "
        "for Cognitive and Somatic Anxiety, state somatic subscale.}",
        "\\end{tablenotes}",
        "\\end{threeparttable}",
        "\\end{table}",
    ])
    return table, values


# ------------------------------------------------------------------------------------------- tests

def test_values(tests, group):
    values = {}
    primary = tests[tests["analysis_sample"] == "primary"].set_index("hypothesis", drop=False)
    for hypothesis, row in primary.iterrows():
        key = hypothesis.replace(" ", "")
        values[f"{key}:report"] = in_text_report(row)
        values[f"{key}:effect"] = effect_text(row)
        # The estimate alone, two decimals (for the abstract).
        values[f"{key}:est"] = (fmt.number(row["estimate"]) if row["estimate_name"] == "dz"
                                else fmt.tex(fmt.bounded(row["estimate"])))
        if row["estimate_name"] == "dz":
            values[f"{key}:diff"] = fmt.number(row["mean_difference"])
            values[f"{key}:diffabs"] = fmt.number(abs(row["mean_difference"]))

    h2_sizes = primary.loc[["H2a", "H2b", "H2c", "H2d"], "estimate"].abs()
    values["H2:absrange"] = f"{fmt.number(h2_sizes.min())}--{fmt.number(h2_sizes.max())}"

    # H1 in full: means, uncorrected t test (single test, no Holm), Wilcoxon signed-rank statistic.
    h1 = primary.loc["H1"]
    complete = group[["sticsa_pre", "sticsa_post"]].dropna()
    wilcoxon = stats.wilcoxon(complete["sticsa_post"], complete["sticsa_pre"])
    values["H1:report"] = (f"$t$({int(h1['df'])}) = {fmt.number(h1['statistic'])}, $p$ {fmt.p(h1['p'])}, "
                           f"$d_z$ = {fmt.number(h1['estimate'])}, 95\\% CI {fmt.ci(h1['ci_low'], h1['ci_high'])}")
    values["H1:wilcoxon"] = f"$T$ = {wilcoxon.statistic:.0f}, $p$ {fmt.p(h1['wilcoxon_p'])}"
    values["n_floor_pre"] = int((complete["sticsa_pre"] == 11).sum())
    values["pct_floor_pre"] = f"{100 * (complete['sticsa_pre'] == 11).mean():.0f}"
    values["n_increase"] = int((group["sticsa_change"] > 0).sum())
    values["n_nochange"] = int((group["sticsa_change"] == 0).sum())
    values["n_decrease"] = int((group["sticsa_change"] < 0).sum())
    values["n_fear_top"] = int((group["height_fear"] >= 6).sum())
    values["n_fear_seven"] = int((group["height_fear"] == 7).sum())
    return values


def confirmatory_table(tests):
    primary = tests[tests["analysis_sample"] == "primary"]
    lines = []
    previous_family = None
    for _, row in primary.iterrows():
        if previous_family is not None and row["family"] != previous_family:
            lines.append("\\addlinespace")
        previous_family = row["family"]
        statistic = f"$t$({int(row['df'])}) = {fmt.number(row['statistic'])}" if row["estimate_name"] == "dz" else "--"
        p_raw = fmt.p(row["p"]).replace("= ", "").replace("< ", "$<$ ") if pd.notna(row.get("p")) else "--"
        if row["family"] == "H1":
            p_holm = "--"
        elif pd.notna(row.get("p_holm")):
            p_holm = fmt.p(row["p_holm"]).replace("= ", "").replace("< ", "$<$ ")
        else:
            p_holm = "--"
        lines.append(f"{row['hypothesis']} & {PREDICTIONS[row['hypothesis']]} & {statistic} & "
                     f"{effect_text(row)} & {p_raw} & {p_holm} & {'Yes' if row['supported'] else 'No'} \\\\")
    return "\n".join([
        "\\begin{table}[tbp]",
        "\\caption{Preregistered Confirmatory Tests, Primary Sample}",
        "\\label{tab:confirmatory}",
        "\\begin{threeparttable}",
        "\\footnotesize\\linespread{1}\\selectfont\\setlength{\\tabcolsep}{3.5pt}",
        "\\begin{tabular}{@{}l>{\\raggedright\\arraybackslash}p{3.0cm}cllll@{}}",
        "\\toprule",
        "Hypothesis & Prediction & Test statistic & Effect size [95\\% CI] & $p$ & $p_\\mathrm{Holm}$ & Supported \\\\",
        "\\midrule",
        *lines,
        "\\bottomrule",
        "\\end{tabular}",
        "\\vspace{4pt}",
        "\\begin{tablenotes}[para,flushleft]",
        f"{{\\small\\textit{{Note.}} $N$ = {int(primary['n'].iloc[0])}. H1 and H2: paired $t$ tests with $d_z$ and "
        "exact 95\\% CIs (noncentral $t$). H3: Pearson $r$ between the confirmatory and exploratory group-mean "
        "series (808 one-second values), 95\\% CI from a circular block bootstrap (30-s blocks, 5,000 resamples); "
        "supported if the lower bound exceeds .50. H4--H6: Spearman $\\rho$ with percentile bootstrap 95\\% CIs "
        "(5,000 resamples). Holm correction within H2 (four tests), H4 (three), H5 (two) and H6 (two); H1 is a "
        "single test. All tests two-sided; a directional hypothesis counts as supported only if significant in "
        "the predicted direction.}",
        "\\end{tablenotes}",
        "\\end{threeparttable}",
        "\\end{table}",
    ])


def sensitivity_table(tests, sizes):
    cells = {}
    for (sample, hypothesis), row in tests.set_index(["analysis_sample", "hypothesis"]).iterrows():
        value = effect_text(row, with_name=False).split(" [")[0]
        if row["estimate_name"] == "r":
            detail = f"lower {fmt.bounded(row['ci_low'], 3)}"
        else:
            detail = "$p_\\mathrm{Holm}$ " + fmt.p(row["p_holm"]) if row["family"] != "H1" else "$p$ " + fmt.p(row["p"])
        mark = "" if row["supported"] else "$^\\dagger$"
        cells[(sample, hypothesis)] = f"{value} ({detail}){mark}"
    lines = []
    for hypothesis in PREDICTIONS:
        name = {"dz": "$d_z$", "r": "$r$", "rho": "$\\rho$"}[
            tests.loc[tests["hypothesis"] == hypothesis, "estimate_name"].iloc[0]]
        lines.append(f"{hypothesis} & {name} & " + " & ".join(
            cells[(s, hypothesis)] for s in ("primary", "stricter_engagement", "without_rejected")) + " \\\\")
    header = " & ".join(f"{SAMPLE_NAMES[s]} ($n$ = {sizes[s]})"
                        for s in ("primary", "stricter_engagement", "without_rejected"))
    return "\n".join([
        "\\begin{table}[tbp]",
        "\\caption{Preregistered Tests Repeated in the Sensitivity Samples}",
        "\\label{tab:sensitivity}",
        "\\begin{threeparttable}",
        "\\footnotesize\\linespread{1}\\selectfont\\setlength{\\tabcolsep}{3.5pt}",
        "\\begin{tabular}{@{}llccc@{}}",
        "\\toprule",
        f"Hypothesis & Effect & {header} \\\\",
        "\\midrule",
        *lines,
        "\\bottomrule",
        "\\end{tabular}",
        "\\vspace{4pt}",
        "\\begin{tablenotes}[para,flushleft]",
        "{\\small\\textit{Note.} Cells show the effect size and, in parentheses, the Holm-adjusted $p$ value (H1: "
        "unadjusted, single test) or, for H3, the lower bound of the 95\\% CI of $r$. $^\\dagger$Hypothesis not "
        "supported under the registered criteria. Stricter engagement: sparse raters (fewer than one rating bout "
        "per minute or more than 180 s without input), participants who failed one attention check and "
        "participants who reported not watching attentively removed. Rejection set removed: participants whose "
        "Prolific submissions were rejected for behaviour on the free-text page removed, although they pass the "
        "registered exclusion rules.}",
        "\\end{tablenotes}",
        "\\end{threeparttable}",
        "\\end{table}",
    ])


def descriptive_analysis_values():
    values = {}
    reliability = pd.read_csv(RESULTS / "reliability.csv").set_index(["analysis_sample", "rating"])
    for rating in ("arousal", "valence"):
        values[f"rel:{rating}"] = fmt.bounded(reliability.loc[("primary", rating), "split_half_reliability"], 3)
    edges = pd.read_csv(RESULTS / "segment_edges.csv")
    for i, row in edges.iterrows():
        values[f"edge{i + 1}:est"] = int(row["estimated_s"])
        values[f"edge{i + 1}:reg"] = int(row["registered_s"])
        values[f"edge{i + 1}:ci"] = f"[{row['ci_low_s']:.0f}, {row['ci_high_s']:.0f}]"
    return values


AGE_SEX = RESULTS / "exploratory_age_sex"


def estimate_with_ci(row, digits=2):
    return f"{fmt.number(row['estimate'], digits)} {fmt.ci(row['ci_low'], row['ci_high'], digits=digits)}"


def p_cell(p):
    return fmt.p(p).replace("= ", "").replace("< ", "$<$ ")


def age_sex(primary, measures):
    """Values and table for the exploratory age and sex analyses (results of 06_age_sex.py)."""
    change = pd.read_csv(AGE_SEX / "sticsa_change.csv").set_index("analysis")
    moderation = pd.read_csv(AGE_SEX / "segment_moderation.csv")
    by_sex = pd.read_csv(AGE_SEX / "sex_by_segment.csv").set_index(["rating", "segment"])

    people = primary.dropna(subset=["sex", "age"])
    change_by_sex = measures.loc[people.index, "sticsa_change"].groupby(people["sex"])
    values = {"n_demo": len(people), "n_demo_female": int((people["sex"] == "Female").sum()),
              "n_demo_male": int((people["sex"] == "Male").sum()),
              "change_female_mean": fmt.number(change_by_sex.mean()["Female"]),
              "change_male_mean": fmt.number(change_by_sex.mean()["Male"])}

    regression_sex = change.loc["regression: female - male (points)"]
    regression_age = change.loc["regression: per 10 years of age (points)"]
    values["agesex:change_sex"] = f"{estimate_with_ci(regression_sex)}, $p$ {fmt.p(regression_sex['p'])}"
    values["agesex:change_age"] = f"{estimate_with_ci(regression_age)}, $p$ {fmt.p(regression_age['p'])}"

    def pick(rating, effect, method_start):
        rows = moderation[(moderation["rating"] == rating) & (moderation["effect"] == effect)
                          & moderation["method"].str.startswith(method_start)]
        return rows.iloc[0]

    lines = [f"STICSA change & Female $-$ male (points) & {estimate_with_ci(regression_sex)} & "
             f"{p_cell(regression_sex['p'])} & -- & -- \\\\",
             f" & Per 10 years of age (points) & {estimate_with_ci(regression_age)} & "
             f"{p_cell(regression_age['p'])} & -- & -- \\\\", "\\addlinespace"]
    for rating in ("arousal", "valence"):
        for i, (effect, label) in enumerate((("sex_x_segment", "Segment $\\times$ sex"),
                                             ("age_x_segment", "Segment $\\times$ age"))):
            mixed, check = pick(rating, effect, "mixed model"), pick(rating, effect, "clustered")
            if mixed["method"].startswith("mixed model, LR"):
                mixed_text, mixed_p = f"$\\chi^2$(3) = {fmt.number(mixed['chi2'])}", p_cell(mixed["p"])
                values[f"agesex:{rating}:{effect}"] = (f"$\\chi^2$(3) = {fmt.number(mixed['chi2'])}, "
                                                       f"$p$ {fmt.p(mixed['p'])}")
            else:
                mixed_text, mixed_p = "did not converge", "--"
                values[f"agesex:{rating}:{effect}"] = "mixed model did not converge"
            check_text = f"$F$(3, {int(check['df_denom'])}) = {fmt.number(check['F'])}"
            values[f"agesex:{rating}:{effect}:check"] = f"{check_text}, $p$ {fmt.p(check['p'])}"
            name = rating.capitalize() if i == 0 else ""
            lines.append(f"{name} & {label} & {mixed_text} & {mixed_p} & {check_text} & {p_cell(check['p'])} \\\\")
        for effect, label in (("main: female_minus_male", "Female $-$ male (film mean)"),
                              ("main: per_10_years", "Per 10 years (film mean)")):
            row = moderation[(moderation["rating"] == rating) & (moderation["effect"] == effect)].iloc[0]
            values[f"agesex:{rating}:{effect.split(': ')[1]}"] = f"{estimate_with_ci(row)}, $p$ {fmt.p(row['p'])}"
            lines.append(f" & {label} & -- & -- & {estimate_with_ci(row)} & {p_cell(row['p'])} \\\\")
        lines.append("\\addlinespace")
    lines.pop()  # no space after the last block

    rise = by_sex.loc[("valence", "rise")]
    values["agesex:valence_rise_diff"] = (f"{fmt.number(rise['difference'])} points "
                                          f"{fmt.ci(rise['ci_low'], rise['ci_high'])}, $p$ {fmt.p(rise['p'])}")
    table = "\n".join([
        "\\begin{table}[tbp]",
        "\\caption{Exploratory Analyses of Age and Sex}",
        "\\label{tab:agesex}",
        "\\begin{threeparttable}",
        "\\footnotesize\\linespread{1}\\selectfont\\setlength{\\tabcolsep}{3.5pt}",
        "\\begin{tabular}{@{}llllll@{}}",
        "\\toprule",
        " & & \\multicolumn{2}{l}{Main analysis} & \\multicolumn{2}{l}{Clustered regression (check)} \\\\",
        "\\cmidrule(lr){3-4}\\cmidrule(l){5-6}",
        "Outcome & Effect & Test or estimate & $p$ & Test or estimate & $p$ \\\\",
        "\\midrule",
        *lines,
        "\\bottomrule",
        "\\end{tabular}",
        "\\vspace{4pt}",
        "\\begin{tablenotes}[para,flushleft]",
        f"{{\\small\\textit{{Note.}} Exploratory analyses, not preregistered tests; $p$ values are uncorrected. "
        f"$n$ = {len(people)} participants of the primary sample with age and sex available. STICSA change: linear "
        "regression on sex and age. Segment means: random-intercept mixed model with segment (sum-coded) $\\times$ "
        "(sex + age), interactions tested with likelihood-ratio tests (main analysis); the same model fitted by "
        "least squares with standard errors clustered by participant, interactions tested with Wald $F$ tests, is "
        "shown as a check, together with the main effects of sex and age averaged over the film. Age effects are "
        "per 10 years; sex effects are female minus male, in scale points.}",
        "\\end{tablenotes}",
        "\\end{threeparttable}",
        "\\end{table}",
    ])
    return values, table


ITEMS_FILE = RESULTS / "exploratory_items" / "sticsa_items.csv"


def item_values_and_table():
    """Exploratory item-level STICSA changes (results of 10_sticsa_items.py): values for the text and Table S6."""
    items = pd.read_csv(ITEMS_FILE).sort_values("rank")
    values = {"items:dz_min": fmt.number(items["dz"].min()), "items:dz_max": fmt.number(items["dz"].max()),
              "items:pholm_max": fmt.p(items["p_holm"].max())}
    for _, row in items.iterrows():
        values[f"items:rank{int(row['rank'])}:label"] = row["label"].lower()
        values[f"items:rank{int(row['rank'])}:dz"] = fmt.number(row["dz"])
    lines = [f"{int(r['rank'])} & {r['label']} (item {int(r['item'])}) & {fmt.number(r['mean_before'])} & "
             f"{fmt.number(r['mean_after'])} & {round(100 * r['share_increased'])} & "
             f"{fmt.number(r['dz'])} {fmt.ci(r['dz_ci_low'], r['dz_ci_high'])} & "
             f"{fmt.p(r['p_holm']).replace('= ', '').replace('< ', '$<$ ')} \\\\" for _, r in items.iterrows()]
    table = "\n".join([
        "\\begin{table}[tbp]",
        "\\caption{Change in Each STICSA Somatic Item (Exploratory)}",
        "\\label{tab:items}",
        "\\begin{threeparttable}",
        "\\small\\linespread{1}\\selectfont",
        "\\begin{tabular}{@{}rlcccll@{}}",
        "\\toprule",
        "Rank & Item & $M$ before & $M$ after & \\% increased & $d_z$ [95\\% CI] & $p_\\mathrm{Holm}$ \\\\",
        "\\midrule",
        *lines,
        "\\bottomrule",
        "\\end{tabular}",
        "\\vspace{4pt}",
        "\\begin{tablenotes}[para,flushleft]",
        f"{{\\small\\textit{{Note.}} Exploratory analysis, not a preregistered test. $N$ = {int(items['n'].iloc[0])} "
        "(primary confirmatory sample). Items answered from 1 (not at all) to 4 (very much so); short labels, original "
        "STICSA item numbers in parentheses. Ranked by $d_z$ (mean change divided by the standard deviation of the "
        "changes; exact 95\\% CI). \\% increased: share of participants whose answer was higher after the film. $p$ "
        "from Wilcoxon signed-rank tests, Holm-corrected across the 11 items.}",
        "\\end{tablenotes}",
        "\\end{threeparttable}",
        "\\end{table}",
    ])
    return values, table


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tests = pd.read_csv(RESULTS / "hypothesis_tests.csv")
    record = run_record.make_record("05_report_numbers.py", "confirmatory", seed=None,
                                    inputs=[*sorted(study_data.DATA.glob("*.csv")), RESULTS / "hypothesis_tests.csv",
                                            RESULTS / "reliability.csv", RESULTS / "segment_edges.csv"])

    participants, valence, arousal = study_data.load()
    measures = hypotheses.participant_measures(participants, valence, arousal)
    completers = participants[participants["sample"] == "confirmatory"]
    samples = study_data.analysis_samples(completers)
    group = measures.loc[samples["primary"].index].join(
        participants.loc[samples["primary"].index, ["concern_safety", "body_intensity"]])

    values = {}
    values.update(sample_values(participants, completers, samples))
    table_1, descriptive_numbers = descriptives(group)
    values.update(descriptive_numbers)
    values.update(test_values(tests, group))
    values.update(descriptive_analysis_values())
    confirmatory_run = json.loads((RESULTS / "run_record_02_confirmatory.json").read_text())
    values["confirmatory_commit"] = confirmatory_run["git_commit"][:7]
    values["seed"] = confirmatory_run["seed"]
    values["python_version"] = confirmatory_run["python"]
    for package, version in confirmatory_run["packages"].items():
        values[f"version:{package}"] = version
    age_sex_run = json.loads((AGE_SEX / "run_record_06_age_sex.json").read_text())
    values["version:statsmodels"] = age_sex_run["packages"]["statsmodels"]

    exploratory = participants[(participants["sample"] == "exploratory") & study_data.is_usable(participants)]
    columns = [("Exploratory, usable", measures.loc[exploratory.index], exploratory),
               ("Confirmatory, all completers", measures.loc[completers.index], completers),
               ("Confirmatory, primary sample", measures.loc[samples["primary"].index], samples["primary"])]

    age_sex_values, age_sex_table = age_sex(samples["primary"], measures)
    values.update(age_sex_values)
    item_values, item_table = item_values_and_table()
    values.update(item_values)
    # Group-mean rating shown by the dot in the task illustration (Supplementary Figure S1; 11_task_illustration.py)
    illustration_second = 636
    values["task:valence"] = fmt.number(valence[samples["primary"].index, illustration_second].mean(), 0)
    values["task:arousal"] = fmt.number(arousal[samples["primary"].index, illustration_second].mean(), 0)
    (OUT / "table_items.tex").write_text(item_table + "\n", encoding="utf-8")

    sizes = {name: len(sample) for name, sample in samples.items()}
    write_values(values, OUT / "numbers.tex")
    (OUT / "table_age_sex.tex").write_text(age_sex_table + "\n", encoding="utf-8")
    (OUT / "table_sample.tex").write_text(sample_table(columns) + "\n", encoding="utf-8")
    (OUT / "table_descriptives.tex").write_text(table_1 + "\n", encoding="utf-8")
    (OUT / "table_confirmatory.tex").write_text(confirmatory_table(tests) + "\n", encoding="utf-8")
    (OUT / "table_sensitivity.tex").write_text(sensitivity_table(tests, sizes) + "\n", encoding="utf-8")
    run_record.save_record(record, OUT)
    print(f"wrote {len(values)} values and 5 tables to {OUT}")


if __name__ == "__main__":
    main()
