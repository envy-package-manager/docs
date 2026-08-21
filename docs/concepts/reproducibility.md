---
sidebar_position: 8
title: Reproducibility
---

# Reproducibility

> **Placeholder content.** Outline for review; verify against sources.

How a clone of the repo becomes the same toolchain everywhere — and where the
sharp edges are.

Will cover:

- **There is no lockfile, on purpose.** envy doesn't solve version ranges, so
  there's nothing to lock: every pin is explicit and lives in the manifest or
  a spec. The manifest *is* the lockfile.
- The pin inventory (what "fully pinned" means):
  1. envy itself: `@envy version`, hardened by `@envy sha256sums`.
  2. specs: `sha256` for URL sources, full-commit `ref` for git, bundle
     `ref` for bundles.
  3. artifacts: `sha256` inside FETCH.
  4. tool versions: `options`.
- envy self-versioning: every command transparently runs under the
  manifest's pinned envy version — projects upgrade envy deliberately, via
  `envy use`, one manifest at a time.
- The trust chain for envy binaries: one `sha256sums` pin in a reviewed
  manifest attests the release manifest, which attests all six platform
  archives; mirrors (`@envy mirror` / `ENVY_MIRROR`) can't tamper undetected.
- Honest edges, documented as such:
  - verification is opt-in per artifact — an unhashed fetch is a
    reproducibility hole (and a performance one: it re-downloads every
    time);
  - user-managed packages mutate hosts and are only as reproducible as the
    host package manager behind them;
  - depots trade "built here" for "built by CI" — the hash key guarantees
    equivalence of inputs, not bit-identical rebuilds.
- Practical checklist: pinning discipline for teams
  ([Pinning & Updating](/guides/pinning)).
