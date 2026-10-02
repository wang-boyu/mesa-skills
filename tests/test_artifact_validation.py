"""Independent CLI contracts for optional, individually installed YAML helpers.

These checks compare net file state; they do not prove absence of transient writes
or assess the truth of source, access, execution, or scientific claims.
"""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys

import pytest
import yaml
from jsonschema import Draft202012Validator  # Required QA dependency, never skip.


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures" / "artifact-validation"
HELPERS = {
    "sources": ("develop-mesa-model", "validate_sources.py"),
    "artifacts": ("evaluate-mesa-model", "validate_artifacts.py"),
}


def available(value="intentionally-absent.csv"):
    return {"availability": "available", "value": value}


def inventory():
    return {"schema_version": "1", "sources": [
        {"id": "survey", "kind": "dataset", "locator": available(),
         "roles": ["input_data", "comparison_evidence"],
         "authority": "Synthetic comparison data", "version": "v1",
         "commit": "declared-unverified-revision",
         "hash": {"algorithm": "sha256", "value": "declared-not-computed"},
         "license_note": "Synthetic metadata", "redistribution_note": "Metadata only",
         "confidentiality_note": "No private values", "notes": "Test record"},
        {"id": "report", "kind": "report",
         "locator": {"availability": "protected", "access_note": "Metadata only"},
         "roles": ["conceptual_model"], "authority": "Synthetic report"},
    ]}


def provenance():
    return {"schema_version": "1", "runs": [{
        "id": "run-a", "status": "complete", "model_revision": available("revision-a"),
        "configuration": {"scenario": "baseline", "parameters": {"population": 12}},
        "environment": {"description": "Synthetic test environment"},
        "randomness": {"policy": "fixed_seed", "seeds": [1729]},
        "command": available("python -c 'raise RuntimeError(\"must not execute\")'"),
        "analysis_revision": available("analysis-a"),
        "inputs": [{"id": "raw", "source_id": "survey", "locator": available()}],
        "raw_outputs": [{"id": "raw", "locator": available("absent-raw.csv")}],
        "derived_outputs": [
            {"id": "summary", "derived_from": ["raw"], "locator": available()},
            {"id": "plot", "derived_from": ["summary"], "locator": available()},
        ],
    }]}


def snapshot(root):
    result = {}
    for path in [root, *sorted(root.rglob("*"))]:
        info = path.lstat()
        content = (os.readlink(path) if path.is_symlink() else
                   path.read_bytes() if stat.S_ISREG(info.st_mode) else None)
        result[path.relative_to(root)] = (info.st_mode, info.st_mtime_ns, content)
    return result


class InstalledValidator:
    def __init__(self, root, helper):
        self.root, self.helper = root, helper
        skill, script = HELPERS[helper]
        self.package = root / "installed" / skill
        shutil.copytree(ROOT / "skills" / skill, self.package)
        self.script = self.package / "scripts" / script
        assert self.script.is_file(), "Absent implementations must fail QA, never skip."
        assert set(path.name for path in self.package.parent.iterdir()) == {skill}
        self.artifacts = root / "user-artifacts"
        self.artifacts.mkdir()
        note = root / "protected-note.txt"
        note.write_bytes(b"Preserve this unrelated user note.\n")
        note.chmod(0o400)
        self.target = self.artifacts / "sources.yaml" if helper == "sources" else self.artifacts

    def write(self, name, content):
        path = self.artifacts / name
        path.write_text(content if isinstance(content, str) else
                        yaml.safe_dump(content, sort_keys=False), encoding="utf-8")
        path.chmod(0o640)
        return path

    def run(self, *arguments, target=None, no_site=False, help_only=False):
        assert not list(self.package.rglob("__pycache__"))
        before = snapshot(self.root)
        environment = os.environ.copy()
        environment.pop("PYTHONPATH", None)
        environment.pop("PYTHONDONTWRITEBYTECODE", None)
        command = [sys.executable, "-I"]
        if no_site:
            command.append("-S")
        command.append(str(self.script))
        command.extend(["--help"] if help_only else
                       [str(self.target if target is None else target), *arguments])
        result = subprocess.run(command, cwd=self.artifacts, env=environment,
                                capture_output=True, text=True, check=False, timeout=60)
        assert snapshot(self.root) == before, "Validator altered package or user files."
        assert not list(self.package.rglob("__pycache__"))
        assert "traceback" not in result.stderr.lower(), result.stderr
        return result


@pytest.fixture
def installed(tmp_path):
    assert not tmp_path.resolve().is_relative_to(ROOT.resolve())
    return lambda helper: InstalledValidator(tmp_path, helper)


