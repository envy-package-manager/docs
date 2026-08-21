---
sidebar_position: 7
title: Troubleshooting
---

# Troubleshooting

> **Placeholder content.** Bucket list for review. Entries to be written from
> real support traffic.

Planned sections:

- **Bootstrap.** The bootstrap script cannot download envy, covering mirror,
  proxy, and checksum-pin failures, plus Windows-specific bootstrap limits.
- **Fetching.** sha256 mismatches, meaning what changed and who to distrust. The
  "re-downloads every run" symptom, which is a missing `sha256`. Git ref
  problems.
- **Resolution errors**, decoded one by one: ambiguous weak reference,
  unsatisfied reference, product collision, unknown setup pair, and dependency
  cycles including fetch-dependency cycles.
- **Spec authoring.** Verb type errors such as "FETCH field must be...".
  Identity mismatch after fetch. Staged-versus-install surprises when mixing
  declarative and function verbs.
- **Environment.** A tool is not on `PATH`, which usually means deployment is
  off, the shell hook is not installed, or the project root is wrong. A stale
  wrapper pointing at the wrong project in nested checkouts.
- **Cache.** Reclaiming space with `envy cache` and safe deletion. Moving the
  cache. Network filesystems.
- **Depots.** Why a depot miss happened, usually options or platform drift, and
  how to force source builds.
