# Optional ODD Markdown checks

Use these checks when they help inspect a full ODD. Both profiles are optional;
a limited summary does not require a full conforming document or a checker pass.
Run with Python 3.12 or later from this skill's directory:

```sh
python scripts/validate_odd.py /path/to/ODD.md
python scripts/validate_odd.py --extended /path/to/ODD.md
```

The first command retains the default structure check. The second explicitly
selects the extended syntax and declaration checks below. `--help` describes
the default invocation; `--extended --help` describes the extended invocation.
Python callers can use `validate_text(text)` or `validate_text(text, extended=True)`;
each returns a tuple of deterministic diagnostics.

Both use only the standard library and read one regular UTF-8 file. They never
write the document, import or run a model, install dependencies, access the
network, resolve citations, or execute document content. Keep the shipped
`scripts/_odd_extended.py` beside the entry point when copying the package.

## Default profile

The default checks the template's seven numbered level-two headings in order,
at most one leading level-one title, subordinate heading placement, and
non-heading text in each element. Extra unnumbered level-two sections are
allowed after element 7 and terminate its body. Use:

- Column-zero ATX headings (`# Title`, `## 1. Purpose and patterns`), with
  level-three through level-six subsections inside the elements or appendix.
  Labels use the template's wording; trailing spaces or closing hash marks work.
  Appendix headings must not start with a digit.
- Unindented paragraphs, flat lists, and pipe tables. Inline code spans must
  open and close on the same line with matching backtick delimiters.
- Column-zero backtick or tilde fences, with at least three marks and a matching
  closer of at least the opener's length. Fence examples supply no headings or
  section text. Backtick fence info cannot contain backticks.
- Standalone HTML comments starting at column zero and ending with `-->` at the
  end of a line. Comments supply no headings or section text.

Indented lines outside fences/comments, blockquotes, nested lists or headings,
Setext headings, raw HTML or inline comments, and reference-link definitions
produce an unsupported-profile diagnostic. HTML tag starts ending at a line
break, such as `<script`, are also rejected. Use inline links. A bare line of
hyphens or equals signs is rejected to avoid Setext ambiguity. Every fence and
comment must close.

Each section needs a non-heading line containing a letter, number, or underscore
outside comments and fences. This catches empty sections, not unfinished thought:
placeholder prose, false statements, and irrelevant text can pass. The default
does not check English declarations, citation strings, or ODD+D activation.

## Extended Markdown profile

The extended profile retains the seven exact numbered element labels in order.
They must be root, column-zero ATX level-two headings; container headings,
indented headings, and Setext headings cannot replace them. Closing hash marks
are compared using their normalized label, so `## 5. Initialization ###` works.

Additional supported forms are:

- Root ATX headings at levels one through six with up to three structural
  indentation columns, and practical two-line Setext level-one/two headings
  (a text line immediately followed by an `===` or `---` underline).
- Recursive, mixed blockquotes (`>`), bullet lists (`-`, `+`, `*`), and ordered
  lists with one through nine digits followed by `.` or `)`. List continuation
  indentation remains active across blank lines. Blockquotes need explicit
  markers; lazy quote continuation is outside the recognized container grammar.
  Partial dedents retain surviving outer containers. Tabs use four-column stops
  measured from the physical line origin. Zero through three residual columns
  can introduce structural syntax; four or more cannot.
- Root and container-relative fences. Openers use at least three matching
  backticks or tildes; closers use the same marker, at least the opener's length,
  and no trailing info. Backtick opener info cannot contain a backtick. A
  container fence ends on a nonblank dedent or sibling item, and that physical
  line is processed again in its surviving context. Any fence still active at
  end of input, or any unclosed comment, produces a diagnostic.
- Inline and multiline HTML comments. Comments and fences are masked without
  joining physical lines. Removing a comment cannot manufacture a heading.
  Four-column pseudo-fences/comments cannot hide later real headings.

At most one root ATX or Setext level-one title may lead the document. Root
unnumbered ATX or Setext level-two appendices may follow element 7. Every root
level-two heading ends the preceding element's body, including an invalidly
placed heading. Container level-one/two headings are invalid at every position.
Level-three through level-six subsections may occur inside elements/appendices,
including containers, but cannot precede element 1. Bare grouping labels
“Overview,” “Design concepts,” and “Details” at levels two through six cannot
substitute for numbered elements.

