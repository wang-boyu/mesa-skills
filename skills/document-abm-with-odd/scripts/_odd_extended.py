"""Opt-in ODD Markdown and declaration profile.

One source-preserving scanner supplies heading, declaration, and body checks.
This is a closed syntax/relation grammar, not a Markdown or English parser.
The public entry point is validate_odd.py; no model/document code is executed.
"""

from __future__ import annotations

import re
from typing import NamedTuple, Sequence


ELEMENTS = (
    "Purpose and patterns",
    "Entities, state variables, and scales",
    "Process overview and scheduling",
    "Design concepts",
    "Initialization",
    "Input data",
    "Submodels",
)
_CANONICAL_HEADINGS = tuple(
    f"## {number}. {title}" for number, title in enumerate(ELEMENTS, start=1)
)
_INLINE_CODE = re.compile(r"(?<!`)(`+)(?!`).*?(?<!`)\1(?!`)")
_NUMBERED_LABEL = re.compile(r"^(\d+)\.\s+(.+?)\s*$")
_ATX_HEADING = re.compile(
    r"^(?P<indent> {0,3})(?P<marks>#{1,6})"
    r"(?:[ \t]+(?P<label>.*?))?[ \t]*$"
)
_SETEXT_UNDERLINE = re.compile(r"^ {0,3}(?P<marker>=+|-+)[ \t]*$")
_FENCE_OPENER = re.compile(
    r"^(?P<indent> {0,3})(?P<run>`{3,}|~{3,})(?P<info>.*)$"
)
_ORDERED_MARKER = re.compile(r"\d{1,9}[.)]")
_SUBSTITUTE_LABELS = frozenset(("overview", "design concepts", "details"))
_ODD_D = re.compile(r"\bodd\+d\b")
_GRIMM_2006 = r"\bgrimm\s+et\s+al\.\s*,?\s*(?:2006(?!\d)|\(\s*2006\s*\))"
_GRIMM_2020 = r"\bgrimm\s+et\s+al\.\s*,?\s*(?:2020(?!\d)|\(\s*2020\s*\))"
_MULLER_2013 = r"\bmüller\s+et\s+al\.\s*,?\s*(?:2013(?!\d)|\(\s*2013\s*\))"

# This is deliberately a small, closed structural classifier rather than a
# natural-language parser. Each visible ODD+D occurrence is classified from
# its containing declaration statement using only these accepted forms.
_ODD_D_AFFIRMATIVE = (
    re.compile(
        r"\bodd\+d\b.{0,50}\b(?:is|was|remains)\s+(?:explicitly\s+)?"
        r"(?:active|applied|used|activated)\b"
    ),
    re.compile(r"\bodd\+d\b.{0,40}\bapplies\s+to\b"),
    re.compile(
        r"\b(?:this (?:document|description|model)|the (?:document|description|model)|we)"
        r"\b\s+(?:explicitly\s+)?(?:apply|applies|use|uses|activate|activates|"
        r"adopt|adopts)"
        r"\s+(?:the\s+)?odd\+d\b"
    ),
)
_ODD_D_NEGATIVE = (
    re.compile(
        r"\bodd\+d\b.{0,80}\b(?:is|was|remains)\s+(?:explicitly\s+)?"
        r"(?:not\s+(?:active|applied|used|activated)|inactive)\b"
    ),
    re.compile(
        r"\b(?:do|does|did|will)\s+not\s+"
        r"(?:apply|use|activate|adopt)\s+(?:the\s+)?odd\+d\b"
    ),
    re.compile(
        r"\bnever\s+(?:apply|applies|use|uses|activate|activates|adopt|adopts)"
        r"\b.{0,50}\bodd\+d\b"
    ),
    re.compile(
        r"\bodd\+d\b.{0,120}\b(?:do|does|did|will)\s+not\s+"
        r"(?:apply|use|activate|adopt)\s+(?:it|this extension|that extension)\b"
    ),
    re.compile(
        r"\bodd\+d\b.{0,100}\bnot\s+(?:active|applied|used|activated)\b"
    ),
)
_ODD_D_MODAL = (
    re.compile(
        r"\bodd\+d\b.{0,60}\b(?:may|might|could|would|should|possibly|perhaps)"
        r"\b.{0,40}\b(?:be\s+)?(?:active|applied|used|activated)\b"
    ),
    re.compile(
        r"\b(?:may|might|could|would|should|possibly|perhaps)\b.{0,50}"
        r"\b(?:apply|use|activate|adopt)\b.{0,40}\bodd\+d\b"
    ),
)
_ODD_D_CONTEXTUAL = (
    re.compile(
        r"\bodd\+d\b.{0,120}\b(?:for context|context only|only for context|"
        r"described|discussed|mentioned|cited|referenced|considered)\b"
    ),
    re.compile(
        r"\b(?:describe|describes|described|discuss|discusses|discussed|mention|"
        r"mentions|mentioned|cite|cites|cited|reference|references|referenced)"
        r"\b.{0,100}\bodd\+d\b"
    ),
)
_MODELED_HUMAN_DECISION = (
    r"(?:\b(?:material|substantial)\s+)?\bmodel(?:ed|led)\s+human\s+"
    r"decision(?:s|-making|\s+making|\s+component)?\b"
)