def assert_pass(result):
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")


def assert_invalid(result, location, category="schema"):
    assert result.returncode == 1, result.stderr
    assert result.stdout == ""
    assert location in result.stderr, result.stderr
    assert category.lower() in result.stderr.lower(), result.stderr


@pytest.mark.parametrize("helper", HELPERS)
def test_valid_inventory_metadata_is_structural_and_nonmutating(installed, helper):
    cli = installed(helper)
    cli.write("sources.yaml", inventory())
    assert_pass(cli.run())


def test_source_cli_accepts_relative_alternate_path_and_reports_supplied_path(installed):
    cli = installed("sources")
    cli.write("alternate.yml", inventory())
    assert_pass(cli.run(target="alternate.yml"))
    data = inventory()
    data["sources"][1]["id"] = "survey"
    cli.write("alternate.yml", data)
    result = cli.run(target="alternate.yml")
    assert_invalid(result, "$.sources[1].id", "duplicate source")
    assert all(line.startswith("alternate.yml:") for line in result.stderr.splitlines())


def test_two_runs_allow_repeated_input_output_ids_and_acyclic_derived_chains(installed):
    cli = installed("artifacts")
    cli.write("sources.yaml", inventory())
    data = provenance()
    second = copy.deepcopy(data["runs"][0])
    second["id"] = "run-b"
    data["runs"].append(second)
    cli.write("experiment_provenance.yaml", data)
    assert_pass(cli.run("--require-provenance"))


def test_optional_artifacts_and_exact_filename_discovery(installed):
    cli = installed("artifacts")
    assert_pass(cli.run())
    for name in ("unrelated.yaml", "sources.yml", "experiment_provenance.yml", "sources.json"):
        cli.write(name, "malformed: [\n")
    assert_pass(cli.run())
    assert_invalid(cli.run("--require-provenance"), "experiment_provenance.yaml", "absent")


def test_missing_artifact_directory_fails_without_creating_it(installed):
    cli = installed("artifacts")
    missing = cli.artifacts / "absent"
    assert_invalid(cli.run(target=missing), str(missing), "directory")
    assert not missing.exists()


@pytest.mark.parametrize("status", ["planned", "running", "complete", "failed", "blocked", "incomplete"])
def test_status_does_not_require_outputs_or_claim_exclusion_membership(installed, status):
    cli = installed("artifacts")
    data = provenance()
    run = data["runs"][0]
    run["status"] = status
    for key in ("inputs", "raw_outputs", "derived_outputs"):
        del run[key]
    run["exclusions"] = [{"reason": "Declared external exclusion", "record_ids": ["external-row"]}]
    cli.write("experiment_provenance.yaml", data)
    assert_pass(cli.run("--require-provenance"))


ID_CASES = [
    ("source", "$.sources[1].id", "duplicate source"),
    ("run", "$.runs[1].id", "duplicate run"),
    ("input", "$.runs[0].inputs[1].id", "duplicate input"),
    ("raw", "$.runs[0].raw_outputs[1].id", "duplicate output"),
    ("derived", "$.runs[0].derived_outputs[2].id", "duplicate output"),
    ("raw-derived", "$.runs[0].derived_outputs[0].id", "duplicate output"),
    ("unknown-source", "$.runs[0].inputs[0].source_id", "unknown source"),
    ("absent-source", "$.runs[0].inputs[0].source_id", "absent"),
    ("unknown-output", "$.runs[0].derived_outputs[0].derived_from[0]", "unknown output"),
    ("other-run-output", "$.runs[0].derived_outputs[0].derived_from[0]", "unknown output"),
    ("input-as-output", "$.runs[0].derived_outputs[0].derived_from[0]", "unknown output"),
    ("self", "$.runs[0].derived_outputs[0].derived_from[0]", "itself"),
    ("cycle", "$.runs[0].derived_outputs", "cyclic"),
]


