---
name: evaluate-mesa-model
description: >-
  Plan, audit, run authorized bounded evaluations, or reanalyze outputs from
  Mesa agent-based models. Use for reproducibility, calibration, sensitivity,
  uncertainty, purpose-specific assessment and replication fidelity, including
  material geography. Production-model changes and ODD authoring are separate tasks.
metadata:
  version: "0.1.0"
  maturity: "experimental"
---

# Evaluate a Mesa model

Answer a purpose-specific question with checkable evidence and bounded
conclusions. A useful evaluation may find a model inadequate, reject a
hypothesis, or remain inconclusive. This Experimental skill does not establish
scientific validity or supported-client status.

## Coordinate the required roles and loops

The host's main task context is the parent. Before assigning substantive work,
read and use the local [workflow and role briefs](references/workflow.md), including
the [writable and audit-only flow diagrams](references/workflow.md#workflow-maps).
Use available native subagents or explicitly identified separate contexts for
bounded assignments. A delegated child handles its assigned slice and returns;
it does not restart this skill or recursively create a team.

- `experiment_designer` is the writable maker for authorized evaluation plans,
  experiment/analysis code, derived outputs and reports. Planning, execution
  and reanalysis each require a separate read-only `evaluation_analyst` to check
  design, run accounting, calculations and interpretation.
- Audit-only uses `evaluation_analyst` for independent evidence review, with
  no maker or correction of the protected model, data or report.
- Read-only `model_spec_analyst` supplies material source/model-authority
  analysis. Independent read-only `mesa_geo_specialist` reviews material
  geographic semantics and evidence, supplementing the primary analyst.
  Neither resolves an unanswered scientific choice or writes artifacts.
- A fresh `evaluation_analyst`, independent of the maker and primary inner
  checker, performs final inference review and outer scope/evidence review.
  One fresh context may cover both only when it reports both functions
  explicitly. Audit-only reviews the audit's conclusions and coverage.

The parent clarifies the contract before dependent work. The inner loop is
maker work → applicable checks → independent findings → parent disposition →
accepted corrections to the owner → affected checks and independent recheck.
Audit-only instead loops through evidence intake, review, disposition and
clarification/recheck. After final integrated checks, fresh inference and outer
reviews can return findings to clarification or the responsible inner role;
affected checks and independent rechecks, final checks, and fresh final reviews
must then run again. A clean first pass needs no manufactured finding.

A small explanation or read-only clarification may need no team; substantive
evaluation plans, execution, reanalysis and complete audits require independent
contexts. If required independence, authority, evidence or checks are missing,
report `incomplete` for useful partial work or `blocked` for dependent work that
cannot proceed. Do not substitute parent self-review, silently install a client,
or claim that role assignment proves enforced permissions or client support.

## Establish what is authorized

Infer the requested operation from the task:

- **Planning:** explain questions, methods, resources, outputs and interpretation
  rules. Do not run simulations or fit parameters.
- **Audit:** inspect supplied evidence and report located findings. Preserve the
  audited model, data and report. An external audit report needs an allowed
  destination; an audit does not authorize correction or new experiments.
- **Execution:** run the agreed experiment or analysis within explicit model,
  input, parameter, compute, storage and stopping limits. Preserve failed attempts.
- **Reanalysis:** calculate from existing outputs into separate derived files.
  Do not silently rerun simulations, overwrite originals or change their run facts.

Use the model specification, code, sources, tests, ODD and earlier results that
are available. Neither a full ODD nor another installed skill is a prerequisite.
Distinguish intended behavior from implemented behavior and observed evidence.
Identify conflicts that would change the question or interpretation; request the
controlling decision rather than choosing the most favorable interpretation.
Missing evidence can limit a claim without preventing useful planning or audit.

Read target repository rules, preserve unrelated work and identify output paths.
Inspect unfamiliar commands and executable model inputs, including imports,
before running them. Execution needs appropriate authority; approval to analyze
is not approval to download data, install dependencies, change production rules
or spend additional resources. Use the intended isolated environment, inspect
declared and installed versions, and consult matching primary API documentation.
Missing runtime dependencies need not prevent static work.
Use the optional [metadata reporter](references/environment-metadata.md) when
a small environment record helps; existing adequate information or normal
Python/pip inspection is also sufficient.

## Design evidence for the question

Write a short design, using the optional [plan](assets/evaluation_plan.md)
when helpful. State:

1. Intended use, question, model revision, comparator and what would count
   as useful evidence or an important discrepancy.
2. Observables, units, independent sampling units, scenarios, parameter ranges,
   initial conditions, seeds or replay strategy, and relevant replications.
3. Metrics, missing/nonfinite-value treatment, exclusions, comparison tolerances,
   uncertainty methods, required observations and stopping or budget limits.
4. Which data and choices are for calibration and which are for assessment.

Choose from [evaluation methods](references/evaluation-methods.md) where
relevant. Verification asks whether implementation follows its specification;
a verification gap is not repaired by a good empirical fit. Calibration chooses
parameters against evidence. Assessment asks how well a model serves a stated
purpose. Sensitivity, uncertainty, robustness, convergence and replication
fidelity answer different questions; no fixed method menu or replication count
is universally sufficient.

For material geographic behavior, read [geography](references/geography.md).
Keep its semantics in the same evaluation. Check CRS, axes, units, projection
distortion, predicates, boundaries, movement/index consistency, raster
alignment and nodata, and spatial-data provenance. Quantify consequences for
counts, distances, exposure, area and uncertainty rather than merely listing
spatial terms. Nearby agents or cells need not be independent assessment units.
Consider spatial grouping, aggregation and edge effects where relevant.
Non-geographic work needs no GIS imports or artifacts; do not replace an
unavailable geographic model with a different plain-Mesa problem.

## Execute or reanalyze without changing the question

Use public model parameters and existing experiment interfaces. If behavior
cannot be varied without editing production rules, report the needed development
change rather than patching the model to improve the result. Documentation
discrepancies likewise require a separately authorized ODD edit.

Keep generated experiment and analysis code maintainable: separate model
construction/run orchestration, meaningful input preparation, and statistical
analysis responsibilities when they grow, using existing project conventions
or focused `experiments.py`, `data.py` and `analysis.py` modules as appropriate.
Do not pack sweeps and inference into a production model class or duplicate
scientific rules in a runner. Use the model's public API; keep imports free of
simulation, fitting, output writes and UI startup. Executable work needs an
explicit entry point. Keep parameters, seeds, units, observation timing and
raw-to-derived transformations inspectable; avoid mutable globals, circular
imports, long multipurpose functions and cosmetic or empty module splits.
Explain a nontrivial chosen layout briefly in existing project notes.

Record practical provenance: model and analysis revision, input identities and
origins, relevant environment, commands, parameters, seeds, attempts, failures,
exclusions and output locations. A small table or run log is often sufficient;
there is no universal manifest or hashing requirement. Retain raw observations
needed for the planned analysis, not only attractive plots or final averages.
Keep originals separate from derived tables and document transformations,
units, missing-value decisions and access or redistribution limitations.
When the task adopts or produces supported YAML evaluation records, use
[optional artifact validation](references/artifact-validation.md) where
available and report invalid or unavailable validation honestly. Ordinary
evaluation needs no YAML, added dependencies or format conversion. The supplied
provenance example illustrates the supported format; it records no observations.
A validation pass proves neither execution nor scientific adequacy.

Check planned, attempted, usable, failed and excluded runs against actual
records. Explain any rerun and preserve its predecessor. Do not keep changing
seeds, metrics or stopping thresholds to hunt for significance. Obtain authority
for changes to the scientific target, protected inputs or execution budget.
Never reconstruct missing measurements as if they had been recorded.

## Check and communicate

Have the independent analyst derive expectations from the design and raw
evidence, using a separate formula or simple known-answer example; calling the
maker's function to assert its own result is insufficient. Check denominators,
sampling units, physical units, nonfinite values and
uncertainty assumptions. The optional [summary helper](references/run-summary.md)
calculates mean, sample standard deviation and standard error from independent
run summaries; it neither establishes independence nor runs a model.

For writable work, the parent disposes findings with reasons and sends accepted
evaluation corrections to the maker. Rerun affected checks and obtain
independent analyst and applicable specialist rechecks, then final repository, numerical,
run-accounting and preservation checks before fresh inference and outer reviews.
Use the ownership and return paths in the required workflow reference. For
audits, use only non-mutating checks against the target, or a parent-arranged
authorized safe copy; do not silently transition into correction.

Use the optional [report](assets/evaluation_report.md) to explain what was
actually done, results including failures and unfavorable findings, uncertainty,
limitations, changed files and unfinished work. Distinguish a completed audit
from a correct audited report, and a reproducible calculation from scientifically
adequate evidence. Bound every conclusion to the model, question, design and
observations actually examined.
Return `complete` only when the authorized outcome, required checks, inner
rechecks, inference review and outer review are complete. An audit may complete
with evidence-backed target defects, but missing required inspection is not a
pass. Missing authority or capability and exhausted agreed limits must leave
the dependent work explicitly `blocked` or `incomplete`.
