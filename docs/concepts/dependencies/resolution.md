---
sidebar_position: 5
title: Resolution
---

# Resolution

> **Placeholder content.** Outline for review. Verify against sources.

How the package graph settles, described by observable behavior rather than
internals.

Will cover:

- The graph is discovered rather than declared up front. envy reads the manifest,
  fetches specs, finds their dependencies, and fetches those specs, until nothing
  new appears. Weak references settle once the picture is complete enough to judge
  them.
- Weak-reference outcomes:
  - Exactly one existing package matches, so it is used.
  - Nothing matches and a fallback is present, so the fallback is instantiated.
  - Nothing matches and there is no fallback, which is reference-only, so envy
    reports an error naming the unsatisfied reference.
  - Several packages match, so envy reports an error listing the candidates. You
    disambiguate, and envy never guesses.
- Product registry rules. Every product name has at most one provider, and
  collisions are errors that name both providers.
- De-duplication. An identical `(identity, options, platform)` anywhere in the
  graph, whether from a manifest entry or a transitive dependency, resolves to
  one package.
- Setup-pair selections are validated against the specs that define them, and
  unknown pair names are errors.
- Error aggregation. envy reports all the resolution problems it can find in one
  run rather than only the first.
- Determinism. The same manifest, specs, and platform produce the same graph. No
  network state or timing affects the outcome.
