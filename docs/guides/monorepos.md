---
sidebar_position: 5
title: Monorepos & Subprojects
---

# Monorepos & Subprojects

> **Placeholder content.** Outline for review; verify against sources.

One repo, many projects — or one superproject composing manifests from
submodules. How manifests nest and compose.

Will cover:

- The two roles: a **root** manifest (`@envy root "true"`, the default) and
  **subproject** manifests (`@envy root "false"`).
- How envy picks the governing manifest: walk up from where you are, prefer
  the root, stop at repo boundaries. Pointer to
  [Manifest Discovery](/concepts/projects/discovery) for exact rules.
- Composition is explicit Lua, not magic inheritance:

```lua title="superproject envy.lua (excerpt)"
local sub = envy.loadenv("src.common.envy")

BUNDLES = sub.BUNDLES
PACKAGES = sub.PACKAGES

envy.extend(PACKAGES, {
  -- superproject-specific additions, e.g. pinning a compiler version the
  -- shared manifest deliberately leaves out
  { spec = "arm.gcc@r1",
    source = envy.abspath("src/common/envy/arm.gcc.lua"),
    options = { version = "15.2.rel1" } },
})
```

- Paths resolve relative to the manifest being evaluated — the pattern of a
  shared manifest exporting a `base` path for its spec files.
- The "deliberate hole" pattern: a shared manifest omits a package (say, the
  compiler) so each superproject pins its own version.
- Working on a subproject standalone: `--subproject`, and gating
  standalone-only entries on an environment variable.
- Each manifest pins its own envy version; `envy use` per manifest.
