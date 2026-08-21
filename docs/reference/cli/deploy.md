---
sidebar_position: 3
title: envy deploy
---

# `envy deploy`

> **Placeholder content.** Verify flags and semantics against sources.

Deploy (or refresh) product wrapper scripts into the project's bin dir from
already-resolved products. The other half of [`sync`](./sync.md). Useful when
packages are installed but the bin dir is missing scripts — e.g. a new
`script`-producing product was added, or the bin dir was cleaned.

## Usage

```
envy deploy [<identities>...] [--manifest=<path>] [--strict] [--subproject]
            [--platform=posix|windows|all]
```

## Arguments & flags

| Argument / flag | Meaning |
| --- | --- |
| `identities` | Optional filters; no identities = all products. |
| `--manifest <path>` | Use this manifest instead of discovery. |
| `--strict` | Error on name collisions with non-envy-managed files. |
| `--subproject` | Use the nearest manifest; don't walk up. Excludes `--manifest`. |
| `--platform posix\|windows\|all` | Which script flavors to write. |

Deployment requires `@envy deploy "true"` in the manifest; only files carrying
the `envy-managed` marker are ever created, updated, or pruned.

## Examples

```bash
./bin/envy deploy                  # refresh every wrapper
./bin/envy deploy --platform all   # write posix + windows flavors
```

## See also

- [Product Scripts](/concepts/environment/product-scripts)
- [Products](/concepts/specs/products)
