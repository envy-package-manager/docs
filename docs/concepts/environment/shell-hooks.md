---
sidebar_position: 2
title: Shell Hooks
---

# Shell Hooks

> **Placeholder content.** Outline for review. Verify against sources.

The convenience layer. Your shell notices envy projects as you `cd` and manages
`PATH` for you.

Will cover:

- The contract. Inside a project, its bin directory is on `PATH` and
  `ENVY_PROJECT_ROOT` is set. Outside, both are removed. The prompt shows 🦝
  while active.
- The same manifest-discovery rules envy itself uses, so root manifests win
  exactly as in [Manifest Discovery](/concepts/projects#manifest-discovery) and
  the hook and the binary always agree.
- Pure shell, zero startup cost, self-updating. Details in
  [Shell Integration](/getting-started/shell-integration).
- Supported shells: bash, zsh, fish, PowerShell.
- Configuration environment variables, and how to disable the hook.
- The relationship to the other two activation mechanisms. Hooks are sugar over
  the same bin directory that [product scripts](./product-scripts.md) populate.
