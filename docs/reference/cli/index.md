---
sidebar_position: 0
title: CLI Reference
slug: /reference/cli
---

# CLI Reference

> **Placeholder content.** Command list verified against sources at skeleton
> time; each command's page needs full flag semantics and examples.

Conventions that hold across every command:

- Human output goes to **stderr**; **stdout** is reserved for machine-readable
  results (`product`, `package`, `hash`, `export`) — always safe to pipe.
- Commands that need a manifest find it by
  [discovery](/concepts/projects/discovery) unless `--manifest` overrides.
- Package `queries` are partial matches against identities.

## Global flags

Accepted by every subcommand.

| Flag | Effect |
| --- | --- |
| `--verbose` | Decision-level narrative (why, not just what). |
| `-q`, `--quiet` | Warnings and errors only. |
| `--trace[=stderr\|file:<path>]` | Structured JSONL event stream ([Logging & Tracing](../observability.md)). |
| `--cache-root <path>` | Override the cache root (env: `ENVY_CACHE_ROOT`). |
| `-v`, `--version` | Print version. |
| `-h`, `--help` | Print help. |

## Commands

### Everyday

| Command | Purpose |
| --- | --- |
| [`envy sync`](./sync.md) | Install packages + deploy product scripts. The everyday command. |
| [`envy install`](./install.md) | Install packages only. |
| [`envy deploy`](./deploy.md) | Deploy product scripts only. |
| [`envy product`](./product.md) | Resolve a product to its path/value, or list all. |
| [`envy package`](./package.md) | Install one package and print its directory. |
| [`envy run`](./run.md) | Run a command with the project bin dir on `PATH`. |

### Project management

| Command | Purpose |
| --- | --- |
| [`envy init`](./init.md) | Initialize a project: manifest, bootstrap scripts, editor config. |
| [`envy use`](./use.md) | Retarget the manifest's pinned envy version. |
| [`envy shell`](./shell.md) | Print the shell-profile line enabling shell hooks. |
| [`envy cache`](./cache.md) | Show cache location and disk usage. |

### Spec authoring

| Command | Purpose |
| --- | --- |
| [`envy git-resolve`](./git-resolve.md) | Resolve a remote branch/tag to a full commit hash. |
| [`envy hash`](./hash.md) | Print `sha256` lines for fingerprint tables and depot indexes. |
| [`envy fetch`](./fetch.md) | Download one resource the way `FETCH` would. |
| [`envy extract`](./extract.md) | Extract an archive the way `STAGE` would. |
| [`envy lua`](./lua.md) | Run a Lua script inside envy's runtime. |

### Depot publishing

| Command | Purpose |
| --- | --- |
| [`envy export`](./export.md) | Export cached packages as depot artifacts. |
| [`envy import`](./import.md) | Import exported artifacts into the cache. |
| [`envy merge-depot`](./merge-depot.md) | Merge per-platform depot indexes. |

### Administration

| Command | Purpose |
| --- | --- |
| [`envy mirror-envy`](./mirror-envy.md) | Mirror an envy release to a directory or S3. |
| [`envy version`](./version.md) | Print version info and bundled licenses. |
