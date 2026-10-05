"""EXPLORATORY: age and sex differences (listed under "Other planned analysis" in the preregistration).

Not registered tests: there is no registered correction family, so p values are uncorrected and the estimates with
their confidence intervals carry the weight. Sex is the Prolific profile field (female/male), not gender. People
without age or sex (Prolific withholds them for rejected submissions) are left out.
"""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

SEGMENT_ORDER = ["baseline", "rise", "plateau", "return"]


def complete_cases(table):
    return table.dropna(subset=["sex", "age"]).copy()


def segment_moderation(long):
    """Does the time course over the four segments differ by sex or by age?

    `long` has one row per participant and segment: participant, segment, value, sex, age.
    Model:  value ~ segment * (sex + age), fitted by least squares with standard errors clustered by participant
    (the four segment means of one person are not independent). Segments are sum-coded, so the sex and age main
    effects are averages over the film. Each interaction (3 terms) is tested with a Wald F test.

    The same model is also fitted as a random-intercept mixed model (the preregistration's example), with each
    interaction tested by a likelihood-ratio test (maximum likelihood, 3 df). Decided before the confirmatory run:
    the mixed model is the main result and the clustered fit is reported next to it as a check; if the mixed model
    does not converge, its result is reported as missing rather than replaced. (In the 21-person exploratory sample its
    random-intercept variance hit zero and the fit did not converge.)
    """
    data = complete_cases(long)
    data["segment"] = pd.Categorical(data["segment"], categories=SEGMENT_ORDER)
    data["female"] = (data["sex"] == "Female").astype(float)
    data["age_10"] = (data["age"] - data["age"].mean()) / 10  # per 10 years, centred

    clusters = pd.factorize(data["participant"])[0]
    full = smf.ols("value ~ C(segment, Sum) * (female + age_10)", data).fit(
        cov_type="cluster", cov_kwds={"groups": clusters})

    def interaction_test(moderator):
        terms = [name for name in full.params.index if "C(segment, Sum)" in name and name.endswith(f":{moderator}")]
        restriction = np.zeros((len(terms), len(full.params)))
        for row, name in enumerate(terms):
            restriction[row, full.params.index.get_loc(name)] = 1
        test = full.f_test(restriction)
        return {"F": float(np.squeeze(test.fvalue)), "df": len(terms), "df_denom": float(test.df_denom),
                "p": float(test.pvalue)}

    confidence = full.conf_int()
    return {
        "n_participants": int(data["participant"].nunique()),
        "sex_x_segment": interaction_test("female"),
        "age_x_segment": interaction_test("age_10"),
        "mixed_model": mixed_model_tests(data),
        # Main effects, averaged over segments: female - male (rating points) and per 10 years of age.
        "female_minus_male": {"estimate": float(full.params["female"]), "ci_low": float(confidence.loc["female", 0]),
                              "ci_high": float(confidence.loc["female", 1]), "p": float(full.pvalues["female"])},
        "per_10_years": {"estimate": float(full.params["age_10"]), "ci_low": float(confidence.loc["age_10", 0]),
                         "ci_high": float(confidence.loc["age_10", 1]), "p": float(full.pvalues["age_10"])},
    }


OPTIMISERS = ["bfgs", "powell", "nm", "lbfgs"]


def fit_mixed_model(formula, data):
    """Maximum-likelihood fit with a random intercept per participant; tries optimisers in turn and returns the first
    fit that converges (None if none does). Different optimisers that converge reach the same solution; on the real
    data L-BFGS alone failed with a singular-matrix error while the others agreed."""
    import warnings

    from statsmodels.tools.sm_exceptions import ConvergenceWarning

    for method in OPTIMISERS:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ConvergenceWarning)  # convergence is checked explicitly
            try:
                fit = smf.mixedlm(formula, data, groups=data["participant"]).fit(reml=False, method=method)
            except np.linalg.LinAlgError:
                continue
        if fit.converged:
            return fit
    return None


def mixed_model_tests(data):
    """Random-intercept mixed model; likelihood-ratio tests of segment x sex and segment x age (3 df each).

    Returns converged = False (and no test results) if any of the three fits fails to converge.
    """
    segment = "C(segment, Sum)"
    formulas = {"full": f"value ~ {segment} * (female + age_10)",
                "no_sex_x_segment": f"value ~ {segment} * age_10 + female",
                "no_age_x_segment": f"value ~ {segment} * female + age_10"}
    fits = {}
    for name, formula in formulas.items():
        fits[name] = fit_mixed_model(formula, data)
        if fits[name] is None:
            return {"converged": False}

    def likelihood_ratio(reduced):
        statistic = 2 * (fits["full"].llf - fits[reduced].llf)
        return {"chi2": float(statistic), "df": 3, "p": float(stats.chi2.sf(statistic, 3))}

    return {"converged": True, "sex_x_segment": likelihood_ratio("no_sex_x_segment"),
            "age_x_segment": likelihood_ratio("no_age_x_segment"),
            "random_intercept_variance": float(fits["full"].cov_re.iloc[0, 0])}


def sex_difference_by_segment(long):
    """Female minus male mean in each segment, with Welch 95% CI and p."""
    rows = []
    for segment in SEGMENT_ORDER:
        part = complete_cases(long[long["segment"] == segment])
        women, men = part.loc[part["sex"] == "Female", "value"], part.loc[part["sex"] == "Male", "value"]
        test = stats.ttest_ind(women, men, equal_var=False)
        ci = test.confidence_interval()
        rows.append({"segment": segment, "n_female": len(women), "n_male": len(men),
                     "mean_female": women.mean(), "mean_male": men.mean(),
                     "difference": women.mean() - men.mean(), "ci_low": ci.low, "ci_high": ci.high,
                     "t": test.statistic, "df": test.df, "p": test.pvalue})
    return pd.DataFrame(rows)


def age_correlation_by_segment(long):
    """Spearman correlation between age and the segment mean, in each segment."""
    rows = []
    for segment in SEGMENT_ORDER:
        part = complete_cases(long[long["segment"] == segment])
        result = stats.spearmanr(part["age"], part["value"])
        rows.append({"segment": segment, "n": len(part), "rho": result.statistic, "p": result.pvalue})
    return pd.DataFrame(rows)


def sticsa_change_model(people):
    """STICSA change ~ sex + age (ordinary least squares): female - male in points, and per 10 years of age."""
    data = complete_cases(people)
    data["female"] = (data["sex"] == "Female").astype(float)
    data["age_10"] = (data["age"] - data["age"].mean()) / 10
    fit = smf.ols("sticsa_change ~ female + age_10", data).fit()
    confidence = fit.conf_int()

    def term(name):
        return {"estimate": float(fit.params[name]), "ci_low": float(confidence.loc[name, 0]),
                "ci_high": float(confidence.loc[name, 1]), "p": float(fit.pvalues[name])}

    return {"n": int(fit.nobs), "female_minus_male": term("female"), "per_10_years": term("age_10"),
            "r_squared": float(fit.rsquared)}
