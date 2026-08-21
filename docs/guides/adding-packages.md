---
sidebar_position: 2
title: Adding Packages
---

# Adding Packages

> **Placeholder content.** Outline for review; verify against sources.

The manifest cookbook: one recipe per common `PACKAGES` entry shape.

Will cover, each with a real-world example:

- From a bundle:
  `{ spec = "envy.uv@r0", bundle = "envy", options = { version = "0.11.30" } }`
- From a spec URL: `source = "https://..."` (+ `sha256`).
- From a git-hosted spec: `source = "git://..."` + pinned `ref`.
- From a project-local spec file: `source = "./envy/local.mytool.lua"`.
- Passing options: strings, booleans, numbers, lists, nested tables — and how
  options distinguish otherwise-identical packages.
- Restricting to platforms: `platforms = { "linux" }`.
- Opting into setup pairs: `setup = { "udev_rules" }`, conditional selection
  (e.g. skip in CI).
- Environment-conditional entries — the manifest is Lua; `os.getenv` and
  `envy.extend` are fair game.
- Verifying the result: `envy sync`, `envy product`, `envy package`.
