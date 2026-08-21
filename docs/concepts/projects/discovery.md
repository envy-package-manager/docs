---
sidebar_position: 3
title: Manifest Discovery & Roots
---

# Manifest Discovery & Roots

> **Placeholder content.** Outline for review; verify against sources.

Which `envy.lua` governs, when there's more than one?

Will cover:

- The upward walk: from your current directory (or a script's directory)
  toward the filesystem root, examining each `envy.lua` on the way.
- `@envy root` semantics: `"true"` (the default) marks a superproject
  boundary and wins immediately; `"false"` says "keep looking above me."
- Repo boundaries: a `.git` directory stops the search.
- What happens when only subproject manifests are found (standalone
  checkout of a subproject: the manifest closest to the top wins).
- `--subproject`: use the nearest manifest, don't walk (on `sync`, `deploy`,
  `use`).
- The guarantee that makes shell hooks, bootstrap scripts, and envy agree on
  the same manifest — and why that matters (PATH must point at the same
  project envy resolves).
- Superproject composition idiom — pointer to
  [Monorepos & Subprojects](/guides/monorepos).
