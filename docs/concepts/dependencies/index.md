---
sidebar_position: 1
title: The Dependency Model
slug: /concepts/dependencies
---

# The Dependency Model

> **Placeholder content.** Outline for review. Verify against sources.

envy dependencies answer a different question than most package managers'.
There is no version solver and no global registry to solve against. Dependencies
are about provisioning and ordering: what must exist, and by when, for this
package to make progress.

Will cover:

- The core ideas, each with its own page:
  - **[Declaring dependencies](./declaring.md)**: four kinds, strong, weak,
    reference-only, and product. Who provides what, and who insists rather than
    defers.
  - **[Phase ordering and `needed_by`](./ordering.md)**: a dependency is needed
    by a specific phase of the dependent, not just "before". A build tool is
    needed by `build`, a download tool by `fetch`.
  - **[Fetch dependencies](./fetch-dependencies.md)**: the extreme case, where
    the Artifactory CLI has to be installed as a package before another
    package's spec can be fetched. Declared inside a manifest entry's `source`
    table.
  - **[Resolution](./resolution.md)**: how the graph grows as specs are read,
    how weak references settle, and what counts as an error.
  - **[Bundles](./bundles.md)**: spec distribution, which rides the same
    dependency machinery.
- The model in short:
  - Specs declare `DEPENDENCIES`. Manifests can add dependency-shaped fields to
    entries.
  - Everything installs in parallel except where an edge says otherwise.
  - Edges are phase-precise, so a dependent can fetch while its build-time
    dependency is still installing.
  - The graph is discovered rather than pre-declared. Reading one spec can
    introduce new packages, recursively.
- What envy does not do: no version-range solving, no diamond mediation, no
  lockfile. Identities and options are exact, so there is nothing to solve.
