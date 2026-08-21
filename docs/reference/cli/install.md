---
sidebar_position: 2
title: envy install
---

# `envy install`

> **Placeholder content.** Verify flags and semantics against sources.

Install manifest packages into the cache. Touches nothing in the project
directory — no scripts are deployed (that's [`deploy`](./deploy.md);
[`sync`](./sync.md) does both).

## Usage

```
envy install [<queries>...] [--manifest=<path>] [--ignore-depot]
```

## Arguments & flags

| Argument / flag | Meaning |
| --- | --- |
| `queries` | Optional partial-match identity filters; no queries = everything. |
| `--manifest <path>` | Use this manifest instead of discovery. |
| `--ignore-depot` | Skip depot lookups; build from source (env: `ENVY_IGNORE_DEPOT`). |

## Examples

```bash
./bin/envy install                 # warm the cache without touching bin/
./bin/envy install arm.gcc         # one package (and its dependencies)
```

## See also

- [`envy sync`](./sync.md), [`envy deploy`](./deploy.md)
- [The Cache](/concepts/cache)
