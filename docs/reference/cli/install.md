---
sidebar_position: 2
title: envy install
---

# `envy install`

Install manifest packages into the cache and stop. No wrappers are written and no
bin directory is created. That is [`deploy`](./deploy.md)'s job, and
[`sync`](./sync.md) does both.

Use it when you want the bytes but not the integration. Warming a CI or Docker
cache, prefetching before going offline, or checking that a spec builds without
disturbing a bin directory you are debugging.

One thing does reach the project directory: a manifest that asks for
[vendoring](/concepts/vendoring) gets its vendored trees copied or checked here,
because they are part of installing rather than part of deploying. A manifest
with no `vendor` entries leaves the tree byte-identical. To run that step on its
own, for one package or with an exemption overridden, use
[`envy vendor`](./vendor.md).

## Usage

```
envy install [<queries>...] [--manifest=<path>] [--ignore-depot]
```

## Arguments and flags

| Argument or flag | Meaning |
| --- | --- |
| `queries` | Which manifest entries to install. See [query forms](./index.md#package-queries). No queries means everything. |
| `--manifest <path>` | Use this manifest instead of [discovery](/concepts/projects#manifest-discovery). |
| `--ignore-depot` | Ignore the [package depot](/concepts/depots) and build from source. Env: `ENVY_IGNORE_DEPOT`. |

There is no `--subproject` and no `--platform`. Discovery always walks to the
project root, and there are no scripts to write, so there is no flavor to
choose. Entries whose `platforms` filter excludes the current machine are
skipped, unless you name one explicitly, which is an error.

## Examples

### To warm a CI cache without touching the work tree

```bash
envy install
```

The tree is byte-identical afterward, so a later `git status` in the job still
means something. Pair it with a cache action keyed on the manifest's hash. A
manifest that vendors is the exception: those directories are written here, by
design, and a project that commits them wants `git status` to stay clean, which
it does when the copies already match.

### To build one package's Docker layer

```bash
RUN envy install envy.python@r1
```

This installs python and its dependencies only, so editing an unrelated package
in the manifest does not invalidate the layer.

### To prefetch everything before going offline

```bash
envy install
```

That is the whole step. The committed wrappers already work, and they resolve
their package out of the cache at call time, so nothing else has to happen before
the plane takes off. Add a `sync` only if you also edited the manifest, since
that is the case where a wrapper has to be written or pruned.

### To check that a spec still builds from source

```bash
ENVY_IGNORE_DEPOT=1 envy install local.armgcc@r0
```

This bypasses the depot and any published artifact, running the spec's real
`FETCH`, `STAGE`, `BUILD`, and `INSTALL` pipeline. It is the usual nightly CI
check that a spec has not rotted.

### To install a manifest that is not in your current directory

```bash
envy install --manifest ~/work/firmware/envy.lua
```

Useful from a scratch shell, or when driving envy from a script that knows the
manifest path but has no working directory inside the project.

## On Windows

`install` writes nothing into the bin directory on any platform, so it has no
`--platform` flag. Wrapper scripts, including the `.bat` twins, come from
[`deploy`](./deploy.md) or from [`sync`](./sync.md).

## See also

- [`envy sync`](./sync.md) for install plus deploy, the everyday command.
- [`envy deploy`](./deploy.md) for the other half.
- [The Cache](/concepts/cache) for where installed packages live and why deleting the cache is safe.
- [Vendoring](/concepts/vendoring) for the one thing `install` writes into the project, and [`envy vendor`](./vendor.md) for running that step alone.