# Base protocol use is classified independently from conditional extensions.
# These patterns enumerate accepted document-to-protocol relations and their
# local negative, modal, and contextual counterparts; they are not a prose
# parser.
_BASE_PROTOCOL_SUBJECT = (
    r"(?:(?:this|the)\s+(?:(?:model\s+)?description|document|model)|"
    r"it|we|the\s+authors)"
)
_ODD_NAME = r"(?:the\s+)?odd"
_PROTOCOL_ROLE = r"(?:documentation|model[- ]description)\s+protocol"
_ODD_PROTOCOL_OBJECT = rf"{_ODD_NAME}\s+protocol"
_ODD_AS_PROTOCOL_ROLE = (
    rf"{_ODD_NAME}\s+as\s+(?:(?:its|the|our)\s+)?{_PROTOCOL_ROLE}"
)
_BASE_PROTOCOL_AFFIRMATIVE = (
    re.compile(
        rf"\b{_BASE_PROTOCOL_SUBJECT}\s+"
        rf"(?:(?:explicitly|affirmatively|currently)\s+)?(?:uses?|adopts?)\s+"
        rf"(?:{_ODD_AS_PROTOCOL_ROLE}|{_ODD_PROTOCOL_OBJECT})\b"
    ),
    re.compile(
        rf"\b{_BASE_PROTOCOL_SUBJECT}\s+"
        rf"(?:(?:explicitly|affirmatively|currently)\s+)?"
        rf"(?:follow|follows|apply|applies)\s+{_ODD_PROTOCOL_OBJECT}\b"
    ),
    re.compile(
        rf"\b{_BASE_PROTOCOL_SUBJECT}\s+(?:is|was)\s+"
        rf"documented\s+according\s+to\s+{_ODD_NAME}"
        rf"(?:\s+protocol|\s+as\s+(?:(?:its|the)\s+)?{_PROTOCOL_ROLE})?\b"
    ),
    re.compile(
        rf"\b{_BASE_PROTOCOL_SUBJECT}\s+(?:is|was)\s+"
        rf"(?:described\s+using|structured\s+under|organized\s+according\s+to)\s+"
        rf"(?:{_ODD_AS_PROTOCOL_ROLE}|{_ODD_PROTOCOL_OBJECT})\b"
    ),
    re.compile(
        rf"\b{_ODD_NAME}\s+(?:is|was)\s+(?:explicitly\s+)?(?:"
        rf"(?:the\s+)?(?:applied\s+)?{_PROTOCOL_ROLE}"
        rf"(?:\s+(?:used|applied|adopted|followed)\s+here)?|"
        rf"(?:used|applied|adopted|followed)\s+as\s+(?:the\s+)?"
        rf"{_PROTOCOL_ROLE})\b"
    ),
    re.compile(
        rf"\bodd\b.{{0,80}}\bit\s+(?:is|was)\s+(?:explicitly\s+)?"
        rf"(?:used|applied|adopted|followed)\s+as\s+(?:the\s+)?"
        rf"{_PROTOCOL_ROLE}\b"
    ),
)
_BASE_PROTOCOL_NEGATIVE = (
    re.compile(
        rf"\b{_BASE_PROTOCOL_SUBJECT}\s+(?:cannot|never|"
        rf"(?:do|does|did|will|can|must)\s+not)\s+"
        rf"(?:use|adopt|follow|apply)\s+"
        rf"(?:{_ODD_AS_PROTOCOL_ROLE}|{_ODD_PROTOCOL_OBJECT})\b"
    ),
    re.compile(
        rf"\b{_BASE_PROTOCOL_SUBJECT}\s+(?:is|was)\s+not\s+"
        rf"(?:documented\s+according\s+to|described\s+using|"
        rf"structured\s+under|organized\s+according\s+to)\s+"
        rf"(?:{_ODD_AS_PROTOCOL_ROLE}|{_ODD_PROTOCOL_OBJECT}|{_ODD_NAME})\b"
    ),
    re.compile(
        rf"\b{_ODD_NAME}\s+(?:is|was)\s+not\s+(?:explicitly\s+)?(?:"
        rf"(?:the\s+)?(?:applied\s+)?{_PROTOCOL_ROLE}|"
        rf"(?:used|applied|adopted|followed)"
        rf"(?:\s+as\s+(?:the\s+)?{_PROTOCOL_ROLE})?)\b"
    ),
    re.compile(
        rf"\bodd\b.{{0,100}}\bit\s+(?:is|was)\s+not\s+"
        rf"(?:used|applied|adopted|followed)\s+as\s+(?:the\s+)?"
        rf"{_PROTOCOL_ROLE}\b"
    ),
    re.compile(
        r"\b(?:the\s+authors|we)\s+considered\s+(?:the\s+)?odd\b"
        r".{0,60}\b(?:do|does|did|will)\s+not\s+adopt\s+it\b"
    ),
    re.compile(
        rf"\bbut\s+(?:{_BASE_PROTOCOL_SUBJECT}\s+)?(?:cannot|never|"
        rf"(?:do|does|did|will|can|must)\s+not)\s+"
        rf"(?:use|adopt|follow|apply)\s+"
        rf"(?:{_ODD_AS_PROTOCOL_ROLE}|{_ODD_PROTOCOL_OBJECT})\b"
    ),
    re.compile(
        rf"\b{_ODD_NAME}\s+(?:is|was)\s+"
        r"(?:described|discussed|mentioned|cited|referenced|considered)\b"
        r".{0,60}\bbut\s+(?:it\s+(?:is|was)\s+)?not\s+"
        rf"(?:used|applied|adopted|followed)(?:\s+as\s+(?:the\s+)?"
        rf"{_PROTOCOL_ROLE})?\b"
    ),
)
_BASE_PROTOCOL_MODAL = (
    re.compile(
        rf"\b{_BASE_PROTOCOL_SUBJECT}\s+"
        rf"(?:may|might|could|would|should)\s+"
        rf"(?:use|adopt|follow|apply)\s+"
        rf"(?:{_ODD_AS_PROTOCOL_ROLE}|{_ODD_PROTOCOL_OBJECT})\b"
    ),
)
_BASE_PROTOCOL_CONTEXTUAL = (
    re.compile(
        rf"\b(?:the\s+)?bibliography\b.{{0,80}}\b"
        rf"(?:describes?|discusses?|mentions?|cites?|references?)\s+"
        rf"{_ODD_PROTOCOL_OBJECT}\b"
    ),
    re.compile(
        rf"\b{_ODD_NAME}\b.{{0,80}}\b"
        r"(?:is|was)\s+(?:described|discussed|mentioned|cited|referenced|considered)"
        r"\b"
    ),
)
_EXPLICIT_EXTENSION_SUBJECT = (
    r"(?:odd\+d|(?:this|that|the)\s+(?:odd\+d\s+)?extension)"
)
_ANY_EXTENSION_SUBJECT = rf"(?:{_EXPLICIT_EXTENSION_SUBJECT}|it)"


