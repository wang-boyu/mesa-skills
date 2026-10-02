#!/usr/bin/env python3
"""Validate optional local source and experiment-provenance YAML artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

ASSETS = Path(__file__).resolve().parents[1] / "assets"
SCHEMA_PATHS = {
    "sources.yaml": ASSETS / "sources.schema.json",
    "experiment_provenance.yaml": ASSETS / "experiment-provenance.schema.json",
}


@dataclass(frozen=True, order=True)
class Diagnostic:
    artifact: str
    location: str
    message: str

    def render(self) -> str:
        return f"{self.artifact}:{self.location}: {self.message}"


def _unique_key_loader(yaml_module: Any) -> type[Any]:
    class UniqueKeyLoader(yaml_module.SafeLoader):
        """Safe YAML loader that rejects ambiguous duplicate mapping keys."""


    def _construct_unique_mapping(
        loader: UniqueKeyLoader, node: Any, deep: bool = False
    ) -> Dict[Any, Any]:
        loader.flatten_mapping(node)
        mapping: Dict[Any, Any] = {}
        key_marks: Dict[Any, Any] = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            try:
                duplicate = key in mapping
            except TypeError as exc:
                raise yaml_module.constructor.ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    "found an unhashable mapping key",
                    key_node.start_mark,
                ) from exc
            if duplicate:
                first_mark = key_marks[key]
                raise yaml_module.constructor.ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    (
                        f"duplicate mapping key {key!r}; first declared at "
                        f"line {first_mark.line + 1}, column {first_mark.column + 1}"
                    ),
                    key_node.start_mark,
                )
            mapping[key] = loader.construct_object(value_node, deep=deep)
            key_marks[key] = key_node.start_mark
        return mapping


    UniqueKeyLoader.add_constructor(
        yaml_module.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_unique_mapping
    )
    return UniqueKeyLoader


def _parse_arguments(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "validate sources.yaml and experiment_provenance.yaml in an artifact "
            "directory"
        )
    )
    parser.add_argument("artifact_dir", type=Path, metavar="ARTIFACT_DIR")
    parser.add_argument("--require-provenance", action="store_true")
    return parser.parse_args(argv)


def _format_json_path(parts: Iterable[Any]) -> str:
    path = "$"
    for part in parts:
        if isinstance(part, int):
            path += f"[{part}]"
        elif isinstance(part, str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", part):
            path += f".{part}"
        else:
            path += f"[{json.dumps(part, ensure_ascii=True)}]"
    return path


def _load_yaml(path: Path, artifact: str) -> Tuple[Optional[Any], List[Diagnostic]]:
    import yaml

    try:
        with path.open("r", encoding="utf-8") as stream:
            return yaml.load(stream, Loader=_unique_key_loader(yaml)), []
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        if mark is None:
            location = "$"
        else:
            location = f"line {mark.line + 1}, column {mark.column + 1}"
        problem = getattr(exc, "problem", None) or str(exc).splitlines()[0]
        return None, [Diagnostic(artifact, location, f"invalid YAML: {problem}")]
    except (OSError, UnicodeError) as exc:
        return None, [Diagnostic(artifact, "$", f"cannot read artifact: {exc}")]


def _load_validator(
    schema_path: Path,
) -> Tuple[Optional[Any], List[Diagnostic]]:
    from jsonschema import Draft202012Validator
    from jsonschema.exceptions import SchemaError

    try:
        with schema_path.open("r", encoding="utf-8") as stream:
            schema = json.load(stream)
        Draft202012Validator.check_schema(schema)
    except json.JSONDecodeError as exc:
        return None, [
            Diagnostic(
                schema_path.name,
                f"line {exc.lineno}, column {exc.colno}",
                f"invalid JSON schema: {exc.msg}",
            )
        ]
    except SchemaError as exc:
        return None, [
            Diagnostic(schema_path.name, "$", f"invalid schema: {exc.message}")
        ]
    except (OSError, UnicodeError) as exc:
        return None, [
            Diagnostic(schema_path.name, "$", f"cannot read schema: {exc}")
        ]
    return Draft202012Validator(schema), []


def _schema_diagnostics(
    artifact: str, document: Any, validator: Any
) -> List[Diagnostic]:
    diagnostics = []
    for error in validator.iter_errors(document):
        if error.validator == "pattern" and error.validator_value == r"\S":
            message = "value must be a nonblank string"
        else:
            message = error.message
        diagnostics.append(
            Diagnostic(
                artifact,
                _format_json_path(error.absolute_path),
                f"schema: {message}",
            )
        )
    return diagnostics


def _duplicate_id_diagnostics(
    artifact: str,
    records: Sequence[Mapping[str, Any]],
    base_path: str,
    label: str,
) -> List[Diagnostic]:
    diagnostics = []
    first_locations: Dict[str, str] = {}
    for index, record in enumerate(records):
        record_id = record["id"]
        location = f"{base_path}[{index}].id"
        if record_id in first_locations:
            diagnostics.append(
                Diagnostic(
                    artifact,
                    location,
                    (
                        f"duplicate {label} id {record_id!r}; first declared at "
                        f"{first_locations[record_id]}"
                    ),
                )
            )
        else:
            first_locations[record_id] = location
    return diagnostics


def _source_diagnostics(document: Mapping[str, Any]) -> List[Diagnostic]:
    return _duplicate_id_diagnostics(
        "sources.yaml", document["sources"], "$.sources", "source"
    )


def _derived_output_cycle_diagnostics(
    artifact: str,
    run_path: str,
    derived_outputs: Sequence[Mapping[str, Any]],
    duplicate_output_ids: bool,
) -> List[Diagnostic]:
    """Report deterministic back edges in a run's derived-output graph."""

    if duplicate_output_ids:
        return []

    derived_ids = {output["id"] for output in derived_outputs}
    graph: Dict[str, List[str]] = {output_id: [] for output_id in sorted(derived_ids)}
    reference_locations: Dict[Tuple[str, str], str] = {}

    for output_index, output in enumerate(derived_outputs):
        output_id = output["id"]
        for reference_index, reference in enumerate(output["derived_from"]):
            if reference not in derived_ids:
                continue
            graph[output_id].append(reference)
            reference_locations[(output_id, reference)] = (
                f"{run_path}.derived_outputs[{output_index}]"
                f".derived_from[{reference_index}]"
            )

    diagnostics: List[Diagnostic] = []
    state = {output_id: "unvisited" for output_id in graph}
    active_path: List[str] = []
    active_positions: Dict[str, int] = {}

    def visit(output_id: str) -> None:
        state[output_id] = "visiting"
        active_positions[output_id] = len(active_path)
        active_path.append(output_id)

        for dependency in sorted(graph[output_id]):
            if state[dependency] == "unvisited":
                visit(dependency)
            elif state[dependency] == "visiting":
                cycle = active_path[active_positions[dependency] :] + [dependency]
                location = reference_locations[(output_id, dependency)]
                if output_id == dependency:
                    message = f"derived output {output_id!r} cannot reference itself"
                else:
                    message = "cyclic derived_from dependency: " + " -> ".join(
                        repr(member) for member in cycle
                    )
                diagnostics.append(Diagnostic(artifact, location, message))

        active_path.pop()
        active_positions.pop(output_id)
        state[output_id] = "visited"

    for output_id in sorted(graph):
        if state[output_id] == "unvisited":
            visit(output_id)

    return diagnostics


