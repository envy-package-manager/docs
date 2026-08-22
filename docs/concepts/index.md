---
sidebar_position: 1
title: Concepts
slug: /concepts
---

# Concepts

The vocabulary, one term at a time. Each entry links to its full page. If you
read them in order, this page is also a reasonable tour of the model.

- **[Manifest](/concepts/projects)**: `envy.lua`, checked into the project. It
  pins envy itself through header directives and declares every package the
  project needs in `PACKAGES`. It is real Lua, not config-file Lua.
- **[Package entry](/concepts/projects#package-entries)**: one row of
  `PACKAGES`. Which spec, where it comes from, which options, which platforms,
  which setup pairs.
- **[Spec](/concepts/specs)**: a Lua file that teaches envy how to acquire one
  kind of package. Each [verb](/concepts/specs/lifecycle) can be a string, a
  table, a function, or omitted.
- **Identity**: a namespaced, versioned spec name such as `acme.gcc@r1`. The
  `@r1` versions the spec, not the tool it installs. The `local.*` namespace is
  reserved for project-local specs.
- **Package**: one concrete installation, keyed by `(identity, options,
  platform)`. Different options coexist as different packages.
- **[Options](/concepts/specs/options)**: the per-entry `options = { ... }`
  table. Validated by the spec, passed to every verb, and part of the package's
  identity.
- **[Product](/concepts/specs/products)**: a named thing a package offers
  consumers. An executable such as `cmake`, or a plain value such as a header
  file path. Consumers ask for the product name, never the install path.
- **[Dependency](/concepts/dependencies)**: a package another package needs,
  with control over how early it is needed, down to "before I can fetch".
- **[Bundle](/concepts/dependencies/bundles)**: a versioned container shipping
  many specs behind one pin.
- **[Platform](/concepts/specs/platforms)**: the OS and architecture envy is
  running on. macOS, Linux, and Windows are equal targets, and filters decide
  which packages a given machine instantiates.
- **[Cache](/concepts/cache)**: the user-wide, content-addressed store all
  projects share. Always safe to delete.
- **[Depot](/concepts/depots)**: the optional prebuilt-artifact layer.
- **[Superproject and subproject](/concepts/projects#manifest-discovery)**:
  nested manifests composing into one project.
- **[Shells & Scripts](/concepts/shells)**: which interpreter runs a string verb,
  and how to make that interpreter a package the project pins.
- **[Reproducibility](/concepts/reproducibility)**: the pin inventory, the trust
  chain, and the honest limits.
