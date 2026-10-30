# Evaluation report

Adapt the sections to the authorized operation and available evidence. Keep one
Markdown results narrative; use no parallel notebook account. Reports with no
quantitative evidence need not include figures or plotting code.

## Model and environment identity

Record the evaluated model revision, relevant configuration, environment
description, and links to the model specification and provenance artifacts.

## Methods and provenance

Describe scenarios, parameters, seeds or sampling, repetitions, comparison
targets, outputs, metrics, diagnostics, exclusions, stopping criteria, commands,
and analysis revision. Link raw and derived outputs without replacing them with
the narrative summary.

## Results by applicable operation

Use only headings that apply:

- implementation-verification audit;
- calibration;
- validation evidence;
- sensitivity and uncertainty;
- robustness;
- convergence and stopping; and
- replication fidelity.

For each operation, connect evidence to the planned claim and preserve negative,
failed, blocked, discrepant, or inconclusive results alongside positive results.

Embed selected generated PNGs using paths relative to this report. For example,
in `docs/evaluation_results.md` (replace this example with a real figure):

```markdown
![Scenario estimates and uncertainty][scenario-figure]

[scenario-figure]: figures/scenario-estimates.png
```

Each figure needs a short interpretation and limitations, readable units,
uncertainty type, sampling unit and relevant sample sizes or incomplete coverage.
Keep zero, missing and unfavorable results visible; do not imply complete paired
comparisons from unequal samples. Include vector exports only when useful.

## Reproduction and checks

Link the actual reusable Python analysis and plotting code and identify saved
plotting inputs, their provenance and required optional analysis dependencies.
Give the actual headless project-root regeneration command and figure destination,
using project-relative paths. State whether regeneration uses a fresh destination
or an explicitly authorized set of derived figures. Preserve raw and accepted
analysis outputs. Explain how permitted inputs can be obtained and any access
limits without copying confidential data or bulk histories.

Report scoped quality and numerical checks, rendered readability inspection,
independent analyst findings and dispositions, and fresh inference and outer
review of the integrated report. Disclose failed or unavailable checks and
unfinished work. Include only checks relevant to the operation; audit-only
does not regenerate or repair the protected target.

## Discrepancies and limitations

Report source or implementation discrepancies, missing evidence, invalidated
assumptions, access constraints, sensitivity to choices, and threats to the
intended interpretation.

## Bounded conclusions

State only conclusions supported for the declared purpose and evidence. Passing
software tests can support implementation verification but never establishes
scientific validity.
