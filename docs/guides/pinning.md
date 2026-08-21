---
sidebar_position: 4
title: Pinning & Updating
---

# Pinning & Updating

> **Placeholder content.** Outline for review. Verify against sources.

How to pin everything, and how to move a pin when you mean to.

Will cover:

- The pinning inventory. There is no lockfile, and every pin lives in the
  manifest or a spec:
  - `@envy version` + `@envy sha256sums` pin envy itself.
  - `options = { version = ... }` pins tool versions per package entry.
  - `sha256` pins downloaded artifacts.
  - `ref`, a full commit hash, pins git sources, and `BUNDLES[...].ref` pins
    bundles.
- `envy git-resolve <url> <ref>` turns a branch or tag into a commit hash at
  authoring time. By convention, record the command as a comment above the pin.
- Updating envy. `envy use <version>` rewrites `@envy version` and refreshes
  `@envy sha256sums`. Run it once per manifest in a superproject tree.
- Updating a package: bump `options.version`, update fingerprints, re-`sync`.
- The cost of not pinning: fetches without `sha256` are re-downloaded on every
  install and can't be trusted from cache. Pointer to
  [Reproducibility](/concepts/reproducibility).
