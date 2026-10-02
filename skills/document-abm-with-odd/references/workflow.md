# Documentation roles and return paths

The parent must read and use this reference for substantive documentation and
complete audit work. The host's main task context coordinates; children receive
only the relevant local role brief, evidence and assigned slice. They return
their work without restarting the whole workflow or recruiting another team.

## Workflow maps

The parent owns clarification, assignments, dispositions and every return path.
The maps summarize the contracts below; audit-only remains a separate evidence
workflow. Iterate only as needed within the agreed scope and budget, with no
fixed round count or mandatory correction on a clean first review.

```text
C: Parent clarifies operation, authority, evidence and bounded contract
   |-- unresolved authority --> evidence / model_spec_analyst --> C
   |                           dependent work waits; unaffected work continues
   `-- writable contract --> I

I: odd_documenter writes + author checks --> independent odd_auditor checks
   + material geography gets independent specialist review
   --> Parent disposes findings
       |-- authority question --> C
       |-- accepted documentation defect --> documenter correction
       |-- evidence / checker gap --> responsible intake / auditor
       |   Both returns --> affected checks + independent auditor recheck
       |                    + affected specialist recheck --> disposition
       `-- inner work reconciled --> F

F: Final integrated documentation / repository / preservation checks
   |-- failure or modifying check --> Parent routes to actual inner owner --> I
   `-- checked --> fresh odd_auditor --> Parent disposition
                   (independent of documenter and primary auditor)
       |-- accepted finding --> C or responsible inner owner
       |                       --> affected checks + independent rechecks
       |                           + affected specialist recheck --> F
       |                       --> fresh outer re-review and disposition
       `-- contract satisfied --> complete; otherwise incomplete / blocked
```

```text
Audit-only: no maker, no target correction
A: Parent takes in protected evidence / clarifies authority
   --> independent odd_auditor + applicable specialist --> Parent disposition
       |-- evidence / authority gap --> intake / clarification / assigned reviewer
       |                              --> independent + affected specialist recheck
       |                              --> A (reconciled evidence)
       `-- inspection reconciled --> final evidence / preservation checks
           --> fresh outer odd_auditor (independent of primary auditor)
           --> Parent disposition
               |-- accepted coverage / evidence gap --> A --> rechecks
               |   --> final checks --> fresh outer re-review
               `-- requested audit complete --> report findings, including defects
Target repair needs separate authorization and a new writable contract.
```

## Contract and handoffs

Before dependent work, reconcile the requested create/update/audit/summary
outcome with source authority and the existing model. Agree the evidence and
model revision, output paths, protected prose and unrelated work, audience,
traceability expectations, ODD+D decision, material geography, applicable
repository checks and their write behavior. Bound time and correction rounds
proportionately. A material unresolved rule or source choice returns to parent
clarification; continue unaffected work without inventing that decision.

Give each child a concise assignment containing its role and task, relevant
model/source revision and locators, local instructions to read, acceptance
expectations, writable/protected paths, and allowed commands and temporary
outputs. For example, an auditor needs the description, actual model modules,
source/specification evidence and check results, with an explicit read-only
assignment. It should not receive an expected favorable verdict.

Every role returns work performed, evidence used, checks actually run and their
results, located findings and consequences, and open questions. A writer also
returns changed paths. The parent accepts, rejects or defers findings with
reasons and routes each to its responsible owner. No universal report schema
is required. Roles below are responsibilities assigned to separate contexts,
not a promise that any particular client has native agents with these names.

## Local role briefs

### `odd_documenter`

Activate for full ODD create/update and substantive writable summaries. Input
is the bounded documentation contract, evidence, actual implementation modules,
existing ODD and accepted correction findings. Write only assigned ODD, summary
or directly coupled documentation paths; author-side structural/semantic checks
and authorized formatters or auto-fixes on those paths belong here. Return the
artifact, changes, traceability, checks, protocol/ODD+D decision, uncertainties
and discrepancies. Do not repair the model, tests, data, sources or evaluation
results, make an unresolved scientific choice, or certify independent review.

### `odd_auditor`

Activate as the independent inner checker for writable work, the primary
audit-only evidence reviewer, or a fresh outer reviewer as assigned. Input is
the contract, current document, source/model evidence, author checks, and, for
outer review, integrated changes and prior dispositions. Produce read-only
findings in the response; no file writes, formatting, fixes, generated reports,
caches or safe-copy creation. Inspect ODD 2020 attribution and seven elements,
conditional ODD+D, source fidelity, process order, units, initialization,
time-varying inputs, stochasticity, observation and major submodels. Trace the
actual agent.py/agents.py/agents/, model.py, optional app.py and relevant
space, process, data, metrics or analysis modules without restructuring them;
follow scheduling, observation and raw-to-derived evidence across interfaces.
Distinguish protocol defects, stale claims, missing authority, contradictions, overclaims
and preferences; return locators, consequences and what would resolve each.
Report unavailable evidence instead of approving an uninspected claim. Never
act as a second author or fix a document and independently approve that fix.

### `model_spec_analyst`

