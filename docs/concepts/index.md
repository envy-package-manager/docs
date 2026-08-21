---
sidebar_position: 1
title: Concepts
slug: /concepts
---

# Concepts

> **Placeholder content.** Outline for review; verify against sources.

The mental model, one noun at a time. Each term links to its full page.

- **[Manifest](/concepts/projects/manifest)** — `envy.lua`, checked into the
  project. Pins envy itself (header directives) and declares every package
  the project needs (`PACKAGES`). It's real Lua, not config-file Lua.
- **[Package entry](/concepts/projects/package-entries)** — one row of
  `PACKAGES`: which spec, where it comes from, which options, which
  platforms, which setup pairs.
- **[Spec](/concepts/specs)** — a Lua file that teaches envy how to acquire
  one kind of package, using [verbs](/concepts/specs/lifecycle) that can each
  be a string, a table, a function, or omitted entirely.
- **Identity** — a namespaced, versioned spec name like `arm.gcc@r1`. The
  `@r1` versions the *spec*, not the tool it installs. `local.*` is reserved
  for project-local specs.
- **Package** — one concrete installation: `(identity, options, platform)`.
  Different options coexist as different packages.
- **[Options](/concepts/specs/options)** — the per-entry `options = { ... }`
  table; validated by the spec, passed to every verb, and part of the
  package's identity.
- **[Product](/concepts/specs/products)** — a named thing a package offers
  consumers: an executable (`cmake`), or just a value/path (a header file, a
  data file). Consumers ask for the product name, never the install path.
- **[Dependency](/concepts/dependencies)** — a package another package needs,
  with control over *when* it's needed — as early as "before I can even fetch."
- **[Bundle](/concepts/dependencies/bundles)** — a versioned container
  shipping many specs behind one pin.
- **[Cache](/concepts/cache)** — the user-wide, content-addressed store all
  projects share. Always safe to delete.
- **[Depot](/concepts/depots)** — the optional prebuilt-artifact layer.
- **[Superproject / subproject](/concepts/projects/discovery)** — nested
  manifests composing into one project world.
