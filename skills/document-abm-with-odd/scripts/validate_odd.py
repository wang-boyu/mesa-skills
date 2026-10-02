#!/usr/bin/env python3
"""Check optional ODD Markdown profiles; never assess scientific validity.

See ../references/structure-checker.md. Exit 0: profile/structure pass;
1: structural/profile diagnostics; 2: invocation or input failure.
"""

from __future__ import annotations

import re
import runpy
import sys
from pathlib import Path

ELEMENTS = (
    "Purpose and patterns",
    "Entities, state variables, and scales",
    "Process overview and scheduling",
    "Design concepts",
    "Initialization",
    "Input data",
    "Submodels",
)
LABELS = tuple(f"{number}. {title}" for number, title in enumerate(ELEMENTS, 1))
HEADING = re.compile(r"^(#{1,6})(?:[ \t]+(.*)|$)")
FENCE = re.compile(r"^(`{3,}|~{3,})(.*)$")
LIST = re.compile(r"^(?:[-+*]|\d+[.)])(?:[ \t]+|$)")
INLINE_CODE = re.compile(r"(?<!`)(`+)(?!`).*?(?<!`)\1(?!`)")


def validate_text(text: str, *, extended: bool = False) -> tuple[str, ...]:
    """Return diagnostics for the default or explicitly selected extended profile."""
    if extended:
        # Load only the shipped sibling, even under isolated Python or run_path.
        # run_path compiles source without writing a package bytecode cache.
        checker = runpy.run_path(str(Path(__file__).with_name("_odd_extended.py")))
        return checker["validate_text"](text)
    return _validate_default(text)


def _validate_default(text: str) -> tuple[str, ...]:
    """Preserve the original narrow profile and its diagnostic order."""
    errors: list[str] = []
    headings: list[str] = []
    bodies = [False] * len(ELEMENTS)
    current: int | None = None
    fence = ""
    comment = False
    seen_content = False

    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip()
        if fence:
            closer = re.escape(fence[0]) + "{" + str(len(fence)) + ",}"
            if re.fullmatch(closer, line):
                fence = ""
            continue
        if comment or line.startswith("<!--"):
            comment = "-->" not in line
            if not comment and line.split("-->", 1)[1].strip():
                errors.append(f"line {number}: comments must occupy standalone lines")
            continue
        if not line:
            continue
        opening = FENCE.fullmatch(line)
        if opening:
            fence, info = opening.groups()
            if fence[0] == "`" and "`" in info:
                errors.append(f"line {number}: backtick fence info contains a backtick")
            continue

        # Refuse ambiguous containers/HTML rather than guessing their rendering.
        without_code = INLINE_CODE.sub("", line)
        list_item = LIST.match(line)
        list_body = line[list_item.end() :] if list_item else ""
        if (
            line[0].isspace()
            or line.startswith(">")
            or re.fullmatch(r"[-=]+", line)
            or re.match(r"^\[[^]]+\]:", line)
            or re.search(r"<(?:/?[A-Za-z][A-Za-z0-9-]*(?:[>\s/]|$)|[!?])", without_code)
            or (
                list_item
                and (
                    LIST.match(list_body)
                    or HEADING.match(list_body)
                    or FENCE.match(list_body)
                    or list_body.startswith(">")
                )
            )
        ):
            errors.append(f"line {number}: unsupported Markdown profile syntax")
            continue
        if "`" in without_code:
            errors.append(f"line {number}: inline code must close on the same line")

        heading = HEADING.fullmatch(line)
        if heading:
            marks, label = heading.groups()
            label = re.sub(r"[ \t]+#+$", "", label or "").strip()
            level = len(marks)
            if level == 1:
                if seen_content:
                    errors.append(f"line {number}: only one leading title is allowed")
                current = None
            elif level == 2:
                headings.append(label)
                current = LABELS.index(label) if label in LABELS else None
            elif not headings:
                errors.append(f"line {number}: subsection precedes the ODD elements")
            seen_content = True
            continue

        seen_content = True
        if current is not None and re.search(r"\w", line):
            bodies[current] = True

    if fence or comment:
        errors.append("unclosed fenced block or HTML comment")
    labels = tuple(headings)
    if labels[:7] != LABELS or any(re.match(r"\d", label) for label in labels[7:]):
        errors.append(
            "expected the seven numbered ODD elements in order, then unnumbered appendices"
        )
    for index, present in enumerate(bodies, 1):
        if not present:
            errors.append(f"element {index} has no visible non-heading text")
    return tuple(errors)


def main(argv: list[str] | None = None) -> int:
    """Read one file; report structure without modifying the document."""
    arguments = sys.argv[1:] if argv is None else argv
    extended = bool(arguments and arguments[0] == "--extended")
    if extended:
        arguments = arguments[1:]
    if arguments in (["-h"], ["--help"]):
        if extended:
            print("usage: validate_odd.py --extended PATH_TO_ODD.md")
            print("Optional extended ODD profile; see references/structure-checker.md.")
        else:
            print("usage: validate_odd.py PATH_TO_ODD.md")
            print("Optional ODD structure check; see references/structure-checker.md.")
        print("Exit 0: pass; 1: structure/profile diagnostics; 2: input error.")
        return 0
    if len(arguments) != 1:
        print("usage: validate_odd.py PATH_TO_ODD.md", file=sys.stderr)
        return 2
    path = Path(arguments[0])
    try:
        if not path.is_file():
            raise OSError("input is not a regular file")
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError, ValueError) as error:
        print(f"{path}: cannot read UTF-8 input: {error}", file=sys.stderr)
        return 2
    try:
        diagnostics = validate_text(content, extended=extended)
    except (OSError, UnicodeError) as error:
        print(f"{path}: cannot inspect selected profile: {error}", file=sys.stderr)
        return 2
    for diagnostic in diagnostics:
        print(f"{path}: {diagnostic}", file=sys.stderr)
    if diagnostics:
        return 1
    if extended:
        print("Extended profile OK; source reading, model fidelity, human behavior, "
              "and scientific validity were not checked.")
    else:
        print("Structure OK; meaning, attribution, and scientific validity were not checked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
