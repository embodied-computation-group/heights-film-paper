"""Step 10 (EXPLORATORY): change in each STICSA somatic item from before to after the film, ranked.

Not a registered test (Holm correction across the 11 items). Primary sample.

Run:  uv run python analysis/10_sticsa_items.py                 (exploratory sample, the default)
      uv run python analysis/10_sticsa_items.py --sample confirmatory
Writes results/<sample>/exploratory_items/sticsa_items.csv and a run record.
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # so `analysis` can be imported
from analysis import run_record, sticsa_items, study_data  # noqa: E402

RESULTS = Path(__file__).resolve().parent.parent / "results"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sample", choices=["exploratory", "confirmatory"], default="exploratory")
    args = parser.parse_args()

    out = RESULTS / args.sample / "exploratory_items"
    record = run_record.make_record("10_sticsa_items.py", args.sample, seed=None,
                                    inputs=sorted(study_data.DATA.glob("*.csv")), settings={"exploratory": True})
    participants, _, _ = study_data.load()
    primary = study_data.analysis_samples(participants[participants["sample"] == args.sample])["primary"]

    table = sticsa_items.item_changes(primary)
    out.mkdir(parents=True, exist_ok=True)
    table.to_csv(out / "sticsa_items.csv", index=False)
    run_record.save_record(record, out)
    with pd.option_context("display.width", 200):
        print(f"{args.sample}: n = {len(primary)}")
        print(table[["rank", "item", "label", "mean_before", "mean_after", "mean_change", "share_increased", "dz",
                     "dz_ci_low", "dz_ci_high", "p_holm"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