class Heading(NamedTuple):
    """One visible Markdown heading classified from a closed syntax subset."""

    level: int
    start: int
    end: int
    label: str
    display: str
    syntax: str
    container: str | None
    indent: int


class SourceLine(NamedTuple):
    """One physical source line with offsets into the original text."""

    start: int
    content_end: int
    end: int
    text: str


class ContainerPart(NamedTuple):
    """One recursively parsed block-container component."""

    kind: str
    marker: str
    continuation: int


class LineContext(NamedTuple):
    """Reusable container context for one physical source line."""

    line: SourceLine
    path: tuple[ContainerPart, ...]
    continued: tuple[bool, ...]
    content_start: int
    content: str
    origin_start: int


class ActiveContext(NamedTuple):
    """Container path inherited by the next physical line."""

    path: tuple[ContainerPart, ...]
    origin_start: int
    prefix_only: bool


class FenceState(NamedTuple):
    """An active root or container-relative fenced block."""

    marker: str
    minimum: int
    path: tuple[ContainerPart, ...]


class StructuralContent(NamedTuple):
    """A line tail normalized for closed structural classification."""

    text: str
    indent: int
    source_body_start: int


def _source_lines(text: str) -> tuple[SourceLine, ...]:
    """Return physical lines without changing source offsets or newline bytes."""

    lines: list[SourceLine] = []
    offset = 0
    for source_line in text.splitlines(keepends=True):
        content = source_line.rstrip("\r\n")
        content_end = offset + len(content)
        lines.append(SourceLine(offset, content_end, offset + len(source_line), content))
        offset += len(source_line)
    return tuple(lines)


def _mask_range(characters: list[str], start: int, end: int) -> None:
    """Mask a source span while retaining every physical line break."""

    for index in range(start, end):
        if characters[index] not in "\r\n":
            characters[index] = " "


def _visual_column(line: str, end: int) -> int:
    """Return the visual column at *end* using four-column tab stops."""

    column = 0
    for character in line[:end]:
        if character == "\t":
            column += 4 - (column % 4)
        else:
            column += 1
    return column


def _structural_content(
    line: str,
    content_start: int,
) -> StructuralContent | None:
    """Normalize zero-to-three-column indentation at a physical line offset."""

    body_start = content_start
    while body_start < len(line) and line[body_start] in " \t":
        body_start += 1
    indent = (
        _visual_column(line, body_start)
        - _visual_column(line, content_start)
    )
    if indent >= 4:
        return None
    return StructuralContent(
        " " * indent + line[body_start:],
        indent,
        body_start,
    )


def _valid_fence_opener(line: str) -> tuple[str, int] | None:
    """Return marker and length for one valid root fenced-block opener."""

    match = _FENCE_OPENER.fullmatch(line)
    if match is None:
        return None
    run = match.group("run")
    if run.startswith("`") and "`" in match.group("info"):
        return None
    return run[0], len(run)


def _valid_fence_closer(line: str, marker: str, minimum: int) -> bool:
    """Return whether *line* closes the active fenced block."""

    match = re.fullmatch(rf" {{0,3}}(?P<run>{re.escape(marker)}+)[ \t]*", line)
    return match is not None and len(match.group("run")) >= minimum


