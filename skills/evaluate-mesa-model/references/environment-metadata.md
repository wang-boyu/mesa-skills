# Optional environment metadata report

Use the local [reporter](../scripts/inspect_environment.py) when a small,
repeatable record of the selected interpreter's package metadata helps the
task. Existing adequate environment information, `python --version` or normal
`python -m pip show` inspection may be sufficient; ordinary work does not
require this utility.

Run it with the intended environment's Python and the actual installed skill
path. For example, from this skill's directory:

```sh
python scripts/inspect_environment.py
python scripts/inspect_environment.py --geo --json
```

The default reads **Mesa** and **NetworkX**, in that order. Explicit `--geo`
adds **Mesa-Geo, NumPy, GeoPandas, Shapely, pyproj, Rasterio, Rtree, libpysal,
affine and xyzservices**, in that order. The only options are `--geo`, `--json`
and help. Python implementation/version comes from `platform`; selected
distribution versions come from `importlib.metadata.version`.

Both output modes render the same collected data. JSON contains `python`
(`implementation`, `version`) and `distributions`, keyed by the names above.
Each distribution has `present`, `state` and `version`:

| State | Present | Version observation |
| --- | --- | --- |
| `available` | `true` | Printable, nonblank metadata string, preserved verbatim; no version parsing. |
| `absent` | `false` | `null`; the lookup raised `PackageNotFoundError`. |
| `blank` | `true` | `null`, empty string or whitespace-only string, retained as received. |
| `unprintable` | `true` | `null`; nonblank text is not printable or conversion to text failed. |
| `failed` | `null` | `null`; another lookup exception left presence unknown. Remaining selected reads continue. |

Nonstrings other than `None` are safely converted to text before classification.
Blankness is checked before printability. Text quotes and escapes values and
spells unknown presence as `unknown`; JSON uses `null`. Neither format exposes
exception payloads or tracebacks. JSON uses two-space indentation and sorted
keys; key order does not change lookup order.

Exit **0** means the report completed, including absent, blank or unprintable
metadata. Exit **2** means a selected read failed (with a partial report and
concise stderr diagnostic), invalid CLI usage, or inability to collect/render
a report. Missing packages alone do not fail the utility. It emits no
compatibility verdict and applies no version policy.

This standard-library helper does not import Mesa, GIS libraries or model code,
run subprocess probes, access the network, inspect environment variables, list
all packages, install dependencies or write files. Metadata does not establish
importability, binary compatibility or runtime behavior; those need separate,
authorized evidence. Version-matched modeling guidance remains separate.
