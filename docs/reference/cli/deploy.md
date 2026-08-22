---
sidebar_position: 3
title: envy deploy
---

# `envy deploy`

Write, refresh, and prune the project's bin directory: one wrapper script per
`script` product, plus the `envy` bootstrap scripts. This is the other half of
[`sync`](./sync.md).

`deploy` resolves the dependency graph but installs nothing. A wrapper is four
lines of shell that calls `envy product <name>` at run time, so the package
behind it installs on first use. That makes `deploy` cheap, and makes a
committed bin directory enough to bootstrap a machine.

Only files carrying envy's `envy-managed` marker are created, updated, or
removed. A wrapper whose product no longer exists is pruned. A file without the
marker belongs to you: envy will not update it, prune it, or overwrite it. That
makes a hand-written `bin/gn` that wraps several products a supported pattern.
See [Product Scripts](/concepts/environment/product-scripts). Note `--strict`
reports such a file as a collision, so a project that owns a product's name
should use a plain `deploy`.

## Usage

```
envy deploy [<identities>...] [--manifest=<path>] [--strict] [--subproject]
            [--platform=posix|windows|all]
```

## Arguments and flags

| Argument or flag | Meaning |
| --- | --- |
| `identities` | Which manifest entries' products to deploy. See [query forms](./index.md#package-queries). None means all. |
| `--manifest <path>` | Use this manifest instead of [discovery](/concepts/projects#manifest-discovery). |
| `--strict` | Error instead of skipping when a bin directory file collides with a product script name and is not envy-managed. |
| `--subproject` | Stop discovery at the nearest manifest instead of walking to the project root. Mutually exclusive with `--manifest`. |
| `--platform posix\|windows\|all` | Which wrapper flavors to write and prune. Defaults to the current OS. |

`@envy bin` is required, and envy creates the directory if it is missing.
Deployment also requires `@envy deploy "true"` in the manifest header. Without
it, `deploy` refreshes the bootstrap scripts, warns that deployment is disabled,
and writes no wrappers.

## Examples

### To restore a bin directory you cleaned or gitignored

```bash
envy deploy
```

This recreates every wrapper from the manifest and refreshes `bin/envy` and
`bin/envy.bat`. No packages are installed, so it is quick. The only thing that
has to be reachable is the specs.

### To pick up a new product without reinstalling

```bash
envy deploy
```

Run this after adding `ctest` to a spec's `PRODUCTS`, or after bumping a spec
revision that renamed one. `deploy` writes the new wrapper and prunes the old
one. The package in the cache is untouched.

### To commit wrappers for every platform the repo supports

```bash
envy deploy --platform all
```

This writes POSIX scripts and `.bat` files together. Pruning follows the same
flag, so `--platform posix` on a Linux CI box cannot delete the Windows wrappers
your colleagues rely on.

### To assert in CI that the committed bin directory is current

```bash
envy deploy --platform all --strict
git diff --exit-code bin/
```

A stale or missing wrapper fails the job, and `--strict` turns a shadowing file
into an error instead of a skip.

### To deploy only one component of a superproject

```bash
cd tools/codegen && ../.envy deploy --subproject
```

:::warning
Filtering by identity narrows the graph, and pruning follows the narrowed graph.
`deploy envy.cmake@r0` leaves cmake's wrappers and removes the other
envy-managed ones. Use a bare `deploy` unless you want that.
:::

## See also

- [Product Scripts](/concepts/environment/product-scripts) for the wrapper contract and the `envy-managed` marker.
- [Products](/concepts/specs/products) for `script = true` versus `script = false`.
- [`envy sync`](./sync.md) for install plus deploy in one step.
