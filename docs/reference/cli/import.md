---
sidebar_position: 17
title: envy import
---

# `envy import`

> **Placeholder content.** Verify flags and semantics against sources.

Import exported package archives into the cache by hand. Normally the depot
does this transparently during `sync`; `import` is the manual path — sneaker-
net transfers, debugging depot artifacts, pre-seeding a machine.

## Usage

```
envy import [<archive>] [--dir=<dir>] [--manifest=<path>] [--checksums=<file>]
```

## Arguments & flags

| Argument / flag | Meaning |
| --- | --- |
| `archive` | A `.tar.zst` package archive, or a `.txt` index manifest. Mutually exclusive with `--dir`. |
| `--dir <dir>` | Import every archive in a directory. |
| `--manifest <path>` | Use this manifest instead of discovery. |
| `--checksums <file>` | Verify archives against an index file. |

## Examples

```bash
./bin/envy import exports/arm.gcc@r1-darwin-arm64-blake3-1a46f3.tar.zst
./bin/envy import --dir ./exports --checksums exports/packages.txt
```

## See also

- [Package Depots](/concepts/depots)
- [`envy export`](./export.md)
