---
sidebar_position: 6
title: Bundles
---

# Bundles

> **Placeholder content.** Outline for review. Verify against sources.

A bundle is a versioned container of specs: one pin that delivers a whole
toolbox of package definitions.

Will cover:

- The consumer side:

```lua
BUNDLES = {
  envy = {
    identity = "envy.package-specs@r3",
    source = "https://github.com/envy-package-manager/package-specs.git",
    -- envy git-resolve https://github.com/envy-package-manager/package-specs main
    ref = "ded36a39bbf13744f5a0e539f2f4741fecb61dd0",
  },
}

PACKAGES = {
  { spec = "envy.uv@r0", bundle = "envy", options = { version = "0.11.30" } },
  { spec = "envy.python@r1", bundle = "envy",
    options = { version = "3.13.14", release = "20260623" } },
}
```

- One `ref` pin covers every spec taken from the bundle, so the whole toolbox
  upgrades atomically.
- The producer side, meaning `envy-bundle.lua` with its `BUNDLE` and `SPECS`
  globals. See [Creating a Bundle](/guides/creating-bundles).
- How bundles arrive. envy materializes the bundle through the
  [fetch-dependency](./fetch-dependencies.md) machinery before reading any spec
  out of it. A bundle can therefore live behind the same bootstrap tooling as
  anything else.
- Inline bundle references on a single entry, using `bundle = { ... }` in place
  of an alias.
- Identity integrity. A spec fetched from a bundle has to declare the identity
  the bundle promised for it.
