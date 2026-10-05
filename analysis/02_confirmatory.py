"""Step 2: the registered tests H1-H6, for the primary sample and both sensitivity samples, plus the registered
descriptive analyses (split-half reliability of the group curves; segment edges re-estimated with bootstrap CIs).

Run:  uv run python analysis/02_confirmatory.py                 (exploratory sample, the default; for development)
      uv run python analysis/02_confirmatory.py --sample confirmatory      (ONCE, when Micah says go)

On the exploratory sample, H3 has no independent second sample and is replaced by a STAND-IN (cohort 1 vs pilot);
those H3 rows are marked as a stand-in and are not a test of anything.

Writes to results/<sample>/: hypothesis_tests.csv, reliability.csv, segment_edges.csv and a run record.
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # so `analysis` can be imported
from analysis import hypotheses, run_record, segmentation, stats_tools, study_data  # noqa: E402

RESULTS = Path(__file__).resolve().parent.parent / "results"
N_BOOT = 5000           # registered: Spearman bootstrap CIs and the H3 block bootstrap
N_SPLITS = 1000         # registered: split-half reliability
N_BOOT_EDGES = 1000     # not specified in the registration (see docs/prereg_log.md)


def group_curves(rows, valence, arousal):
    """Group-mean valence and arousal series (mean across participants at each second)."""
    return {"valence": valence[rows].mean(axis=0), "arousal": arousal[rows].mean(axis=0)}


def run_tests(name, group, participants, measures, valence, arousal, sample, seed):
    """All registered tests for one analysis sample, as a list of result rows."""
    group_measures = measures.loc[group.index]
    tested, reference = study_data.h3_groups(participants, group, sample)

    h3_rows = hypotheses.test_h3(group_curves(tested.index, valence, arousal),
                                 group_curves(reference.index, valence, arousal), n_boot=N_BOOT, seed=seed)
    if sample != "confirmatory":
        for row in h3_rows:
            row["description"] = (f"STAND-IN, not a test: cohort 1 (n = {len(tested)}) vs pilot "
                                  f"(n = {len(reference)}), {row['hypothesis'].split()[1]}")
    for row in h3_rows:
        row["n_tested"], row["n_reference"] = len(tested), len(reference)

    rows = [hypotheses.test_h1(group_measures), *hypotheses.test_h2(group_measures), *h3_rows,
            *hypotheses.test_correlations(group_measures, n_boot=N_BOOT, seed=seed)]
    for row in rows:
        row["analysis_sample"] = name
    return rows


def reliability(name, group, valence, arousal, seed):
    """Split-half reliability (Spearman-Brown) of the group-mean curves."""
    return [{"analysis_sample": name, "rating": rating, "n": len(group),
             "split_half_reliability": stats_tools.split_half_reliability(ratings[group.index], N_SPLITS, seed)}
            for rating, ratings in (("valence", valence), ("arousal", arousal))]


def segment_edges(name, group, arousal, seed):
    """Segment edges re-estimated from the group-mean arousal, next to the registered edges."""
    result = segmentation.bootstrap_breakpoints(arousal[group.index], n_breakpoints=3, n_boot=N_BOOT_EDGES,
                                                seed=seed)
    registered = [end for _, end in list(study_data.SEGMENTS.values())[:3]]
    names = ["baseline -> rise", "rise -> plateau", "plateau -> return"]
    return [{"analysis_sample": name, "edge": edge, "registered_s": fixed, "estimated_s": estimate,
             "ci_low_s": low, "ci_high_s": high, "n": len(group)}
            for edge, fixed, estimate, low, high in
            zip(names, registered, result["breakpoints"], result["ci_low"], result["ci_high"])]


def print_summary(tests):
    """A readable overview in the terminal."""
    columns = ["analysis_sample", "hypothesis", "description", "n", "estimate_name", "estimate", "ci_low",
               "ci_high", "p", "p_holm", "supported"]
    with pd.option_context("display.width", 200, "display.max_colwidth", 60):
        print(tests[columns].round(4).to_string(index=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sample", choices=["exploratory", "confirmatory"], default="exploratory")
    parser.add_argument("--seed", type=int, default=20261004)
    args = parser.parse_args()

    out = RESULTS / args.sample
    settings = {"n_boot": N_BOOT, "n_splits": N_SPLITS, "n_boot_edges": N_BOOT_EDGES}
    record = run_record.make_record("02_confirmatory.py", args.sample, args.seed,
                                    sorted(study_data.DATA.glob("*.csv")), settings)
    run_record.check_run_allowed(record, out)

    participants, valence, arousal = study_data.load()
    assert list(participants.index) == list(range(len(participants)))  # row number = position in rating arrays
    measures = hypotheses.participant_measures(participants, valence, arousal)
    samples = study_data.analysis_samples(participants[participants["sample"] == args.sample])

    tests, reliabilities, edges = [], [], []
    for name, group in samples.items():
        print(f"{name}: n = {len(group)}")
        tests += run_tests(name, group, participants, measures, valence, arousal, args.sample, args.seed)
        reliabilities += reliability(name, group, valence, arousal, args.seed)
    edges += segment_edges("primary", samples["primary"], arousal, args.seed)

    tests = pd.DataFrame(tests)
    tests.insert(0, "sample", args.sample)
    out.mkdir(parents=True, exist_ok=True)
    tests.to_csv(out / "hypothesis_tests.csv", index=False)
    pd.DataFrame(reliabilities).to_csv(out / "reliability.csv", index=False)
    pd.DataFrame(edges).to_csv(out / "segment_edges.csv", index=False)
    run_record.save_record(record, out)

    print_summary(tests)
    print(pd.DataFrame(reliabilities).round(3).to_string(index=False))
    print(pd.DataFrame(edges).to_string(index=False))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
