# Invented saved-estimate reporting exercise

These values and intervals are invented test inputs, not observations from a
scientific model. The plotting code reads accepted estimates directly from
`results/estimates.json`; no estimation, pairing or simulation occurs here.

![Saved scenario means and confidence intervals](figures/estimates.png)

The points show saved mean score changes; bars show supplied 95% confidence
interval endpoints. For this invented example the sampling unit is an independent
run, and the declared method is a bootstrap interval calculated upstream.
Reference is zero with interval [-1, 1]; Lower is -2 with interval [-3, -0.5].
The scenario labels show available/planned sample counts. Lower has 6/8 runs;
Unavailable has 0/8 and no estimate or interval. No missing value is drawn as
zero, and these unequal samples are not presented as paired comparisons.
This exercise supports no substantive model inference.

From the project root, using an environment with Matplotlib and Seaborn:

```sh
python evaluation/plot_results.py --output-dir docs/figures
```

The input JSON is compact, fully invented and retained for reproducibility.
The destination must be unused. To regenerate without changing the original
figure, choose a fresh directory, for example `docs/figures-repeat`, and update
the report link if selecting that new figure. No raw or accepted outputs are
overwritten.