def _parse_explicit_container(
    line: str,
    cursor: int,
) -> tuple[ContainerPart, int] | None:
    """Parse one explicit container marker at *cursor*."""

    marker_start = cursor
    while marker_start < len(line) and line[marker_start] == " ":
        if marker_start - cursor == 3:
            return None
        marker_start += 1
    if marker_start >= len(line):
        return None

    if line[marker_start] == ">":
        end = marker_start + 1
        if end < len(line) and line[end] in " \t":
            end += 1
        return ContainerPart("blockquote", ">", 0), end

    marker = ""
    kind = ""
    if line[marker_start] in "-+*":
        marker = line[marker_start]
        kind = "bullet"
    else:
        ordered = _ORDERED_MARKER.match(line, marker_start)
        if ordered is not None:
            marker = ordered.group(0)
            kind = "ordered"
    if not marker:
        return None

    marker_end = marker_start + len(marker)
    if marker_end < len(line) and line[marker_end] not in " \t":
        return None
    padding_end = marker_end
    while padding_end < len(line) and line[padding_end] in " \t":
        padding_end += 1
    continuation_end = _visual_column(line, padding_end)
    if padding_end == marker_end:
        continuation_end += 1
    continuation = continuation_end - _visual_column(line, cursor)
    return ContainerPart(kind, marker, continuation), padding_end


def _parse_remaining_containers(
    line: str,
    cursor: int,
    path: list[ContainerPart],
    continued: list[bool],
) -> int:
    """Append every explicit recursive container remaining on *line*."""

    while True:
        parsed = _parse_explicit_container(line, cursor)
        if parsed is None:
            return cursor
        part, cursor = parsed
        path.append(part)
        continued.append(False)


def _consume_continuation(line: str, cursor: int, columns: int) -> int | None:
    """Consume list continuation, allowing legal heading indent from a tab."""

    position = cursor
    current_column = _visual_column(line, cursor)
    target_column = current_column + columns
    while (
        position < len(line)
        and line[position] in " \t"
        and current_column < target_column
    ):
        if line[position] == " ":
            current_column += 1
        else:
            current_column += 4 - (current_column % 4)
        position += 1

    overshoot = current_column - target_column
    if not 0 <= overshoot <= 3:
        return None
    if overshoot:
        indentation_end = position
        while indentation_end < len(line) and line[indentation_end] in " \t":
            indentation_end += 1
        residual_indent = (
            _visual_column(line, indentation_end)
            - _visual_column(line, position)
        )
        if overshoot + residual_indent >= 4:
            return None
    return position


def _fresh_line_context(line: SourceLine) -> LineContext:
    """Parse recursive explicit containers without inherited list state."""

    path: list[ContainerPart] = []
    continued: list[bool] = []
    cursor = _parse_remaining_containers(line.text, 0, path, continued)
    return LineContext(
        line,
        tuple(path),
        tuple(continued),
        cursor,
        line.text[cursor:],
        line.start,
    )


def _continued_line_context(
    line: SourceLine,
    active: ActiveContext,
) -> LineContext | None:
    """Parse a line against the preceding recursive container path."""

    cursor = 0
    path: list[ContainerPart] = []
    continued: list[bool] = []
    inherited_list = False
    for expected in active.path:
        parsed = _parse_explicit_container(line.text, cursor)
        if expected.kind == "blockquote":
            if parsed is None or parsed[0].kind != "blockquote":
                if not path:
                    return None
                break
            part, cursor = parsed
            path.append(part)
            continued.append(False)
            continue

        if parsed is not None and parsed[0].kind in {"bullet", "ordered"}:
            part, cursor = parsed
            path.append(part)
            continued.append(False)
            continue

        continuation_end = _consume_continuation(
            line.text,
            cursor,
            expected.continuation,
        )
        if continuation_end is None:
            if not path:
                return None
            break
        cursor = continuation_end
        path.append(expected)
        continued.append(True)
        inherited_list = True

    cursor = _parse_remaining_containers(line.text, cursor, path, continued)
    origin_start = (
        active.origin_start
        if active.prefix_only and inherited_list
        else line.start
    )
    return LineContext(
        line,
        tuple(path),
        tuple(continued),
        cursor,
        line.text[cursor:],
        origin_start,
    )


def _line_context(line: SourceLine, active: ActiveContext) -> LineContext:
    """Build the reusable recursive container context for one line."""

    if active.path:
        continued = _continued_line_context(line, active)
        if continued is not None:
            return continued
    return _fresh_line_context(line)


def _active_context(
    context: LineContext,
    content: str | None = None,
) -> ActiveContext:
    """Return the container state inherited by the following line."""

    semantic_content = context.content if content is None else content
    prefix_only = bool(context.path) and not semantic_content.strip()
    origin = context.origin_start if prefix_only else context.line.start
    return ActiveContext(context.path, origin, prefix_only)


def _path_signature(
    path: Sequence[ContainerPart],
) -> tuple[tuple[str, str, int], ...]:
    """Return the deterministic identity of a recursive container path."""

    return tuple((part.kind, part.marker, part.continuation) for part in path)


def _matches_contained_fence(context: LineContext, fence: FenceState) -> bool:
    """Return whether a nonblank line remains in a contained fence."""

    if _path_signature(context.path) != _path_signature(fence.path):
        return False
    return all(
        part.kind == "blockquote" or context.continued[index]
        for index, part in enumerate(fence.path)
    )


