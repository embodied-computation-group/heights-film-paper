"""Step 6 (EXPLORATORY): age and sex differences in the somatic-anxiety change and the rating time course.

Listed under "Other planned analysis" in the preregistration; not registered tests. p values are uncorrected.
Sex is Prolific's profile field (female/male). Primary sample, people with age and sex available.

Run:  uv run python analysis/06_age_sex.py                 (exploratory sample, the default)
      uv run python analysis/06_age_sex.py --sample confirmatory

Writes results/<sample>/exploratory_age_sex/:
  sticsa_change.csv        STICSA change ~ sex + age (regression), plus Welch t (sex) and Spearman (age)
  segment_moderation.csv   per rating: segment x sex and segment x age (mixed model LR tests = main result;
                           clustered OLS Wald F tests as a check),
                           main effects of sex and age averaged over the film
  sex_by_segment.csv       female - male difference per segment (Welch 95% CI)
  age_by_segment.csv       Spearman correlation of age with each segment mean
and figures fig7_time_course_by_sex, fig8_age_sex (in results/<sample>/figures/).
"""
import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # so `analysis` can be imported
from analysis import demographics, hypotheses, plot_style, run_record, stats_tools, study_data  # noqa: E402

RESULTS = Path(__file__).resolve().parent.parent / "results"


def long_segment_means(measures, people, rating):
    """One row per participant and segment, with sex and age."""
    rows = []
    for segment in study_data.SEGMENTS:
        rows.append(pd.DataFrame({"participant": people["participant"].to_numpy(), "segment": segment,
                                  "value": measures.loc[people.index, f"{rating}_{segment}"].to_numpy(),
                                  "sex": people["sex"].to_numpy(), "age": people["age"].to_numpy()}))
    return pd.concat(rows, ignore_index=True)


def sticsa_table(measures, people):
    data = people[["sex", "age"]].join(measures[["sticsa_change"]])
    model = demographics.sticsa_change_model(data)
    complete = demographics.complete_cases(data)
    women = complete.loc[complete["sex"] == "Female", "sticsa_change"]
    men = complete.loc[complete["sex"] == "Male", "sticsa_change"]
    welch = stats.ttest_ind(women, men, equal_var=False)
    spearman = stats.spearmanr(complete["age"], complete["sticsa_change"])
    rows = [
        {"analysis": "regression: female - male (points)", "n": model["n"], **model["female_minus_male"]},
        {"analysis": "regression: per 10 years of age (points)", "n": model["n"], **model["per_10_years"]},
        {"analysis": "Welch t: female - male (points)", "n": len(complete),
         "estimate": women.mean() - men.mean(), "ci_low": welch.confidence_interval().low,
         "ci_high": welch.confidence_interval().high, "p": welch.pvalue},
        {"analysis": "Spearman: age", "n": len(complete), "estimate": spearman.statistic, "p": spearman.pvalue},
    ]
    return pd.DataFrame(rows), {"mean_female": women.mean(), "mean_male": men.mean(),
                                "n_female": len(women), "n_male": len(men)}


# ------------------------------------------------------------------------------------------- figures

def time_course_by_sex(valence, arousal, people, sample, out):
    fig, axes = plt.subplots(2, 1, figsize=(7.2, 5.0), sharex=True)
    seconds = np.arange(study_data.FILM_SECONDS)
    for ax, rating, ratings in ((axes[0], "arousal", arousal), (axes[1], "valence", valence)):
        plot_style.shade_segments(ax, label=ax is axes[0])
        for sex in ("Female", "Male"):
            rows = people.index[people["sex"] == sex]
            values = ratings[rows]
            mean = values.mean(axis=0)
            half_width = stats.t.ppf(0.975, len(rows) - 1) * values.std(axis=0, ddof=1) / np.sqrt(len(rows))
            colour = plot_style.SEX_COLOURS[sex]
            ax.fill_between(seconds, mean - half_width, mean + half_width, color=colour, alpha=0.18, lw=0)
            ax.plot(seconds, mean, color=colour, ls=plot_style.SEX_LINES[sex], lw=1.6,
                    label=f"{sex.lower()} (n = {len(rows)})")
        ax.set_ylim(0, 100)
        ax.set_ylabel(plot_style.RATING_LABELS[rating])
        ax.legend(loc="lower left", fontsize=8)
    plot_style.minutes_axis(axes[1])
    axes[0].set_title("Exploratory: group-mean ratings by sex (mean with 95% CI)", loc="left", pad=14)
    note(fig, sample)
    plot_style.save(fig, out / "fig7_time_course_by_sex")


