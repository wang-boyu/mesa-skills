"""Product-local metadata, resource links and isolated helper checks."""
import ast
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import unquote, urlsplit

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILLS = sorted((ROOT / "skills").iterdir())
LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
HELPERS = (
    ("document-abm-with-odd", "validate_odd.py"),
    ("evaluate-mesa-model", "summarize_runs.py"),
)
ODD_EXAMPLE = "\n\n".join((
    "## 1. Purpose and patterns\n\nExplore a synthetic fixed-rate counter.",
    "## 2. Entities, state variables, and scales\n\nOne counter stores integer tokens.",
    "## 3. Process overview and scheduling\n\nAdd one token, then record each tick.",
    "## 4. Design concepts\n\nThe deterministic total is observed after updates.",
    "## 5. Initialization\n\nThe counter starts at zero tokens.",
    "## 6. Input data\n\nNo external inputs vary during the run.",
    "## 7. Submodels\n\nIncrement by one; stop after three ticks.",
)).encode("utf-8") + b"\n"


def check_local_links(document, boundary):
    for raw in LINK.findall(document.read_text(encoding="utf-8")):
        target = raw.split()[0].strip("<>")
        url = urlsplit(target)
        if url.scheme or url.netloc or not url.path:
            continue
        resolved = (document.parent / unquote(url.path)).resolve()
        assert resolved.is_relative_to(boundary.resolve()), (document, target)
        assert resolved.is_file(), (document, target)


@pytest.mark.parametrize("skill", SKILLS, ids=lambda p: p.name)
def test_metadata_and_local_resources(skill):
    assert skill.is_dir() and not skill.is_symlink()
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---\n")
    _, frontmatter, body = text.split("---", 2)
    metadata = yaml.safe_load(frontmatter)
    assert metadata["name"] == skill.name
    assert re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", skill.name)
    assert len(skill.name) <= 64
    assert isinstance(metadata["description"], str)
    assert 0 < len(metadata["description"]) <= 1024
    assert body.strip()
    assert all(isinstance(k, str) and isinstance(v, str)
               for k, v in metadata.get("metadata", {}).items())
    for path in skill.rglob("*"):
        assert not path.is_symlink(), path
        if path.suffix == ".md":
            check_local_links(path, skill)
        if path.suffix == ".py":
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


@pytest.mark.parametrize("skill", SKILLS, ids=lambda p: p.name)
def test_individually_copied_package(skill, tmp_path):
    copied = tmp_path / "only-skill"
    shutil.copytree(skill, copied)
    for document in copied.rglob("*.md"):
        check_local_links(document, copied)
    elsewhere = tmp_path / "working"
    elsewhere.mkdir()
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    for script in copied.glob("scripts/*.py"):
        # Private implementation modules are package resources, not CLI entrypoints.
        if script.name.startswith("_"):
            continue
        completed = subprocess.run(
            [sys.executable, "-I", "-S", "-B", str(script), "--help"],
            cwd=elsewhere, env=env, text=True, capture_output=True, check=False,
            timeout=5)
        assert completed.returncode == 0, completed.stderr
    assert not list(copied.rglob("__pycache__"))


def run_copied_helper(tmp_path, skill_name, script_name, content):
    """Execute one isolated package; content=None supplies a named pipe."""
    assert not tmp_path.resolve().is_relative_to(ROOT.resolve())
    copied = tmp_path / "only-skill"
    shutil.copytree(ROOT / "skills" / skill_name, copied)
    working = tmp_path / "working"
    working.mkdir()
    target = working / "input"
    if content is None:
        os.mkfifo(target)
    else:
        target.write_bytes(content)
    (working / "unrelated.txt").write_bytes(b"Preserve this user note.\n")

    def snapshot():
        return {
            path.relative_to(tmp_path): (
                path.stat().st_mode, path.stat().st_mtime_ns,
                path.read_bytes() if path.is_file() else None,
            )
            for path in tmp_path.rglob("*")
        }

    before = snapshot()
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, "-I", "-S", "-B", str(copied / "scripts" / script_name),
         str(target)],
        cwd=working, env=env, text=True, capture_output=True, check=False,
        timeout=5,
    )
    assert snapshot() == before
    return result


def test_copied_odd_helper_checks_a_document(tmp_path):
    result = run_copied_helper(tmp_path, *HELPERS[0], ODD_EXAMPLE)
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert "Structure OK" in result.stdout
    assert "meaning, attribution, and scientific validity were not checked" in result.stdout


def test_copied_summary_helper_computes_independent_run_statistics(tmp_path):
    result = run_copied_helper(tmp_path, *HELPERS[1], b"[2, 4]\n")
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert json.loads(result.stdout) == {
        "n": 2, "mean": 3, "sample_sd": math.sqrt(2), "standard_error": 1,
    }


@pytest.mark.parametrize("helper, content, status, diagnostic", (
    (HELPERS[0], b"<script\n" + ODD_EXAMPLE, 1, "unsupported Markdown profile syntax"),
    (HELPERS[0], b"# No elements\n", 1, "expected the seven numbered ODD elements"),
    (HELPERS[0], b"\xff", 2, "cannot read UTF-8 input"),
    (HELPERS[1], b"[2,]\n", 1, "invalid run summaries"),
    (HELPERS[1], b"[true, 4]\n", 1, "run values must be numbers"),
    (HELPERS[1], b"\xff", 2, "cannot read input"),
), ids=("odd-html", "odd-missing-elements", "odd-utf8",
        "summary-json", "summary-boolean", "summary-utf8"))
def test_copied_helpers_reject_bad_inputs(tmp_path, helper, content, status, diagnostic):
    result = run_copied_helper(tmp_path, *helper, content)
    assert result.returncode == status, result.stderr
    assert result.stdout == ""
    assert diagnostic in result.stderr


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="named pipes are unavailable")
@pytest.mark.parametrize("helper", HELPERS, ids=("odd", "summary"))
def test_copied_helpers_reject_fifo_without_a_writer(tmp_path, helper):
    result = run_copied_helper(tmp_path, *helper, None)
    assert result.returncode == 2, result.stderr
    assert result.stdout == ""
    assert "not a regular file" in result.stderr


def test_readme_and_example_links():
    check_local_links(ROOT / "README.md", ROOT)
    for document in (ROOT / "examples").glob("*.md"):
        check_local_links(document, ROOT)
