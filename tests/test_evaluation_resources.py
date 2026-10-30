"""Standalone evaluation assets and a tiny synthetic reporting consumer.

The routine suite stays offline. Plot checks use optional Matplotlib/Seaborn;
actual hook downloads and execution are a separate disposable-project exercise.
"""

import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
EVALUATION = ROOT / "skills" / "evaluate-mesa-model"
FIXTURE = ROOT / "tests" / "fixtures" / "evaluation-reporting"


def test_standalone_quality_assets(tmp_path):
    package = tmp_path / "only-evaluation"
    shutil.copytree(EVALUATION, package)
    quality = package / "assets" / "quality"
    config = yaml.safe_load((quality / ".pre-commit-config.yaml").read_text())
    hooks = {
        hook["id"]: hook
        for repository in config["repos"]
        for hook in repository["hooks"]
    }
    assert {
        "ruff-check",
        "ruff-format",
        "codespell",
        "trailing-whitespace",
        "end-of-file-fixer",
        "check-yaml",
        "check-toml",
    } <= hooks.keys()
    assert "--fix" in hooks["ruff-check"]["args"]
    assert list(hooks).index("ruff-check") < list(hooks).index("ruff-format")
    assert "--ignore-words=.codespellignore" in hooks["codespell"]["args"]
    assert not (quality / ".codespellignore").read_text().strip()
    for path in ("inputs/measurements.csv", "results/estimates.json"):
        assert re.search(config["exclude"], path)
    ruff = tomllib.loads((quality / "ruff.toml").read_text())
    assert ruff["force-exclude"]
    assert "I" in ruff["lint"]["select"]
    assert {"inputs", "results"} <= set(ruff["extend-exclude"])


@pytest.fixture
def report_project(tmp_path):
    project = tmp_path / "report project"
    shutil.copytree(FIXTURE, project)
    return project


def run_plot(project, tmp_path, *arguments):
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment.update(
        PYTHONDONTWRITEBYTECODE="1",
        MPLCONFIGDIR=str(tmp_path / "matplotlib-cache"),
        MPLBACKEND="Agg",
    )
    return subprocess.run(
        [sys.executable, *arguments],
        cwd=project,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def test_plot_import_requires_no_plotting_dependencies_or_writes(
    report_project, tmp_path
):
    before = {
        p.relative_to(report_project): p.read_bytes()
        for p in report_project.rglob("*")
        if p.is_file()
    }
    checked = run_plot(
        report_project,
        tmp_path,
        "-I",
        "-S",
        "-B",
        "-c",
        "import runpy, sys; runpy.run_path('evaluation/plot_results.py'); "
        "assert 'matplotlib' not in sys.modules; assert 'seaborn' not in sys.modules",
    )
    assert checked.returncode == 0, checked.stderr
    assert {
        p.relative_to(report_project): p.read_bytes()
        for p in report_project.rglob("*")
        if p.is_file()
    } == before


@pytest.mark.runtime
def test_saved_points_intervals_and_missing_coverage(
    report_project, monkeypatch, tmp_path
):
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path / "matplotlib-cache"))
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg")
    pytest.importorskip("seaborn")
    import matplotlib.pyplot as plt

    path = report_project / "evaluation" / "plot_results.py"
    spec = importlib.util.spec_from_file_location("synthetic_plot", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    before_style = dict(matplotlib.rcParams)
    figure, axes = module.build_figure(
        module.read_estimates(report_project / "results" / "estimates.json")
    )
    try:
        assert dict(matplotlib.rcParams) == before_style
        assert len(axes.containers) == 2
        for container, point, endpoints, position in zip(
            axes.containers, [0, -2], [(-1, 1), (-3, -0.5)], [0, 1], strict=True
        ):
            line, _, bars = container.lines
            assert list(line.get_xdata()) == [point]
            assert list(line.get_ydata()) == [position]
            assert bars[0].get_segments()[0].tolist() == [
                [endpoints[0], position],
                [endpoints[1], position],
            ]
        assert [label.get_text() for label in axes.get_yticklabels()] == [
            "Reference (8/8 runs)",
            "Lower (6/8 runs)",
            "Unavailable (0/8 runs)",
        ]
        assert [text.get_text() for text in axes.texts] == ["No estimate"]
        assert axes.get_xlabel() == "Mean score change (points)"
        assert axes.get_xlim()[0] < -3 < 0 < 1 < axes.get_xlim()[1]
    finally:
        plt.close(figure)
    assert not plt.fignum_exists(figure.number)


@pytest.mark.runtime
def test_headless_regeneration_relative_figure_and_preserved_inputs(
    report_project, tmp_path
):
    pytest.importorskip("matplotlib")
    pytest.importorskip("seaborn")
    inputs = report_project / "results" / "estimates.json"
    before = inputs.read_bytes()
    command = ("evaluation/plot_results.py", "--output-dir", "docs/figures")
    first = run_plot(report_project, tmp_path, *command)
    assert first.returncode == 0, first.stderr
    report = (report_project / "docs" / "evaluation_results.md").read_text()
    images = re.findall(r"!\[[^]]*\]\(([^)]+)\)", report)
    assert images and all(not Path(link).is_absolute() for link in images)
    for link in images:
        image = report_project / "docs" / link
        assert image.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    original_figure = image.read_bytes()
    repeated = run_plot(report_project, tmp_path, *command)
    assert repeated.returncode != 0
    assert image.read_bytes() == original_figure
    regenerated = run_plot(
        report_project,
        tmp_path,
        "evaluation/plot_results.py",
        "--output-dir",
        "docs/figures-repeat",
    )
    assert regenerated.returncode == 0, regenerated.stderr
    assert (report_project / "docs/figures-repeat/estimates.png").is_file()
    missing = run_plot(
        report_project,
        tmp_path,
        "evaluation/plot_results.py",
        "--inputs",
        "results/absent.json",
        "--output-dir",
        "docs/missing-input",
    )
    assert missing.returncode != 0
    assert not (report_project / "docs/missing-input").exists()
    assert inputs.read_bytes() == before
