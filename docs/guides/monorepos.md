---
sidebar_position: 5
title: Monorepos & Subprojects
---

# Monorepos & Subprojects

> **Placeholder content.** Outline for review. Verify against sources.

One repo with many projects, or one superproject composing manifests from
submodules. How manifests nest and compose.

Will cover:

- The two roles: a root manifest, `@envy root "true"`, which is the default, and
  subproject manifests, `@envy root "false"`.
- How envy picks the governing manifest. It walks up from where you are, prefers
  the root, and stops at repo boundaries. See
  [Manifest Discovery](/concepts/projects#manifest-discovery) for the exact
  rules.
- Composition is explicit Lua rather than inheritance:

```lua title="superproject envy.lua (excerpt)"
local sub = envy.loadenv("src.common.envy")

BUNDLES = sub.BUNDLES
PACKAGES = sub.PACKAGES

envy.extend(PACKAGES, {
  -- Superproject-specific additions, for example pinning a compiler version
  -- the shared manifest leaves out on purpose.
  { spec = "acme.armgcc@r1",
    source = envy.abspath("src/common/envy/acme.armgcc.lua"),
    options = { version = "15.2.rel1" } },
})
```

- Paths resolve relative to the manifest being evaluated, which is why a shared
  manifest exports a base path for its spec files.
- The deliberate-hole pattern. A shared manifest omits a package, such as the
  compiler, so each superproject pins its own version.
- Working on a subproject standalone with `--subproject`, and gating
  standalone-only entries on an environment variable.
- Each manifest pins its own envy version, so `envy use` runs per manifest.
