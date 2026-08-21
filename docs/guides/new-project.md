---
sidebar_position: 1
title: Starting a Project
---

# Starting a Project

> **Placeholder content.** Outline for review; verify against sources.

End-to-end walkthrough: empty repo → committed, self-bootstrapping toolchain.

Will cover:

- Getting a throwaway envy binary and running
  `envy init <project-dir> <bin-dir>`.
- Choosing init options: `--mirror` (private release mirror), `--pin-sums`
  (checksum-pin the envy release), `--deploy` (product script deployment
  on/off), `--root` (subproject manifests), `--platform` (which script
  flavors to write for cross-platform repos).
- Anatomy of the freshly-written `envy.lua` and its `-- @envy` header.
- Adding your first package and running the first `sync`.
- What to commit: manifest, both bootstrap scripts, `.luarc.json`, deployed
  wrappers (and what to `.gitignore`).
- Recommended repo conventions: recording `envy git-resolve` commands as
  comments next to pinned refs; a `local.` spec directory for project-local
  specs.
