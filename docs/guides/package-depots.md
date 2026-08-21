---
sidebar_position: 7
title: Running a Package Depot
---

# Running a Package Depot

> **Placeholder content.** Outline for review; verify against sources.

Set up the optional prebuilt-artifact layer: CI builds packages once,
everyone else's `sync` downloads instead of building.

Will cover:

- The loop at a glance:
  1. CI runs `envy export --depot-prefix <url>` on each platform (with
     `ENVY_IGNORE_DEPOT=1` so exports always build from source).
  2. `envy merge-depot` combines per-platform manifests with the existing
     index (`--existing`, `--retain-*` for garbage-collection policy).
  3. Upload artifacts + merged `packages.txt` to the depot (any dumb file
     host works; S3 is typical).
  4. Projects list the index in `PACKAGE_DEPOTS` and get depot hits on the
     next `sync`.
- A worked GitHub Actions nightly workflow (multi-platform matrix).
- Which packages are depot-eligible (`EXPORTABLE`, user-managed exclusions).
- Authenticated depots: depot entries with their own dependencies (e.g. the
  AWS CLI must be installed before the depot index can be fetched) — pointer
  to [Package Depots](/concepts/depots) concepts.
- Opting out per-run: `--ignore-depot` / `ENVY_IGNORE_DEPOT`.
