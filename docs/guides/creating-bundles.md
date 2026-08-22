---
sidebar_position: 6
title: Creating a Bundle
---

# Creating a Bundle

> **Placeholder content.** Outline for review. Verify against sources.

Distribute a family of related specs as one versioned, pinnable unit.

Will cover:

- When a bundle beats loose spec URLs: a shared org toolchain, one `ref` to pin
  instead of many URLs, and atomic upgrades.
- Bundle anatomy, meaning a repo or archive with `envy-bundle.lua`:

```lua title="envy-bundle.lua"
BUNDLE = "acme.toolchain@r1"
SPECS = {
  ["acme.cmake@r0"] = "specs/cmake.lua",
  ["acme.ninja@r0"] = "specs/ninja.lua",
}
```

- The identity-match rule. Each referenced spec file's `IDENTITY` has to match
  its `SPECS` key.
- Consuming a bundle from a manifest: the `BUNDLES` alias map, with identity,
  source, and pinned `ref`, and `bundle = "alias"` in package entries.
- Migrating project-local specs into a bundle without breaking consumers.
  Identities stay the same, and only the source moves.
- Versioning discipline: when to bump the bundle identity rather than a spec
  identity.
- Shipping Lua helpers next to the specs, so the bundle presents an API rather
  than a pile of files. See
  [Shipping an API with your specs](/concepts/dependencies/bundles#shipping-an-api-with-your-specs).
