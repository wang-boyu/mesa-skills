# Choose methods for the claim

## Sampling and reproducibility

Define the independent unit before computing uncertainty. Agents, cells and
successive timepoints within one run are generally not independent replications.
For independent run summaries, sample variance uses n − 1 and estimated standard
error of the mean is s / √n. Dependence, pairing, unequal weights or time-series
structure may require a different calculation.

Independent run means [2, 4] give mean 3 and SE 1. Repeating each value four times
does not create eight independent runs; the smaller naive SE is misleading.
An all-equal sample has zero estimated sampling variation, not proof that input,
parameter or structural uncertainty is absent.

Decide how to handle empty samples, missing/nonfinite observations, failed runs,
duplicate records and zero denominators. Retain exclusions and explain their
effect; never silently clip, impute or drop adverse evidence. Repeated runs need
model revision, seeds, dependency versions and execution order sufficient for
reproduction. Same-seed replay checks repeatability in that environment, not
robustness over random outcomes.

Confidence intervals need assumptions appropriate to the sampling design.
Small n does not establish normality or accurate coverage. A frequentist
confidence level describes repeated-sampling coverage of the procedure, not a
posterior probability for the realized interval. See
[NIST's mean-interval discussion](https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm).
Use domain-appropriate replication or dependence-aware methods rather than a
fixed count. Bootstrap the actual sampling unit, not correlated rows.

## Calibration and assessment

Specify objective, parameters, bounds, selection method, initializations,
calibration data, stopping rule and budget before fitting. Keep attempted
candidates and failures, not only the selected optimum. Discuss weak
identification, nonunique fits and parameter uncertainty.

Keep assessment observations out of parameter selection, preprocessing fitting,
metric selection and stopping decisions when claiming held-out assessment.
Using assessment results to tune changes that design. If reuse is intentional,
disclose it and narrow the claim. Training fit is not independent validation.
The [scikit-learn leakage guidance](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage)
explains this principle; using that library is not required.

## Sensitivity, uncertainty and robustness

Tie comparisons to an observable and purpose. Sensitivity considers effects of
parameter or design changes, including relevant interactions; one-at-a-time
changes do not cover interactions. Separate Monte Carlo noise from uncertain
inputs, measurements, parameters and structural assumptions. Pair random streams
only when justified and account for pairing in analysis.

Robustness concerns conclusions across relevant changes of seeds, schedules,
assumptions, inputs, metrics or representation. Report adverse regions and
uncertainty in differences, preserving comparable units and denominators.
A synthetic oracle checks calculation or implementation behavior; it is not
empirical evidence of a model's adequacy.

## Convergence, stopping and fidelity

Distinguish warm-up bias, time-horizon effects, Monte Carlo precision,
optimization progress and spatial resolution. State which convergence question
is tested and compare suitable diagnostics. Termination, a smooth plot or one
favorable comparison does not establish convergence. At the budget limit,
report unresolved precision or convergence honestly.

For replication, name the comparator and fidelity target: conceptual rules,
implementation, qualitative patterns, distributions or quantitative outcomes.
Record source discrepancies and differences in initialization, process order,
parameters, measurements and geography. Similar means can hide different
mechanisms, extremes and failure rates. State what agreed, what differed and
which conclusions remain unsupported.
