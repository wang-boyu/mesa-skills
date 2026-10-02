---
name: document-abm-with-odd
description: >-
  Create, update, audit, or summarize an agent-based model description using
  ODD 2020, with ODD+D for material human decisions and geographic guidance
  when relevant. Use code, specifications, sources, or existing documentation.
  Documentation does not authorize model changes or new experiments.
metadata:
  version: "0.1.0"
  maturity: "experimental"
---

# Document an ABM with ODD

Produce a readable account of the model that distinguishes what is intended,
what is implemented, and what is unknown. This skill works independently with
existing models and documentation; no previous development workflow is needed.
This Experimental skill has no supported client. Documentation quality does
not establish scientific validity.

## Coordinate the required roles and loops

The host's main task context is the parent. Before assigning substantive work,
read and use the local [workflow and role briefs](references/workflow.md), including
the [writable and audit-only flow diagrams](references/workflow.md#workflow-maps).
Delegate bounded slices through available native subagents or explicitly
identified separate contexts. A delegated child performs its assigned role and
returns; reading this skill does not ask it to restart the workflow or assemble
another team.

- For create, update, and substantive writable summaries, `odd_documenter`
  writes authorized documentation and a separate read-only `odd_auditor`
  checks protocol, semantics, source fidelity, and traceability.
- For a complete audit-only workflow, `odd_auditor` is the primary read-only
  evidence reviewer; there is no documenter or target correction.
- Use read-only `model_spec_analyst` for material source/model-authority
  ambiguity, and independent read-only `mesa_geo_specialist` when geography
  is material. The specialist supplements the auditor; neither chooses an
  unresolved scientific rule or owns documentation changes.
- After inner work and final checks, a fresh `odd_auditor` context independent
  of both documenter and primary auditor performs outer consistency review.
  In audit-only work it reviews audit completeness and honesty.

The parent clarifies scope and authority before dependent work. The inner loop
is documenter work → checks → independent auditor findings → parent disposition
→ accepted corrections to the documenter → affected checks and independent
recheck. Audit-only uses evidence intake, independent review, disposition and
evidence clarification/recheck while preserving the target. The outer loop is
final integrated checks → fresh review → parent route-back → affected inner
rechecks → final checks → fresh outer re-review. Accepted findings must take
those return paths; a clean first pass needs no invented correction round.

A small explanation or read-only clarification may need no team; substantive
documentation and complete audits require these independent contexts. If one
is unavailable, disclose the missing review and return useful partial work as
`incomplete`, or `blocked` when no meaningful authorized progress remains.
Self-review cannot satisfy that missing review, and role assignment does not
prove technical permission enforcement or client support.

## Establish the evidence

Infer create, update, audit, or summary from the request. Identify the model
and revision being described, the audience, desired detail, available evidence,
and output location. Use repository conventions or `docs/ODD.md` for a new full
description. Read target repository rules and applicable quality commands
before editing; inspect unfamiliar executable commands before running them.
Preserve unrelated changes and protected prose. Keep all actions within the
user's authorization.

Accept inputs directly from conversation, attachments, files, sources, model
specifications, production code, tests, and existing evaluation reports. A
prepared manifest is unnecessary. Inspect relevant behavior and retain useful
locators: source pages, code symbols or lines, dataset versions, and decisions.
Do not copy protected source material or infer redistribution rights.

Code shows implemented rules; a specification or author explains intent and
rationale; tests describe checked behavior; experiment results support only
their stated conclusions. An existing ODD may be stale. Label discrepancies
such as “the specification calls for simultaneous updates; the code updates
agents sequentially.” Do not silently reconcile them, invent missing rationale,
or turn an assumption into an observation. Ask for a decision only when it
prevents useful progress; otherwise document the uncertainty and its effect.

## Write the seven elements

Use the ODD 2020 second update and read the focused
[protocol and attribution guidance](references/odd-protocol-and-attribution.md).
Begin a full description with a short protocol statement crediting Grimm et
al. (2006) and Grimm et al. (2020). The [full template](assets/ODD.md) supplies
the seven numbered elements and prompts; replace prompts with model content.

1. **Purpose and patterns:** the intended questions, uses, and patterns used
   to assess relevance, with limits on the claims the model can support.
2. **Entities, state variables, and scales:** agents, collectives, environment,
   variables and units, and temporal and spatial resolution and extent.
3. **Process overview and scheduling:** who does what, in which order, when
   changes become visible, activation and update semantics, and stopping.
4. **Design concepts:** the applicable concepts and design rationale, including
   emergence, interaction, adaptation, stochasticity, and observation.
5. **Initialization:** the starting population, environment, parameter values,
   placement, randomness, and static files used to construct the initial state.
6. **Input data:** external inputs that vary during a run and their timing and
   transformations. State when there are none; distinguish initial data.
7. **Submodels:** rules, equations, parameters, random draws, algorithms, and
   consequential edge cases in enough detail for the requested audience.

Place code pointers near material claims without replacing explanations with
code dumps. Document known rationale and supporting evidence alongside the
relevant rule. For complex models, use subsections and references to detailed
algorithms; keep the complete model understandable from the full description.
Trace the model's actual agent.py/agents.py/agents/, model.py, optional app.py
and relevant space, process, data and metrics modules, including where scheduling,
observation and raw-to-derived evidence cross their interfaces. Do not
rename or reorganize a user's implementation during documentation; report a
structure problem with its effect on traceability and route it to development.

Use ODD+D only when modeled human decisions materially shape the model. Explain
the triggering component, cite Müller et al. (2013), and integrate relevant
decision concerns into the same seven elements. Geography, non-human adaptation,
or algorithmic learning alone does not trigger ODD+D.

When geography matters, read [geography](references/geography.md) and integrate
CRS, axes, units, geometry, movement, predicates, boundaries, raster alignment,
and spatial-data provenance into the same ODD. Missing GIS dependencies may
limit executable verification while still allowing useful static description.
Preserve spatial behavior and evidence gaps. Non-geographic work needs no GIS
references, tooling, or artifacts.

## Deliver the requested outcome

**Create:** assemble the full ODD from available evidence. Clearly identify a
description of a proposed model when implementation is absent. Unknown details
can remain explicit; do not present an incomplete account as replication-ready.

**Update:** compare the existing ODD with current evidence and revise stale or
authorized content. Preserve authorship and unrelated style. Check affected
elements together: a scheduling change may also affect submodels and design
concepts. Explain material differences and unresolved conflicts.

**Audit:** preserve the target ODD, model, tests, sources, and unrelated files.
Return findings with locators, evidence, consequences, and suggested corrections;
distinguish defects from preferences and unavailable evidence. Run only checks
known to be non-mutating on the target, or inspect and run them on a safe copy.
Report unexpected changes as failed preservation evidence. An audit finding
does not authorize correction. Completing an audit does not mean its target is
correct.

**Summary:** derive a concise account from the full ODD, link to it, and retain
material assumptions and limitations. If the available ODD is partial or stale,
label the summary's limits. The documenter may adapt the optional
[summary](assets/ODD_SUMMARY.md) to the audience and available evidence, retaining
its link to the full description. Do not silently repair the source document or
imply that the summary replaces a full ODD.

## Check and hand off

Compare the description with the actual evidence for process order, units,
randomness, initialization, inputs, observables, and major rules. Check
attribution and conditional ODD+D manually. Follow the required documenter,
auditor and outer loops above, including affected specialist rechecks. A
documentation finding returns to the documenter; an evidence or authority gap
returns to intake or clarification. Report what each review actually examined.

The optional [Markdown checker](references/structure-checker.md) finds heading
and empty-section mistakes in its default narrow profile. Explicit `--extended`
selection adds a broader closed Markdown profile and checks recognized opening
protocol, citation, and conditional ODD+D declaration strings. Neither profile
proves source reading, source fidelity, human-decision behavior, semantic
correctness, or scientific validity. Distinguish document diagnostics from
unsupported syntax and unavailable inspection; inspect valid documents manually
when their style is outside the profile. A limited summary needs no full ODD
or checker pass before the authorized summary work can proceed.
Run applicable repository checks and inspect the final documentation diff and
protected inputs before each outer review. Keep auto-fixing commands within
documenter ownership. In writable work, a modifying final check returns through
the inner loop; in audit-only work it remains failure evidence and follows the
evidence loop without activating a documenter.

Deliver the requested document, findings, or summary, with evidence used,
important gaps, checks performed, and limitations. For substantial unresolved
questions, the documenter can adapt the optional [gap record](assets/odd_gaps.md)
in an authorized documentation path, or keep its useful fields beside the
relevant ODD element. Audit-only reviewers return those fields in their response;
only the parent may write a separately authorized external audit record. Remove
unused prompts and avoid duplicate records. Documentation does not authorize
model changes or new experiments. Return implementation issues
to development and requests for new analyses to evaluation, with their evidence;
neither handoff requires another installed skill. Use `complete` only when the
requested outcome, required independent reviews, accepted corrections, affected
rechecks and final checks are complete. A complete audit may retain located
target defects; missing required audit evidence is `incomplete` or `blocked`,
not a passed audit. Unresolved authority, unavailable review or checks, and
exhausted agreed limits prevent completion of the dependent work.
