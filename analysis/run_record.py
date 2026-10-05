"""A record of every analysis run, saved next to its results.

It answers "which code, which data and which settings produced these numbers?": the git commit, whether there
were uncommitted changes, a fingerprint (SHA-256) of each input file, the random seed, the package versions and
the exact command.

It also guards the confirmatory run of the registered tests (02_confirmatory.py): that run happens once, from a
clean committed state. Figures and descriptive tables are not covered by the preregistration and can be redrawn.
"""
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGES = ["numpy", "pandas", "scipy", "matplotlib", "statsmodels"]


def git(*arguments):
    return subprocess.run(["git", *arguments], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def code_changed(porcelain_status):
    """True if `git status --porcelain` output lists any file outside results/.

    Each line is a two-letter status, a space, then the path, so the path starts at the 4th character.
    """
    changed = [line for line in porcelain_status.splitlines() if line.strip()]
    return any(not line[3:].strip('"').startswith("results/") for line in changed)


def has_uncommitted_changes():
    """True if any file outside results/ differs from the last commit (including new, untracked files)."""
    status = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True,
                            check=True).stdout  # not stripped: the first line may start with a space
    return code_changed(status)


def file_fingerprint(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def make_record(script, sample, seed, inputs, settings=None):
    """Everything needed to say how a run was made."""
    return {
        "script": script,
        "sample": sample,
        "seed": seed,
        "settings": settings or {},
        "started": datetime.now().astimezone().isoformat(timespec="seconds"),
        "command": " ".join(sys.argv),
        "git_commit": git("rev-parse", "HEAD"),
        "uncommitted_changes": has_uncommitted_changes(),
        "inputs": {str(path): file_fingerprint(path) for path in inputs},
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "packages": {name: version(name) for name in PACKAGES},
    }


def record_path(script, folder):
    return Path(folder) / f"run_record_{Path(script).stem}.json"


def save_record(record, folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    path = record_path(record["script"], folder)
    path.write_text(json.dumps(record, indent=2))
    return path


def check_run_allowed(record, folder):
    """Stop a confirmatory run that is not from a clean commit, or that has been run before."""
    if record["sample"] != "confirmatory":
        return
    if record["uncommitted_changes"]:
        raise RuntimeError("The confirmatory run needs a clean committed state: commit or remove the "
                           "uncommitted changes first (see `git status`).")
    if record_path(record["script"], folder).exists():
        raise RuntimeError(f"{record['script']} has already been run on the confirmatory sample "
                           f"(see {record_path(record['script'], folder)}). It is run once only.")
