---
sidebar_position: 1
title: GitHub Actions
---

# GitHub Actions

There is no setup action to install, and no `envy` to put on `PATH`. A repo that
committed its bootstrap script and its wrappers already has everything CI needs.
Check out, restore the cache, and run the tools.

## The minimal job

```yaml title=".github/workflows/presubmit.yml"
on: [pull_request]

env:
  ENVY_CACHE_ROOT: ${{ github.workspace }}/.envy-cache

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - uses: actions/cache@v5
        with:
          path: ${{ env.ENVY_CACHE_ROOT }}
          key: envy-${{ runner.os }}-${{ runner.arch }}-${{ hashFiles('**/envy.lua') }}
          restore-keys: |
            envy-${{ runner.os }}-${{ runner.arch }}-

      - run: ./bin/cmake -S . -B build
      - run: ./bin/cmake --build build
```

Note what is missing. There is no `envy sync` step. `./bin/cmake` is a
[wrapper script](/concepts/environment/product-scripts) that calls
`envy product cmake`, which downloads the pinned envy on first use and installs
cmake on demand. Anything the build touches installs the same way, so the job
lists the tools it runs rather than a provisioning sequence.

Add an explicit `./bin/envy sync` step for either of two reasons. One, you want
the install to be its own timed step that fails on its own. Two, a later step
reads the bin directory instead of invoking a wrapper.

## Caching the envy cache

This is the only part of the integration that needs thought.

**Point `ENVY_CACHE_ROOT` somewhere predictable.** The platform default lives
outside the workspace and differs per runner OS. Setting it at the workflow level
gives every job one path to cache. If that path is inside the checkout, add it to
`.gitignore`, or a job that runs `git add .` will try to commit a toolchain.

**Key on OS, arch, and every manifest in the tree.** envy cache entries are
per-platform and per-architecture. An x86_64 cache does nothing for an arm64
runner. Manifests decide the package set, and a superproject has more than one.
`hashFiles('**/envy.lua')` covers all of them.

**Do not hash spec files into the key.** A package's cache entry is named by its
identity plus its options, not by the spec that built it. Editing a local spec
without bumping its revision or changing an option produces the same entry.
Hashing specs would churn the GitHub cache without changing what envy installs.
Bump the spec revision when its behavior changes. That is what revisions are
for.

**Use `restore-keys`.** `actions/cache` saves at the end of a job only when the
primary key missed. Three cases follow from that:

| Situation | What happens |
| --- | --- |
| Exact key hit | Everything restores, nothing installs, nothing is saved. |
| Manifest edited, prefix hit | The previous cache restores, envy installs only what changed, and the job saves a new entry under the new key. |
| No hit at all | Everything installs from scratch, and the job saves. |

The middle case is why `restore-keys` matters. Without it, changing one pinned
version throws away a multi-gigabyte toolchain and re-downloads all of it. A
partial restore is always safe. The cache is content-addressed and additive.
Entries envy does not recognize are ignored, and missing ones are fetched.

**Expect matrix jobs to race.** Several jobs on the same OS and arch share a key.
The first to finish saves, and the others log `Unable to reserve cache` and carry
on. That warning is not a failure.

**Watch the size.** GitHub keeps 10 GB per repository and evicts entries unused
for 7 days, so a wide toolchain can push older entries out. Two habits help. Run
`jlumbroso/free-disk-space` before large installs on Linux runners, and keep an
eye on what the cache holds with [`envy cache`](/reference/cli/cache).

## A real multi-platform workflow

Trimmed from a production firmware repo. The same three envy-related pieces
appear in every job, and everything else is ordinary CI.

