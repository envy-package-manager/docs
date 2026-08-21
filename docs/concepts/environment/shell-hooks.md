---
sidebar_position: 2
title: Shell Hooks
---

# Shell Hooks

> **Placeholder content.** Outline for review; verify against sources.

The convenience layer: your shell notices envy projects as you `cd` and
manages `PATH` for you.

Will cover:

- Conceptual contract: inside a project, its bin dir is on `PATH` and
  `ENVY_PROJECT_ROOT` is set; outside, both are cleanly removed. The prompt
  shows 🦝 while active.
- Same manifest-discovery rules as envy itself — root manifests win, exactly
  as in [Manifest Discovery](/concepts/projects/discovery), so the hook and
  the binary always agree.
- Pure shell, zero startup cost, self-updating (details in
  [Getting Started → Shell Integration](/getting-started/shell-integration)).
- Supported shells: bash, zsh, fish, PowerShell.
- Configuration env vars and disabling.
- Relationship to the other two activation mechanisms — hooks are sugar over
  the same bin dir that [product scripts](./product-scripts.md) populate.
