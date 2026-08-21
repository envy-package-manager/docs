---
sidebar_position: 1
title: The Manifest
---

# The Manifest

> **Placeholder content.** Outline for review; verify against sources.

`envy.lua` is the single source of truth for a project's toolchain: it pins
envy itself and declares every package.

Will cover:

- **The `@envy` header** — comment directives at the top of the file, read by
  both the bootstrap scripts and envy proper:

```lua
-- @envy version "0.1.9"
-- @envy sha256sums "c8c5...c44c"
-- @envy mirror "https://my-mirror.example.com"
-- @envy schema "1"
-- @envy bin "bin"
-- @envy deploy "true"
-- @envy root "true"
```

  - Directive semantics, one by one (`bin` is required; `sha256sums`
    requires `version`; `root` defaults to true; `deploy` defaults to off;
    `cache-posix` / `cache-win` overrides).
  - The header-end rule: the first line of Lua code ends the header;
    directive-shaped comments below it are just comments.
- **The globals**:
  - `PACKAGES` (required) — the list of package entries.
  - `BUNDLES` — alias → bundle pin map.
  - `PACKAGE_DEPOTS` — optional prebuilt-artifact indexes.
  - `DEFAULT_SHELL` — which shell runs string verbs and returned scripts,
    project-wide (pointer to [Shells & Scripts](/concepts/specs/shells)).
- **The manifest is a program**: conditionals on `os.getenv`, composition via
  `envy.loadenv` / `envy.extend`, path anchoring via `envy.abspath`.
- What the manifest deliberately is *not*: there's no lockfile beside it —
  every pin lives here or in a spec
  ([Reproducibility](/concepts/reproducibility)).