def _scan_markdown(
    text: str,
) -> tuple[str, tuple[LineContext, ...], tuple[str, ...], tuple[tuple[int, int], ...]]:
    """Mask fences/comments, retaining contexts and literal inline-code spans."""

    lines = _source_lines(text)
    characters = list(text)
    contexts: list[LineContext] = []
    inline_code_spans: list[tuple[int, int]] = []
    active = ActiveContext((), 0, False)
    fence: FenceState | None = None
    in_comment = False
    diagnostics: list[str] = []

    for number, line in enumerate(lines, 1):
        context = _line_context(line, active)
        raw = line.text
        structural = _structural_content(raw, context.content_start)

        if fence is not None:
            if not fence.path:
                _mask_range(characters, line.start, line.content_end)
                root_structural = _structural_content(raw, 0)
                if root_structural is not None and _valid_fence_closer(
                    root_structural.text,
                    fence.marker,
                    fence.minimum,
                ):
                    fence = None
                contexts.append(context)
                active = ActiveContext((), line.start, False)
                continue

            if not raw.strip():
                _mask_range(characters, line.start, line.content_end)
                contexts.append(context)
                continue

            if _matches_contained_fence(context, fence):
                _mask_range(characters, line.start, line.content_end)
                if structural is not None and _valid_fence_closer(
                    structural.text,
                    fence.marker,
                    fence.minimum,
                ):
                    fence = None
                contexts.append(context)
                active = _active_context(context)
                continue

            # A nonblank dedent or sibling ends the contained fence. The same
            # physical line is then processed once in its already-built context.
            fence = None

        if not in_comment and structural is not None:
            possible_fence = _FENCE_OPENER.fullmatch(structural.text)
            if (
                possible_fence is not None
                and possible_fence.group("run").startswith("`")
                and "`" in possible_fence.group("info")
            ):
                diagnostics.append(f"line {number}: backtick fence info contains a backtick")
            opener = _valid_fence_opener(structural.text)
            if opener is not None:
                fence = FenceState(opener[0], opener[1], context.path)
                _mask_range(characters, line.start, line.content_end)
                contexts.append(context)
                active = _active_context(context)
                continue

        if in_comment:
            comment_text = raw
            comment_offset = 0
        else:
            comment_text = context.content
            comment_offset = context.content_start
            if structural is None:
                inline_code_spans.extend(
                    (
                        line.start + comment_offset + code.start(),
                        line.start + comment_offset + code.end(),
                    )
                    for code in _INLINE_CODE.finditer(comment_text)
                )
                contexts.append(context)
                active = _active_context(context)
                continue

        position = 0
        while position < len(comment_text):
            if in_comment:
                closing = comment_text.find("-->", position)
                if closing < 0:
                    _mask_range(
                        characters,
                        line.start + comment_offset + position,
                        line.content_end,
                    )
                    break
                _mask_range(
                    characters,
                    line.start + comment_offset + position,
                    line.start + comment_offset + closing + 3,
                )
                in_comment = False
                position = closing + 3
                continue

            opening = comment_text.find("<!--", position)
            code = _INLINE_CODE.search(comment_text, position)
            if code is not None and (opening < 0 or code.start() < opening):
                # Retain literal text for section bodies, but exclude it from
                # declaration evidence. Earlier comments take precedence.
                inline_code_spans.append(
                    (
                        line.start + comment_offset + code.start(),
                        line.start + comment_offset + code.end(),
                    )
                )
                position = code.end()
                continue
            if opening < 0:
                break
            closing = comment_text.find("-->", opening + 4)
            if closing < 0:
                _mask_range(
                    characters,
                    line.start + comment_offset + opening,
                    line.content_end,
                )
                in_comment = True
                break
            _mask_range(
                characters,
                line.start + comment_offset + opening,
                line.start + comment_offset + closing + 3,
            )
            position = closing + 3

        contexts.append(context)
        if raw.strip():
            visible_content = "".join(
                characters[
                    line.start + context.content_start : line.content_end
                ]
            )
            active = _active_context(context, visible_content)
        elif not any(part.kind in {"bullet", "ordered"} for part in active.path):
            active = ActiveContext((), 0, False)

    if fence is not None or in_comment:
        diagnostics.append("unclosed fenced block or HTML comment")
    visible = "".join(characters)
    # Keep the default's explicit unsupported-input diagnostics for forms that
    # are still outside this profile. Inspect masked lines, so examples remain
    # inert; inspect raw tag starts through physical line ends, too.
    for number, context in enumerate(contexts, 1):
        line = visible[context.line.start : context.line.content_end]
        without_code = _INLINE_CODE.sub("", line)
        if (
            re.match(r"^\s*\[[^]]+\]:", line[context.content_start :])
            or re.search(r"<(?:/?[A-Za-z][A-Za-z0-9-]*(?:[>\s/]|$)|[!?])", without_code)
        ):
            diagnostics.append(f"line {number}: unsupported Markdown profile syntax")
        elif "`" in without_code:
            diagnostics.append(f"line {number}: inline code must close on the same line")
    return visible, tuple(contexts), tuple(diagnostics), tuple(inline_code_spans)


def _atx_label(raw_label: str | None) -> str:
    """Return the visible label of an ATX heading without a closing sequence."""

    label = (raw_label or "").strip()
    return re.sub(r"[ \t]+#+[ \t]*$", "", label).strip()


