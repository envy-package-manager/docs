---
sidebar_position: 2
title: Build Systems
---

# Build Systems

> **Placeholder content.** Outline for review. Verify against sources.

Feed envy-resolved tool and file paths into GN, CMake, Make, or anything else
that can run a program.

Will cover:

- The primitive. `envy product <name>` prints an absolute path, and
  `envy product --json` dumps every product at once for one-shot ingestion.
- Non-script products work the same way. A header-only library's spec exports
  `{ value = "doctest.h", script = false }`. Your build system consumes the
  resolved path, with no bin-directory wrapper involved.
- GN: `exec_script` over an `envy product --json` helper, declaring the
  manifests as inputs so a manifest edit re-runs generation.
- CMake: resolving toolchain paths at configure time.
- Wrapper-script pattern for meta-tools (a committed `bin/gn` that syncs, then
  resolves `gn`/`ninja`/`python3` products and dispatches).
- Do not hardcode cache paths. They are content-addressed and move when
  options change, so always resolve through `envy product` or `envy package`.
