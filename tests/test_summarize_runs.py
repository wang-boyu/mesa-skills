"""Numerical, negative and preservation checks; no model execution."""
import json
import math
import os
from pathlib import Path
import runpy
import subprocess
import sys

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "skills/evaluate-mesa-model/scripts/summarize_runs.py"
# Loading a file as a script avoids writing import bytecode into the skill.
summarize = runpy.run_path(str(SCRIPT))["summarize"]


def test_independent_arithmetic():
    result = summarize([2, 4])
    assert result == {"n": 2, "mean": 3, "sample_sd": math.sqrt(2), "standard_error": 1}
    assert summarize([2] * 4 + [4] * 4)["standard_error"] == pytest.approx(1 / math.sqrt(7))
    # The smaller number is arithmetic, not justification for pooling dependent rows.
    assert summarize([0, 0])["sample_sd"] == 0
    assert summarize([-2, 0, 2])["sample_sd"] == 2


@pytest.mark.parametrize("values", [
    [], [1], {}, None, [True, 2], [1, "2"], [1, None],
    [1, float("nan")], [float("inf"), 1], [-float("inf"), 1],
    [10 ** 400, 1], [-1.7e308, 1.7e308],
])
def test_unsuitable_values(values):
    with pytest.raises(ValueError):
        summarize(values)


def invoke(path):
    return subprocess.run([sys.executable, "-I", "-S", "-B", str(SCRIPT), str(path)],
                          text=True, capture_output=True, check=False, timeout=5)


def test_cli_success_preserves_input(tmp_path):
    target = tmp_path / "runs.json"
    target.write_text("[2, 4]\n")
    before = (target.read_bytes(), target.stat().st_mode, target.stat().st_mtime_ns)
    for _ in range(2):
        result = invoke(target)
        assert result.returncode == 0
        assert json.loads(result.stdout)["standard_error"] == 1
        assert result.stderr == ""
    assert (target.read_bytes(), target.stat().st_mode, target.stat().st_mtime_ns) == before


@pytest.mark.parametrize("content", ["[1,]", "NaN", "[NaN, 2]", "[true, 2]", "[1]", "{}"])
def test_cli_invalid_data(tmp_path, content):
    target = tmp_path / "bad.json"
    target.write_text(content)
    result = invoke(target)
    assert result.returncode == 1
    assert result.stdout == ""
    assert "invalid run summaries" in result.stderr
    assert target.read_text() == content


def test_cli_unreadable_input(tmp_path):
    assert invoke(tmp_path / "absent").returncode == 2
    assert invoke(tmp_path).returncode == 2
    invalid = tmp_path / "invalid.json"
    invalid.write_bytes(b"\xff")
    assert invoke(invalid).returncode == 2


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="named pipes are unavailable")
def test_cli_rejects_fifo_without_waiting_for_a_writer(tmp_path):
    target = tmp_path / "input.pipe"
    os.mkfifo(target)
    result = invoke(target)
    assert result.returncode == 2
    assert result.stdout == ""
    assert "not a regular file" in result.stderr
