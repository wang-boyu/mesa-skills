# Mesa implementation and refactoring

## Establish the execution context

Inspect project constraints, lock files, the Python interpreter, and installed
package metadata before choosing APIs. Ordinary `python --version` and
`python -m pip show mesa networkx` can identify a selected environment without
importing model code. The optional [metadata reporter](environment-metadata.md)
provides a small text/JSON record without importing those libraries; adequate
existing information is also sufficient. Inspect only relevant packages; add
Mesa-Geo inspection only for geographic work. Metadata alone does not prove imports or a model run
succeed. Mesa 3.5.x top-level imports need NetworkX; the official `network`
extra provides it when an isolated installation is authorized.

The intended runtime is CPython 3.12–3.14 and Mesa 3.5.x. Match non-obvious
behavior to the installed release's source and official documentation. Do not
mix examples from older schedulers or unreleased Mesa versions into that
target. New execution on a different version needs its own checks; static
analysis can still identify migration work without claiming compatibility.

## Mesa 3.5 patterns

Initialize every model with `super().__init__`, passing an integer seed through
`rng=seed` for new code. Use model-owned `random` and `rng` for their respective
Python and NumPy draws. Supplying both `seed` and `rng` is invalid; the `seed`
keyword emits a future warning. New agent constructors call
`super().__init__(model)`, which registers the agent and assigns a model-global
ID. Keep source identifiers separately and use `agent.remove()` for model
deregistration, coordinating any space cleanup. Do not overwrite `model.agents`
or manually change its registration collection. These behaviors are defined
in the [Mesa 3.5.1 model source](https://mesa.readthedocs.io/v3.5.1/_modules/mesa/model.html).

Choose activation from the model specification: `agents.do("step")` preserves
collection order; `agents.shuffle_do("step")` randomizes it. Synchronous rules
need a compute phase based on old state followed by a commit phase; shuffling
does not make sequential state changes simultaneous. Explicitly order stages
and types, and select only intended active entities. See the
[Mesa 3.5.1 activation tutorial](https://mesa.readthedocs.io/v3.5.1/tutorials/2_agent_activation.html).

Use `AgentSet.to_list()` when positional access is necessary. Public
`Model.run_for`, `run_until`, and event-scheduling methods are available in
3.5; preserve event priority, tie order, time meaning, and the task's stopping
behavior when using them. Do not assume every advancement method honors a
custom stop flag identically. Review migration effects in the
[Mesa 3.5.1 migration guide](https://mesa.readthedocs.io/v3.5.1/migration_guide.html)
and verify them in the selected environment.

Collection and portrayal should observe state without consuming model random
draws or changing behavior. Specify whether data are collected initially,
before or after each update, and at termination. Retain the observations needed
by the intended analysis; final aggregates cannot recover an unrecorded
trajectory. Choose public space and collection APIs that match the model and
installed release; inspect warnings instead of suppressing unfamiliar ones.

## Preserve behavior during refactoring

Give production and QA owners the structure target before work. For a
nontrivial model, a useful starting layout is:

```text
project/
|-- agents.py              agent state, decisions and interactions
|-- model.py               initialization, activation, shared state and services
|-- app.py                 optional UI composition and portrayal
`-- tests/                 independent behavioral and regression checks
```

This is an illustration, not a scaffold to create automatically. Use agent.py
for one agent implementation, agents.py for a cohesive set, or an agents/
package when types or responsibilities justify it. model.py coordinates stages,
model-level processes, global state, stopping and collection. Agents may call
public model services for shared resources, environment queries or coordinated
interactions; responsibility and source fidelity determine the boundary, not a
blanket ban on agent-to-model calls. Keep agent decisions readable in their
appropriate owner rather than hiding all behavior behind empty wrappers.
Preserve established meaningful conventions. A small explicitly requested
teaching snippet may remain in one file; it is not an exception for a substantial
agent/model/UI/analysis system.

Add app.py only when UI is required. It wires presentation to public model APIs
and does not duplicate scientific rules. Importing the computational model must
not start a UI server, require UI-only dependencies, or run a simulation. Keep
server/simulation execution behind explicit entry points. Visualizers observe
state without modifying it or consuming model randomness; test repeated portrayal
against state and random-stream preservation, not just rendered appearance.

Add space.py for substantial environment/spatial operations, processes.py for
cohesive shared or model-level processes, data.py for meaningful input preparation,
metrics.py for observations, visualization.py for portrayal, experiments.py for
run orchestration, or analysis.py for statistical analysis only when those
responsibilities warrant a separate module. Separate meaningful raw-input
preparation, experiment orchestration and statistical analysis from model rules;
keep parameters, seeds, units and observation timing inspectable. Do not use
model.py as a renamed God class with cosmetic agent wrappers. Avoid circular
imports, wildcard imports, global mutable state, hidden import side effects,
long multipurpose methods and deeply nested rules. Use meaningful names,
focused comments/docstrings and useful type hints without needless abstractions
or one-function-per-file fragmentation. Explain the chosen boundaries in a
short existing project note, not empty scaffold files.

Before production restructuring, independent QA characterizes interfaces, state transitions, activation
order, random draw order, initialization, observables, and stopping. Save small
baseline results under explicit inputs, seeds, and environment versions where
execution is authorized. Compare trajectories as well as final outputs when
intermediate behavior matters. Use justified numerical tolerances; a broad
tolerance must not hide changed behavior.

Review the final code against the conceptual specification, including source
decisions and applicable geography. Run relevant invariant, reproducibility,
and integrated checks after fixes. Describe remaining coverage gaps and
intentional changes explicitly. Implementation agreement is bounded software
evidence; scientific adequacy needs purpose-specific evaluation.

Worker and QA assignments must explicitly carry these headless-import,
state/RNG-neutral observation and refactor-baseline acceptance criteria. The
fresh outer reviewer inspects the actual responsibility boundaries, source
fidelity and evidence for all three criteria even when tests pass. A cosmetically
split or monolithic design returns to the worker; a missing or invalid regression returns to QA. Apply the
[workflow's correction and re-review sequence](workflow.md), preserving the
baseline and scientific target rather than weakening expectations to obtain a pass.
