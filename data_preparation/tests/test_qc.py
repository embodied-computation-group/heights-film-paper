"""Synthetic check that the QC automation/engagement flags separate human-like from scripted sessions.

Run: python tests/test_qc.py
"""
import json
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "qc"))
from qc_lib import flags, load_session, session_metrics  # noqa: E402

TEXT_HUMAN = ("I saw people climbing up a very tall building in a city with lots of skyscrapers. At first it was "
              "just stairs and corridors but then they got onto the roof and the edge. My hands got sweaty when "
              "the camera looked straight down and I felt a bit sick. The woman leaning over the edge made me "
              "really tense. Towards the end I calmed down when they were back inside. The rating was a bit hard "
              "at first but I got used to it after a few minutes and it was fine.")


def make_session(path: Path, scripted: bool, seed: int) -> None:
    rng = np.random.default_rng(seed)
    lines = [{"type": "meta", "prolific_pid": "BOT" if scripted else "HUMAN", "dimension": "anxiety", "n_loads": 1}]
    t = np.arange(0, 808.9, 0.05)
    value = 0.0
    samples, inputs = [], []
    for i, ts in enumerate(t):
        if scripted:
            # constant-velocity, perfectly vertical moves every 0.5 s, plus periodic jumps
            if i % 10 == 0:
                dx, dy = 0, (-400 if i % 4000 == 0 else -3)
                value = min(100, max(0, value - dy * 100 / 518))
                inputs.append([round(ts, 3), ts * 1000, round(value, 1), "m", dx, dy])
        elif rng.random() < 0.15:
            dx, dy = int(rng.normal(0, 2)), int(rng.normal(0, 6))
            if dx or dy:
                value = min(100, max(0, value - dy * 100 / 518))
                inputs.append([round(ts, 3), ts * 1000, round(value, 1), "m", dx, dy])
        samples.append([round(ts, 3), round(ts, 2), ts * 1000, round(value, 1), 1])
    for k in range(0, len(samples), 600):
        lines.append({"type": "chunk", "t": f"2026-10-04T00:{k // 600:02d}", "tag": "film", "chunk": k // 600,
                      "samples": samples[k:k + 600],
                      "inputs": [r for r in inputs if samples[k][0] <= r[0] < samples[min(k + 600, len(samples) - 1)][0] + 1e-9],
                      "events": []})
    n_chars = len(TEXT_HUMAN)
    trials = [
        {"task": "consent", "consent": True},
        {"task": "attention", "n_checks": 1, "n_failed": 0},
        {"task": "attention", "n_checks": 1, "n_failed": 0},
        {"task": "final_text", "text": TEXT_HUMAN, "n_words": len(TEXT_HUMAN.split()), "n_chars": n_chars,
         "n_keys": 3 if scripted else int(n_chars * 1.1), "rt": 240000, "away_ms": 0},
        {"task": "end"},
    ]
    lines += [{"type": "trial", "trial": tr} for tr in trials]
    lines.append({"type": "final", "summary": {"film_untrusted_events": 120 if scripted else 0}, "integrity": {}, "data": []})
    path.write_text("\n".join(json.dumps(x) for x in lines), encoding="utf8")


def main() -> None:
    with tempfile.TemporaryDirectory() as d:
        for name, scripted in (("human.ndjson", False), ("bot.ndjson", True)):
            make_session(Path(d) / name, scripted, seed=1)
        res = {}
        for name in ("human.ndjson", "bot.ndjson"):
            r = session_metrics(load_session(Path(d) / name))
            r["verdict"], rej, rev = flags(r)
            res[name] = (r, rej, rev)
            print(f"{name}: {r['verdict']}  teleports={r['n_teleports']} identical_run={r['identical_run_max']} "
                  f"pure_axis={r['frac_pure_axis']} keys/char={r['text_keys_per_char']} untrusted={r['untrusted_events']}")
            for x in rej:
                print("   REJECT-ELIGIBLE:", x)
            for x in rev:
                print("   review:", x)
        h, b = res["human.ndjson"], res["bot.ndjson"]
        assert h[0]["verdict"] == "OK", h
        assert b[0]["verdict"] == "REJECT-ELIGIBLE"
        joined = " ".join(b[2])
        assert "identical mouse steps" in joined and "off-axis" in joined and "isolated mouse jumps" in joined, b[2]
        print("OK: human-like session passes, scripted session is flagged on every automation signal")


if __name__ == "__main__":
    main()
