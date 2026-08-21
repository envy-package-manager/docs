---
sidebar_position: 6
title: Bundles
---

# Bundles

> **Placeholder content.** Outline for review; verify against sources.

A bundle is a versioned container of specs — one pin that delivers a whole
toolbox of package definitions.

Will cover:

- The consumer side:

```lua
BUNDLES = {
  envy = {
    identity = "envy.package-specs@r1",
    source = "https://github.com/envy-package-manager/package-specs.git",
    -- envy git-resolve https://github.com/envy-package-manager/package-specs main
    ref = "9bdb0a11cefa3e83418cff37dc68ea755c07a237",
  },
}

PACKAGES = {
  { spec = "envy.uv@r0", bundle = "envy", options = { version = "0.11.30" } },
  { spec = "envy.python@r0", bundle = "envy", options = { version = "3.13.14" } },
}
```

- One `ref` pin covers every spec taken from the bundle — upgrade the whole
  toolbox atomically.
- The producer side (`envy-bundle.lua`, `BUNDLE`, `SPECS`) — pointer to the
  [Creating a Bundle](/guides/creating-bundles) guide.
- How bundles arrive: the bundle itself is materialized through the
  [fetch-dependency](./fetch-dependencies.md) machinery before any spec is
  read out of it — bundles can live behind the same bootstrap tooling as
  anything else.
- Inline bundle references on a single entry (`bundle = { ... }` in place of
  an alias).
- Identity integrity: a spec fetched from a bundle must declare the identity
  the bundle promised for it.
