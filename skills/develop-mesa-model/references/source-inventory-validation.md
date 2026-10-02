# Optional source inventory validation

Use a structured source inventory when stable source identities and automated
checks are useful. Existing project records may be sufficient; do not require a
manifest before intake or create one solely to run this helper. The model maker
owns authorized inventory creation and correction. Independent review checks
its claims and source authority; an audit reports defects without changing it.

Adapt the optional [sources.yaml template](../assets/sources.yaml), replacing
its example values and removing irrelevant optional fields. The existing YAML
format is defined by the local [source schema](../assets/sources.schema.json).
The format does not require copying protected source content into the project.
When the task adopts this YAML contract and validation is available, check newly
created or changed inventories before handing them off. Report unavailable
validation as an inspection limitation; it does not authorize installation.

The helper needs PyYAML and jsonschema. Use an already authorized environment
containing the [optional dependencies](../validation-requirements.txt), or obtain
permission for the relevant project-local dependency installation. Installing
this skill or using its other guidance does not require those dependencies.
From the installed skill directory:

```sh
python scripts/validate_sources.py /path/to/sources.yaml
```

The supplied path may have another filename. Validation reads one UTF-8 regular
file using the schema beside this installed skill; it does not search sibling
skills, import a model, execute source commands, access the network or edit the
inventory. Help works without the optional dependencies.

The helper checks duplicate YAML mapping keys, values outside the strict JSON
domain, schema version and field shapes, nonblank required fields, allowed source
kinds and roles, unique source IDs and unique roles. Available locators require
a nonblank value and may include an access note. Protected or unavailable
locators require a nonblank access note and omit the value.

Exit 0 is a silent structural pass. Exit 1 reports invalid content with sorted,
location-bearing diagnostics. Exit 2 means inspection could not run, including
invalid invocation, missing dependencies, unavailable input or an invalid local
schema. Record an unavailable inspection accurately; it is not a pass.

The helper does not dereference locators, verify hashes, inspect a source map,
determine source authority or validate the selected interpretation. A permitted
locator, version or hash declaration is not evidence of actual access or source
fidelity. Review these separately using the
[source-grounded development guidance](source-grounded-development.md).
