# Development roles and return paths

## Workflow map

The parent owns clarification, assignments, finding disposition and routing.
Children perform only their assigned slice. This map summarizes the ownership
and return paths below; repeat as evidence requires within the agreed budget,
without a fixed number of rounds or an invented finding on a clean first pass.

```text
C: Parent clarifies purpose, sources, authority and bounded contract
   |-- unresolved authority --> evidence / model_spec_analyst --> C
   |                           dependent work waits; unaffected work continues
   `-- resolved --> QA expectations (refactor baseline before production) --> I

I: mesa_model_worker makes change + owner checks
   --> independent_model_qa checks; material geography also gets specialist review
   --> Parent disposes findings
       |-- authority question --> C
       |-- accepted defect --> actual owner corrects
       |                      production: worker; tests/fixtures: QA
       |                      --> affected checks + independent recheck
       |                          + affected specialist recheck --> disposition
       `-- inner work reconciled --> F

F: Final integrated / repository checks on current artifacts
   |-- failure or modifying check --> Parent routes to actual owner --> I
   `-- checked --> fresh mesa_model_reviewer --> Parent disposition
                   (independent of worker and primary QA)
       |-- accepted finding --> C or responsible inner owner
       |                       --> affected checks + independent rechecks
       |                           + affected specialist recheck --> F
       |                       --> fresh outer re-review and disposition
       `-- contract satisfied --> complete; otherwise report incomplete / blocked
```

## Parent and bounded handoffs

The host's main task context coordinates the workflow. Read this reference
before delegating substantive implementation. Establish intent, source
authority, output and protected paths, existing changes, required checks,
allowed commands/temporary outputs, and proportional time/run/iteration limits.
Resolve material choices before dependent edits; continue unaffected useful
work without inventing behavior. Revisit this contract when evidence changes it.

Assign each child one role slice, not the entire development skill. Include the
task, relevant source/model revision or supplied files, applicable local guidance,
acceptance expectations, owned/protected paths and permitted commands/outputs.
For the worker and QA, name the real agent/model/UI/analysis boundaries and
acceptance checks: headless model imports without UI-only dependencies or
execution, preserved refactor baselines, and collection/portrayal that leaves
state and model random streams unchanged. Include applicable source and
geographic semantics; a file list alone is not an architecture target.
The child returns to the parent without recursively building a team. Handoff
does not confer new Git, dependency, network, scientific or correction authority.
Independent contexts must actually work: a role name or a renamed stage in the
same context is not separation. No particular client or telemetry is required.
Report observed assignments and returned work, not an unproved sandbox boundary
or statistical independence of opinions.

## Role briefs

Every return states work performed, changed paths if any, commands actually run
and outcomes (including failures/skips), located findings and their consequences,
open questions and limits. Reviewers return findings in their response, not by
editing the target. The parent can retain a short disposition note when useful.

| Role / activation | Inputs and allowed outputs | Prohibited actions and expected return |
|---|---|---|
| `mesa_model_worker`: substantive production creation/change/refactor | Model contract, sources, existing code, architecture target and QA expectations; writes only assigned production model/agent/app paths and coupled specifications/run instructions | No QA tests/fixtures, scientific target changes or self-certification. Return implementation choices, actual checks, changes and deviations. |
| `independent_model_qa`: substantive writable work; before production for refactor baseline | Contract, source behavior, interfaces, existing tests and baseline; independently writes assigned tests, fixtures and QA utilities; executes bounded checks with declared outputs | No production fixes, copied production logic as an oracle, or weaker expectations merely to pass. Return baseline, independently derived expectations, coverage and behavioral/test-validity findings. |
| `mesa_model_reviewer`: fresh outer instance required; earlier review when source/API/architecture risk warrants | Contract, actual modules, sources, tests, findings/dispositions and integrated check evidence; read-only response | No edits or self-approval. Review source/conceptual fidelity, Mesa APIs, readable boundaries, integration and test validity; reject monolithic or cosmetic splits even with passing tests. |
| `mesa_model_verifier`: conditional execution separation for consequential, stochastic, environment-sensitive or substantial final checks | Agreed commands, environment, revision and acceptance expectations; non-authoring runs may create only declared temporary outputs/caches | No source/test patches, auto-fixes or scientific redesign to obtain a pass. Return exact commands, observations and unavailable checks. Non-authoring execution is not automatically filesystem read-only. |
| `model_spec_analyst`: material intent/source/authority ambiguity | Conflicting source locators, model/specification, rules and fidelity alternatives; read-only response | No file changes, execution that produces outputs, or choice between unresolved scientific authorities. Return alternatives, consequences, governing evidence and the exact decision needed. |
| `mesa_geo_specialist`: material geography only | Integrated contract, code/tests and relevant [geography](geography.md); read-only response | No model/tests/fixtures/docs/experiment edits, correction approval or replacement of primary QA/reviewer. Return CRS/units, representation, geometry/topology, distance/movement/index, raster and provenance findings and exact-version limits. |

Only the applicable roles run. Non-geographic work activates no geographic
specialist or references. A small explanation or read-only clarification need
not use a full team, but substantive implementation and refactoring require
separate worker and QA plus fresh outer review. If required independence cannot
be provided, disclose the missing role/review and useful remaining work; seek
the missing prerequisite when it blocks progress, not an automatic installation
or parent self-review substitute.

## Inner correction loop

1. QA establishes independent behavioral expectations; for a refactor it
   captures baseline/characterization before production changes. The worker
   receives the architecture target in [implementation](implementation.md).
2. The worker makes a bounded change and runs applicable owner-side checks;
   QA independently supplies tests and checks observable behavior. Conditional
   source/geographic review supplements, never replaces, the primary checker.
3. The parent accepts/rejects each finding with a reason and identifies its
   owner. Production defects return to worker; test/fixture defects to QA;
   authority questions to clarification. A finding is not permission to change
   science. Documentation/evaluation outside development ownership is a handoff,
   not an automatic invocation of another installed skill.
4. The responsible owner makes only the accepted correction. Rerun affected
   checks and obtain independent recheck of the correction; affected geographic
   findings also return for specialist recheck. A reviewer who edits cannot
   independently approve that edit. Recheck QA corrections against the contract
   in a non-authoring context rather than letting QA self-certify a faulty oracle.

## Final verification and outer loop

After clean inner work, run relevant integrated/repository checks and verify
implementation against the contract. Compare protected inputs and unrelated
work proportionately; safe check workspaces may have declared outputs/caches.
Inspect unfamiliar commands before running them. Auto-fixes are owner edits,
requiring scope inspection and affected independent rechecks. Prefer check-only
final commands; before/after equality is net preservation evidence, not proof
of no transient writes or OS enforcement.

Assign a fresh `mesa_model_reviewer` context, independent of maker and primary
inner QA, to the integrated result. It checks intent/source/code/specification
agreement, actual agent/model/UI/analysis responsibilities, headless imports,
baseline preservation, state/RNG-neutral observation, omitted requirements,
authority, unrelated work, evidence sufficiency and overclaims. Parent integration
is not independent review. Accepted outer findings return to clarification or the responsible
inner owner; then rerun affected inner checks, independent rechecks, final
verification and a fresh outer re-review. A final checklist alone is not this
return path. A genuinely clean first pass can finish without invented findings.

Stop at task-specific resource/iteration limits; any diagnostic rerun must have
a reason and remaining authority. Report `complete` only when requested work,
valid independent QA, required verification and a clean current outer review
are done. Use `blocked` for a missing prerequisite preventing dependent progress,
or `incomplete` for useful partial work with remaining checks/findings/reviews.
Never equate software verification with scientific validity.
