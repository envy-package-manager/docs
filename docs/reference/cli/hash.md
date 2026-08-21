---
sidebar_position: 12
title: envy hash
---

# `envy hash`

> **Placeholder content.** Verify flags and semantics against sources.

Print `sha256sum`-style lines for files — the authoring-time tool for
building spec fingerprint tables and depot index entries.

## Usage

```
envy hash <paths...> [--prefix=<url>]
```

## Arguments & flags

| Argument / flag | Meaning |
| --- | --- |
| `paths` | Files (or directories — hashed as their contained archives) to hash. |
| `--prefix <url>` | Prepend a URL prefix to each name, producing depot-index-ready lines. |

## Examples

```bash
envy hash cmake-4.2.3-macos-universal.tar.gz
# c2302d3e...41b5b  cmake-4.2.3-macos-universal.tar.gz

envy hash exports/*.tar.zst --prefix s3://acme-envy-packages/
# lines that drop straight into a depot packages.txt
```

## See also

- [Writing a Spec](/guides/writing-a-spec) — fingerprint tables.
- [Running a Package Depot](/guides/package-depots)
