---
sidebar_position: 9
title: Reproducibility
---

# Reproducibility

> **Placeholder content.** Outline for review. Verify against sources.

How a clone of the repo becomes the same toolchain everywhere, and where the
sharp edges are.

Will cover:

- There is no lockfile. envy does not solve version ranges, so there is nothing
  to lock. Every pin is explicit and lives in the manifest or a spec. The
  manifest is the lockfile.
- The pin inventory, which is what "fully pinned" means:
  1. envy itself: `@envy version`, hardened by `@envy sha256sums`.
  2. specs: `sha256` for URL sources, a full commit `ref` for git, and a bundle
     `ref` for bundles.
  3. artifacts: `sha256` inside `FETCH`.
  4. tool versions: `options`.
- envy self-versioning. Every command runs under the manifest's pinned envy
  version, so a project upgrades envy with `envy use`, one manifest at a time.
- The trust chain for envy binaries. One `sha256sums` pin in a reviewed manifest
  covers the release checksum file, which covers all six platform archives. A
  mirror named by `@envy mirror` or `ENVY_MIRROR` therefore cannot tamper
  undetected.
- Known limits:
  - Verification is opt-in per artifact. An unhashed fetch is a reproducibility
    hole, and also a performance one, because it re-downloads every time.
  - User-managed packages mutate hosts and are only as reproducible as the host
    package manager behind them.
  - Depots trade "built here" for "built by CI". The hash key guarantees
    equivalent inputs rather than bit-identical rebuilds.
- A practical checklist for team pinning discipline, in
  [Pinning & Updating](/guides/pinning).
