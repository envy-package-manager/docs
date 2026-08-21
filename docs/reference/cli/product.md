---
sidebar_position: 4
title: envy product
---

# `envy product`

> **Placeholder content.** Verify flags and semantics against sources.

Resolve a named product to its concrete path or value, printed to stdout.
Omit the name to list every product. This is the universal integration
primitive — build systems, scripts, and the deployed wrappers themselves all
consume it.

## Usage

```
envy product [<product>] [--manifest=<path>] [--json]
```

## Arguments & flags

| Argument / flag | Meaning |
| --- | --- |
| `product` | Product name; omit to list all products. |
| `--manifest <path>` | Use this manifest instead of discovery. |
| `--json` | Machine-readable dump of every product at once. |

Works for `script = false` products too — a header-only library's
`doctest_cpp_h` resolves to an absolute file path with no wrapper involved.

## Examples

```bash
./bin/envy product cmake                 # /Users/you/.../pkg/bin/cmake
./bin/envy product doctest_cpp_h         # absolute path to doctest.h
./bin/envy product --json                # everything, for build-system ingestion
CC="$(./bin/envy product arm-none-eabi-gcc)"
```

## See also

- [Products](/concepts/specs/products)
- [Build Systems](/guides/integrations/build-systems)
