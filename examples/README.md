# Example and runtime regressions

`core_model.py` is a six-trader conserving-transfer model: every trader starts
with ten units; each step activates traders in random order, transferring one
unit to another trader when possible. It collects initial and post-step totals
and individual wealth. Runs stop at the caller's chosen step count. This is an
API example, not an empirical economic model.

In an authorized project-local environment with the runtime dependencies from
`requirements-examples.txt` and the test dependencies installed, run from this
directory's parent:

```console
python examples/core_model.py
python -m pytest -m runtime
```

The example prints nine total-wealth observations, all 60. Core tests check
registration, conservation, seed replay, collection, and invalid inputs. The
geographic tests use synthetic geometry and in-memory rasters to check the
documented Mesa-Geo 0.9.3 caveats, including explicit nodata and mask ownership.
No external GIS data or network service is used.

Rasterio 1.5.1 with Affine 3.0.1 emits pending-deprecation warnings from its
`from_bounds` implementation. The regressions leave these upstream warnings
visible; their presence does not change the numeric assertions.

The non-runtime suite can collect without Mesa or GIS dependencies:

```console
python -m pytest -m "not runtime"
```

These are direct software regressions. They do not demonstrate that a client
invoked or followed a skill, validate a scientific model, or complete the wider
cross-skill workflow assessment. The geographic tests' nodata/mask round trip
uses [Rasterio's explicit mask API](https://rasterio.readthedocs.io/en/stable/topics/masks.html)
and [in-memory files](https://rasterio.readthedocs.io/en/stable/topics/memory-files.html).
