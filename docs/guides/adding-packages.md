---
sidebar_position: 2
title: Adding Packages
---

# Adding Packages

> **Placeholder content.** Outline for review. Verify against sources.

A manifest cookbook, one recipe per common `PACKAGES` entry shape.

Will cover, each with a real example:

- From a bundle:
  `{ spec = "envy.uv@r0", bundle = "envy", options = { version = "0.11.30" } }`.
- From a spec URL, with `source = "https://..."` plus `sha256`.
- From a git-hosted spec, with `source = "https://....git"` plus a pinned
  `ref`.
- From a project-local spec file, with
  `source = envy.abspath("envy/local.mytool.lua")`.
- Passing options: strings, booleans, numbers, lists, and nested tables, and how
  options distinguish otherwise identical packages.
- Restricting to platforms with `platforms = { "linux" }`.
- Opting into setup pairs with `setup = { "udev_rules" }`, including conditional
  selection such as skipping in CI.
- Environment-conditional entries. The manifest is Lua, so `os.getenv` and
  `envy.extend` are available.
- Verifying the result with `envy sync`, `envy product`, and `envy package`.
