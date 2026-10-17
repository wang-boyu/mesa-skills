"""Independent checks of copied development resources and a tiny model exercise.

The model is a synthetic consumer of the output asset, not a scientific model
acceptance claim. Real hook execution is a separate, task-local integration check;
the ordinary product suite does not download or install quality tools.
"""

import importlib.util
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tomllib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
DEVELOPMENT = ROOT / "skills" / "develop-mesa-model"
QUALITY = DEVELOPMENT / "assets" / "quality"
MODEL_FIXTURE = ROOT / "tests" / "fixtures" / "development-model"


@pytest.fixture
def allocator(tmp_path):
    copied = tmp_path / "run_output.py"
    shutil.copy2(DEVELOPMENT / "assets" / "run_output.py", copied)
    spec = importlib.util.spec_from_file_location("copied_run_output", copied)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.allocate_run_directory


def test_quality_templates_cover_required_checks_without_project_exceptions():
    config = yaml.safe_load((QUALITY / ".pre-commit-config.yaml").read_text())
    hooks = {
        hook["id"]: hook
        for repository in config["repos"]
        for hook in repository["hooks"]
    }
    required = {
        "ruff-check",
        "ruff-format",
        "codespell",
        "trailing-whitespace",
        "end-of-file-fixer",
        "check-yaml",
        "check-toml",
    }
    assert required <= hooks.keys()
    assert "--fix" in hooks["ruff-check"].get("args", [])
    ordered = [
        hook["id"] for repository in config["repos"] for hook in repository["hooks"]
    ]
    assert ordered.index("ruff-check") < ordered.index("ruff-format")
    for repository in config["repos"]:
        assert re.fullmatch(r"v?\d+\.\d+\.\d+", repository["rev"])
    spelling_arguments = hooks["codespell"].get("args", [])
    assert any(".codespellignore" in argument for argument in spelling_arguments)
    assert not [
        line
        for line in (QUALITY / ".codespellignore").read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    with (QUALITY / "ruff.toml").open("rb") as stream:
        ruff = tomllib.load(stream)
    assert "I" in ruff["lint"]["select"]


def test_allocator_preserves_partial_runs_and_claims_first_unused_name(
    allocator, tmp_path
):
    output = tmp_path / "nested" / "outputs"
    partial = output / "run-0001"
    partial.mkdir(parents=True)
    partial_file = partial / "unfinished.csv"
    partial_file.write_bytes(b"unfinished but valuable\n")
    occupied = output / "run-0002"
    occupied.write_bytes(b"existing file, not a run directory\n")
    third = output / "run-0003"
    third.symlink_to(partial, target_is_directory=True)
    before = (partial_file.read_bytes(), occupied.read_bytes(), os.readlink(third))
    random_before = random.getstate()

    first = allocator(output)
    second = allocator(output)

    assert first == output / "run-0004"
    assert second == output / "run-0005"
    assert first.is_dir() and second.is_dir()
    assert list(first.iterdir()) == list(second.iterdir()) == []
    assert (
        partial_file.read_bytes(),
        occupied.read_bytes(),
        os.readlink(third),
    ) == before
    assert random.getstate() == random_before


def test_allocator_retries_a_name_claimed_during_allocation(
    allocator, tmp_path, monkeypatch
):
    original_mkdir = Path.mkdir
    claimed = []

    def competing_mkdir(path, *args, **kwargs):
        # A competing writer wins immediately before the candidate mkdir. The
        # filesystem itself raises FileExistsError; no fabricated return oracle.
        if path.name == "run-0001" and not claimed:
            original_mkdir(path)
            (path / "partial.txt").write_text("competitor's partial result\n")
            claimed.append(path)
        return original_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", competing_mkdir)
    assert allocator(tmp_path) == tmp_path / "run-0002"
    assert (claimed[0] / "partial.txt").read_text() == "competitor's partial result\n"


def test_allocator_claims_distinct_directories_under_concurrent_calls(
    allocator, tmp_path
):
    output = tmp_path / "outputs"
    with ThreadPoolExecutor(max_workers=8) as pool:
        allocated = list(pool.map(lambda _: allocator(output), range(16)))
    assert len(set(allocated)) == 16
    assert {path.name for path in allocated} == {
        f"run-{number:04d}" for number in range(1, 17)
    }
    assert all(path.is_dir() for path in allocated)


def test_allocator_reuses_a_gap_and_propagates_invalid_parent(allocator, tmp_path):
    output = tmp_path / "outputs"
    (output / "run-0002").mkdir(parents=True)
    assert allocator(output) == output / "run-0001"
    blocked = tmp_path / "not-a-directory"
    blocked.write_text("preserve this file\n")
    with pytest.raises(OSError):
        allocator(blocked / "outputs")
    assert blocked.read_text() == "preserve this file\n"


@pytest.fixture
def model_project(tmp_path):
    project = tmp_path / "model with spaces"
    shutil.copytree(MODEL_FIXTURE, project)
    shutil.copy2(
        DEVELOPMENT / "assets" / "run_output.py", project / "transfer" / "run_output.py"
    )
    return project


def run_model(project, *arguments):
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, *arguments],
        cwd=project,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


@pytest.mark.runtime
def test_small_model_replays_rules_observation_and_portable_outputs(model_project):
    # These separately retained checks run against the same production fixture
    # used by the documented CLI, from a root unrelated to this repository.
    checked = run_model(model_project, "-m", "pytest", "-q", "-p", "no:cacheprovider")
    assert checked.returncode == 0, checked.stdout + checked.stderr
    assert "4 passed" in checked.stdout
    first = run_model(model_project, "-m", "transfer", "--steps", "6", "--seed", "41")
    assert first.returncode == 0, first.stderr
    first_path = model_project / first.stdout.strip()
    first_bytes = (first_path / "observations.json").read_bytes()
    second = run_model(model_project, "-m", "transfer", "--steps", "6", "--seed", "41")
    assert second.returncode == 0, second.stderr
    second_path = model_project / second.stdout.strip()
    assert first_path == model_project / "outputs" / "run-0001"
    assert second_path == model_project / "outputs" / "run-0002"
    assert first_path != second_path
    assert (first_path / "observations.json").read_bytes() == first_bytes
    assert json.loads((second_path / "observations.json").read_text()) == json.loads(
        first_bytes
    )
    assert not list(model_project.rglob("__pycache__"))
