---
sidebar_position: 7
title: Running a Package Depot
---

# Running a Package Depot

> **Placeholder content.** Outline for review. Verify against sources.

Set up the optional prebuilt-artifact layer. CI builds packages once, and
everyone else's `sync` downloads instead of building.

Will cover:

- The loop:
  1. CI runs `envy export --depot-prefix <url>` on each platform, with
     `ENVY_IGNORE_DEPOT=1` so exports always build from source.
  2. `envy merge-depot` combines the per-platform indexes with the existing one,
     using `--existing` and the `--retain-*` flags for garbage-collection
     policy.
  3. Upload the artifacts and the merged `packages.txt` to the depot. Any file
     host works, and S3 is typical.
  4. Projects list the index in `PACKAGE_DEPOTS` and get depot hits on the next
     `sync`.
- A worked GitHub Actions nightly workflow with a multi-platform matrix.
- Which packages are depot-eligible: `EXPORTABLE` specs, and why user-managed
  packages are excluded.
- Authenticated depots, where a depot entry has its own dependencies, for example
  the AWS CLI being installed before the index can be fetched. See
  [Package Depots](/concepts/depots).
- Opting out per run with `--ignore-depot` or `ENVY_IGNORE_DEPOT`.
