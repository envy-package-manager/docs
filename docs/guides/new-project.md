---
sidebar_position: 1
title: Starting a Project
---

# Starting a Project

> **Placeholder content.** Outline for review. Verify against sources.

An end-to-end walkthrough from an empty repo to a committed, self-bootstrapping
toolchain.

Will cover:

- Getting a throwaway envy binary and running
  `envy init <project-dir> <bin-dir>`.
- Choosing init options. `--mirror` for a private release mirror. `--pin-sums`
  to checksum-pin the envy release. `--deploy` for product script deployment.
  `--root` for subproject manifests. `--platform` for which script flavors to
  write in a cross-platform repo.
- Anatomy of the freshly written `envy.lua` and its `-- @envy` header.
- Adding your first package and running the first `sync`.
- What to commit: the manifest, both bootstrap scripts, `.luarc.json`, and the
  deployed wrappers. Also what to put in `.gitignore`.
- Repo conventions: record `envy git-resolve` commands as comments next to
  pinned refs, and keep project-local specs in one directory.