def age_sex_panels(measures, people, sample, out):
    data = demographics.complete_cases(people[["sex", "age"]].join(measures))
    fig, axes = plt.subplots(1, 4, figsize=(10.5, 3.0), gridspec_kw={"width_ratios": [0.8, 1, 1.2, 1.2]})
    rng = np.random.default_rng(0)

    # A: STICSA change by sex
    ax = axes[0]
    for i, sex in enumerate(("Female", "Male")):
        values = data.loc[data["sex"] == sex, "sticsa_change"]
        ax.scatter(i + rng.uniform(-0.15, 0.15, len(values)), values, s=9, color=plot_style.SEX_COLOURS[sex],
                   alpha=0.5, edgecolor="white", linewidth=0.3)
        half_width = stats.t.ppf(0.975, len(values) - 1) * values.std(ddof=1) / np.sqrt(len(values))
        ax.errorbar(i, values.mean(), yerr=half_width, fmt="o", color=plot_style.TEXT, mfc="white", ms=6, capsize=3,
                    lw=1.5)
    ax.set_xticks([0, 1], ["Female", "Male"])
    ax.set_xlim(-0.6, 1.6)
    ax.set_ylabel("STICSA somatic change (points)")
    ax.set_title("A  STICSA change by sex", loc="left", fontsize=8.5)

    # B: STICSA change by age
    ax = axes[1]
    # Age and change are whole numbers, so some people share a position: a small jitter keeps every point visible.
    ax.scatter(data["age"] + rng.uniform(-0.4, 0.4, len(data)), data["sticsa_change"] + rng.uniform(-0.3, 0.3, len(data)),
               s=16, color=plot_style.TEXT_SOFT, alpha=0.6, edgecolor="white", linewidth=0.4)
    ax.text(0.02, 0.98, f"n = {len(data)}", transform=ax.transAxes, va="top", fontsize=7.5,
            color=plot_style.TEXT_SOFT)
    grid = np.linspace(data["age"].min(), data["age"].max(), 100)
    fit, low, high = stats_tools.linear_fit_band(data["age"], data["sticsa_change"], grid)
    ax.fill_between(grid, low, high, color=plot_style.TEXT, alpha=0.12, lw=0)
    ax.plot(grid, fit, color=plot_style.TEXT, lw=1.3)
    ax.set_xlabel("Age (years)")
    ax.set_title("B  STICSA change by age", loc="left", fontsize=8.5)

    # C, D: segment means by sex
    for ax, rating, letter in ((axes[2], "arousal", "C"), (axes[3], "valence", "D")):
        for shift, sex in ((-0.08, "Female"), (0.08, "Male")):
            values = data.loc[data["sex"] == sex, [f"{rating}_{s}" for s in study_data.SEGMENTS]]
            means = values.mean()
            half_widths = stats.t.ppf(0.975, len(values) - 1) * values.std(ddof=1) / np.sqrt(len(values))
            ax.errorbar(np.arange(4) + shift, means, yerr=half_widths, color=plot_style.SEX_COLOURS[sex],
                        ls=plot_style.SEX_LINES[sex], marker="o", ms=5, mfc="white", capsize=3, lw=1.5,
                        label=sex.lower())
        ax.set_xticks(range(4), list(study_data.SEGMENTS), fontsize=7.5)
        ax.set_ylim(0, 100)
        ax.set_ylabel(f"{rating.capitalize()} segment mean (0–100)")
        ax.set_title(f"{letter}  {rating.capitalize()} by sex (mean ± 95% CI)", loc="left", fontsize=8.5)
        ax.legend(fontsize=7, loc="lower center")
    fig.tight_layout()
    note(fig, sample)
    plot_style.save(fig, out / "fig8_age_sex")