def _classify_headings(
    visible: str,
    contexts: Sequence[LineContext],
) -> tuple[Heading, ...]:
    """Classify headings from the scanner's recursive line contexts."""

    headings: list[Heading] = []
    atx_line_starts: set[int] = set()
    for context in contexts:
        line = context.line
        visible_line = visible[line.start : line.content_end]
        if not visible_line.strip():
            continue

        structural = _structural_content(line.text, context.content_start)
        if structural is None:
            continue
        match = _ATX_HEADING.fullmatch(structural.text)
        if match is None:
            continue
        marker_start = structural.source_body_start
        marker_end = marker_start + len(match.group("marks"))
        if visible_line[marker_start:marker_end] != match.group("marks"):
            continue
        label_start, label_end = (
            match.span("label")
            if match.group("label") is not None
            else (len(structural.text), len(structural.text))
        )
        source_label_start = (
            structural.source_body_start
            + label_start
            - structural.indent
        )
        source_label_end = (
            structural.source_body_start
            + label_end
            - structural.indent
        )
        visible_label = visible_line[
            source_label_start:source_label_end
        ]
        headings.append(
            Heading(
                level=len(match.group("marks")),
                start=context.origin_start,
                end=line.content_end,
                label=_atx_label(visible_label),
                display=line.text.strip(),
                syntax="ATX",
                container=(
                    "/".join(part.kind for part in context.path)
                    if context.path
                    else None
                ),
                indent=structural.indent,
            )
        )
        atx_line_starts.add(line.start)

    for index in range(len(contexts) - 1):
        context = contexts[index]
        underline_context = contexts[index + 1]
        line = context.line
        underline_line = underline_context.line
        if line.start in atx_line_starts:
            continue
        visible_line = visible[line.start : line.content_end]
        visible_underline = visible[
            underline_line.start : underline_line.content_end
        ]
        if not visible_line.strip() or not visible_underline.strip():
            continue

        structural = _structural_content(line.text, context.content_start)
        underline_structural = _structural_content(
            underline_line.text,
            underline_context.content_start,
        )
        if structural is None or underline_structural is None:
            continue

        if _path_signature(context.path) != _path_signature(
            underline_context.path
        ):
            continue
        underline_match = _SETEXT_UNDERLINE.fullmatch(underline_structural.text)
        if underline_match is None:
            continue
        marker_start = underline_structural.source_body_start
        marker_end = marker_start + len(underline_match.group("marker"))
        if (
            visible_underline[marker_start:marker_end]
            != underline_match.group("marker")
        ):
            continue
        if context.path:
            if _ATX_HEADING.fullmatch(structural.text) is not None:
                continue
            if any(
                part.kind != "blockquote"
                and not underline_context.continued[path_index]
                for path_index, part in enumerate(context.path)
            ):
                continue
            visible_label = visible_line[context.content_start :].strip()
            if not visible_label:
                continue
            level = 1 if underline_match.group("marker").startswith("=") else 2
            heading_container = "/".join(part.kind for part in context.path)
            indent = structural.indent
        else:
            if (
                _ATX_HEADING.fullmatch(structural.text) is not None
                or _SETEXT_UNDERLINE.fullmatch(structural.text) is not None
            ):
                continue
            visible_label = visible_line.strip()
            if not visible_label:
                continue
            level = 1 if underline_match.group("marker").startswith("=") else 2
            heading_container = None
            indent = structural.indent

        headings.append(
            Heading(
                level=level,
                start=context.origin_start,
                end=underline_line.content_end,
                label=visible_label,
                display=f"{line.text.strip()} (Setext)",
                syntax="Setext",
                container=heading_container,
                indent=indent,
            )
        )

    return tuple(sorted(headings, key=lambda heading: (heading.start, heading.end)))


def _blank_heading_spans(text: str, headings: Sequence[Heading]) -> str:
    """Blank complete heading spans without joining surrounding prose."""

    characters = list(text)
    for heading in headings:
        for index in range(heading.start, min(heading.end, len(characters))):
            if characters[index] not in "\r\n":
                characters[index] = " "
    return "".join(characters)


def _declaration_statements(declaration: str) -> tuple[str, ...]:
    """Return normalized declaration sentences while preserving abbreviations."""

    normalized = " ".join(declaration.casefold().split())
    return tuple(
        statement.strip()
        for statement in re.split(r"(?<!et al\.)(?<=[.!?])\s+", normalized)
        if statement.strip()
    )


def _classify_base_protocol_relation(statement: str) -> str:
    """Classify a statement with a small closed protocol-relation grammar."""

    affirmative = any(
        pattern.search(statement) for pattern in _BASE_PROTOCOL_AFFIRMATIVE
    )
    negative = any(pattern.search(statement) for pattern in _BASE_PROTOCOL_NEGATIVE)
    if affirmative and negative:
        return "contradictory"
    if negative:
        return "negative"
    if affirmative:
        return "affirmative"
    if any(pattern.search(statement) for pattern in _BASE_PROTOCOL_MODAL):
        return "modal"
    if any(pattern.search(statement) for pattern in _BASE_PROTOCOL_CONTEXTUAL):
        return "contextual"
    return "unrelated"


def _classify_odd_d_statement(statement: str) -> tuple[str, bool]:
    """Classify one ODD+D-bearing statement and flag mixed polarity."""

    affirmative = any(pattern.search(statement) for pattern in _ODD_D_AFFIRMATIVE)
    negative = any(pattern.search(statement) for pattern in _ODD_D_NEGATIVE)
    modal = any(pattern.search(statement) for pattern in _ODD_D_MODAL)
    contextual = any(pattern.search(statement) for pattern in _ODD_D_CONTEXTUAL)

    if affirmative and negative:
        return "indeterminate", True
    if modal:
        return "indeterminate", False
    if affirmative:
        return "affirmative", False
    if negative:
        return "explicit-negative", False
    if contextual:
        return "contextual", False
    return "indeterminate", False


