"""Step 1: describe the sample - completions, registered exclusions, analysis samples, age, sex and input device.

Run:  uv run python analysis/01_sample.py                 (exploratory sample, the default)
      uv run python analysis/01_sample.py --sample confirmatory

Writes results/<sample>/exclusions.csv, sample_description.csv and a run record.
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # so `analysis` can be imported
from analysis import run_record, study_data  # noqa: E402

RESULTS = Path(__file__).resolve().parent.parent / "results"


def count_exclusions(completers):
    """How many completers each registered exclusion rule removes (one person can break several rules)."""
    rules = completers["registered_exclusion"].dropna()
    rules = rules[rules != ""].str.split("; ").explode()
    counts = rules.value_counts().rename_axis("rule").reset_index(name="n_participants")
    total = pd.DataFrame({"rule": ["completed the study", "excluded (any rule)", "usable"],
                          "n_participants": [len(completers), int((~study_data.is_usable(completers)).sum()),
                                             int(study_data.is_usable(completers).sum())]})
    return pd.concat([total, counts], ignore_index=True)


def describe(name, group):
    """Size, age, sex and input device of one analysis sample."""
    row = {"analysis_sample": name, "n": len(group),
           "age_mean": group["age"].mean(), "age_sd": group["age"].std(),
           "age_min": group["age"].min(), "age_max": group["age"].max(),
           "age_missing": int(group["age"].isna().sum())}
    for sex, count in group["sex"].fillna("missing").value_counts().items():
        row[f"sex_{sex.lower()}"] = int(count)
    for device, count in group["input_device"].fillna("missing").value_counts().items():
        row[f"device_{device}"] = int(count)
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sample", choices=["exploratory", "confirmatory"], default="exploratory")
    args = parser.parse_args()

    out = RESULTS / args.sample
    inputs = sorted(study_data.DATA.glob("*.csv"))
    record = run_record.make_record("01_sample.py", args.sample, seed=None, inputs=inputs)

    participants, _, _ = study_data.load()
    completers = participants[participants["sample"] == args.sample]

    exclusions = count_exclusions(completers)
    samples = study_data.analysis_samples(completers)
    description = pd.DataFrame([describe(name, group) for name, group in samples.items()]).fillna(0)

    out.mkdir(parents=True, exist_ok=True)
    exclusions.to_csv(out / "exclusions.csv", index=False)
    description.to_csv(out / "sample_description.csv", index=False)
    run_record.save_record(record, out)

    print(f"\n{args.sample} sample - exclusions under the registered rules")
    print(exclusions.to_string(index=False))
    print("\nAnalysis samples")
    print(description.round(1).T.to_string(header=False))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
