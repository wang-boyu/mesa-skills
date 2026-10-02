# Evaluation roles, ownership and return paths

The parent must read and use this reference for substantive evaluation and
complete audit work. The host's main task context coordinates bounded separate
contexts, supplies relevant local briefs and evidence, integrates results and
disposes findings. A child performs its assigned slice and returns; reading
the skill does not ask it to repeat the full workflow or assemble another team.

## Workflow maps

The parent owns clarification, assignments, dispositions and every return path.
These maps summarize the contracts below. Repeat when evidence requires it
within the agreed scope and budget; there is no fixed round count and a clean
first pass needs no invented finding.

```text
C: Parent clarifies operation, scientific authority, design and bounded contract
   |-- unresolved authority --> evidence / model_spec_analyst --> C
   |                           dependent work waits; unaffected work continues
   `-- writable contract --> I

I: experiment_designer makes plan / authorized runs / reanalysis + owner checks
   --> independent evaluation_analyst + applicable geographic specialist
   --> Parent disposes findings
       |-- authority question --> C
       |-- accepted artifact defect --> experiment_designer correction
       |-- evidence / checker gap --> responsible intake / analyst
       |   Both returns --> affected checks + independent analyst recheck
       |                    + affected specialist recheck --> disposition
       `-- inner work reconciled --> F

F: Final integrated numerical / run-accounting / repository / preservation checks
   |-- failure or modifying check --> Parent routes to actual inner owner --> I
   `-- checked --> fresh evaluation_analyst --> Parent disposition
                   (independent of maker and primary analyst)
                   1. inference review
                   2. outer scope / evidence review
       |-- accepted finding from either --> C or responsible inner owner
       |   --> affected checks + independent + affected specialist rechecks --> F
       |   --> fresh inference AND outer re-reviews --> disposition
       `-- both reviews satisfy contract --> complete; else incomplete / blocked
```

```text
Audit-only: no maker, simulations or target correction
A: Parent takes in protected evidence / clarifies authority
   --> independent evaluation_analyst + applicable specialist
   --> Parent disposition
       |-- evidence / authority gap --> intake / clarification / assigned reviewer
       |   --> independent + affected specialist recheck --> A
       `-- inspection reconciled --> final numerical / evidence / preservation checks
           --> fresh evaluation_analyst (independent of primary auditor)
               1. audit inference review; 2. audit scope / evidence review
           --> Parent disposition
               |-- accepted gap from either --> A --> rechecks --> final checks
               |   --> fresh inference AND outer re-reviews
               `-- requested audit complete --> report findings, including defects
Target repair needs separate authorization and a new writable contract.
```

## Contract and handoffs

Before dependent writing or execution, agree the requested planning, audit,
execution or reanalysis outcome; purpose, claims and controlling source
authority; model and input identities; observables, units, comparison and
independent sampling units; metrics, uncertainty, exclusions and stopping;
authorized paths, commands, temporary outputs and compute/storage limits;
applicable repository checks and their write behavior; and independent review
expectations. Keep the design proportional and freeze material choices before
their use. Missing or conflicting authority returns to parent clarification;
do not select a favorable interpretation. Continue unaffected authorized work.

Each handoff states the role and bounded task, relevant model/source/analysis
revision and evidence, local instructions, acceptance expectations, protected
and writable paths, allowed commands and outputs. Give checkers original
records and design assumptions from which to derive expectations, not only
the maker's computed answers. Each role returns work performed, checks actually
run, evidence-backed findings with locators and consequences, and open
questions; the maker also returns changed paths and run/output accounting.
The parent accepts, rejects or defers findings with reasons and assigns their
owner. No schema or native named-agent installation is required for a handoff.

## Local role briefs

### `experiment_designer`

Activate as the writable maker for substantive planning, authorized bounded
execution or reanalysis; never for audit-only. Input is the agreed design,
public model interface, inspected executable sources, original evidence and
accepted findings. Write only assigned plans, experiment/analysis code,
authorized outputs, provenance and reports, including owner-side checks and
in-scope auto-fixes. Planning runs no simulations or fitting; reanalysis uses
existing raw outputs and separate derived paths, with no model simulations.
Neither mode needs model imports to perform its work. Execution performs only
agreed runs and retains failed attempts. Return changed paths, design and
provenance, attempts/results, checks, limitations and unresolved findings.

