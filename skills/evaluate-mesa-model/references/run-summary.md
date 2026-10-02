# Optional independent-run summary

Use this standard-library helper only for finite, equally weighted, independent
numeric run summaries. It reads a JSON array from one UTF-8 regular file without
editing it, importing a model or running simulations. It requires Python 3.12
or newer.

From this skill's directory:

```sh
python scripts/summarize_runs.py /path/to/run-values.json
```

For [2, 4], output has n = 2, mean = 3, sample standard deviation = √2 and standard
error = 1. The sample standard deviation uses n − 1; standard error is s / √n.
The helper rejects fewer than two values, booleans, strings, missing/nonfinite
numbers and nonfinite results. Exit 0 prints JSON; exit 1 reports unsuitable data;
exit 2 reports an unreadable file or invalid invocation.

It cannot establish independence, decide exclusions, account for weights or
dependence, or provide a justified confidence interval. Do not pass repeated
timepoints or individual agents as independent runs without a suitable design.
Record units, run identities, failures and exclusions alongside the input;
those facts are not contained in the numeric array.