def _provenance_diagnostics(document: Mapping[str, Any]) -> List[Diagnostic]:
    artifact = "experiment_provenance.yaml"
    runs = document["runs"]
    diagnostics = _duplicate_id_diagnostics(artifact, runs, "$.runs", "run")

    for run_index, run in enumerate(runs):
        run_path = f"$.runs[{run_index}]"
        inputs = run.get("inputs", [])
        diagnostics.extend(
            _duplicate_id_diagnostics(
                artifact, inputs, f"{run_path}.inputs", "input"
            )
        )

        raw_outputs = run.get("raw_outputs", [])
        derived_outputs = run.get("derived_outputs", [])
        output_locations: Dict[str, str] = {}
        duplicate_output_ids = False
        for collection_name, outputs in (
            ("raw_outputs", raw_outputs),
            ("derived_outputs", derived_outputs),
        ):
            for output_index, output in enumerate(outputs):
                output_id = output["id"]
                location = f"{run_path}.{collection_name}[{output_index}].id"
                if output_id in output_locations:
                    duplicate_output_ids = True
                    diagnostics.append(
                        Diagnostic(
                            artifact,
                            location,
                            (
                                f"duplicate output id {output_id!r}; first declared "
                                f"at {output_locations[output_id]}"
                            ),
                        )
                    )
                else:
                    output_locations[output_id] = location

        declared_output_ids = set(output_locations)
        for output_index, output in enumerate(derived_outputs):
            for reference_index, reference in enumerate(output["derived_from"]):
                if reference not in declared_output_ids:
                    diagnostics.append(
                        Diagnostic(
                            artifact,
                            (
                                f"{run_path}.derived_outputs[{output_index}]"
                                f".derived_from[{reference_index}]"
                            ),
                            f"unknown output id {reference!r}",
                        )
                    )

        diagnostics.extend(
            _derived_output_cycle_diagnostics(
                artifact,
                run_path,
                derived_outputs,
                duplicate_output_ids,
            )
        )

    return diagnostics