def _odd_d_declaration_signals(
    statements: tuple[str, ...],
) -> tuple[tuple[str, ...], bool, tuple[str, ...]]:
    """Classify every ODD+D occurrence in the visible declaration region."""

    classifications: list[str] = []
    affirmative_statements: list[str] = []
    mixed_polarity = False
    for statement in statements:
        occurrences = tuple(_ODD_D.finditer(statement))
        if not occurrences:
            continue
        classification, mixed = _classify_odd_d_statement(statement)
        classifications.extend(classification for _ in occurrences)
        mixed_polarity = mixed_polarity or mixed
        if classification == "affirmative":
            affirmative_statements.append(statement)
    return tuple(classifications), mixed_polarity, tuple(affirmative_statements)


def _is_affirmative_supplementation(statement: str) -> bool:
    """Match a closed positive relation from the extension to base ODD 2020."""

    patterns = (
        rf"\b{_ANY_EXTENSION_SUBJECT}\s+supplements?\s+(?:the\s+)?"
        r"odd\s+2020\b(?!\s+only\s+as\s+(?:protocol\s+)?context\b)",
        rf"\b{_EXPLICIT_EXTENSION_SUBJECT}\s+(?:is|was)\s+active\s+and\s+"
        r"supplements?\s+(?:the\s+)?odd\s+2020\b"
        r"(?!\s+only\s+as\s+(?:protocol\s+)?context\b)",
    )
    return any(re.search(pattern, statement) for pattern in patterns)


def _is_affirmative_human_scope(
    statement: str,
    *,
    allow_referential_subject: bool,
) -> bool:
    """Match a closed positive extension-to-human-scope relation."""

    subject = (
        _ANY_EXTENSION_SUBJECT
        if allow_referential_subject
        else _EXPLICIT_EXTENSION_SUBJECT
    )
    relations = (
        rf"\b{subject}\s+(?:directly\s+)?"
        rf"(?:covers?|documents?|addresses?|represents?)\s+(?:the\s+)?"
        rf"{_MODELED_HUMAN_DECISION}",
        rf"\b{subject}\s+(?:is|was)\s+active"
        rf"(?:\s+as\s+(?:a\s+)?conditional\s+extension)?\s+for\s+"
        rf"(?:the\s+)?{_MODELED_HUMAN_DECISION}",
        rf"\b{subject}\s+applies\s+to\s+(?:the\s+)?"
        rf"{_MODELED_HUMAN_DECISION}",
        rf"\b{subject}\s+(?:(?:is|was)\s+active\s+and\s+)?"
        rf"supplements?\s+(?:the\s+)?odd\s+2020\s+for\s+(?:the\s+)?"
        rf"{_MODELED_HUMAN_DECISION}",
    )
    return any(re.search(relation, statement) for relation in relations)


def _without_standalone_prompts(body: str) -> str:
    """Remove every complete bracket-only block, keeping surrounding prose.

    Brackets balance across physical lines. A link or prose sharing the final
    line is content, not a standalone template prompt.
    """

    lines = body.splitlines(keepends=True)
    index = 0
    while index < len(lines):
        if not lines[index].lstrip().startswith("["):
            index += 1
            continue
        depth = 0
        end = index
        complete = False
        while end < len(lines):
            for column, character in enumerate(lines[end]):
                if character == "[":
                    depth += 1
                elif character == "]":
                    depth -= 1
                    if depth == 0:
                        complete = not lines[end][column + 1 :].strip()
                        break
            if depth == 0:
                break
            end += 1
        if complete:
            for position in range(index, end + 1):
                lines[position] = "\n" if lines[position].endswith("\n") else ""
            index = end + 1
        else:
            index += 1
    return "".join(lines)


