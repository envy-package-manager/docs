---
sidebar_position: 6
title: Creating a Bundle
---

# Creating a Bundle

> **Placeholder content.** Outline for review; verify against sources.

Distribute a family of related specs as one versioned, pinnable unit.

Will cover:

- When a bundle beats loose spec URLs: shared org toolchain, one `ref` to pin
  instead of N URLs, atomic upgrades.
- Bundle anatomy — a repo (or archive) with `envy-bundle.lua`:

```lua title="envy-bundle.lua"
BUNDLE = "acme.toolchain@r1"
SPECS = {
  ["acme.cmake@r0"] = "specs/cmake.lua",
  ["acme.ninja@r0"] = "specs/ninja.lua",
}
```

- The identity-match rule: each referenced spec file's `IDENTITY` must match
  its `SPECS` key.
- Consuming a bundle from a manifest: the `BUNDLES` alias map (identity,
  source, pinned `ref`) and `bundle = "alias"` in package entries.
- Migrating project-local specs into a bundle without breaking consumers
  (identities stay the same; only the source moves).
- Versioning discipline: when to bump the bundle identity vs a spec identity.