@pytest.mark.parametrize("mutation,location,category", ID_CASES, ids=[x[0] for x in ID_CASES])
def test_identifier_and_reference_scope(installed, mutation, location, category):
    cli = installed("artifacts")
    sources, data = inventory(), provenance()
    run = data["runs"][0]
    if mutation == "source":
        sources["sources"][1]["id"] = "survey"
    elif mutation == "run":
        data["runs"].append(copy.deepcopy(run))
    elif mutation == "input":
        run["inputs"].append(copy.deepcopy(run["inputs"][0]))
    elif mutation in ("raw", "derived"):
        outputs = run[f"{mutation}_outputs"]
        outputs.append(copy.deepcopy(outputs[0]))
    elif mutation == "raw-derived":
        run["derived_outputs"][0]["id"] = "raw"
    elif mutation == "unknown-source":
        run["inputs"][0]["source_id"] = "unknown"
    elif mutation in ("unknown-output", "other-run-output", "input-as-output"):
        run["derived_outputs"][0]["derived_from"] = ["elsewhere"]
        if mutation == "other-run-output":
            second = copy.deepcopy(run)
            second["id"] = "run-b"
            second["raw_outputs"][0]["id"] = "elsewhere"
            data["runs"].append(second)
        elif mutation == "input-as-output":
            run["inputs"][0]["id"] = "elsewhere"
    elif mutation == "self":
        run["derived_outputs"][0]["derived_from"] = ["summary"]
    elif mutation == "cycle":
        run["derived_outputs"][0]["derived_from"] = ["plot"]
    if mutation != "absent-source":
        cli.write("sources.yaml", sources)
    cli.write("experiment_provenance.yaml", data)
    first = cli.run()
    assert_invalid(first, location, category)
    if mutation == "cycle":
        assert first.stderr == cli.run().stderr
        assert first.stderr.splitlines() == sorted(first.stderr.splitlines())


SOURCE_CASES = [
    ("missing-authority", "$.sources[0]"), ("blank-id", "$.sources[0].id"),
    ("blank-authority", "$.sources[0].authority"), ("version", "$.schema_version"),
    ("kind", "$.sources[0].kind"), ("role", "$.sources[0].roles[0]"),
    ("duplicate-role", "$.sources[0].roles"), ("unknown-field", "$.sources[0]"),
]


@pytest.mark.parametrize("helper", HELPERS)
@pytest.mark.parametrize("mutation,location", SOURCE_CASES, ids=[x[0] for x in SOURCE_CASES])
def test_source_closed_schema(installed, helper, mutation, location):
    cli = installed(helper)
    data = inventory()
    source = data["sources"][0]
    if mutation == "missing-authority":
        del source["authority"]
    elif mutation.startswith("blank-"):
        source[mutation.removeprefix("blank-")] = " \t"
    elif mutation == "version":
        data["schema_version"] = "2"
    elif mutation == "kind":
        source["kind"] = "spreadsheet"
    elif mutation == "role":
        source["roles"] = ["unsupported"]
    elif mutation == "duplicate-role":
        source["roles"] = ["input_data", "input_data"]
    else:
        source["unexpected"] = True
    cli.write("sources.yaml", data)
    assert_invalid(cli.run(), location)


LOCATORS = [
    (available(), True),
    ({**available(), "access_note": "Declared access"}, True),
    ({"availability": "protected", "access_note": "Restricted"}, True),
    ({"availability": "unavailable", "access_note": "Absent"}, True),
    ({"availability": "available"}, False),
    ({"availability": "available", "value": " "}, False),
    ({"availability": "protected"}, False),
    ({"availability": "protected", "access_note": " "}, False),
    ({"availability": "unavailable"}, False),
    ({"availability": "unavailable", "access_note": " "}, False),
    ({"availability": "protected", "access_note": "Restricted", "value": "secret"}, False),
    ({"availability": "unavailable", "access_note": "Absent", "value": "secret"}, False),
]


@pytest.mark.parametrize("placement", ["source", "evaluation-source", "input", "model_revision", "output"])
@pytest.mark.parametrize("locator,valid", LOCATORS)
def test_access_locator_contract(installed, placement, locator, valid):
    cli = installed("sources" if placement == "source" else "artifacts")
    if placement in ("source", "evaluation-source"):
        data = inventory()
        data["sources"][0]["locator"] = locator
        cli.write("sources.yaml", data)
        location = "$.sources[0].locator"
    else:
        data = provenance()
        run = data["runs"][0]
        del run["inputs"][0]["source_id"]
        if placement == "model_revision":
            run[placement] = locator
            location = "$.runs[0].model_revision"
        else:
            key = "inputs" if placement == "input" else "raw_outputs"
            run[key][0]["locator"] = locator
            location = f"$.runs[0].{key}[0].locator"
        cli.write("experiment_provenance.yaml", data)
    result = cli.run()
    assert_pass(result) if valid else assert_invalid(result, location)


@pytest.mark.parametrize("helper,artifact", [("sources", "sources.yaml"),
    ("artifacts", "sources.yaml"), ("artifacts", "experiment_provenance.yaml")])
