---
sidebar_position: 2
title: First Steps
---

# First Steps

A tour from a fresh clone to running project tools, and then the three commands
worth knowing.

## Run a tool

In a project that is already set up, there is nothing to do first:

```console
$ git clone https://github.com/acme/firmware && cd firmware
$ ./bin/cmake --version
[envy.cmake@r0] installed (8.2s)
cmake version 4.4.0
```

That one line of install output is the whole setup. `bin/cmake` is a committed
wrapper, it asked `bin/envy` for cmake's path, `bin/envy` downloaded the pinned
envy, and envy installed cmake. The second call prints only cmake's own output.

Only what that tool needed was installed, not the whole manifest. See
[Installation](./installation.md).

## Install everything at once

`sync` is the command for when on-demand is not what you want:

```console
$ ./bin/envy sync
[envy.cmake@r0] installed (8.2s)
[envy.ninja@r0] installed (1.1s)
[envy.python@r1] installed (31.4s)
deploy: 12 product script(s) (0 created, 0 updated, 12 unchanged, 0 removed)
```

One line per package, then one summary line for the bin directory. Reach for it
before going offline, after editing the manifest, and in CI when you want the job
to fail at install rather than mid-compile.

`sync` is idempotent and incremental. Running it again installs nothing and
prints the same deploy summary with everything unchanged.

## The three verbs

They are not synonyms.

| Command | Packages | Bin directory |
| --- | --- | --- |
| [`envy install`](../reference/cli/install.md) | installs | untouched |
| [`envy deploy`](../reference/cli/deploy.md) | untouched | written, refreshed, pruned |
| [`envy sync`](../reference/cli/sync.md) | installs | written, refreshed, pruned |

`install` is for warming a cache without touching the work tree, which is what
you want in a Docker layer or a CI cache step. `deploy` is for restoring a bin
directory you cleaned, or picking up a product a spec just added, without
reinstalling anything.

## Three ways to run project tools

1. **The wrappers.** `./bin/cmake`. Committed, zero setup, works in any shell and
   in CI. See [Product Scripts](/concepts/environment/product-scripts).
2. **[`envy run`](../reference/cli/run.md).** `envy run make -j` puts the bin
   directory on `PATH` for one command and sets `ENVY_PROJECT_ROOT`. Good for
   scripts, git hooks, and CI.
3. **[Shell integration](./shell-integration.md).** `cd` into the project and its
   tools are on `PATH` until you leave.

All three reach the same packages. Pick by context rather than by preference:
wrappers and `envy run` are deterministic anywhere, hooks are for interactive
work.

## Asking envy questions

```console
$ ./bin/envy product                      # every product, and who provides it
cmake          bin/cmake     envy.cmake@r0{version="4.4.0"}
ctest          bin/ctest     envy.cmake@r0{version="4.4.0"}
python3        bin/python3   envy.python@r1{version="3.13.14"}

$ ./bin/envy product cmake                # one product, resolved
/Users/you/Library/Caches/envy/packages/envy.cmake@r0/darwin-arm64-blake3-49a9b2620de8c380/pkg/bin/cmake

$ ./bin/envy package envy.cmake@r0        # the package's whole tree
/Users/you/Library/Caches/envy/packages/envy.cmake@r0/darwin-arm64-blake3-49a9b2620de8c380/pkg

$ ./bin/envy cache                        # what is on disk, largest first
Cache: /Users/you/Library/Caches/envy
...
```

`envy product <name>` installs the provider if it is missing, so it doubles as
"install just this one thing".

## Working on a subset

Queries select manifest entries by identity:

```bash
./bin/envy sync envy.cmake@r0     # this entry and its dependencies
./bin/envy install python         # matches any namespace and revision
```

See [query forms](../reference/cli/index.md#package-queries). One caveat worth
knowing early: a filtered `sync` prunes wrappers outside the filtered subgraph,
so follow it with a bare `sync` when you are done iterating.

## What is safe

- **Deleting the cache.** Everything in it is reconstructible. `rm -rf` is the
  supported cleanup tool.
- **Running `sync` repeatedly.** It is incremental, and a no-op when nothing
  changed.
- **Interrupting a run.** A partial install is never marked complete, so the next
  run redoes it. Verified downloads survive, so the retry is cheaper.

## Next

- [Shell integration](./shell-integration.md) for `cd`-based activation.
- [Adding Packages](../guides/adding-packages.md) for editing the manifest.
- [Concepts](/concepts) for how any of this works.
