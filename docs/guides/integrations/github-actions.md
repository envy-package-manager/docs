---
sidebar_position: 1
title: GitHub Actions
---

# GitHub Actions

> **Placeholder content.** Outline for review. Verify against sources.

Will cover:

- The minimal job: check out, run `./bin/envy sync --platform all`, use the
  deployed wrappers.
- Caching the envy cache: point `ENVY_CACHE_ROOT` into the workspace and use
  `actions/cache` keyed on a hash of every `envy.lua` in the tree.
- Windows runners: `bin\envy.bat`, and notes on script flavors.
- Keeping CI hermetic. No setup pair mutates the runner unless selected, and
  the manifest can gate host-mutating pairs off in CI.
- Depot publishing from CI. See
  [Running a Package Depot](../package-depots.md).