@pytest.mark.parametrize("content,category", [
    ('schema_version: "1"\nschema_version: "1"\n', "duplicate mapping key"),
    ('schema_version: "1"\nunclosed: [\n', "invalid YAML"),
])
def test_yaml_parse_errors(installed, helper, artifact, content, category):
    cli = installed(helper)
    cli.write(artifact, content)
    assert_invalid(cli.run(), artifact, category)


@pytest.mark.parametrize("value,location", [
    ("!!set {alpha: null, beta: null}", "$.sources[0].roles"),
    ("&cycle [*cycle]", "$.sources[0].roles[0]"),
    ("{1: value}", "$.sources[0].roles"),
    (".nan", "$.sources[0].roles"),
    (".inf", "$.sources[0].roles"),
])
def test_source_rejects_non_json_yaml_deterministically(installed, value, location):
    cli = installed("sources")
    text = yaml.safe_dump(inventory(), sort_keys=False)
    text = text.replace("  roles:\n  - input_data\n  - comparison_evidence", "  roles: " + value)
    assert "  roles: " + value in text
    cli.write("sources.yaml", text)
    first = cli.run()
    assert_invalid(first, location, "JSON domain")
    assert first.stderr == cli.run().stderr


@pytest.mark.parametrize("field", ["model_revision", "configuration", "environment", "randomness", "command", "analysis_revision"])
def test_provenance_requires_run_description_fields(installed, field):
    cli = installed("artifacts")
    data = provenance()
    del data["runs"][0][field]
    cli.write("experiment_provenance.yaml", data)
    result = cli.run()
    assert_invalid(result, "$.runs[0]")
    assert field in result.stderr


@pytest.mark.parametrize("mutation,location", [("version", "$.schema_version"),
    ("status", "$.runs[0].status"), ("unknown-field", "$.runs[0]")])
def test_provenance_closed_version_and_status_schema(installed, mutation, location):
    cli = installed("artifacts")
    data = provenance()
    if mutation == "version":
        data["schema_version"] = "2"
    else:
        data["runs"][0]["status" if mutation == "status" else "extra"] = "validated"
    cli.write("experiment_provenance.yaml", data)
    assert_invalid(cli.run(), location)


RANDOMNESS = [
    ({"policy": "fixed_seed", "seeds": [1]}, True),
    ({"policy": "fixed_seed"}, False),
    ({"policy": "fixed_seed", "seeds": []}, False),
    ({"policy": "fixed_seed", "seeds": [1, 2]}, False),
    ({"policy": "seed_set", "seeds": [1, "seed-key"]}, True),
    ({"policy": "seed_set"}, False),
    ({"policy": "seed_set", "seeds": []}, False),
    ({"policy": "seed_set", "seeds": [1, 1]}, False),
    ({"policy": "sampled", "seeds": [1]}, True),
    ({"policy": "sampled", "description": "External ledger"}, True),
    ({"policy": "sampled", "seeds": [1], "description": "External ledger"}, True),
    ({"policy": "sampled"}, False),
    ({"policy": "sampled", "seeds": []}, False),
    ({"policy": "sampled", "seeds": [], "description": "External ledger"}, False),
    ({"policy": "replayed", "description": "Ledger replay"}, True),
    ({"policy": "replayed", "description": "Ledger replay", "seeds": [1]}, True),
    ({"policy": "replayed"}, False),
    ({"policy": "replayed", "seeds": [1]}, False),
    ({"policy": "replayed", "description": " "}, False),
    ({"policy": "not_applicable"}, True),
    ({"policy": "not_applicable", "seeds": [1]}, False),
    ({"policy": "unknown"}, False),
]


@pytest.mark.parametrize("randomness,valid", RANDOMNESS)
def test_randomness_conditional_schema(installed, randomness, valid):
    cli = installed("artifacts")
    data = provenance()
    data["runs"][0]["randomness"] = randomness
    del data["runs"][0]["inputs"]
    cli.write("experiment_provenance.yaml", data)
    result = cli.run()
    assert_pass(result) if valid else assert_invalid(result, "$.runs[0].randomness")


@pytest.mark.parametrize("exclusion,valid", [
    ({"reason": "Declared reason"}, True),
    ({"reason": " "}, False),
    ({"reason": "Declared reason", "record_ids": []}, False),
    ({"reason": "Declared reason", "record_ids": ["row", "row"]}, False),
    ({"reason": "Declared reason", "record_ids": ["outside-any-dataset"]}, True),
])
def test_exclusion_shape_without_membership_claims(installed, exclusion, valid):
    cli = installed("artifacts")
    data = provenance()
    run = data["runs"][0]
    del run["inputs"]
    run["exclusions"] = [exclusion]
    cli.write("experiment_provenance.yaml", data)
    result = cli.run()
    assert_pass(result) if valid else assert_invalid(result, "$.runs[0].exclusions[0]")


