"""Focused extended ODD syntax and closed-relation checks, not model fidelity."""

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
    "Purpose and patterns", "Entities, state variables, and scales",
    "Process overview and scheduling", "Design concepts", "Initialization",
    "Input data", "Submodels",
)
BODIES = (
    "Compare the spatial distribution of household wealth after transfers.",
    "Twenty households each hold an integer number of tokens.",
    "Each step shuffles households and executes transfers sequentially.",
    "Inequality emerges; measurement occurs after a whole step.",
    "Each household receives one token and a supplied seed initializes the RNG.",
    "No external inputs vary during a run.",
    "A household with tokens transfers one to a uniformly sampled household.",
)
BASE = (
    "This description uses ODD as its documentation protocol, specifically the ODD 2020 "
    "second update (Grimm et al. 2006; Grimm et al. 2020)."
)
ACTIVE = (
    "ODD+D is active as a conditional extension for material modeled human "
    "decision-making; it supplements ODD 2020 for that human decision component "
    "(Müller et al. 2013)."
)
VERSION = "The referenced version is the ODD 2020 second update (Grimm et al. 2006; Grimm et al. 2020)."


def document(declaration: str = BASE, *, title: str = "") -> str:
    return f"{title}\n\n{declaration}\n\n" + "\n\n".join(
        f"## {number}. {label}\n{body}"
        for number, (label, body) in enumerate(zip(ELEMENTS, BODIES), 1)
    ) + "\n"


def run_checker(path: Path, *, extended: bool = True, checker: Path = CHECKER) -> subprocess.CompletedProcess[str]:
    # -I ignores Python environment flags. Deliberately omit -B: the copied
    # standalone package must also avoid bytecode writes under ordinary use.
    environment = dict(os.environ)
    environment.pop("PYTHONDONTWRITEBYTECODE", None)
    return subprocess.run(
        [sys.executable, "-I", "-S", str(checker), *(["--extended"] if extended else []), str(path)],
        cwd=path.parent, env=environment, capture_output=True, text=True,
        check=False, timeout=10,
    )