Activate only for material ambiguity in intent, source authority, entities,
rules, scales, scheduling or evidence interpretation. Input is the disputed
claims with source locators, model/specification excerpts and the parent's
question. Return read-only analysis of alternatives, supporting evidence and
their documentation consequences. Write no files and run no models or
write-producing checks. Do not choose an unresolved user/scientific decision,
authorize correction, or replace the documenter, auditor or geographic review.

### `mesa_geo_specialist`

Activate only when geographic behavior or claims are material. Input is the
assigned geographic slice, contract, actual spatial model/source evidence,
integrated ODD and local [geography guidance](geography.md). Independently review
CRS, axes, units, distance and area methods, geometry, topology, predicates and
boundaries, movement/index behavior, raster alignment/nodata, spatial inputs,
provenance and exact-version limitations as applicable. Return read-only
located findings, effects on the integrated seven elements, and evidence gaps.
Write no model, tests, ODD, data, experiments, reports, caches or safe copies;
run no experiments or write-producing verification. Do not settle authority,
replace the primary auditor or own completion. Non-geographic work does not
activate this role or load GIS references merely because Mesa-Geo is installed.

## Writable inner loop

1. The parent gives `odd_documenter` the bounded contract; the documenter writes
   the assigned document and runs applicable author-side checks.
2. A separate `odd_auditor` inspects the actual artifact and evidence. Material
   geography receives an additional independent specialist review.
3. The parent disposes findings with evidence. Accepted documentation defects
   return to `odd_documenter`; missing evidence returns to intake/auditor;
   source ambiguity returns to clarification or `model_spec_analyst`.
   Production/test defects go to the implementation owner and analysis defects
   to the evaluation owner as evidence handoffs, without authorizing repairs.
4. The documenter makes accepted in-scope corrections and reruns affected
   structural, semantic, traceability and repository checks. Obtain independent
   auditor recheck and, for a geographic correction, affected specialist
   recheck. Do not weaken a valid expectation or rewrite scientific intent to
   make the document appear consistent. Repeat within the agreed limits.

## Final checks and outer loop

After inner findings are reconciled, inspect the integrated document, changed
paths and protected inputs. Run applicable final repository and documentation
checks before each outer review. The optional local structure checker assesses
only its [documented profile](structure-checker.md); an unsupported Markdown
feature needs manual structural inspection, not an unauthorized rewrite.

Keep check outputs/caches explicitly scoped. A final check that modifies the
reviewed artifact returns to the documenter: inspect its effect, rerun affected
checks, obtain independent recheck, then rerun final checks on the corrected
state. A before/after comparison is useful preservation evidence but does not
prove that no transient write occurred. No reviewer applies an auto-fix.

A fresh `odd_auditor` context independent of both the documenter and primary
inner auditor then checks integrated intent/source/model/document agreement,
readability and traceability across actual modules, missing requirements,
contradictions, scope, unrelated-work preservation and unsupported claims.
The parent coordinates this review and cannot substitute its own assessment.

Accepted outer findings return to clarification, documenter, auditor, evidence
intake or the applicable analyst/specialist. The responsible owner resolves the
finding; affected inner checks and independent rechecks run, final integrated
checks run again, and a fresh outer context re-reviews the current result.
Renaming the same maker or inner checker does not make a fresh context. A clean
first review may finish without correction; do not manufacture iterations.

## Audit-only evidence loop

Preserve the target ODD, model, tests, sources and unrelated files. No
`odd_documenter` is assigned and no target correction occurs. The parent takes
in evidence, assigns read-only `odd_auditor` and material specialist review,
disposes findings, then sends evidence gaps to intake, the auditor, specialist
or source clarification for reconciliation and independent recheck.

Run checks on the target only when their invocation is established to be
non-mutating. Otherwise the parent may arrange a bounded safe copy in an
authorized location for inspected checks, with declared outputs/caches; the
auditor and specialist remain read-only. Unexpected target/copy changes are
failure evidence, never authorized correction or a passed preservation check.
If no safe method exists for a required check, disclose the missing inspection.
A separately authorized external audit report may be written by the parent
outside the protected target; that does not make the auditor an artifact editor.

Final evidence and preservation checks precede a fresh outer `odd_auditor`,
separate from the primary auditor, reviewing the audit's coverage, findings,
evidence sufficiency and honesty. Accepted outer gaps return through evidence
intake/clarification, independent recheck and final checks, then fresh outer
re-review. They never activate a maker. An audit can complete while reporting
defects, including structural failures, if the requested inspection and reviews
are complete. Missing inspection is different from an inspected defect.

Corrections require separate authorization. Preserve original findings, end
the audit-only workflow and agree a new writable contract before assigning a
documenter; do not erase the original audit conclusions.

## Completion

For writable work, complete means the requested document, required checks,
accepted corrections and independent inner/outer reviews satisfy the contract.
For audit-only, it means the requested audit is complete, not that its target is
correct. A small clarification can remain a small response, but substantive
writable work and complete audits cannot use that exception to omit reviewers.
When required independent contexts, authority or checks are unavailable, state
which work did not occur: return `incomplete` with useful partial work, or
`blocked` when the missing prerequisite prevents meaningful progress. Report
exhausted limits and unresolved findings rather than continuing indefinitely.
Observed separate work is not proof of OS-enforced permissions or independent
opinions, and establishes no client support or scientific validity.
