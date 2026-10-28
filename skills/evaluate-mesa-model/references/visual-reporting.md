# Visual reporting from saved analysis

For substantive quantitative evaluation or authorized reanalysis, normally
deliver reusable Python analysis/plotting code under `evaluation/`, one Markdown
results narrative under `docs/`, and selected static figures under
`docs/figures/`. Preserve a meaningful existing layout and create only useful
modules. These are conventions for the evaluated model project, not directories
to add to the skill repository. Use Python and Markdown, not notebooks, Jupyter
dependencies, dashboards or browser apps.

Planning proposes useful views, required inputs and interpretation rules without
fabricating results. Audit-only inspects existing evidence without creating or
regenerating target artifacts. Small, non-quantitative or evidence-limited work
need not manufacture charts or install plotting tools.

## Keep statistics in the analysis

Prefer a focused module such as `evaluation/plot_results.py` with reusable
functions and an explicit entry point. Read saved analysis results. Keep
estimation, pairing, exclusions and uncertainty methods in the analysis
implementation; plotting may load, reshape and perform documented display-unit
conversions without duplicating that analysis.

Plotting must not import or run the scientific model, fit parameters, fetch
missing data, silently rerun experiments or write files on import. Missing
inputs are a disclosed limitation, not authority to reconstruct unobserved
results or launch simulations. Preserve raw and accepted analysis outputs.

Prefer Matplotlib with a restrained Seaborn theme, respecting project style.
Apply styling inside plotting calls or contexts, for example
`with sns.axes_style("whitegrid"), sns.plotting_context("paper"):`; do not change
global styling on import. Draw saved estimates and interval endpoints directly
with Matplotlib primitives. Do not impose an additional statistical method just
to draw error bars. Seaborn functions can aggregate, bootstrap or fit by default:
for example, `lineplot` defaults to a mean and bootstrapped confidence interval.
If used for already-computed values, disable estimation and interval calculation
(`estimator=None, errorbar=None`) and preserve the intended ordering and gaps.
Never silently smooth, aggregate or replace the agreed analysis.

Consult the current official documentation for
[style contexts](https://seaborn.pydata.org/tutorial/aesthetics.html),
[error-bar semantics](https://seaborn.pydata.org/tutorial/error_bars.html) and
[`lineplot` behavior](https://seaborn.pydata.org/generated/seaborn.lineplot.html)
when selecting calls or resolving version differences.

## Show the question and its limits

Select a small set of views that answers the question: distributions,
comparisons, trajectories or sensitivity as applicable. There is no universal
figure menu or count. Use readable labels, units, captions, appropriate scales
and consistent scenario encodings; distinguish scenarios with markers, line
styles or direct labels as well as color. Identify the uncertainty type and
independent sampling unit, and show sample sizes or incomplete coverage where
they affect interpretation.

Preserve zero, unfavorable and missing results. Do not conceal important
intervals, replace missing values with zero, silently interpolate gaps or imply
that unequal or incomplete samples form complete paired comparisons. Explain
missing observations and unavailable comparisons in the figure or adjacent
text. Display choices must preserve the analysis and its limitations.

## Deliver and regenerate

Embed selected PNGs with report-relative links, short interpretations and
limitations. For a report at `docs/evaluation_results.md`, an illustrative image
path is `figures/scenario-estimates.png`; see the
[report template](../assets/evaluation_report.md) for Markdown syntax. Use actual
generated filenames and meaningful alt text. Vector exports are
useful when publication or editing calls for them, not a second required set.

Document the actual project-root regeneration command, required saved inputs,
their provenance and the project's optional analysis environment. For example,
if the delivered entry point accepts these arguments:

```sh
MPLBACKEND=Agg python evaluation/plot_results.py --input results/estimates.csv --output-dir docs/figures/report-01
```

Replace example paths and options with those the delivered code actually uses;
avoid personal absolute paths. Run headlessly and close figures after saving.
Use a fresh figure destination or explicitly authorized regeneration of
designated derived figures. Do not silently replace unrelated or historical
results. Keep compact plotting inputs when sharing is permitted, or explain
how to obtain them and any access-related reproduction limit. Do not copy
confidential data or bulk histories to make a report self-contained.

Keep plotting dependencies in the target project's appropriate optional
analysis environment, within authorized setup. Installing this skill must not
install plotting tools or modify the user's Python environment. Apply the
[scoped quality checks](project-quality.md) to authored code and documents.

## Check through the existing roles

The `experiment_designer` owns plotting code, figures and the narrative. The
independent `evaluation_analyst` compares plotted values, interval endpoints,
labels and claims with their saved inputs and agreed analysis. Inspect rendered
figures for readability, clipping and misleading scales as well as numeric
correspondence. Reproduction that writes files or caches belongs in a
parent-arranged authorized location; the analyst remains read-only. Fresh
inference and outer review include the integrated visual report, using the
existing correction and recheck paths in [the workflow](workflow.md).
