"""Status of one Prolific cohort, using data already fetched by qc/review.py.

  python qc/cohort_status.py <prolific_study_id>

Prints Prolific status counts, QC verdicts and flags for the cohort, whether it is finished (no ACTIVE or
RESERVED submissions), and the submission IDs that may be approved (AWAITING REVIEW and not REJECT-ELIGIBLE).
Last line is machine-readable JSON.
"""
import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sid = sys.argv[1]
subs = json.loads((ROOT / "data" / "raw" / f"prolific_{sid}.json").read_text(encoding="utf8"))
subs = subs.get("results", subs) if isinstance(subs, dict) else subs
status = Counter(x.get("status") for x in subs)
rep = pd.read_csv(ROOT / "qc" / "out" / "qc_report.csv")
by_pid = {r["prolific_pid"]: r for r in rep.to_dict("records")}

approvable, held, flagged = [], [], []
for x in subs:
    pid, st = x.get("participant_id"), x.get("status")
    r = by_pid.get(pid, {})
    verdict = r.get("verdict", "NO-DATA")
    if st == "AWAITING REVIEW":
        (held if verdict == "REJECT-ELIGIBLE" else approvable).append(x.get("id"))
    reasons = "; ".join(str(v) for v in (r.get("reject_reasons"), r.get("review_reasons")) if isinstance(v, str) and v)
    if verdict in ("REJECT-ELIGIBLE",) or (reasons and "did not complete" not in reasons):
        flagged.append(f"{pid[:8]} [{st}] {verdict}: {reasons}")

finished = status.get("ACTIVE", 0) == 0 and status.get("RESERVED", 0) == 0
print(f"Prolific statuses: {dict(status)}")
print(f"finished: {finished} | approvable: {len(approvable)} | held (reject-eligible): {len(held)}")
for f in flagged:
    print("  " + f)
print(json.dumps({"finished": finished, "approvable": approvable, "held": held, "status": dict(status)}))
