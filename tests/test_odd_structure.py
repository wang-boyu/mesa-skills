"""Focused checks for the shipped optional ODD structure helper."""

from __future__ import annotations

import contextlib
import io
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "skills" / "document-abm-with-odd"
CHECKER = PACKAGE / "scripts" / "validate_odd.py"
MODULE = runpy.run_path(str(CHECKER))
CHECK = MODULE["validate_text"]
ELEMENTS = (
    "Purpose and patterns",
    "Entities, state variables, and scales",
    "Process overview and scheduling",
    "Design concepts",
    "Initialization",
    "Input data",
    "Submodels",
)
BODIES = (
    "Explore how random transfers change the distribution of wealth.",
    "The model contains 20 households; wealth is measured in tokens.",
    "Each step shuffles households, then updates transfers sequentially.",
    "Inequality emerges; observation records wealth after each whole step.",
    "Every household starts with one token; a supplied seed initializes the RNG.",
    "No external inputs vary during a run.",
    "A household with a token gives one token to a uniformly sampled household.",
)


def document() -> str:
    return "# Transfer model\n\n" + "\n\n".join(
        f"## {number}. {label}\n\n{body}"
        for number, (label, body) in enumerate(zip(ELEMENTS, BODIES), 1)
    ) + "\n"


def run_checker(path: Path, *, checker: Path = CHECKER) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", "-S", "-B", str(checker), str(path)],
        cwd=path.parent,
        capture_output=True,
        text=True,
        check=False,
    )


