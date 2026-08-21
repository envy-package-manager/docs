---
sidebar_position: 2
title: Package Entries
---

# Package Entries

> **Placeholder content.** Outline for review; verify against sources.

Every element of `PACKAGES` is a table describing one requested package.

Will cover:

- The full field reference:
  - `spec` — the identity being requested (required).
  - `source` — where the spec lives: URL string, local path, git URL — or a
    table with its own `fetch` function and
    [fetch dependencies](/concepts/dependencies/fetch-dependencies).
  - `bundle` — take the spec from a bundle instead (mutually exclusive with
    `source`).
  - `sha256` — integrity pin for a downloaded spec.
  - `ref` — commit pin; required for git sources.
  - `subdir` — spec location within a fetched tree.
  - `options` — the knobs this package is built with; part of its identity.
  - `platforms` — restrict the entry to some platforms.
  - `setup` — which of the spec's setup pairs to run
    ([SETUP](/concepts/specs/setup)).
  - `needed_by`, `product`, `weak` — dependency-shaping fields, covered in
    [Dependencies](/concepts/dependencies/declaring).
- Identity syntax: `namespace.name@version`; what the `@version` means (spec
  revision, not tool version); the `local.*` namespace.
- Entries must be tables — a bare identity string is an error, on purpose.
- How two entries for the same spec with different options become two
  independent packages.
