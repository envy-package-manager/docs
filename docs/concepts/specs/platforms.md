---
sidebar_position: 11
title: Platforms
---

# Platforms

> **Placeholder content.** Outline for review; verify against sources.

Will cover:

- Platform vocabulary: `darwin`, `linux`, `windows`, optionally
  arch-qualified (`darwin-arm64`, `linux-x86_64`); `envy.PLATFORM`,
  `envy.ARCH`, `envy.PLATFORM_ARCH`, `envy.EXE_EXT` in Lua.
- The four places platform filters apply, and how they combine:
  1. Manifest entry `platforms = { ... }` — "this project only needs it
     here."
  2. Spec `PLATFORMS = { ... }` — "this package only exists here."
  3. Per-SETUP-pair `PLATFORMS` — "this host tweak only applies here."
  4. Per-product `platforms` — "this tool only ships here."
  An entry whose filters intersect to nothing simply never instantiates.
- Everything runs on the host platform: envy fetches/builds *for* the machine
  it's on; cross-platform repos get their coverage from CI matrices, not
  cross-building.
- Distinct concept, easily confused: `--platform posix|windows|all` on
  `init`/`sync`/`deploy` controls which *script flavors* are written to the
  bin dir, so a repo can commit both POSIX and Windows wrappers regardless of
  where you ran the command.
- Whole-spec platform switching (`if envy.PLATFORM == "windows" then ... end`
  around entire verb definitions).
