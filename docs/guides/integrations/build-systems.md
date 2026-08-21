---
sidebar_position: 2
title: Build Systems
---

# Build Systems

> **Placeholder content.** Outline for review; verify against sources.

Feed envy-resolved tool and file paths into GN, CMake, Make, or anything else
that can run a program.

Will cover:

- The universal primitive: `envy product <name>` prints an absolute path;
  `envy product --json` dumps every product at once for one-shot ingestion.
- Non-script products are first-class: a header-only library's spec can
  export `{ value = "doctest.h", script = false }` and your build system
  consumes the resolved path — no bin-dir wrapper involved.
- GN: `exec_script` over an `envy product --json` helper; declaring the
  manifests as inputs so a manifest edit re-runs generation.
- CMake: resolving toolchain paths at configure time.
- Wrapper-script pattern for meta-tools (a committed `bin/gn` that syncs, then
  resolves `gn`/`ninja`/`python3` products and dispatches).
- Do not hardcode cache paths: they're content-addressed and move when
  options change; always resolve through `envy product` / `envy package`.