class OddStructureTests(unittest.TestCase):
    def test_help_is_successful_without_reading_a_document(self) -> None:
        for option in ("-h", "--help"):
            with self.subTest(option=option):
                with patch.object(Path, "read_text", side_effect=AssertionError("read")):
                    with contextlib.redirect_stdout(io.StringIO()) as stdout:
                        self.assertEqual(MODULE["main"]([option]), 0)
                self.assertIn("usage:", stdout.getvalue())
                self.assertIn("structure", stdout.getvalue())

    def test_plain_document_and_supported_body_forms(self) -> None:
        forms = (
            BODIES[2],
            "### Activation\nEach household acts once.\n###### Timing\nUpdates are immediate.",
            "- Shuffle households.\n- Transfer one token.\n1. Record total wealth.",
            "| Variable | Unit |\n| --- | --- |\n| Wealth | tokens |",
            "Use `model.agents` and ``literal ` marker``; `<tag>` is inline code.",
            "See [details](<https://example.org>) and <https://example.org>.",
            "No inputs. <!-- this inline comment is deliberately unsupported -->",
        )
        for body in forms[:-1]:
            with self.subTest(body=body):
                self.assertEqual(CHECK(document().replace(BODIES[2], body)), ())
        self.assertTrue(CHECK(document().replace(BODIES[2], forms[-1])))

    def test_optional_title_and_trailing_appendices(self) -> None:
        self.assertEqual(CHECK(document().removeprefix("# Transfer model\n\n")), ())
        self.assertEqual(CHECK(document() + "\n## References\nA source.\n## Notes\nA note.\n"), ())
        closed = document().replace("## 5. Initialization", "## 5. Initialization ###   ")
        self.assertEqual(CHECK(closed), ())
        self.assertEqual(CHECK(document().replace("\n", "\r\n")), ())

    def test_seven_headings_cannot_be_missing_reordered_duplicated_or_renamed(self) -> None:
        for number, label in enumerate(ELEMENTS, 1):
            heading = f"## {number}. {label}"
            variants = (
                document().replace(heading, ""),
                document().replace(heading, heading + "\n" + heading),
                document().replace(heading, heading + " changed"),
                document().replace(heading, "###" + heading[2:]),
            )
            for candidate in variants:
                with self.subTest(number=number, candidate=candidate):
                    self.assertTrue(CHECK(candidate))
        shuffled = document().replace("## 1. Purpose and patterns", "## TEMP")
        shuffled = shuffled.replace("## 2. Entities, state variables, and scales", "## 1. Purpose and patterns")
        shuffled = shuffled.replace("## TEMP", "## 2. Entities, state variables, and scales")
        self.assertTrue(CHECK(shuffled))

    def test_heading_hierarchy_and_appendix_placement(self) -> None:
        for addition in ("# Second title", "## References", "### Preamble"):
            with self.subTest(addition=addition):
                self.assertTrue(CHECK(addition + "\n\n" + document()))
        for heading in ("# Misplaced title", "## References", "## 8. More", "## 8"):
            with self.subTest(heading=heading):
                candidate = document().replace("## 3. Process overview", heading + "\n\n## 3. Process overview")
                self.assertTrue(CHECK(candidate))
        self.assertTrue(CHECK(document() + "\n## 8. Extra\nText.\n"))
        self.assertTrue(CHECK(document() + "\n# Late title\n"))

    def test_every_element_requires_its_own_non_heading_text(self) -> None:
        empty_forms = ("", "<!-- comment -->", "### Only a heading", "```text\nexample\n```", "---")
        for number, body in enumerate(BODIES, 1):
            for empty in empty_forms:
                with self.subTest(number=number, empty=empty):
                    errors = CHECK(document().replace(body, empty))
                    self.assertIn(f"element {number} has no visible non-heading text", errors)
        errors = CHECK(document().replace(BODIES[6], "## References\nOnly appendix text."))
        self.assertIn("element 7 has no visible non-heading text", errors)

    def test_untouched_template_is_not_a_filled_description(self) -> None:
        errors = CHECK((PACKAGE / "assets" / "ODD.md").read_text(encoding="utf-8"))
        self.assertEqual(len(errors), 7)
        self.assertTrue(all("no visible non-heading text" in error for error in errors))

    def test_structure_does_not_attempt_english_attribution_or_decision_inference(self) -> None:
        for prose in ("", "ODD+D may be used. No authors are cited.", "ODD is not used; the model is scientifically valid."):
            with self.subTest(prose=prose):
                self.assertEqual(CHECK(document().replace(BODIES[0], BODIES[0] + "\n" + prose)), ())

    def test_comments_and_fences_cannot_supply_or_interrupt_headings(self) -> None:
        wrappers = (("<!--", "-->"), ("```markdown", "```"), ("~~~~", "~~~~~"))
        for start, end in wrappers:
            with self.subTest(start=start):
                hidden = f"{start}\n# Hidden title\n## Hidden section\n{end}\n"
                self.assertEqual(CHECK(document().replace(BODIES[2], BODIES[2] + "\n" + hidden)), ())
                self.assertTrue(CHECK(f"{start}\n{document()}\n{end}\n"))
        self.assertEqual(CHECK(document() + "\n```\n<!-- unclosed text inside code\n```\n"), ())
        self.assertEqual(CHECK(document() + "\n<!--\n``` not a fence\n-->\n"), ())

    def test_fence_closer_must_match_marker_length_and_have_no_info(self) -> None:
        for bad in ("```", "~~~~", "```` trailing", "    ````"):
            with self.subTest(bad=bad):
                example = f"````markdown\n{bad}\n## Hidden\n`````\n"
                self.assertEqual(CHECK(document() + "\n" + example), ())
        for start in ("```", "~~~", "<!--"):
            with self.subTest(start=start):
                self.assertIn("unclosed fenced block or HTML comment", CHECK(document() + "\n" + start))
        self.assertTrue(CHECK(document() + "\n```bad`info\n```\n"))

    def test_unsupported_markdown_never_silently_passes(self) -> None:
        examples = (
            "    ## Hidden", "\t## Hidden", " ## Indented", "> ## Quoted",
            "- ## List heading", "12) ## List heading", "- > Quoted", "- - Nested",
            "- item\n\n  ### Continued", "- item\n\t### Tab continuation",
            "Heading\n======", "Heading\n------", "[ref]: https://example.org",
            "<div>\n## Hidden\n</div>", "<!-- hidden --> ## New heading",
            "Text <!-- inline -->", "`unclosed code", "`` unmatched `",
            "    ```\n## Visible after pseudo-fence\n    ```",
            "    <!--\n## Visible after pseudo-comment\n    -->",
        )
        for example in examples:
            with self.subTest(example=example):
                self.assertTrue(CHECK(document() + "\n" + example + "\n"))

    def test_html_block_starts_at_line_end_cannot_hide_the_document(self) -> None:
        plain = document().removeprefix("# Transfer model\n\n")
        for opening in ("<script", "<pre", "<style", "<textarea", "<SCRIPT", "<div", "</div"):
            with self.subTest(opening=opening):
                self.assertIn(
                    "line 1: unsupported Markdown profile syntax",
                    CHECK(opening + "\n" + plain),
                )
                self.assertEqual(CHECK(f"`{opening}`\n\n" + plain), ())
                self.assertEqual(CHECK(f"```text\n{opening}\n```\n\n" + plain), ())

    def test_exit_codes_diagnostics_and_target_preservation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            unrelated = root / "notes.txt"
            unrelated.write_bytes(b"user content\n")
            for content, expected in ((document().encode(), 0), (b"not ODD\n", 1), (b"\xff", 2)):
                path = root / "ODD.md"
                path.write_bytes(content)
                path.chmod(0o440)
                before = {p.name: (p.read_bytes(), p.stat().st_mode, p.stat().st_mtime_ns) for p in root.iterdir()}
                first, second = run_checker(path), run_checker(path)
                self.assertEqual(first.returncode, expected, first.stderr)
                self.assertEqual((first.stdout, first.stderr), (second.stdout, second.stderr))
                if expected:
                    self.assertIn(str(path), first.stderr)
                    self.assertEqual(first.stdout, "")
                else:
                    self.assertIn("were not checked", first.stdout)
                after = {p.name: (p.read_bytes(), p.stat().st_mode, p.stat().st_mtime_ns) for p in root.iterdir()}
                self.assertEqual(before, after)
                path.chmod(0o600)

    def test_invalid_invocation_and_unreadable_inputs_exit_two(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for path in (root / "missing.md", root):
                self.assertEqual(run_checker(path).returncode, 2)
            for arguments in ([], ["one.md", "two.md"]):
                with contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(MODULE["main"](arguments), 2)
            file = root / "ODD.md"
            file.write_text(document(), encoding="utf-8")
            with patch.object(Path, "read_text", side_effect=PermissionError("denied")):
                with contextlib.redirect_stderr(io.StringIO()) as stderr:
                    self.assertEqual(MODULE["main"]([str(file)]), 2)
            self.assertIn("denied", stderr.getvalue())
            if hasattr(os, "mkfifo"):
                fifo = root / "input.pipe"
                os.mkfifo(fifo)
                self.assertEqual(run_checker(fifo).returncode, 2)

    def test_copied_package_runs_without_site_packages_or_repository_imports(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            copied = root / "standalone"
            shutil.copytree(PACKAGE, copied, ignore=shutil.ignore_patterns("__pycache__"))
            path = root / "ODD.md"
            path.write_text(document(), encoding="utf-8")
            result = run_checker(path, checker=copied / "scripts" / "validate_odd.py")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((root / "internal").exists())
            self.assertFalse((copied / "scripts" / "__pycache__").exists())


if __name__ == "__main__":
    unittest.main()
