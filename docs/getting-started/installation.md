---
sidebar_position: 1
title: Installation
---

# Installation

> **Placeholder content.** Outline for review. Verify against sources.

envy has no installation of its own. Projects commit a small bootstrap script
that downloads the envy version the project pins.

Will cover:

- Joining an existing project, which is the common case. Clone, run
  `./bin/envy sync`, or wherever the project's bin directory is, and you are
  done. The bootstrap script fetches the pinned envy binary into the user-wide
  cache on first run.
- Starting a new project. Grab any envy binary temporarily, run
  `envy init <project-dir> <bin-dir>`, commit the results, and throw the
  temporary binary away. See [Starting a Project](/guides/new-project).
- What `envy init` writes: the `envy.lua` manifest, the `<bin>/envy` and
  `<bin>/envy.bat` bootstrap scripts, and `.luarc.json` for editor support.
- Where envy keeps its data: a per-user cache at `~/Library/Caches/envy` on
  macOS, `$XDG_CACHE_HOME/envy` or `~/.cache/envy` on Linux, and
  `%LOCALAPPDATA%\envy` on Windows. Override it with `ENVY_CACHE_ROOT`.
- Supported platforms: macOS, Linux, and Windows on arm64 and x86_64.
- Air-gapped and private-network installs with `@envy mirror` and
  `ENVY_MIRROR`. See [Reproducibility](/concepts/reproducibility) and
  `envy mirror-envy` in the [CLI reference](/reference/cli).
