---
sidebar_position: 1
title: The Dependency Model
slug: /concepts/dependencies
---

# The Dependency Model

> **Placeholder content.** Outline for review; verify against sources.

envy dependencies answer a different question than most package managers'.
There is no version solver and no global registry to solve against.
Dependencies are about **provisioning and ordering**: *what must exist, and by
when, for this package to make progress?*

Will cover:

- The core ideas, each with its own page:
  - **[Declaring dependencies](./declaring.md)** — four kinds: strong, weak,
    reference-only, and product dependencies. Who provides what, and who
    insists vs. who defers.
  - **[Phase ordering & `needed_by`](./ordering.md)** — dependencies aren't
    just "before/after"; a dependency is needed *by a specific phase* of the
    dependent. A build tool is needed by `build`; a download tool is needed
    by `fetch`.
  - **[Fetch dependencies](./fetch-dependencies.md)** — the extreme case:
    "I need the Artifactory CLI installed as a package before I can even
    *fetch* this other package." Declared inside a manifest entry's `source`
    table.
  - **[Resolution](./resolution.md)** — how the graph grows as specs are
    read, how weak references settle, what's an error.
  - **[Bundles](./bundles.md)** — spec distribution, which rides the same
    dependency machinery.
- The one-paragraph summary of the whole model:
  - Specs declare `DEPENDENCIES`; manifests can add dependency-shaped fields
    to entries.
  - Everything installs in parallel except where an edge says otherwise.
  - Edges are phase-precise, so a dependent can fetch while its build-time
    dependency is still installing.
  - The graph is *discovered*, not pre-declared: reading one spec can
    introduce new packages, recursively.
- What envy deliberately does not do: no version-range solving, no diamond
  mediation, no lockfile — identities and options are exact, so there is
  nothing to solve.
