---
sidebar_position: 1
title: Concepts
slug: /concepts
---

# Concepts

> **Placeholder content.** Outline for review. Verify against sources.

The vocabulary, one term at a time. Each entry links to its full page.

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
- **[Cache](/concepts/cache)**: the user-wide, content-addressed store all
  projects share. Always safe to delete.
- **[Depot](/concepts/depots)**: the optional prebuilt-artifact layer.
- **[Superproject and subproject](/concepts/projects#manifest-discovery)**:
  nested manifests composing into one project.