def _source_reference_diagnostics(
    provenance: Mapping[str, Any],
    sources: Optional[Mapping[str, Any]],
    sources_present: bool,
) -> List[Diagnostic]:
    artifact = "experiment_provenance.yaml"
    declared_source_ids = (
        {source["id"] for source in sources["sources"]} if sources is not None else set()
    )
    diagnostics = []
    for run_index, run in enumerate(provenance["runs"]):
        for input_index, input_record in enumerate(run.get("inputs", [])):
            if "source_id" not in input_record:
                continue
            source_id = input_record["source_id"]
            location = f"$.runs[{run_index}].inputs[{input_index}].source_id"
            if not sources_present:
                diagnostics.append(
                    Diagnostic(
                        artifact,
                        location,
                        (
                            f"source id {source_id!r} cannot be resolved because "
                            "sources.yaml is absent"
                        ),
                    )
                )
            elif sources is not None and source_id not in declared_source_ids:
                diagnostics.append(
                    Diagnostic(artifact, location, f"unknown source id {source_id!r}")
                )
    return diagnostics


def _validate_artifact_directory(
    artifact_dir: Path, schema_paths: Mapping[str, Path]
) -> List[Diagnostic]:
    """Return all deterministic diagnostics for the two recognized artifacts."""

    if not artifact_dir.is_dir():
        return [
            Diagnostic(
                str(artifact_dir), "$", "artifact directory does not exist or is not a directory"
            )
        ]

    documents: Dict[str, Any] = {}
    schema_valid: Dict[str, bool] = {}
    diagnostics: List[Diagnostic] = []

    validators: Dict[str, Any] = {}
    for artifact in sorted(schema_paths):
        validator, schema_diagnostics = _load_validator(schema_paths[artifact])
        diagnostics.extend(schema_diagnostics)
        if validator is not None:
            validators[artifact] = validator

    for artifact in sorted(schema_paths):
        artifact_path = artifact_dir / artifact
        if not artifact_path.is_file():
            continue
        document, parse_diagnostics = _load_yaml(artifact_path, artifact)
        diagnostics.extend(parse_diagnostics)
        if parse_diagnostics:
            schema_valid[artifact] = False
            continue

        validator = validators.get(artifact)
        if validator is None:
            schema_valid[artifact] = False
            continue
        artifact_schema_diagnostics = _schema_diagnostics(artifact, document, validator)
        diagnostics.extend(artifact_schema_diagnostics)
        documents[artifact] = document
        schema_valid[artifact] = not artifact_schema_diagnostics

    sources = documents.get("sources.yaml")
    provenance = documents.get("experiment_provenance.yaml")
    valid_sources = sources if schema_valid.get("sources.yaml") else None
    valid_provenance = (
        provenance if schema_valid.get("experiment_provenance.yaml") else None
    )

    if valid_sources is not None:
        diagnostics.extend(_source_diagnostics(valid_sources))
    if valid_provenance is not None:
        diagnostics.extend(_provenance_diagnostics(valid_provenance))
        diagnostics.extend(
            _source_reference_diagnostics(
                valid_provenance,
                valid_sources,
                sources_present=(artifact_dir / "sources.yaml").is_file(),
            )
        )

    return sorted(set(diagnostics))


def validate_artifact_directory(
    artifact_dir: Path, *, require_provenance: bool = False
) -> List[Diagnostic]:
    """Return structural diagnostics using only this package's local schemas."""
    diagnostics = _validate_artifact_directory(artifact_dir, SCHEMA_PATHS)
    if require_provenance and not (artifact_dir / "experiment_provenance.yaml").is_file():
        diagnostics.append(Diagnostic(
            "experiment_provenance.yaml", "$", "required provenance artifact is absent"
        ))
    return sorted(set(diagnostics))


def main(argv: Optional[Sequence[str]] = None) -> int:
    arguments = _parse_arguments(argv)
    try:
        diagnostics = validate_artifact_directory(
            arguments.artifact_dir, require_provenance=arguments.require_provenance
        )
    except ImportError as exc:
        print(Diagnostic(
            "validator", "$", "validation dependencies are unavailable; install "
            "PyYAML>=6.0 and jsonschema>=4.21 from validation-requirements.txt "
            f"in an authorized environment ({exc})"
        ).render(), file=sys.stderr)
        return 2
    except (OSError, ValueError) as exc:
        diagnostics = [Diagnostic("validator", "$", f"internal contract error: {exc}")]

    for diagnostic in diagnostics:
        print(diagnostic.render(), file=sys.stderr)
    return 1 if diagnostics else 0


if __name__ == "__main__":
    raise SystemExit(main())
