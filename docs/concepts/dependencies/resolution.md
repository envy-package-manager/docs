---
sidebar_position: 5
title: Resolution
---

# Resolution

> **Placeholder content.** Outline for review; verify against sources.

How the package graph settles — described by observable behavior, not
internals.

Will cover:

- The graph is discovered, not declared up front: envy reads the manifest,
  fetches specs, finds their dependencies, fetches *those* specs, and so on
  until nothing new appears. Weak references are settled once the picture is
  complete enough to judge them.
- Weak-reference outcomes:
  - exactly one existing package matches → it's used;
  - nothing matches, fallback present → the fallback is instantiated;
  - nothing matches, no fallback (reference-only) → error naming the
    unsatisfied reference;
  - multiple matches → error listing the ambiguous candidates (you
    disambiguate; envy never guesses).
- Product registry rules: every product name has at most one provider;
  collisions are hard errors with both providers named.
- De-duplication: identical `(identity, options, platform)` across the whole
  graph — manifest entries and transitive dependencies alike — resolves to
  one package.
- Setup-pair selections are validated against the specs that define them;
  unknown pair names are errors.
- Error aggregation: envy reports all resolution problems it can find in one
  run, not just the first.
- Determinism: same manifest + specs + platform → same graph. No network
  state or timing influences resolution outcomes.
