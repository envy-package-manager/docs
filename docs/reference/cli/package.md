---
sidebar_position: 5
title: envy package
---

# `envy package`

Ensure one package and its dependencies are installed, then print its absolute
package directory to stdout. This is the identity-oriented counterpart to
[`envy product`](./product.md). Use it when you need the tree rather than a
single named entry point.

Typical consumers are build systems and scripts. They want an include directory,
a sysroot, or a share directory that the spec's author never gave a product
name.

## Usage

```
envy package <identity> [--manifest=<path>] [--ignore-depot]
```

## Arguments and flags

| Argument or flag | Meaning |
| --- | --- |
| `identity` | Which manifest entry to install. Required. See [query forms](./index.md#package-queries). |
| `--manifest <path>` | Use this manifest instead of [discovery](/concepts/projects#manifest-discovery). |
| `--ignore-depot` | Ignore the [package depot](/concepts/depots) and build from source. Env: `ENVY_IGNORE_DEPOT`. |

The query has to land on exactly one thing. Matching several distinct identities
is an error that lists them, and so is matching one identity configured with two
different `options` sets. Add namespace, revision, or the full canonical key to
disambiguate:

```bash
envy package python                       # error: ambiguous
envy package envy.python@r1               # error: two option variants
envy package 'envy.python@r1{version="3.13.14",provide_python3=true}'
```

Two other errors: a query naming an entry excluded on this platform, and a query
naming a package that is not cache-managed. A
[user-managed](/concepts/specs/user-managed) package has no cache tree to print.

## Examples

### To get an include directory for a compiler flag

```bash
DOCTEST="$(envy package envy.doctest-cpp@r0)"
clang++ -I"$DOCTEST" test.cpp
```

### To install one package and inspect what it laid down

```bash
ls "$(envy package envy.cmake@r0)"
# bin  doc  man  share
```

The printed path is the package's `pkg/` tree, the installed root that products
resolve relative to.

### To pre-seed a single dependency in a container build

```bash
RUN envy package envy.ninja@r0 > /dev/null
```

This installs ninja and its dependencies without deploying wrappers or touching
the rest of the manifest.

### To rebuild one package from source while debugging its spec

```bash
envy package --ignore-depot local.armgcc@r0
```

## See also

- [`envy product`](./product.md) for resolving a named entry point instead of a tree.
- [The Cache](/concepts/cache) for why you resolve paths instead of hardcoding them.