def note(fig, sample):
    text = "EXPLORATORY SAMPLE – development run" if sample == "exploratory" else "Confirmatory sample"
    fig.text(0.995, 0.005, f"{text}; exploratory analysis", ha="right", va="bottom", fontsize=7,
             color=plot_style.TEXT_SOFT)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sample", choices=["exploratory", "confirmatory"], default="exploratory")
    args = parser.parse_args()

    out = RESULTS / args.sample
    tables = out / "exploratory_age_sex"
    tables.mkdir(parents=True, exist_ok=True)
    record = run_record.make_record("06_age_sex.py", args.sample, seed=None,
                                    inputs=sorted(study_data.DATA.glob("*.csv")), settings={"exploratory": True})
    plot_style.use()

    participants, valence, arousal = study_data.load()
    measures = hypotheses.participant_measures(participants, valence, arousal)
    primary = study_data.analysis_samples(participants[participants["sample"] == args.sample])["primary"]
    people = demographics.complete_cases(primary)
    print(f"{args.sample}: {len(primary)} in the primary sample, {len(people)} with age and sex "
          f"({(people['sex'] == 'Female').sum()} female, {(people['sex'] == 'Male').sum()} male)")

    change_table, change_means = sticsa_table(measures, people)
    moderation, by_sex, by_age = [], [], []
    for rating in ("arousal", "valence"):
        long = long_segment_means(measures, people, rating)
        result = demographics.segment_moderation(long)
        mixed = result["mixed_model"]
        for effect in ("sex_x_segment", "age_x_segment"):
            if mixed["converged"]:
                moderation.append({"rating": rating, "effect": effect, "method": "mixed model, LR test (main)",
                                   "n": result["n_participants"], **mixed[effect]})
            else:
                moderation.append({"rating": rating, "effect": effect, "method": "mixed model: did not converge",
                                   "n": result["n_participants"]})
            moderation.append({"rating": rating, "effect": effect, "method": "clustered OLS, Wald F (check)",
                               "n": result["n_participants"], **result[effect]})
        for effect in ("female_minus_male", "per_10_years"):
            moderation.append({"rating": rating, "effect": f"main: {effect}", "method": "clustered OLS",
                               "n": result["n_participants"],
                               **result[effect]})
        by_sex.append(demographics.sex_difference_by_segment(long).assign(rating=rating))
        by_age.append(demographics.age_correlation_by_segment(long).assign(rating=rating))

    change_table.to_csv(tables / "sticsa_change.csv", index=False)
    pd.DataFrame(moderation).to_csv(tables / "segment_moderation.csv", index=False)
    pd.concat(by_sex).to_csv(tables / "sex_by_segment.csv", index=False)
    pd.concat(by_age).to_csv(tables / "age_by_segment.csv", index=False)

    figures = out / "figures"
    time_course_by_sex(valence, arousal, people, args.sample, figures)
    age_sex_panels(measures, people, args.sample, figures)
    run_record.save_record(record, tables)

    with pd.option_context("display.width", 200):
        print("\nSTICSA change", {k: round(v, 2) for k, v in change_means.items()})
        print(change_table.round(3).to_string(index=False))
        print("\nTime course: segment x sex and segment x age")
        print(pd.DataFrame(moderation).round(3).to_string(index=False))
        print("\nFemale - male by segment")
        print(pd.concat(by_sex)[["rating", "segment", "mean_female", "mean_male", "difference", "ci_low", "ci_high",
                                 "p"]].round(3).to_string(index=False))
        print("\nAge by segment (Spearman)")
        print(pd.concat(by_age).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