Do not edit production rules, production tests, source data, existing raw
evidence or ODD documents, duplicate rules in experiment code, exceed agreed
resources or alter the scientific target for a favorable result. Use the
model's public API; needed production/ODD corrections are separate handoffs.
In the maker assignment, identify actual experiment orchestration, input
preparation, metric calculation and inference modules and their public model
interfaces. Preserve meaningful existing boundaries; imports must not run
simulations, fit parameters, start a UI, require UI-only dependencies or write
outputs. Observation and metric collection must leave model state and model
random streams unchanged. For authorized experiment-code refactoring, preserve
baseline inputs, outputs, run order and scientific interpretation. Do not certify
your own work as independently checked or reviewed.

### `evaluation_analyst`

Activate as the independent inner checker, primary audit-only evidence
reviewer, or fresh final inference/outer reviewer as assigned. Input is the
design and authority, model/analysis evidence, raw records, all run attempts,
derived outputs and claims; final review also receives integrated changes,
check results and prior dispositions. Produce findings only in the response:
write no files, reports, caches or safe copies, apply no fixes and run no
simulations or write-producing computations. Necessary reproduction with
outputs is arranged by the parent in a separately authorized location.

Independently check design, fit/assessment separation, sampling units,
run accounting, failures, exclusions, formulas, denominators, physical units,
nonfinite/missing values, uncertainty and interpretation. Derive important
expectations with independent arithmetic/formulas or known-answer cases from
raw evidence; a call to the maker's function is not an independent oracle.
Return located findings, acceptance expectations, reproducibility limitations
and what conclusions the evidence can support. Do not fix and approve your
own correction, settle an unanswered scientific choice, or replace material
geographic specialist review.

### `model_spec_analyst`

Activate only for material ambiguity in source/model/scientific authority,
purpose, hypotheses, fidelity target, estimand or interpretation. Input is the
disputed choice, relevant source locators and model/evidence excerpts. Return
read-only analysis of alternatives, evidential support and consequences for
the evaluation. Write no files, run no models or write-producing computation,
and do not choose the unresolved user/scientific decision or authorize work.
The parent obtains controlling direction; this role does not replace the maker,
primary analyst or geographic specialist. Geography or missing runtime alone
does not trigger source-authority analysis.

### `mesa_geo_specialist`

Activate only for material geographic design or evidence. Input is its
assigned geographic slice, agreed design, spatial model/data/calculations and
the local [geography guidance](geography.md). Independently review CRS, axes,
units, transformations, geometry/topology, predicates and boundaries,
movement/index semantics, raster alignment/nodata, provenance and version
limitations; examine spatial sampling units, dependence, leakage, aggregation
and valid-area denominators as applicable. Return read-only located findings,
quantitative consequences and missing evidence. Write no model, tests, data,
ODD, experiments, outputs, reports, caches or safe copies and run no experiments
or write-producing checks. It neither settles authority nor owns general
inference or completion, and supplements rather than replaces the analyst.
Non-geographic work needs neither this role nor geographic references.

## Writable inner loop

1. The maker produces the agreed plan, executes only the agreed bounded runs,
   or reanalyzes existing outputs, then performs applicable owner-side checks.
   Preserve originals, failed attempts, unfavorable results and required raw
   observations; planning produces no fabricated run evidence.
2. A separate read-only analyst reviews design, calculations, accounting and
   claims. Material geography also receives independent specialist review.
3. The parent disposes findings. Accepted evaluation artifact defects return to
   `experiment_designer`; checker evidence gaps return to the analyst/intake;
   source-authority questions return to clarification or `model_spec_analyst`.
   Route production/test defects to implementation and ODD defects to
   documentation with evidence; that handoff is not repair authorization.
