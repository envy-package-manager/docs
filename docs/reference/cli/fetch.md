---
sidebar_position: 13
title: envy fetch
---

# `envy fetch`

> **Placeholder content.** Verify flags and semantics against sources.

Download one resource exactly the way a spec's `FETCH` verb would — same
schemes, same behavior. A spec-authoring aid: test a URL before wiring it
into a spec.

## Usage

```
envy fetch <source> <destination> [--manifest-root=<path>] [--ref=<ref>]
```

## Arguments & flags

| Argument / flag | Meaning |
| --- | --- |
| `source` | URL (any scheme FETCH supports). Required. |
| `destination` | Where to write the result. Required. |
| `--ref <ref>` | Commit/ref for git sources. |
| `--manifest-root <path>` | Resolve relative/local sources against this root. |

## Examples

```bash
envy fetch https://example.com/tool-1.2.tar.gz /tmp/tool.tar.gz
envy fetch git://github.com/org/repo --ref 7bc9a0b... /tmp/repo
```

## See also

- [FETCH](/concepts/specs/fetch)
