# Model specification

Use only prompts that help define this model. Reuse an existing project note
where possible; remove unused prompts instead of filling them with placeholders.

- **Purpose:** intended use, research question, and limits on claims.
- **Entities and state:** agents, environment, resources, and relevant variables.
- **Scales:** time and space, units, boundaries, and meaning of one update.
- **Initialization:** population, initial state, inputs, defaults, constraints.
- **Processes:** rules, interactions, activation order, update phases, ties.
- **Randomness:** distributions, random streams, seeds, replay expectations.
- **Observables:** outputs, units, aggregation, collection timing, interpretation.
- **Invariants and stopping:** protected accounting or state relationships,
  model stopping conditions, and any separate run limit.
- **Sources and decisions:** locators, fidelity target, conflicts, authorized
  interpretations, assumptions, and explicit unknowns.
- **Verification:** small expected behaviors, boundary cases, invariants, and
  reproducibility checks that show implementation follows this specification.
- **Geography, when applicable:** representations and layers; CRS, axes, units,
  transformations; geometry and topology; movement, index and predicate
  semantics; raster shape, affine, nodata, masks and alignment; spatial-data
  provenance and limitations.

Keep scientific evaluation needs visible, but do not describe software checks
as proof of scientific validity.