@pytest.mark.parametrize("helper", HELPERS)
def test_help_without_dependencies_and_actual_validation_missing_dependencies(installed, helper):
    cli = installed(helper)
    cli.write("sources.yaml", inventory())
    help_result = cli.run(no_site=True, help_only=True)
    assert help_result.returncode == 0
    assert "usage:" in help_result.stdout.lower()
    assert help_result.stderr == ""
    result = cli.run(no_site=True)
    assert result.returncode == 2
    assert result.stdout == ""
    assert "dependenc" in result.stderr.lower()


@pytest.mark.parametrize("defect", ["missing", "directory", "invalid-utf8", "fifo"])
def test_source_input_inspection_failures_exit_two(installed, defect):
    cli = installed("sources")
    if defect == "directory":
        cli.target.mkdir()
    elif defect == "invalid-utf8":
        cli.target.write_bytes(b"\xff")
    elif defect == "fifo":
        os.mkfifo(cli.target)
    result = cli.run()
    assert result.returncode == 2
    assert result.stdout == ""
    assert "cannot read" in result.stderr.lower()
    assert str(cli.target) in result.stderr


SCHEMA_FAILURES = [
    ("sources", "sources.schema.json", 2),
    ("artifacts", "sources.schema.json", 1),
    ("artifacts", "experiment-provenance.schema.json", 1),
]


@pytest.mark.parametrize("helper,schema_name,status", SCHEMA_FAILURES)
@pytest.mark.parametrize("defect", ["missing", "malformed-json", "invalid-schema"])
def test_local_schema_failures_have_distinct_exit_codes(installed, helper, schema_name, status, defect):
    cli = installed(helper)
    cli.write("sources.yaml", inventory())
    schema = cli.package / "assets" / schema_name
    if defect == "missing":
        schema.unlink()
    elif defect == "malformed-json":
        schema.write_text("{bad\n", encoding="utf-8")
    else:
        schema.write_text(json.dumps({"$schema": "https://json-schema.org/draft/2020-12/schema",
                                      "type": 7}), encoding="utf-8")
    result = cli.run()
    assert result.returncode == status, result.stderr
    assert result.stdout == ""
    assert schema_name in result.stderr and "schema" in result.stderr.lower()


@pytest.mark.parametrize("declaration", [None, "https://json-schema.org/draft/2019-09/schema"])
def test_source_schema_requires_supported_draft(installed, declaration):
    cli = installed("sources")
    cli.write("sources.yaml", inventory())
    schema = {"type": "object"}
    if declaration is not None:
        schema["$schema"] = declaration
    path = cli.package / "assets" / "sources.schema.json"
    path.write_text(json.dumps(schema), encoding="utf-8")
    result = cli.run()
    assert result.returncode == 2
    assert "draft" in result.stderr.lower()


@pytest.mark.parametrize("helper", HELPERS)
def test_shipped_template_is_only_a_structurally_valid_example(installed, helper):
    cli = installed(helper)
    name = "sources.yaml" if helper == "sources" else "experiment_provenance.yaml"
    cli.write(name, (cli.package / "assets" / name).read_text(encoding="utf-8"))
    assert_pass(cli.run())


FIXTURE_CASES = [
    ("valid/evaluation-provenance", "artifacts", 0, ""),
    ("valid/evaluation-provenance", "sources", 0, ""),
    ("valid/protected-and-unavailable-sources", "sources", 0, ""),
    ("valid/randomness-policy-matrix", "artifacts", 0, ""),
    ("invalid/multiple-errors", "artifacts", 1, "schema"),
    ("invalid/multiple-errors", "sources", 1, "schema"),
    ("invalid/derived-output-cycle", "artifacts", 1, "cyclic"),
    ("invalid/missing-protected-access-note", "sources", 1, "access_note"),
]


@pytest.mark.parametrize("fixture,helper,status,category", FIXTURE_CASES)
def test_representative_retained_artifact_examples(installed, fixture, helper, status, category):
    cli = installed(helper)
    for path in (FIXTURES / fixture).iterdir():
        shutil.copy2(path, cli.artifacts / path.name)
    first = cli.run()
    if status == 0:
        assert_pass(first)
    else:
        assert_invalid(first, "$", category)
        assert first.stderr == cli.run().stderr
        lines = first.stderr.splitlines()
        assert lines == sorted(lines)
        if "multiple-errors" in fixture:
            assert len(lines) >= 2
