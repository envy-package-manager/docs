---
sidebar_position: 16
title: envy export
---

# `envy export`

> **Placeholder content.** Verify flags and semantics against sources.

Export cached packages as depot artifacts (`.tar.zst`), printing
`sha256  path` index lines to stdout. The producer end of the depot loop —
typically run by CI, per platform.

## Usage

```
envy export [<queries>...] -o <dir> [--manifest=<path>]
            [--depot-prefix=<url>] [--ignore-depot]
```

## Arguments & flags

| Argument / flag | Meaning |
| --- | --- |
| `queries` | Optional identity filters; no queries = every exportable package. |
| `-o, --output-dir <dir>` | Where archives are written. |
| `--manifest <path>` | Use this manifest instead of discovery. |
| `--depot-prefix <url>` | Prefix index lines with the depot URL. |
| `--ignore-depot` | Build from source rather than re-exporting depot hits — publishers should always set this (env: `ENVY_IGNORE_DEPOT`). |

Only [`EXPORTABLE`](/concepts/specs/install) content ships installed trees;
non-exportable specs export their fetched artifacts; user-managed packages
are never exported.

## Examples

```bash
ENVY_IGNORE_DEPOT=1 ./bin/envy export -o exports \
  --depot-prefix s3://acme-envy-packages/ > exports/macos-packages.txt
```

## See also

- [Running a Package Depot](/guides/package-depots) — the full CI loop.
- [`envy merge-depot`](./merge-depot.md), [`envy import`](./import.md)
