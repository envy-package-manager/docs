---
sidebar_position: 7
title: Troubleshooting
---

# Troubleshooting

> **Placeholder content.** Bucket list for review; entries to be written
> from real support traffic.

Planned sections:

- **Bootstrap**: bootstrap script can't download envy (mirror, proxy,
  checksum-pin failures); Windows-specific bootstrap limits.
- **Fetching**: sha256 mismatches (what changed, who to distrust); the
  "re-downloads every run" symptom (missing `sha256`); git ref problems.
- **Resolution errors**, decoded one by one: ambiguous weak reference;
  unsatisfied reference; product collision; unknown setup pair; dependency
  cycles (including fetch-dependency cycles).
- **Spec authoring**: verb type errors ("FETCH field must be..."); identity
  mismatch after fetch; staged-vs-install surprises when mixing declarative
  and function verbs.
- **Environment**: tool not on PATH (deploy off? shell hook not installed?
  wrong project root?); stale wrapper points at the wrong project in nested
  checkouts.
- **Cache**: reclaiming space (`envy cache`, safe deletion); moving the
  cache; network filesystems.
- **Depots**: why a depot miss happened (options/platform drift); forcing
  source builds.