Every element needs visible non-heading text after masking headings, comments,
fences, and **all** standalone bracket-only prompt blocks. Multiline or repeated
`[replace this prompt]` blocks supply no content; prose around brackets does.
Container markers alone supply no content. This corrects the former behavior
that removed only a final bracket prompt and compared raw closing-hash headings.
Raw HTML, reference-link definitions, invalid backtick fence info, and unclosed
inline code remain diagnostic. This is a closed profile, not full CommonMark:
indentation beyond the recognized structural range is treated as nonstructural
text, not as another supported heading or masking form.

## Extended opening declarations

Only visible non-heading prose **before element 1** supplies declaration evidence.
All classified heading spans are excluded, including invalid/container headings
and both Setext lines. Comments, fenced examples, closed inline code spans, later
body text, and bibliography credits cannot fill a missing opening declaration or
activate ODD+D. Inline code still supplies literal section-body content.
Recognition is case-insensitive and uses a closed grammar of short, local
relations, not a general English parser.

The base declaration needs recognized affirmative document-to-protocol use, a
`2020` token, the words `second update`, and both Grimm et al. credits. Recognized
relations include a document/description/model or “we” that uses/adopts/follows/
applies the ODD protocol; uses/adopts ODD as its documentation protocol; is/was
documented according to ODD; is/was described using, structured under, or organized
according to the ODD protocol or ODD as a documentation protocol; and ODD being
used/applied/adopted/followed as the documentation or model-description protocol.
The implementation also recognizes the corresponding short ODD-is-protocol forms
and local referential “it” forms. Negative, modal, and context-only statements
cannot establish affirmative use. Recognized affirmative and negative statements
in the opening conflict, including when distributed across sentences.

For example:

> This description uses ODD as its documentation protocol, specifically the
> ODD 2020 second update (Grimm et al. 2006; Grimm et al. 2020).

Required credits recognize `Grimm et al. 2006`, `Grimm et al., 2006`,
`Grimm et al. (2006)`, and `Grimm et al., (2006)`, with the corresponding four
forms for 2020. Author and year must match; DOI-only strings and wrong authors
cannot supply these credits. Separate `2020` and `second update` tokens are
simple declaration checks, not proof of an applied version or coherent meaning.

Every ODD+D-bearing opening sentence is classified using recognized forms:

- Affirmative: ODD+D is/was/remains optionally “explicitly” active/applied/used/
  activated; ODD+D applies to; or this/the document/description/model or “we”
  apply/use/activate/adopt ODD+D (including third-person verb forms).
- Negative: explicit not-active/not-applied/not-used/not-activated or inactive
  forms; do/does/did/will not apply/use/activate/adopt; and never-apply/use/activate/
  adopt forms. Recognized affirmative and negative declarations conflict.
- Contextual: short described/discussed/mentioned/cited/referenced/considered or
  context-only relations. Modal or otherwise unrecognized extension language
  produces an indeterminate-declaration diagnostic.

An active, noncontradictory extension additionally needs Müller et al. (2013),
using the same punctuation families and the accented author name, affirmative
supplementation of ODD 2020, and an affirmative extension-to-human-scope relation.
Human scope recognizes modeled/modelled human decisions, decision-making,
decision making, or a decision component, optionally preceded by material or
substantial. The extension must cover/document/address/represent that scope,
be active for it, apply to it, or supplement ODD 2020 for it. These statements
may be distributed across the opening; “It” can supply human scope only with a
current or prior recognized active extension. Human keywords alone, a model's
scope alone, or supplementation only as protocol context do not suffice.

> ODD+D is active. It supplements ODD 2020. This extension covers material
> modeled human decision-making (Müller et al. 2013).

Absent, negative, and context-only extension declarations require no Müller
credit. These string relations do not prove that human decisions occur in the
model or establish whether the extension is scientifically appropriate.

## Outcomes and inspection limits

Exit `0` means the selected profile passed; `1` means structural, declaration,
or unsupported-syntax diagnostics; `2` means invalid invocation, nonregular or
unreadable/non-UTF-8 input, or unavailable inspection of the selected profile.
A FIFO is rejected before reading it. A diagnostic includes the inspected path;
unsupported syntax calls for manual inspection and does not itself establish a
defect in a legitimate ODD. An unavailable check is not a pass or a document
finding. Preserve audited targets instead of rewriting them to satisfy this tool.

Neither profile establishes source reading, accurate attribution beyond recognized
strings, source-to-code fidelity, semantic correctness, human behavior, or
scientific validity. The independent ODD auditor and fresh outer review remain
necessary for substantive work. Report the selected profile and its actual result
alongside the human/model evidence review, preserving unresolved limitations.
