# Optional source and experiment-provenance validation

Use this helper when an evaluation uses the existing structured YAML provenance
format and mechanical checks are useful. A proportional table or run log may be
sufficient for another task. Do not create manifests, empty outputs or invented
observations merely to satisfy a layout. The experiment designer owns authorized
provenance creation and correction; the independent analyst reviews its evidence.
An audit reports defects and does not authorize correction.

Adapt the optional [experiment provenance template](../assets/experiment_provenance.yaml),
replacing its example values and removing irrelevant optional collections. The
local [provenance schema](../assets/experiment-provenance.schema.json) defines the
existing YAML format. Supplied source references use the local
[source schema](../assets/sources.schema.json); no companion skill is required.
When the task adopts this YAML contract and validation is available, check newly
created or changed records before handing them off. Report unavailable validation
accurately; it does not authorize dependency installation or fabricated evidence.

Use an authorized Python environment containing the
[optional PyYAML and jsonschema dependencies](../validation-requirements.txt).
Install dependencies only in an appropriately authorized project environment.
Neither installing the skill nor using its other tools requires them. From the
installed skill directory:

```sh
python scripts/validate_artifacts.py /path/to/artifact-directory
python scripts/validate_artifacts.py /path/to/artifact-directory --require-provenance
```

Only `sources.yaml` and `experiment_provenance.yaml` in that directory are read;
other filenames are not discovered. Either optional artifact may be absent by
default. Use `--require-provenance` when the agreed operation requires that file.
The helper uses only its own schema assets, reads without editing artifacts,
imports no model, executes no recorded command and accesses no network. Help
works without the optional dependencies.

It checks:

- duplicate YAML keys, the closed version-1 schema and nonblank fields;
- unique source and run IDs within their respective documents;
- unique input IDs per run and unique output IDs across that run's raw and
  derived output collections;
- within-run output references and acyclic derived-output lineage, including
  rejection of self-reference;
- declared input source IDs against the local source inventory;
- status values: planned, running, complete, failed, blocked and incomplete;
- fixed-seed, seed-set, sampled, replayed and not-applicable randomness shapes;
- exclusion reasons and optional nonempty unique record-ID lists; and
- available/protected/unavailable locator shape and access notes.

Fixed seed requires exactly one seed; seed set requires one or more. Sampled
requires seeds, a description, or both. Replayed requires a description and may
include seeds. Not-applicable omits seeds. An available locator requires a value;
protected or unavailable locators omit it and require a non-sensitive access note.

Exit 0 is a silent structural pass. Exit 1 reports sorted, location-bearing
parse, schema or reference errors. Invalid invocation or unavailable optional
dependencies exits 2. Missing or invalid local schema assets fail inspection;
they never produce a passing result.

Structural success does not show that a run occurred or completed, validate
status transitions, infer planned counts, inspect actual locator targets or
hashes, resolve excluded record IDs against data, establish a scientifically
appropriate seed policy or justify a claim. Output references remain within a
single run; input and output IDs are separate namespaces. The independent
analyst must check actual attempts, failures, exclusions, raw-to-derived
transformations and conclusions against the design and original evidence.
Preserve originals and use separate authorized outputs for reanalysis. Keep
unavailable evidence and limitations explicit.