def validate_text(text: str) -> tuple[str, ...]:
    """Return deterministic structural diagnostics for ODD Markdown text."""

    visible, lines, scan_diagnostics, inline_code_spans = _scan_markdown(text)
    diagnostics = list(scan_diagnostics)
    classified_headings = _classify_headings(visible, lines)
    semantic_visible = _blank_heading_spans(visible, classified_headings)
    characters = list(semantic_visible)
    for context in lines:
        if context.path:
            _mask_range(characters, context.line.start, context.line.start + context.content_start)
    semantic_visible = "".join(characters)
    level_one_headings = tuple(
        heading
        for heading in classified_headings
        if heading.level == 1 and heading.container is None
    )
    valid_leading_title = len(level_one_headings) == 1 and not visible[
        : level_one_headings[0].start
    ].strip()
    if level_one_headings and not valid_leading_title:
        diagnostics.append("expected at most one leading level-one document title")

    numbered_headings = tuple(
        heading
        for heading in classified_headings
        if heading.level == 2
        and heading.container is None
        and heading.syntax == "ATX"
        and heading.indent == 0
        and _NUMBERED_LABEL.fullmatch(heading.label) is not None
    )
    headings = tuple(f"## {heading.label}" for heading in numbered_headings)

    if headings != _CANONICAL_HEADINGS:
        diagnostics.append(
            "expected exactly the seven numbered ODD 2020 elements in canonical order"
        )

    level_two_headings = tuple(
        heading
        for heading in classified_headings
        if heading.level == 2 and heading.container is None
    )
    numbered_starts = {heading.start for heading in numbered_headings}
    last_numbered_start = (
        numbered_headings[-1].start if numbered_headings else None
    )
    for heading in level_two_headings:
        if heading.start in numbered_starts:
            continue
        if re.match(r"\d", heading.label):
            diagnostics.append(f"supporting level-two heading {heading.display!r} must be unnumbered")
        if last_numbered_start is None or heading.start < last_numbered_start:
            diagnostics.append(
                f"supporting level-two heading {heading.display!r} must appear after "
                "element 7"
            )

    substitutes = tuple(
        heading.display
        for heading in classified_headings
        if 2 <= heading.level <= 6
        and heading.label.casefold() in _SUBSTITUTE_LABELS
    )
    if substitutes:
        diagnostics.append(
            "grouping labels must not substitute for numbered ODD elements: "
            + ", ".join(substitutes)
        )

    first_element = (
        numbered_headings[0].start if numbered_headings else len(visible)
    )
    for heading in classified_headings:
        if heading.container is None:
            continue
        if heading.level <= 2:
            diagnostic = (
                f"container-prefixed heading {heading.display!r} is not permitted "
                "as a top-level title or supporting section"
            )
            if heading.start < first_element:
                diagnostic += " and must not appear before element 1"
            diagnostics.append(diagnostic)
        elif heading.start < first_element:
            diagnostics.append(
                f"container-prefixed heading {heading.display!r} must not appear "
                "before element 1"
            )

    premature_root_subordinates = tuple(
        heading
        for heading in classified_headings
        if heading.container is None
        and 3 <= heading.level <= 6
        and heading.start < first_element
    )
    for heading in premature_root_subordinates:
        diagnostics.append(
            f"subordinate heading {heading.display!r} must not appear before element 1"
        )

    declaration_characters = list(semantic_visible[:first_element])
    for start, end in inline_code_spans:
        if start < first_element:
            _mask_range(declaration_characters, start, min(end, first_element))
    declaration = "".join(declaration_characters)
    normalized_declaration = " ".join(declaration.casefold().split())
    declaration_sentences = _declaration_statements(declaration)
    base_protocol_signals = {
        _classify_base_protocol_relation(sentence)
        for sentence in declaration_sentences
    }
    base_protocol_contradictory = (
        "contradictory" in base_protocol_signals
        or {"affirmative", "negative"}.issubset(base_protocol_signals)
    )
    if base_protocol_contradictory:
        diagnostics.append(
            "declaration region contains contradictory affirmative and negative "
            "ODD protocol statements"
        )
    elif "affirmative" not in base_protocol_signals:
        diagnostics.append(
            "declaration region is missing affirmative use of ODD as the "
            "documentation protocol"
        )

    declaration_checks = (
        (r"\b2020\b", "ODD 2020"),
        (r"second\s+update", "second update"),
        (_GRIMM_2006, "Grimm et al. (2006)"),
        (_GRIMM_2020, "Grimm et al. (2020)"),
    )
    for pattern, label in declaration_checks:
        if not re.search(pattern, normalized_declaration):
            diagnostics.append(f"declaration region is missing {label}")

    odd_d_signals, mixed_polarity, _ = (
        _odd_d_declaration_signals(declaration_sentences)
    )
    signal_set = set(odd_d_signals)
    contradictory = mixed_polarity or {
        "affirmative",
        "explicit-negative",
    }.issubset(signal_set)
    if contradictory:
        diagnostics.append(
            "ODD+D declaration region contains contradictory affirmative and "
            "negative classification statements"
        )
    if "indeterminate" in signal_set and not mixed_polarity:
        diagnostics.append(
            "ODD+D declaration region contains structurally indeterminate "
            "classification language"
        )

    if "affirmative" in signal_set and not contradictory:
        if not re.search(_MULLER_2013, normalized_declaration):
            diagnostics.append(
                "affirmative ODD+D declaration region is missing Müller et al. "
                "(2013)"
            )

        supplementation_statements = tuple(
            sentence
            for sentence in declaration_sentences
            if _is_affirmative_supplementation(sentence)
        )
        prior_active_extension = False
        human_boundary = False
        for sentence in declaration_sentences:
            classification = (
                _classify_odd_d_statement(sentence)[0]
                if _ODD_D.search(sentence)
                else "absent"
            )
            current_active_extension = classification == "affirmative"
            if _is_affirmative_human_scope(
                sentence,
                allow_referential_subject=(
                    prior_active_extension or current_active_extension
                ),
            ):
                human_boundary = True
            prior_active_extension = (
                prior_active_extension or current_active_extension
            )
        if not supplementation_statements or not human_boundary:
            diagnostics.append(
                "affirmative ODD+D declaration region is missing explicit "
                "supplementation of ODD 2020 for modeled human decision-making"
            )

    if headings == _CANONICAL_HEADINGS:
        for index, heading_match in enumerate(numbered_headings):
            next_h2 = next(
                (
                    heading
                    for heading in level_two_headings
                    if heading.start >= heading_match.end
                ),
                None,
            )
            end = next_h2.start if next_h2 else len(visible)
            body = semantic_visible[heading_match.end : end]
            body = _without_standalone_prompts(body)
            if not re.search(r"\w", body):
                diagnostics.append(f"element {index + 1} has no visible content")

    return tuple(sorted(set(diagnostics)))
