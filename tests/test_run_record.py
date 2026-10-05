"""Tests for analysis/run_record.py (what we save about every analysis run).

Run:  uv run pytest
"""
import hashlib
import json

import pytest

from analysis import run_record


def test_run_record_lists_code_version_inputs_seed_and_packages(tmp_path):
    data_file = tmp_path / "numbers.csv"
    data_file.write_text("a,b\n1,2\n")

    record = run_record.make_record(script="02_confirmatory.py", sample="exploratory", seed=123,
                                    inputs=[data_file])

    assert record["script"] == "02_confirmatory.py"
    assert record["sample"] == "exploratory"
    assert record["seed"] == 123
    assert record["inputs"][str(data_file)] == hashlib.sha256(data_file.read_bytes()).hexdigest()
    assert len(record["git_commit"]) == 40
    assert isinstance(record["uncommitted_changes"], bool)
    assert "numpy" in record["packages"] and "scipy" in record["packages"]
    assert "command" in record and "python" in record and "started" in record


def test_run_record_is_saved_as_readable_json(tmp_path):
    record = {"script": "x.py", "seed": 1}

    path = run_record.save_record(record, tmp_path)

    assert json.loads(path.read_text()) == record
    assert path.name == "run_record_x.json"


def test_confirmatory_run_is_refused_with_uncommitted_changes(tmp_path):
    record = {"sample": "confirmatory", "uncommitted_changes": True, "script": "x.py"}

    with pytest.raises(RuntimeError, match="uncommitted"):
        run_record.check_run_allowed(record, tmp_path)


def test_confirmatory_run_is_refused_if_it_has_already_been_run(tmp_path):
    record = {"sample": "confirmatory", "uncommitted_changes": False, "script": "x.py"}
    run_record.save_record(record, tmp_path)

    with pytest.raises(RuntimeError, match="already"):
        run_record.check_run_allowed(record, tmp_path)


def test_clean_first_confirmatory_run_and_any_exploratory_run_are_allowed(tmp_path):
    run_record.check_run_allowed({"sample": "confirmatory", "uncommitted_changes": False, "script": "x.py"},
                                 tmp_path)
    run_record.check_run_allowed({"sample": "exploratory", "uncommitted_changes": True, "script": "x.py"},
                                 tmp_path)


def test_changed_results_files_do_not_count_as_uncommitted_code_changes():
    # `git status --porcelain` lines start with a two-letter status and a space; the first line can start with a
    # space (" M"), which must not be stripped away.
    only_results = " M results/exploratory/run_record_01_sample.json\n?? results/confirmatory/\n"
    code_changed = " M results/exploratory/x.csv\n M analysis/hypotheses.py\n"

    assert not run_record.code_changed(only_results)
    assert run_record.code_changed(code_changed)
