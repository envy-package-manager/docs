---
sidebar_position: 1
title: Anatomy of a Spec
slug: /concepts/specs
---

# Anatomy of a Spec

> **Placeholder content.** Outline for review; verify against sources.

A spec is a Lua file that teaches envy how to acquire one kind of package.
Spec-level names are UPPERCASE globals; everything else is ordinary Lua.

Will cover:

- The one hard requirement: `IDENTITY = "ns.name@ver"` — everything else has
  a sensible default or is optional.
- The complete global roster and where each is documented:
  - Verbs: [`FETCH`](./fetch.md), [`STAGE`](./stage.md),
    [`BUILD`](./build.md), [`INSTALL`](./install.md), [`SETUP`](./setup.md).
  - Declarations: [`OPTIONS`](./options.md), [`PRODUCTS`](./products.md),
    [`DEPENDENCIES`](/concepts/dependencies/declaring),
    [`PLATFORMS`](./platforms.md),
    [`USER_MANAGED`](./user-managed.md), `EXPORTABLE`.
- The core design idea: **every verb accepts multiple shapes** — a string for
  the simple case, a table for the declarative case, a function for the
  programmatic case, or nothing at all for the default behavior. A
  twenty-line spec and a two-line spec are both idiomatic.
- A tour of three real specs, smallest to largest: a two-liner (URL fetch +
  default everything), a mid-size prebuilt-binary spec, and a
  setup-only host-package spec.
- Where specs live: alongside the project (`local.*`), at URLs, in git, in
  [bundles](/concepts/dependencies/bundles).
- Spec code runs on the host platform only; write platform switches with
  `envy.PLATFORM` / `envy.ARCH`.