4. The maker corrects accepted in-scope defects and reruns affected checks;
   obtain independent analyst recheck and affected geographic specialist
   recheck. Do not weaken an expectation or change the target to pass.
   A diagnostic rerun states the question, changed code/input/design if any,
   affected run set, expected evidence and remaining budget, and preserves its
   predecessor. Planning still runs no simulations/fitting and reanalysis no
   new simulations. Stop at agreed scope/resource limits without seed hunting.

## Final verification, inference and outer loop

After inner work is reconciled, run applicable final repository, numerical,
run-accounting, reproducibility and protected-input checks. Check current
artifacts, not just an earlier maker result. Test/reproduction execution may
write outputs or caches; inspect commands and keep those in declared locations.
The maker owns artifact-changing checks and fixes. If a final command modifies
the artifact being reviewed, return to owner correction, affected checks and
independent recheck, then rerun final verification on the resulting state.
Before/after equality is net preservation evidence, not proof of no transient
write. Reviewers remain non-authoring.

Assign a fresh `evaluation_analyst` context independent of the maker and primary
inner checker to these two explicit functions; one fresh context may do both:

- **Inference review:** what follows from the actual design and evidence?
  Examine unsupported certainty, dependence, leakage, exclusions, seed/metric
  selection, weak convergence and unperformed work presented as observations.
- **Outer scope/evidence review:** does the integrated result respect user
  intent, source authority, model/report agreement, maintainable experiment
  structure across actual model/runner/data/metrics/analysis interfaces,
  headless imports, baseline preservation and state/RNG-neutral observation,
  ownership, changed paths, protected inputs, unrelated work, missing requirements
  and bounded conclusions?

The parent coordinates and disposes these findings but cannot certify its own
integration as independent. Accepted findings from either final review return
to clarification, the responsible maker, primary analyst, evidence intake or
conditional reviewer. Rerun affected inner checks and independent rechecks,
then final integrated checks, then fresh inference and outer re-reviews. Both
current final reviews must satisfy the contract; a checklist or second summary
does not replace this actual return path. A clean first pass needs no invented
finding. Renaming the same effective context does not make it independent.

## Audit-only evidence loop

No maker, simulations or target correction. The parent preserves supplied
model, data, raw outputs, report and unrelated work; takes in evidence; assigns
the independent read-only analyst and applicable conditional reviewers; then
disposes findings. Evidence gaps return to intake, the analyst, specialist or
source clarification for reconciliation and independent recheck. They cannot
activate `experiment_designer` or silently amend the target.

Run only established non-mutating invocations against the target. Otherwise
the parent may arrange an authorized bounded safe copy and inspected checks
with declared outputs/caches; the analyst/specialist creates or mutates no copy.
Unexpected target/copy modification is failure evidence, not an authorized
correction or passed preservation check. An unavailable safe method leaves the
required inspection incomplete. The parent may write a separately authorized
external audit report outside the protected target without turning the analyst
into an artifact editor.

Final evidence, numerical and preservation checks precede fresh inference and
outer reviews separate from the primary auditor. Review the audit's claims,
coverage, evidence sufficiency and honesty, not an assumption that its target
is sound. Accepted outer gaps return through evidence intake/clarification,
independent recheck and final checks, then fresh final re-reviews. An audit may
complete with evidence-backed target defects; missing required inspection is
different from an inspected failed check. A correction needs separate authority:
retain original findings, end audit-only work and agree a new writable contract.

## Completion and unavailable independence

The parent reports the authorized operation, actual work/runs and failures,
artifacts, findings/dispositions, checks, inner rechecks, distinct inference and
outer outcomes, and limitations. Complete writable work requires its requested
outcome and current checks/reviews; a complete audit can retain defects in the
audited report. Useful partial work with missing reviews, evidence or exhausted
limits is `incomplete`; a missing prerequisite preventing meaningful dependent
work is `blocked`. Disclose exactly what did not occur rather than treating
blocking as successful experimentation.

A genuinely small explanation or read-only clarification need not launch a
team. That exception does not cover substantive plans, execution, reanalysis
or complete audits. When independent contexts are unavailable, do useful safe
work, disclose the unperformed review and do not substitute self-review or
automatically install a client. Observed role work does not prove OS permission
enforcement, independence of opinions, native integration or scientific validity.
