---
sidebar_position: 5
title: envy package
---

# `envy package`

> **Placeholder content.** Verify flags and semantics against sources.

Ensure one package (plus its transitive dependencies) is installed, then
print its absolute package directory to stdout. The identity-oriented sibling
of [`envy product`](./product.md) — use it when you need the package's tree,
not a single named entry point.

## Usage

```
envy package <identity> [--manifest=<path>] [--ignore-depot]
```

## Arguments & flags

| Argument / flag | Meaning |
| --- | --- |
| `identity` | Package identity; partial matches accepted. |
| `--manifest <path>` | Use this manifest instead of discovery. |
| `--ignore-depot` | Skip depot lookups; build from source. |

Exit status: 0 with the path on stdout; 1 with `not found`.

## Examples

```bash
./bin/envy package envy.doctest-cpp      # .../packages/envy.doctest-cpp@r0/<hash>/pkg
DOCTEST_DIR="$(./bin/envy package envy.doctest-cpp)"
```

## See also

- [The Cache](/concepts/cache) — why you resolve paths instead of hardcoding
  them.
