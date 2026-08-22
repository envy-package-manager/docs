---
sidebar_position: 3
title: Phase Ordering & needed_by
---

# Phase Ordering & `needed_by`

> **Placeholder content.** Outline for review. Verify against sources.

A dependency edge in envy has a time attached: the phase of the dependent that
has to wait. That is `needed_by`.

Will cover:

- The intuition, with three examples:
  - A build tool, such as cmake for a source build, is `needed_by = "build"`.
    The dependent can fetch and stage its own sources while cmake installs.
  - A fetch tool, such as an Artifactory CLI for a spec whose `FETCH` shells out
    to it, is `needed_by = "fetch"`. Note that `https://` and `s3://` need no
    such tool, because envy fetches both itself.
  - A companion that `INSTALL` invokes is `needed_by = "install"`.
- Valid values: `check`, `import`, `fetch`, `stage`, `build`, `install`. These
  are the phases of the dependent that can wait on a dependency.
- The default is `build`. If a verb earlier than `BUILD` uses a dependency, most
  often `FETCH`, say so explicitly. Otherwise the dependency may not exist yet
  when your `FETCH` runs.
- What "ready" means. The dependency is fully installed, through its own setup,
  before the gated phase starts. Ungated phases of the dependent run
  concurrently with it.
- Where `needed_by` can appear: on `DEPENDENCIES` entries in specs, and on
  dependency-shaped fields in manifest entries.
- The limit. `needed_by` cannot gate acquiring the dependent's own spec, which
  happens earlier than any phase you can name. For that, see
  [Fetch Dependencies](./fetch-dependencies.md).
- Parallelism consequences: why envy installs are fast, and how to read
  `--verbose` output to see what waited on what.
