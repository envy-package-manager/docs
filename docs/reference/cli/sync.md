---
sidebar_position: 1
title: envy sync
---

# `envy sync`

> **Placeholder content.** Verify flags and semantics against sources.

Install every package the manifest requests, then deploy product wrapper
scripts into the project bin dir. `sync` = [`install`](./install.md) +
[`deploy`](./deploy.md). The command you run after cloning, after editing the
manifest, and whenever in doubt — it is idempotent and incremental.

## Usage

```
envy sync [<queries>...] [--manifest=<path>] [--strict] [--subproject]
          [--platform=posix|windows|all] [--ignore-depot]
```

## Arguments & flags

| Argument / flag | Meaning |
| --- | --- |
| `queries` | Optional partial-match identity filters; no queries = everything. |
| `--manifest <path>` | Use this manifest instead of discovery. |
| `--strict` | Error (instead of skip) when a non-envy-managed file collides with a product script name. |
| `--subproject` | Use the nearest manifest; don't walk up to the root. Excludes `--manifest`. |
| `--platform posix\|windows\|all` | Which script flavors to write. |
| `--ignore-depot` | Skip depot lookups; build from source (env: `ENVY_IGNORE_DEPOT`). |

## Examples

```bash
./bin/envy sync                    # everything, everyday
./bin/envy sync python             # just packages matching "python"
./bin/envy sync --platform all     # commit both posix and windows wrappers
./bin/envy sync --ignore-depot     # force source builds this run
```

## See also

- [First Steps](/getting-started/first-steps) — the sync/install/deploy
  triangle.
- [Product Scripts](/concepts/environment/product-scripts)
