#!/usr/bin/env python3
"""Validate one sources.yaml against this installed skill's vendored schema."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SCHEMA_DRAFT = "https://json-schema.org/draft/2020-12/schema"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "assets" / "sources.schema.json"


@dataclass(frozen=True, order=True)
class Diagnostic:
    artifact: str
    location: str
    message: str

    def render(self) -> str:
        return f"{self.artifact}:{self.location}: {self.message}"


class ValidationSetupError(Exception):
    """Report a failure in validation machinery rather than user input."""

    def __init__(self, artifact: str, message: str) -> None:
        super().__init__(message)
        self.artifact = artifact

    def render(self) -> str:
        return Diagnostic(self.artifact, "$", str(self)).render()


def _parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="validate one sources.yaml with the installed skill contract"
    )
    parser.add_argument("inventory", type=Path, metavar="SOURCES_YAML")
    return parser.parse_args(argv)


def _load_dependencies(display_path: str) -> tuple[Any, Any, type[Exception]]:
    try:
        import yaml
        from jsonschema import Draft202012Validator
        from jsonschema.exceptions import SchemaError
    except ImportError as exc:
        raise ValidationSetupError(
            display_path,
            "validation dependencies are unavailable; install PyYAML>=6.0 and "
            "jsonschema>=4.21 from validation-requirements.txt in an authorized "
            f"environment ({exc})"
        ) from exc
    return yaml, Draft202012Validator, SchemaError


def _unique_key_loader(yaml_module: Any) -> type[Any]:
    class UniqueKeyLoader(yaml_module.SafeLoader):
        """Safe YAML loader that rejects ambiguous duplicate mapping keys."""

    def construct_unique_mapping(
        loader: Any, node: Any, deep: bool = False
    ) -> Iterable[dict[Any, Any]]:
        mapping: dict[Any, Any] = {}
        yield mapping
        loader.flatten_mapping(node)
        key_marks: dict[Any, Any] = {}
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
                        f"duplicate mapping key {key!r}; first declared at line "
                        f"{first_mark.line + 1}, column {first_mark.column + 1}"
                    ),
                    key_node.start_mark,
                )
            mapping[key] = loader.construct_object(value_node, deep=deep)
            key_marks[key] = key_node.start_mark

    UniqueKeyLoader.add_constructor(
        yaml_module.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_unique_mapping,
    )
    return UniqueKeyLoader


def _format_instance_path(parts: Iterable[Any]) -> str:
    path = "$"
    for part in parts:
        if isinstance(part, int):
            path += f"[{part}]"
        elif isinstance(part, str) and re.fullmatch(
            r"[A-Za-z_][A-Za-z0-9_]*", part
        ):
            path += f".{part}"
        else:
            path += f"[{json.dumps(part, ensure_ascii=True)}]"
    return path


def _read_inventory(path: Path, display_path: str) -> str:
    try:
        if not path.is_file():
            raise ValidationSetupError(
                display_path, "cannot read input: path is missing or not a file"
            )
        return path.read_text(encoding="utf-8")
    except ValidationSetupError:
        raise
    except (OSError, UnicodeError) as exc:
        raise ValidationSetupError(
            display_path, f"cannot read input as UTF-8: {exc}"
        ) from exc


def _read_schema() -> Mapping[str, Any]:
    display_path = str(SCHEMA_PATH)
    try:
        schema_text = SCHEMA_PATH.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ValidationSetupError(
            display_path, f"cannot read internal schema: {exc}"
        ) from exc

    try:
        schema = json.loads(schema_text)
    except json.JSONDecodeError as exc:
        raise ValidationSetupError(
            display_path,
            f"malformed internal schema JSON at line {exc.lineno}, column "
            f"{exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(schema, dict):
        raise ValidationSetupError(
            display_path, "malformed internal schema: root must be an object"
        )

    declared_draft = schema.get("$schema")
    if declared_draft is None:
        raise ValidationSetupError(
            display_path,
            "malformed internal schema: missing Draft 2020-12 $schema declaration"
        )
    if declared_draft != SCHEMA_DRAFT:
        raise ValidationSetupError(
            display_path,
            "wrong internal schema draft: expected Draft 2020-12 declaration "
            f"{SCHEMA_DRAFT!r}, found {declared_draft!r}"
        )
    return schema


def _load_inventory(text: str, yaml_module: Any, loader: type[Any]) -> Any:
    try:
        return yaml_module.load(text, Loader=loader)
    except yaml_module.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        position = (
            ""
            if mark is None
            else f" at line {mark.line + 1}, column {mark.column + 1}"
        )
        problem = getattr(exc, "problem", None) or str(exc).splitlines()[0]
        raise ValueError(f"invalid YAML{position}: {problem}") from exc


def _schema_diagnostics(
    document: Any, validator: Any, display_path: str
) -> list[Diagnostic]:
    diagnostics = []
    for error in validator.iter_errors(document):
        message = (
            "value must be a nonblank string"
            if error.validator == "pattern" and error.validator_value == r"\S"
            else error.message
        )
        diagnostics.append(
            Diagnostic(
                display_path,
                _format_instance_path(error.absolute_path),
                f"schema: {message}",
            )
        )
    return diagnostics


def _json_domain_diagnostics(document: Any, display_path: str) -> list[Diagnostic]:
    """Reject YAML values that cannot be represented by strict JSON."""

    diagnostics: list[Diagnostic] = []
    active_containers: set[int] = set()

    def add(parts: tuple[Any, ...], message: str) -> None:
        diagnostics.append(
            Diagnostic(display_path, _format_instance_path(parts), message)
        )

    def visit(value: Any, parts: tuple[Any, ...]) -> None:
        value_type = type(value)
        if value is None or value_type in (str, bool, int):
            return
        if value_type is float:
            if not math.isfinite(value):
                add(parts, "non-finite YAML number is outside the JSON domain")
            return

        if value_type is list:
            container_id = id(value)
            if container_id in active_containers:
                add(
                    parts,
                    "recursive YAML alias creates a cycle outside the JSON domain",
                )
                return
            active_containers.add(container_id)
            try:
                for index, item in enumerate(value):
                    visit(item, (*parts, index))
                    if diagnostics:
                        return
            finally:
                active_containers.remove(container_id)
            return

        if value_type is dict:
            container_id = id(value)
            if container_id in active_containers:
                add(
                    parts,
                    "recursive YAML alias creates a cycle outside the JSON domain",
                )
                return
            active_containers.add(container_id)
            try:
                string_keys = []
                invalid_key_types = set()
                for key in value:
                    if type(key) is str:
                        string_keys.append(key)
                    else:
                        invalid_key_types.add(type(key).__name__)
                if invalid_key_types:
                    key_type = min(invalid_key_types)
                    add(
                        parts,
                        "YAML mapping key type "
                        f"{key_type} is outside the JSON domain; "
                        "JSON object keys must be strings",
                    )
                    return
                for key in sorted(string_keys):
                    visit(value[key], (*parts, key))
                    if diagnostics:
                        return
            finally:
                active_containers.remove(container_id)
            return

        add(parts, f"YAML value type {value_type.__name__} is outside the JSON domain")

    visit(document, ())
    return sorted(set(diagnostics), key=Diagnostic.render)


def _duplicate_source_id_diagnostics(
    document: Any, display_path: str
) -> list[Diagnostic]:
    if not isinstance(document, Mapping):
        return []
    sources = document.get("sources")
    if not isinstance(sources, list):
        return []

    diagnostics = []
    first_locations: dict[str, str] = {}
    for index, source in enumerate(sources):
        if not isinstance(source, Mapping):
            continue
        source_id = source.get("id")
        if not isinstance(source_id, str):
            continue
        location = f"$.sources[{index}].id"
        if source_id in first_locations:
            diagnostics.append(
                Diagnostic(
                    display_path,
                    location,
                    (
                        f"duplicate source id {source_id!r}; first declared at "
                        f"{first_locations[source_id]}"
                    ),
                )
            )
        else:
            first_locations[source_id] = location
    return diagnostics


def validate_inventory(path: Path) -> list[Diagnostic]:
    """Return deterministic diagnostics for invalid inventory content."""

    display_path = str(path)
    yaml_module, validator_type, schema_error_type = _load_dependencies(display_path)
    inventory_text = _read_inventory(path, display_path)
    schema = _read_schema()
    try:
        validator_type.check_schema(schema)
    except schema_error_type as exc:
        raise ValidationSetupError(
            str(SCHEMA_PATH), f"invalid internal schema: {exc.message}"
        ) from exc

    loader = _unique_key_loader(yaml_module)
    try:
        document = _load_inventory(inventory_text, yaml_module, loader)
    except ValueError as exc:
        return [Diagnostic(display_path, "$", str(exc))]

    json_domain_diagnostics = _json_domain_diagnostics(document, display_path)
    if json_domain_diagnostics:
        return json_domain_diagnostics

    validator = validator_type(schema)
    diagnostics = _schema_diagnostics(document, validator, display_path)
    diagnostics.extend(_duplicate_source_id_diagnostics(document, display_path))
    return sorted(set(diagnostics), key=Diagnostic.render)


def main(argv: Sequence[str] | None = None) -> int:
    display_path = "source validator"
    try:
        arguments = _parse_arguments(argv)
        display_path = str(arguments.inventory)
        diagnostics = validate_inventory(arguments.inventory)
    except ValidationSetupError as exc:
        print(exc.render(), file=sys.stderr)
        return 2
    except Exception as exc:
        print(
            Diagnostic(
                display_path, "$", f"unexpected validation failure: {exc}"
            ).render(),
            file=sys.stderr,
        )
        return 2

    for diagnostic in diagnostics:
        print(diagnostic.render(), file=sys.stderr)
    return 1 if diagnostics else 0


if __name__ == "__main__":
    raise SystemExit(main())