class OddExtendedTests(unittest.TestCase):
    def assert_passes(self, text: str) -> None:
        self.assertEqual(CHECK(text, extended=True), ())

    def assert_diagnostic(self, text: str, *fragments: str) -> None:
        diagnostics = CHECK(text, extended=True)
        self.assertTrue(diagnostics)
        normalized = "\n".join(diagnostics).casefold()
        for fragment in fragments:
            self.assertIn(fragment.casefold(), normalized)

    def test_extended_is_explicit_and_default_diagnostics_stay_exact(self) -> None:
        plain = document("")
        self.assertEqual(CHECK(plain), ())
        self.assertEqual(CHECK(plain, extended=False), ())
        self.assert_diagnostic(plain, "missing affirmative use", "missing Grimm et al. (2006)")
        self.assertEqual(CHECK("not ODD\n"), (
            "expected the seven numbered ODD elements in order, then unnumbered appendices",
            *(f"element {number} has no visible non-heading text" for number in range(1, 8)),
        ))
        self.assertEqual(CHECK(document("").replace(BODIES[0], "> quoted prose")), (
            "line 6: unsupported Markdown profile syntax",
            "element 1 has no visible non-heading text",
        ))
        prompt = document().replace(BODIES[2], "[replace this]")
        self.assertEqual(CHECK(prompt), ())
        self.assert_diagnostic(prompt, "element 3 has no visible content")

    def test_historical_affirmative_base_forms_and_distributed_evidence(self) -> None:
        forms = (
            "This description follows the ODD protocol.",
            "This description adopts ODD as the model-description protocol.",
            "The model is documented according to ODD.",
            "This model description is described using the ODD protocol.",
            "This model description is structured under ODD as its documentation protocol.",
            "This model description is organized according to the ODD protocol.",
            "This description applies the ODD protocol.",
            "This document follows ODD. ODD is the documentation protocol used here.",
            "This description is structured under ODD. It uses ODD as its documentation protocol.",
            "This model description follows the ODD protocol. This unrelated implementation note is not a protocol requirement.",
        )
        for statement in forms:
            with self.subTest(statement=statement):
                self.assert_passes(document(statement + "\n\n" + VERSION))
        self.assert_passes(document(
            "This model description is structured under ODD as its documentation protocol. "
            "It follows the 2020 second update described by Grimm et al. (2020), building on "
            "the original protocol introduced by Grimm et al. (2006)."
        ))

    def test_negative_modal_context_and_contradictory_base_declarations(self) -> None:
        forms = (
            "This description cannot use ODD as its documentation protocol.",
            "This description will not use ODD as its documentation protocol.",
            "This description may use ODD as its documentation protocol.",
            "This description could use ODD as its documentation protocol.",
            "This description should use ODD as its documentation protocol.",
            "This model description is not structured under ODD as its documentation protocol.",
            "ODD is discussed, but it is not used as the documentation protocol.",
            "The authors considered ODD but did not adopt it.",
            "The bibliography describes the ODD protocol for comparison.",
            "This declaration cites ODD research. The implementation protocol is described elsewhere.",
        )
        for statement in forms:
            with self.subTest(statement=statement):
                self.assert_diagnostic(document(statement + " " + VERSION), "missing affirmative use")
        self.assert_diagnostic(document(BASE + " ODD is not the applied documentation protocol."), "contradictory", "ODD protocol")

    def test_credit_punctuation_and_wrong_author_or_year_boundaries(self) -> None:
        complete = BASE + " " + ACTIVE
        for name, year in (("Grimm", 2006), ("Grimm", 2020), ("Müller", 2013)):
            credit = f"{name} et al. {year}"
            for replacement in (f"{name} et al., {year}", f"{name} et al. ({year})", f"{name} et al., ({year})"):
                with self.subTest(credit=replacement):
                    self.assert_passes(document(complete.replace(credit, replacement)))
            for replacement in (f"Not{name} et al. {year}", f"{name} et al. {year + 1}", f"{name} et al. {year}1", ""):
                with self.subTest(wrong_credit=replacement):
                    self.assert_diagnostic(document(complete.replace(credit, replacement)), f"missing {name} et al. ({year})")
        self.assert_diagnostic(document(complete.replace("Müller", "Muller")), "missing Müller")
        self.assert_diagnostic(document(BASE.replace("second update", "updated edition")), "missing second update")
        self.assert_diagnostic(document(BASE.replace("2020", "2019")), "missing ODD 2020", "missing Grimm et al. (2020)")
        self.assert_diagnostic(document(
            "This description uses ODD as its documentation protocol and applies the ODD 2020 second update. "
            "Its identifiers are 10.1016/j.ecolmodel.2006.04.023 and 10.18564/jasss.4259."
        ), "missing Grimm et al. (2006)", "missing Grimm et al. (2020)")

    def test_declarations_and_credits_only_in_hidden_or_later_regions_do_not_count(self) -> None:
        wrappers = (
            lambda s: f"<!-- {s} -->", lambda s: f"```text\n{s}\n```",
            lambda s: f"~~~\n{s}\n~~~", lambda s: f"# {s}",
            lambda s: f"{s}\n===", lambda s: f"### {s}",
            lambda s: f"> - ## {s}", lambda s: f"12)\n    #### {s}",
            lambda s: f"-\titem\n\n\t{s}\n\t---",
        )
        for wrap in wrappers:
            with self.subTest(hidden=wrap(BASE)):
                self.assert_diagnostic(document(wrap(BASE)), "missing affirmative use", "missing second update", "missing Grimm et al. (2006)")
                no_credit = (BASE + " " + ACTIVE).replace(" (Müller et al. 2013)", "")
                self.assert_diagnostic(document(no_credit, title=wrap("Müller et al. 2013")), "missing Müller et al. (2013)")
        for location in (BODIES[0], BODIES[6]):
            with self.subTest(later=location):
                self.assert_diagnostic(document("").replace(location, location + "\n" + BASE), "missing affirmative use")
        self.assert_diagnostic(document("") + "\n## References\n" + BASE, "missing Grimm et al. (2020)")

    def test_odd_d_activation_negation_context_and_indeterminate_grammar(self) -> None:
        inactive = (
            "ODD+D is not used because the model contains no material modeled human decision-making.",
            "This document does not apply ODD+D.",
            "ODD+D was considered for context but is not applied to this model.",
            "ODD+D was considered but is not active for this model.",
            "The ODD+D protocol is described here only for context; this statement does not apply it.",
            "Non-human adaptation and learning are modeled. ODD+D is not active.",
        )
        for statement in inactive:
            with self.subTest(inactive=statement):
                self.assert_passes(document(BASE + " " + statement))
        for statement in ("ODD+D may be active for this model.", "ODD+D is a conditional extension for stakeholder choices (Müller et al. 2013)."):
            with self.subTest(indeterminate=statement):
                self.assert_diagnostic(document(BASE + " " + statement), "indeterminate")
        for statement in ("ODD+D is active.", "We apply ODD+D.", "This model uses ODD+D.", "ODD+D applies to modeled human decisions."):
            with self.subTest(active=statement):
                self.assert_passes(document(BASE + " " + statement + " It supplements ODD 2020. This extension covers modeled human decisions (Müller et al. 2013)."))
        self.assert_diagnostic(document(BASE + " " + ACTIVE + " ODD+D is not active."), "contradictory")
        self.assert_diagnostic(document(BASE + " ODD+D is active but ODD+D is not used."), "contradictory")

    def test_human_scope_requires_extension_relation_and_supplementation(self) -> None:
        positive = (
            "This extension covers material modeled human decision-making.",
            "It covers material modeled human decision-making.",
            "This extension documents substantial modelled human decisions.",
            "This extension addresses modeled human decision making.",
            "This extension represents modelled human decision component.",
        )
        negative = (
            "This extension lacks material modeled human decision-making.",
            "This extension covers anything other than material modeled human decision-making.",
            "This extension covers human agents and decision variables.",
            "The model contains material modeled human decision-making.",
            "This extension covers modeled material human decision-making.",
        )
        for statement in positive + negative:
            candidate = document(BASE + " ODD+D is active. It supplements ODD 2020. " + statement + " (Müller et al. 2013).")
            with self.subTest(scope=statement):
                if statement in positive:
                    self.assert_passes(candidate)
                else:
                    self.assert_diagnostic(candidate, "missing explicit supplementation", "human decision")
        self.assert_passes(document(BASE + " " + ACTIVE))
        for statement in (
            "ODD+D is active (Müller et al. 2013). It supplements ODD 2020 only as protocol context.",
            "ODD+D is active and supplements ODD 2020 for insect decisions (Müller et al. 2013). Material modeled human decision-making is absent.",
            "ODD+D is active for material modeled human decision-making (Müller et al. 2013), but it does not supplement or integrate with ODD 2020.",
            "It covers modeled human decisions. ODD+D is active. This extension supplements ODD 2020 (Müller et al. 2013).",
        ):
            with self.subTest(scope_failure=statement):
                self.assert_diagnostic(document(BASE + " " + statement), "missing explicit supplementation")

    def test_title_and_appendix_syntax_with_canonical_root_elements(self) -> None:
        for title in ("# Transfer model", "   # Transfer model ###", "Transfer model\n===", "  Transfer model\n  ==="):
            with self.subTest(title=title):
                self.assert_passes(document(title=title))
        for appendix in ("## References", "   ## References", "References\n---"):
            with self.subTest(appendix=appendix):
                self.assert_passes(document() + "\n" + appendix + "\nA source.\n")
        for number, label in enumerate(ELEMENTS, 1):
            heading = f"## {number}. {label}"
            with self.subTest(closing_hash=heading):
                self.assert_passes(document().replace(heading, heading + " ###  "))
            for replacement in (" " + heading, "> " + heading, f"{number}. {label}\n---", "###" + heading[2:]):
                with self.subTest(noncanonical=replacement):
                    self.assert_diagnostic(document().replace(heading, replacement), "seven numbered ODD 2020 elements")
        self.assert_diagnostic(document(title="# One\n\nSecond\n==="), "at most one leading")
        self.assert_diagnostic(document() + "\nLate title\n===", "at most one leading")
        self.assert_diagnostic(document() + "\n## 8. Extra\nText.", "seven numbered ODD 2020 elements")

    def test_subsections_and_forbidden_grouping_hierarchy(self) -> None:
        for level in range(3, 7):
            heading = "#" * level + " Detail"
            with self.subTest(level=level):
                self.assert_passes(document().replace(BODIES[2], heading + "\n" + BODIES[2]))
                self.assert_passes(document() + "\n## References\n" + heading + "\nSource.")
                self.assert_diagnostic(document(heading + "\n\n" + BASE), "must not appear before element 1")
        for label in ("Overview", "Details", "Design concepts"):
            for level in (2, 3, 6):
                with self.subTest(group=label, level=level):
                    self.assert_diagnostic(document() + "\n" + "#" * level + " " + label, "grouping labels")

    def test_every_root_level_two_ends_its_preceding_element_body(self) -> None:
        for number, body in enumerate(BODIES, 1):
            for heading in ("## Supporting material", "   ## Supporting material", "Supporting material\n---"):
                with self.subTest(number=number, heading=heading):
                    candidate = document().replace(body, heading + "\nContent belongs to a sibling section.")
                    self.assert_diagnostic(candidate, f"element {number} has no visible content")
                    if number < 7:
                        self.assert_diagnostic(candidate, "must appear after element 7")

    def test_recursive_loose_and_tab_containers_classify_headings(self) -> None:
        containers = (
            "> > {heading}", "> - {heading}", "- > {heading}", "12) {heading}",
            "12.\n    {heading}", "- item\n\n  {heading}",
            "-\titem\n\t{heading}", "12)\titem\n\n\t{heading}",
            "> - item\n>\n>   {heading}", "- - item\n\n    {heading}",
        )
        for container in containers:
            for level in (1, 2, 3, 6):
                heading = container.format(heading="#" * level + " Supporting detail")
                with self.subTest(container=container, level=level):
                    candidate = document().replace(BODIES[2], BODIES[2] + "\n" + heading)
                    if level <= 2:
                        self.assert_diagnostic(candidate, "container-prefixed heading", "not permitted as a top-level")
                    else:
                        self.assert_passes(candidate)
        for heading in (
            "> > Details\n> > ---", "- item\n\n  Detail\n  ===",
            "12)\titem\n\n\tDetail\n\t---",
        ):
            with self.subTest(setext=heading):
                self.assert_diagnostic(document().replace(BODIES[2], BODIES[2] + "\n" + heading), "container-prefixed heading")

    def test_nested_heading_spans_cannot_supply_evidence_or_activate_extensions(self) -> None:
        for container in ("> > {text}\n> > ===", "12)\n    #### {text}", "-\titem\n\n\t### {text}"):
            with self.subTest(container=container):
                self.assert_diagnostic(document(container.format(text=BASE)), "missing affirmative use", "missing Grimm et al. (2020)")
                candidate = document(BASE + " " + ACTIVE, title=container.format(text="ODD+D is not active."))
                errors = "\n".join(CHECK(candidate, extended=True))
                self.assertIn("container-prefixed heading", errors)
                self.assertNotIn("contradictory", errors)

    def test_comments_fences_and_physical_newlines_preserve_visible_structure(self) -> None:
        for indent in range(4):
            spaces = " " * indent
            for opener, closer in (("<!--", "-->"), ("```markdown", "````"), ("~~~~", "~~~~~")):
                hidden = f"{spaces}{opener}\n## Hidden\nHidden title\n===\nODD+D is active.\n{spaces}{closer}\n"
                with self.subTest(indent=indent, opener=opener):
                    self.assert_passes(hidden + document())
        self.assert_passes(document("###<!-- neutral --> " + BASE))
        self.assert_passes("Not a Setext title\n<!-- comment\nwith more text -->\n===\n" + document())
        self.assert_passes(document().replace("\n", "\r\n"))
        self.assert_passes(document(BASE.replace("protocol,", "protocol, <!-- aside -->")))
        for pseudo in ("    ```markdown\n## References\n    ```", "    <!--\n## References\n    -->"):
            with self.subTest(pseudo=pseudo):
                self.assert_diagnostic(document().replace(BODIES[2], BODIES[2] + "\n" + pseudo), "must appear after element 7")

    def test_container_fences_closers_dedents_and_partial_outer_context(self) -> None:
        examples = (
            "> ````markdown\n> ## Hidden\n> ```\n> ODD+D is active.\n> ````",
            "- ~~~~ model\n  ## Hidden\n  ~~~~ trailing\n  ODD+D is active.\n  ~~~~~",
            "12. ```markdown\n    ## Hidden\n    ~~~\n    ODD+D is active.\n    ````",
            "> > ~~~~\n> > ## Hidden\n> > ~~~~ trailing\n> > ~~~~~",
            "> - ```\n>   ## Hidden\n>   ```",
            "-\t```\n\t## Hidden\n\t```",
            "> <!--\n> ## Hidden\n> -->", "12) <!--\n    ## Hidden\n    -->",
        )
        for hidden in examples:
            with self.subTest(hidden=hidden):
                self.assert_passes(hidden + "\n\n" + document())
        for prefix in ("> ```\n> ## Hidden", "- ```\n  ## Hidden", "12) ```\n    ## Hidden"):
            with self.subTest(dedent=prefix):
                candidate = document().replace(BODIES[2], BODIES[2] + "\n" + prefix + "\n## References\nSource.")
                self.assert_diagnostic(candidate, "must appear after element 7")
                self.assertNotIn("Hidden", "\n".join(CHECK(candidate, extended=True)))
                self.assert_diagnostic(document() + "\n" + prefix, "unclosed fenced block")
        for content in (
            "> - ```\n>   ## Hidden\n> ## Revealed outer section",
            "- - ```\n    ## Hidden\n  ## Revealed outer section",
            "- ```\n  ## Hidden\n- ## Revealed sibling section",
        ):
            with self.subTest(partial=content):
                self.assert_diagnostic(document().replace(BODIES[2], content), "container-prefixed heading", "Revealed")

    def test_visible_body_excludes_all_prompt_blocks_and_container_markers(self) -> None:
        empty = (
            "[Replace this prompt]", "[First prompt]\n\n[Second prompt]",
            "[A multiline\nprompt]\n[Another\nprompt]", "[Nested [prompt] text]",
            "[Prompt]\n<!-- note -->\n[Another prompt]", "[Prompt]\n### Only heading\n[Another prompt]",
            ">", "-", "12)", "> -", "-\t<!-- hidden -->\n\t### Heading only",
            "```\nExample text\n```", "<!-- invisible -->", "### Heading only",
            "- [First prompt]\n\n  [Second prompt]",
        )
        for body in empty:
            with self.subTest(empty=body):
                self.assert_diagnostic(document().replace(BODIES[2], body), "element 3 has no visible content")
        for body in (
            "[Prompt]\nThe algorithm samples one household.\n[Prompt]",
            "Substantive prose [with an annotation].", "[annotation] accompanying prose.",
            "[Reference](https://example.org)", "> Household wealth is nonnegative.",
            "-\tHousehold wealth is nonnegative.\n\t### Detail",
        ):
            with self.subTest(prose=body):
                self.assert_passes(document().replace(BODIES[2], body))

    def test_complete_inline_code_spans_keep_literal_comment_openers_visible(self) -> None:
        for body in (
            "Use `<!--` as the literal comment opener.",
            "Use ``literal ` <!--`` as text.",
            "Use `<!-- literal -->` in the input.",
            "- Use `<!--` inside a list.",
        ):
            with self.subTest(body=body):
                candidate = document().replace(BODIES[2], body)
                self.assertEqual(CHECK(candidate), ())
                self.assert_passes(candidate)
        self.assert_diagnostic(
            document().replace(BODIES[2], "Use `literal`. <!-- real unclosed comment"),
            "unclosed fenced block or HTML comment",
        )

        self.assert_passes(document().replace(BODIES[2], "Use `<!--` as text. <!-- a real comment follows -->"))
        # A real comment opened first controls the backticks in its contents.
        self.assert_passes(document().replace(BODIES[2], "<!-- ` hidden --> " + BODIES[2]))
        self.assert_diagnostic(document().replace(
            BODIES[2], "<!-- ` hidden -->\n## References\n<!-- ` hidden --> Source."
        ), "must appear after element 7", "element 3 has no visible content")

    def test_inline_literals_cannot_supply_or_contradict_declaration_evidence(self) -> None:
        for delimiter in ("`", "``"):
            def literal(text: str) -> str:
                return delimiter + text + delimiter

            with self.subTest(delimiter=delimiter, evidence="whole declaration"):
                self.assert_diagnostic(
                    document(literal(BASE)), "missing affirmative use",
                    "missing second update", "missing Grimm et al. (2006)",
                    "missing Grimm et al. (2020)",
                )
            for credit in ("Grimm et al. 2006", "Grimm et al. 2020", "Müller et al. 2013"):
                with self.subTest(delimiter=delimiter, credit=credit):
                    self.assert_diagnostic(
                        document((BASE + " " + ACTIVE).replace(credit, literal(credit))),
                        "missing " + credit.replace(". ", ". (") + ")",
                    )
            for hidden, visible in (
                ("It supplements ODD 2020.", "This extension covers modeled human decisions."),
                ("This extension covers modeled human decisions.", "It supplements ODD 2020."),
            ):
                with self.subTest(delimiter=delimiter, conditional_evidence=hidden):
                    self.assert_diagnostic(document(
                        BASE + " ODD+D is active (Müller et al. 2013). "
                        + literal(hidden) + " " + visible
                    ), "missing explicit supplementation")
            for prose, example in (
                (BASE, "ODD+D is active."),
                (BASE, "ODD+D may be active."),
                (BASE, "This description does not use ODD as its documentation protocol."),
                (BASE + " " + ACTIVE, "ODD+D is not active."),
            ):
                with self.subTest(delimiter=delimiter, inert_example=example):
                    self.assert_passes(document(prose + " " + literal(example)))
            with self.subTest(delimiter=delimiter, ordering="code before comment"):
                self.assert_passes(document(
                    "Use " + literal("<!--") + " as a literal. <!-- real comment --> " + BASE
                ))
            with self.subTest(delimiter=delimiter, ordering="comment before code"):
                self.assert_passes(document("<!-- " + delimiter + " hidden --> " + BASE))

    def test_commented_heading_markers_cannot_consume_visible_prose(self) -> None:
        for level in (1, 2, 3, 6):
            prefix = "<!-- A heading example\n" + "#" * level + " Hidden heading --> "
            with self.subTest(level=level, location="declaration"):
                self.assert_passes(document(prefix + BASE))
            with self.subTest(level=level, location="element body"):
                self.assert_passes(document().replace(BODIES[2], prefix + BODIES[2]))
        # A comment cannot expose a new ATX marker by removing its own prefix.
        self.assert_passes(document().replace(
            BODIES[2], "<!-- hidden prefix --> ## Heading-looking text " + BODIES[2]
        ))
        # A masked Setext underline cannot turn preceding prose into a title.
        self.assert_passes(document(BASE + "\n<!--\n===\n-->"))
        self.assert_passes(document().replace(BODIES[2], BODIES[2] + "\n<!--\n---\n-->"))

    def test_tab_columns_resolve_container_headings_at_one_to_three_residual_columns(self) -> None:
        for template in (
            "- item\n\t# {text}", "-  item\n\t### {text}",
            "1. item\n\t###### {text}", "1) item\n\n\t{text}\n\t---",
            "- item\n\n\t {text}\n\t ===",
            "> - item\n>\t  \t### {text}",
        ):
            with self.subTest(template=template):
                self.assert_diagnostic(
                    document(template.format(text=BASE)),
                    "container-prefixed heading", "missing affirmative use",
                    "missing Grimm et al. (2006)",
                )
        for body in ("- item\n\t ### Detail", "-  item\n\t### Detail", "1. item\n\t###### Detail"):
            with self.subTest(body=body):
                self.assert_passes(document().replace(BODIES[2], body))
                self.assert_diagnostic(document().replace(BODIES[2], body.replace("item", "<!-- hidden -->")), "element 3 has no visible content")

    def test_current_unsupported_input_boundaries_are_diagnostic(self) -> None:
        for body in ("<script\nalert(1)", "<div>text</div>", "</div", "[ref]: https://example.org", "- [ref]: https://example.org", "`unclosed", "```bad`info\n```"):
            with self.subTest(body=body):
                self.assert_diagnostic(document().replace(BODIES[2], body), "line")
        for body in ("Use `model.agents`, ``literal ` marker`` and `<script`.", "See [details](https://example.org) and <https://example.org>."):
            with self.subTest(inline=body):
                self.assert_passes(document().replace(BODIES[2], body))
        for body in ("<!-- unclosed", "```\nunclosed example"):
            with self.subTest(unclosed=body):
                self.assert_diagnostic(document() + "\n" + body, "unclosed fenced block or HTML comment")

    def test_cli_outputs_exit_codes_determinism_and_input_preservation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "ODD.md"
            (root / "notes.txt").write_bytes(b"unrelated user content\n")
            cases = ((document().encode(), 0), (document("").encode(), 1), (b"\xff", 2))
            for content, expected in cases:
                with self.subTest(expected=expected):
                    path.write_bytes(content)
                    path.chmod(0o440)
                    before = {p.name: (p.read_bytes(), p.stat().st_mode, p.stat().st_mtime_ns) for p in root.iterdir()}
                    first, second = run_checker(path), run_checker(path)
                    self.assertEqual(first.returncode, expected, first.stderr)
                    self.assertEqual((first.returncode, first.stdout, first.stderr), (second.returncode, second.stdout, second.stderr))
                    if expected:
                        self.assertEqual(first.stdout, "")
                        self.assertIn(str(path), first.stderr)
                    else:
                        self.assertEqual(first.stderr, "")
                        self.assertEqual(first.stdout, "Extended profile OK; source reading, model fidelity, human behavior, and scientific validity were not checked.\n")
                    after = {p.name: (p.read_bytes(), p.stat().st_mode, p.stat().st_mtime_ns) for p in root.iterdir()}
                    self.assertEqual(before, after)
                    path.chmod(0o600)
            path.write_text(document(""), encoding="utf-8")
            default = run_checker(path, extended=False)
            self.assertEqual(default.returncode, 0, default.stderr)
            self.assertEqual(default.stdout, "Structure OK; meaning, attribution, and scientific validity were not checked.\n")
            self.assertEqual(default.stderr, "")

    def test_cli_invalid_inputs_and_invocations_are_unavailable_not_findings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for path in (root / "missing.md", root):
                result = run_checker(path)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertIn(str(path), result.stderr)
            if hasattr(os, "mkfifo"):
                fifo = root / "ODD.pipe"
                os.mkfifo(fifo)
                self.assertEqual(run_checker(fifo).returncode, 2)
            for arguments in (["--extended"], ["--extended", "one", "two"]):
                with contextlib.redirect_stderr(io.StringIO()) as stderr:
                    self.assertEqual(MODULE["main"](arguments), 2)
                self.assertIn("usage:", stderr.getvalue())
            path = root / "ODD.md"
            path.write_text(document(), encoding="utf-8")
            with patch.object(Path, "read_text", side_effect=PermissionError("denied")):
                with contextlib.redirect_stderr(io.StringIO()) as stderr:
                    self.assertEqual(MODULE["main"](["--extended", str(path)]), 2)
            self.assertIn("denied", stderr.getvalue())
        for arguments in (["-h"], ["--help"], ["--extended", "-h"], ["--extended", "--help"]):
            with self.subTest(help=arguments), patch.object(Path, "read_text", side_effect=AssertionError("read")):
                with contextlib.redirect_stdout(io.StringIO()) as stdout:
                    self.assertEqual(MODULE["main"](arguments), 0)
                self.assertIn("usage:", stdout.getvalue())

    def test_full_copied_skill_is_isolated_and_does_not_create_bytecode(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            copied = root / "standalone"
            shutil.copytree(PACKAGE, copied, ignore=shutil.ignore_patterns("__pycache__"))
            path = root / "ODD.md"
            path.write_text(document(), encoding="utf-8")
            checker = copied / "scripts" / "validate_odd.py"
            before = {str(p.relative_to(copied)): p.read_bytes() for p in copied.rglob("*") if p.is_file()}
            for extended in (True, False):
                result = run_checker(path, checker=checker, extended=extended)
                self.assertEqual(result.returncode, 0, result.stderr)
            after = {str(p.relative_to(copied)): p.read_bytes() for p in copied.rglob("*") if p.is_file()}
            self.assertEqual(before, after)
            self.assertFalse(list(copied.rglob("__pycache__")))
            (copied / "scripts" / "_odd_extended.py").unlink()
            unavailable = run_checker(path, checker=checker)
            self.assertEqual(unavailable.returncode, 2)
            self.assertIn("cannot inspect selected profile", unavailable.stderr)
            self.assertEqual(run_checker(path, checker=checker, extended=False).returncode, 0)


if __name__ == "__main__":
    unittest.main()
