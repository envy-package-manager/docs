---
sidebar_position: 1
title: Installation
---

# Installation

> **Placeholder content.** Outline for review; verify against sources.

The headline: **envy has no installation of its own.** Projects commit a small
bootstrap script that downloads the exact envy version the project pins.

Will cover:

- **Joining an existing project** (the 99% case): clone, run `./bin/envy sync`
  (or wherever the project's bin dir is), done. The bootstrap script fetches
  the pinned envy binary into the user-wide cache on first run.
- **Starting a new project**: grab any envy binary temporarily, run
  `envy init <project-dir> <bin-dir>`, commit the results, throw the temp
  binary away. Links to the [Starting a Project](/guides/new-project) guide.
- What `envy init` writes: `envy.lua` manifest, `<bin>/envy` +
  `<bin>/envy.bat` bootstrap scripts, `.luarc.json` for editor support.
- Where envy keeps its data: per-user cache (macOS `~/Library/Caches/envy`,
  Linux `$XDG_CACHE_HOME/envy` or `~/.cache/envy`, Windows
  `%LOCALAPPDATA%\envy`), overridable with `ENVY_CACHE_ROOT`.
- Supported platforms: macOS, Linux, Windows on arm64 and x86_64.
- Air-gapped / private-network installs: `@envy mirror` and `ENVY_MIRROR`
  (pointer to [Reproducibility](/concepts/reproducibility) and
  `envy mirror-envy` in the [CLI reference](/reference/cli)).
