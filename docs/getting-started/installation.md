---
sidebar_position: 1
title: Installation
---

# Installation

envy has no installation of its own. A project commits a small bootstrap script,
and that script downloads the exact envy version the project pins, the first
time something needs it.

## Joining an existing project

Clone the repo and run the tool you came for:

```bash
git clone https://github.com/acme/firmware
cd firmware
./bin/cmake --version
```

That is the whole procedure. There is no install step and no `envy sync` to run
first. The first call does the work:

1. `bin/cmake` is a committed [wrapper script](/concepts/environment/product-scripts)
   that asks `bin/envy` where cmake is.
2. `bin/envy` is a committed bootstrap script. It downloads the pinned envy
   release into the cache.
3. envy installs cmake, and cmake runs.

Later calls skip straight to the last step. The first call installs only what
that tool needs, not the whole manifest, so trying one tool in an unfamiliar
repo is cheap.

[`envy sync`](/reference/cli/sync) exists for maintaining the bin directory after
a manifest edit, and for installing everything up front rather than on demand.
Using a project that is already set up does not require it.

If a project deploys no wrappers, its entry point is
[`envy run`](/reference/cli/run) instead:

```bash
./bin/envy run ./scripts/build.sh
```

Same story. The bootstrap script fetches the pinned envy, and the script resolves
what it needs as it goes.

## Starting a new project

You need one throwaway envy binary, once. Download any release, run
[`envy init`](/reference/cli/init), commit the result, and delete the binary:

```bash
/tmp/envy init . ./bin --pin-sums --deploy=true
```

The project is self-bootstrapping from then on. See
[Starting a Project](/guides/new-project) for the full walkthrough.

`init` writes the `envy.lua` manifest, the `bin/envy` and `bin/envy.bat`
bootstrap scripts, and a `.luarc.json` for editor support. Commit all of it,
along with the product wrappers `sync` deploys later.

## Where envy keeps its data

One cache, shared by every project on the machine unless a project asks for its
own tree:

| Platform | Default location |
| --- | --- |
| macOS | `~/Library/Caches/envy` |
| Linux | `$XDG_CACHE_HOME/envy`, or `~/.cache/envy` |
| Windows | `%LOCALAPPDATA%\envy` |

Override it with `ENVY_CACHE_ROOT` or `--cache-root`. A project can also keep
its packages inside its own tree with `@envy cache-local`, and you can switch
either way per project with `envy cache --local` / `--shared`. Deleting the
cache is always safe. See [The Cache](/concepts/cache).

## Supported platforms

macOS, Linux, and Windows, on arm64 and x86_64. Windows is a supported target
rather than a WSL footnote, with its own `bin\envy.bat` bootstrap script and
`.bat` wrappers.

## Private networks and air-gapped machines

A project can point bootstrap at your own mirror instead of envy's GitHub
releases, with `@envy mirror` in the manifest or `ENVY_MIRROR` in the
environment. Populate the mirror with
[`envy mirror-envy`](/reference/cli/mirror-envy). See
[Reproducibility](/concepts/reproducibility) for the trust chain that keeps a
mirror from needing extra trust.