```yaml title=".github/workflows/presubmit.yml"
on:
  pull_request:
  merge_group:

concurrency:
  group: ${{ github.workflow }}-${{ github.head_ref || github.run_id }}
  cancel-in-progress: true

env:
  ENVY_CACHE_ROOT: ${{ github.workspace }}/.envy-cache

jobs:
  build:
    name: build (${{ matrix.name }})
    runs-on: ${{ matrix.runner }}
    timeout-minutes: 30
    strategy:
      matrix:
        include:
          - { name: linux-x64,   runner: ubuntu-latest,  envy: ./bin/envy }
          - { name: linux-arm64, runner: ubuntu-arm64,   envy: ./bin/envy }
          - { name: mac-arm64,   runner: macos-latest,   envy: ./bin/envy }
          - { name: win-x64,     runner: windows-latest, envy: bin\envy.bat }
    steps:
      - name: Free disk space
        if: runner.os == 'Linux'
        uses: jlumbroso/free-disk-space@v1.3.1

      - uses: actions/checkout@v6

      - uses: actions/cache@v5
        with:
          path: ${{ env.ENVY_CACHE_ROOT }}
          key: envy-${{ runner.os }}-${{ runner.arch }}-${{ hashFiles('**/envy.lua') }}
          restore-keys: |
            envy-${{ runner.os }}-${{ runner.arch }}-

      - name: Install packages
        run: ${{ matrix.envy }} sync

      - name: Build and test
        run: ${{ matrix.envy }} run ./scripts/build.sh

  all-checks-pass:
    needs: [build]
    runs-on: ubuntu-latest
    if: always()
    steps:
      - name: Fail with upstream jobs
        run: exit 1
        if: needs.build.result != 'success'
```

Three details worth copying. The matrix carries the envy command per runner,
because Windows needs `bin\envy.bat`. `envy run` hands the build script the
project's bin directory and `ENVY_PROJECT_ROOT`, so the script needs to know
nothing about CI. And one `all-checks-pass` gate depending on every matrix leg
keeps branch protection stable while jobs come and go.

## Keeping the runner clean

CI runners are disposable, but host state is still worth being deliberate about.
[SETUP pairs](/concepts/specs/setup) run only when a manifest entry selects them,
so gate the ones that mutate a machine:

```lua title="envy.lua"
local ci = os.getenv("CI")

PACKAGES = {
  { spec = "acme.jlink@r1", source = specs .. "acme.jlink.lua",
    options = { version = "9.30" },
    setup = not ci and { "udev_rules" } or nil },
}
```

Everything else installs into the cache, so a job leaves nothing behind that the
next job could depend on by accident.

## Publishing to a depot

A depot export job is the one place where you do **not** want the cache.
Publishers have to build from source, so the workflow sets
`ENVY_IGNORE_DEPOT: 1` and restores nothing:

```yaml title=".github/workflows/envy-package-depot.yml"
on:
  schedule: [{ cron: "0 4 * * *" }]
  workflow_dispatch:

env:
  ENVY_CACHE_ROOT: ${{ github.workspace }}/.envy-cache
  ENVY_IGNORE_DEPOT: 1

jobs:
  export:
    runs-on: ${{ matrix.runner }}
    strategy:
      matrix:
        include:
          - { name: linux-x64, runner: ubuntu-latest,  envy: ./bin/envy }
          - { name: win-x64,   runner: windows-latest, envy: bin\envy.bat }
    steps:
      - uses: actions/checkout@v6
      - name: Export
        run: |
          mkdir -p envy-export
          ${{ matrix.envy }} export -o envy-export \
            --depot-prefix s3://acme-envy-packages/ > envy-export/${{ matrix.name }}.txt
      - uses: actions/upload-artifact@v7
        with:
          name: envy-export-${{ matrix.name }}
          path: envy-export/
```

A later job merges the per-platform indexes with
[`envy merge-depot`](/reference/cli/merge-depot) and uploads. See
[Running a Package Depot](../package-depots.md) for the whole loop.

## See also

- [`envy sync`](/reference/cli/sync) and [`envy run`](/reference/cli/run)
- [The Cache](/concepts/cache) for what is in the directory you are caching
- [Product Scripts](/concepts/environment/product-scripts) for why no setup step is needed
