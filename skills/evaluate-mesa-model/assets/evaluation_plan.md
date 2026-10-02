# Evaluation plan

Use only the evaluation operations needed for the stated purpose. Calibration,
validation evidence, sensitivity, uncertainty, robustness, convergence, and
replication fidelity are distinct operations; none is mandatory merely because
this template names it.

## Purpose, claims, and scope

State the intended use, claims to assess, relevant model revision, active
capabilities, exclusions, and limitations known before experiments begin.

## Applicable operations

Mark the operations that apply and explain why:

- [ ] implementation-verification audit
- [ ] calibration
- [ ] validation evidence
- [ ] sensitivity and uncertainty
- [ ] robustness
- [ ] convergence and stopping
- [ ] replication fidelity

## Experiment design

For each applicable operation, connect the claim or purpose to the planned
evidence:

| Operation or claim ID | Scenarios and parameters | Seeds, sampling, and repetitions | Comparison target | Outputs and metrics | Diagnostics | Exclusions | Stopping or sufficiency criterion |
|---|---|---|---|---|---|---|---|

Document configuration ranges rather than only selected values. Identify raw
and derived outputs separately and state how run provenance will be recorded.

## Interpretation rules

Define how results will be interpreted, including what would weaken a claim,
trigger a targeted rerun, expose an unsupported inference, or leave the work
blocked or incomplete. Software-test success alone must not be treated as
scientific validation.
