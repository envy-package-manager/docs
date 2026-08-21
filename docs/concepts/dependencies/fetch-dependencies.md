---
sidebar_position: 4
title: Fetch Dependencies
---

# Fetch Dependencies

> **Placeholder content.** Outline for review; verify against sources.

The bootstrap problem: *"This package's spec lives in Artifactory. I need the
Artifactory CLI — itself an envy package — installed before I can even fetch
the spec, let alone the payload."* Ordinary dependencies can't express this:
they order phases of packages whose specs envy already has. Fetch
dependencies order the *acquisition of the spec itself*.

Will cover:

- The shape — a manifest entry whose `source` is a table carrying both the
  tools it needs and the custom fetch that uses them:

```lua
PACKAGES = {
  { spec = "corp.toolchain@r2",
    source = {
      -- installed, end to end, before corp.toolchain's spec is fetched:
      dependencies = {
        { spec = "tools.jfrog-cli@r1",
          source = "https://specs.example.com/tools.jfrog-cli.lua",
          sha256 = "..." },
      },
      fetch = function(...)
        -- free to use the jfrog CLI here, e.g. via envy.product/envy.package
      end,
    },
    options = { version = "2.81.0" } },
}
```

- The guarantee: every entry in `source.dependencies` is taken through its
  *entire* lifecycle (install and setup included) before the dependent's
  spec is fetched. Compare `needed_by = "fetch"`, which only gates payload
  fetching — this gates everything.
- `source.dependencies` requires `source.fetch`: if nothing custom runs, you
  didn't need the tool.
- Chains: the fetch dependency's own spec can have fetch dependencies;
  bootstrap chains resolve bottom-up.
- Weak and product references are legal inside `source.dependencies` — "use
  the project's uploader if it has one."
- Where else this machinery appears (transparently): fetching
  [bundles](./bundles.md), and authenticated
  [depot](/concepts/depots) indexes with `DEPENDS`.
- Failure modes and diagnostics: cycles among fetch dependencies are
  detected and reported.
