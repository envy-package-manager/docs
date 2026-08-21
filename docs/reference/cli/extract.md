---
sidebar_position: 14
title: envy extract
---

# `envy extract`

> **Placeholder content.** Verify flags and semantics against sources.

Extract an archive exactly the way a spec's `STAGE` verb would — same format
support, same selective-extraction globs. Test your `strip`/`only` choices
before writing them into a spec.

## Usage

```
envy extract <archive> [<destination>] [--only=<path|glob>]...
```

## Arguments & flags

| Argument / flag | Meaning |
| --- | --- |
| `archive` | Archive file (anything libarchive reads: tar, zip, zstd, ...). Required. |
| `destination` | Output directory; default TBD (document). |
| `--only <path\|glob>` | Selective extraction; repeatable. Same glob rules as STAGE's `only`. |

## Examples

```bash
envy extract cmake.tar.gz /tmp/cmake
envy extract llvm.tar.zst /tmp/ct --only 'bin/clang-format*' --only 'LICENSE*'
```

## See also

- [STAGE](/concepts/specs/stage) — glob rules, `strip` semantics.
