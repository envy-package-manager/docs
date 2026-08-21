---
sidebar_position: 20
title: envy version
---

# `envy version`

> **Placeholder content.** Verify flags and semantics against sources.

Print version information.

## Usage

```
envy version [--licenses]
```

## Flags

| Flag | Meaning |
| --- | --- |
| `--licenses` | Print the licenses of every third-party component bundled in the envy binary. |

Note the interplay with pinning: inside a project, the reported version is
the manifest-pinned envy actually running, which may differ from whatever
binary you invoked.

## Examples

```bash
./bin/envy version
./bin/envy version --licenses | less
```
