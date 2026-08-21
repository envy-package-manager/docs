---
sidebar_position: 1
title: GitHub Actions
---

# GitHub Actions

> **Placeholder content.** Outline for review; verify against sources.

Will cover:

- The minimal job: check out, run `./bin/envy sync --platform all`, use the
  deployed wrappers.
- Caching the envy cache: point `ENVY_CACHE_ROOT` into the workspace and use
  `actions/cache` keyed on a hash of every `envy.lua` in the tree.
- Windows runners: `./bin/envy.bat`, script-flavor notes.
- Keeping CI hermetic: no setup pairs that mutate the runner unless selected;
  gating host-mutating pairs off in CI from the manifest.
- Depot publishing from CI — pointer to
  [Running a Package Depot](../package-depots.md).
