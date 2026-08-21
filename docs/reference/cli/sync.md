---
sidebar_position: 1
title: envy sync
---

# `envy sync`

Install every package the manifest requests, then deploy product wrapper scripts
into the project's bin directory. `sync` is [`install`](./install.md) plus
[`deploy`](./deploy.md). Run it after cloning, after editing the manifest, and
whenever you are unsure. It is idempotent and incremental.

A run does the following, in order:

1. Re-exec into the envy version the manifest pins.
2. Refresh the `.luarc.json` type paths for that version.
3. Install every target package concurrently, skipping anything already cached.
4. Restamp the bootstrap scripts.
5. Write, refresh, and prune the product wrappers in the bin directory.

## Usage

```
envy sync [<queries>...] [--manifest=<path>] [--strict] [--subproject]
          [--platform=posix|windows|all] [--ignore-depot]
```

## Arguments and flags

| Argument or flag | Meaning |
| --- | --- |
| `queries` | Which manifest entries to sync. See [query forms](./index.md#package-queries). No queries means everything. |
| `--manifest <path>` | Use this manifest instead of [discovery](/concepts/projects#manifest-discovery). |
| `--strict` | Error instead of skipping when a file in the bin directory collides with a product script name and is not envy-managed. |
| `--subproject` | Stop discovery at the nearest manifest instead of walking to the project root. Mutually exclusive with `--manifest`. |
| `--platform posix\|windows\|all` | Which wrapper flavors to write: shell scripts, `.bat` files, or both. Defaults to the current OS. |
| `--ignore-depot` | Ignore the [package depot](/concepts/depots) and build from source. Env: `ENVY_IGNORE_DEPOT`. |

`@envy bin` is required, because `sync` has nowhere to deploy without it. envy
creates the bin directory if it is missing. Deployment also needs
`@envy deploy "true"`. Without it, packages install and `sync` warns that
deployment is off.

## Examples

### To get a freshly cloned project ready to build

```bash
./bin/envy sync
```

That is the whole onboarding step. The committed `bin/envy` bootstrap script
downloads the pinned envy, which installs every package and deploys a wrapper
per product. `./bin/cmake` then works on a machine that has never seen cmake.

### To pick up a package you just added to the manifest

```bash
./bin/envy sync
```

The same command. Cached packages are skipped, the new one installs, and the new
product's wrapper appears in the bin directory.

### To install one package while iterating on its spec

```bash
./bin/envy sync envy.cmake@r0
```

Dependencies come along. Unrelated packages are left alone.

:::warning
A filtered `sync` only knows about the filtered subgraph, and the deploy step
prunes envy-managed wrappers it does not recognize. In a project with ten
products, `sync envy.cmake@r0` leaves cmake's wrappers and removes the others.
Run a bare `./bin/envy sync` to restore them.
:::

### To commit wrappers for a platform you are not on

```bash
./bin/envy sync --platform all
```

This writes both the POSIX scripts and the `.bat` files, so a Windows colleague
gets working wrappers from a repo synced on macOS. Pruning is limited to the
flavors you name, so `--platform posix` never touches `.bat` files.

### To sync only the component you are standing in

```bash
cd libs/firmware && ../../bin/envy sync --subproject
```

In a [superproject](/concepts/projects#manifest-discovery), discovery normally
walks up to the manifest marked `@envy root "true"`. `--subproject` stops at the
nearest manifest instead, syncing that component's packages into that
component's bin directory.

### To verify a build from source, ignoring prebuilt artifacts

```bash
./bin/envy sync --ignore-depot
```

Or set `ENVY_IGNORE_DEPOT=1` in the environment, which is the usual form in CI.
Every package rebuilds through its full pipeline instead of downloading from the
depot. This checks that a spec still builds, not just that someone once
published it.

### To catch a name collision instead of skipping it

```bash
./bin/envy sync --strict
```

Without `--strict`, a hand-written `bin/format` that shadows a `format` product
is left in place and skipped. With it, the run fails and names the file. Worth
having in CI.

### To see why a package rebuilt

```bash
envy --verbose sync
envy --trace=file:/tmp/sync.jsonl sync
```

`--verbose` narrates each package's decisions. `--trace` records the machinery
underneath. Both are [global flags](./index.md#global-flags), so they go before
the subcommand.

## See also

- [First Steps](/getting-started/first-steps) for the sync, install, and deploy triangle.
- [Product Scripts](/concepts/environment/product-scripts) for what gets written to the bin directory.
- [`envy install`](./install.md) and [`envy deploy`](./deploy.md) for the two halves.
