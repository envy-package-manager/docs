---
sidebar_position: 7
title: The Cache
---

# The Cache

One per-user store serves every project on the machine. It is content-addressed,
safe under concurrent use, and always safe to delete.

Nothing outside the cache points into it by absolute path. Projects resolve paths
through [`envy product`](../reference/cli/product.md) and
[`envy package`](../reference/cli/package.md) at call time, so the cache can be
deleted, moved, or rebuilt without touching a single project.

## What is in it

```
~/Library/Caches/envy/
├── envy/
│   ├── 0.1.9/            # envy binaries, one directory per pinned version
│   ├── 0.1.10/
│   └── latest            # the newest version envy has resolved, a bare string
├── locks/                # per-entry lock files, empty between runs
├── packages/
│   └── envy.cmake@r0/
│       └── darwin-arm64-blake3-49a9b2620de8c380/
│           ├── envy-complete
│           └── pkg/      # the installed package
├── shell/
│   ├── hook.bash
│   ├── hook.zsh
│   ├── hook.fish
│   └── hook.ps1
└── specs/
    └── envy.package-specs@r3/
        └── blake3-2598ffe12c0d51fd/
            ├── envy-complete
            └── pkg/      # the fetched spec or bundle
```

Five things live there. envy's own pinned binaries, so several projects can pin
several versions. Fetched specs and bundles. Installed package trees. The shell
hook files [`envy shell`](../reference/cli/shell.md) points your profile at. And
lock files, which exist only while work is in flight.

## Content addressing

A package entry is named `<identity>/<platform>-<arch>-blake3-<hash>`, where the
hash covers the identity, the serialized options, and any resolved
[weak dependency](./dependencies/resolution.md) keys.

Two consequences fall out of that. Different option sets coexist rather than
overwrite, so a project can hold two Pythons at once. And ten projects that pin
the same package with the same options share one entry, so the second project to
ask for cmake 4.4.0 installs nothing.

Bumping an option does not modify an entry, it names a new one. The old tree stays
until you delete it, which is why `envy cache` sometimes shows two variants of
one identity.

Deliberately not in the hash: [setup-pair selections](./specs/setup.md) and depot
configuration. The same artifact serves a machine that selected `udev_rules` and
one that did not.

## Where the root lives

| Platform | Default |
| --- | --- |
| macOS | `~/Library/Caches/envy` |
| Linux | `$XDG_CACHE_HOME/envy`, or `~/.cache/envy` |
| Windows | `%LOCALAPPDATA%\envy` |

Precedence, highest first:

1. `--cache-root <path>`
2. `ENVY_CACHE_ROOT`
3. The discovered manifest's `@envy cache-posix` or `@envy cache-win` directive.
   A relative path anchors to the manifest's directory, never the working
   directory.
4. The platform default.

envy reads that directive out of the manifest as text and never runs the
manifest's Lua to get it, so a broken manifest above your working directory
cannot break a cache lookup.

The most common reason to move it is CI, where the cache has to sit somewhere the
runner's cache action can archive:

```yaml
env:
  ENVY_CACHE_ROOT: ${{ github.workspace }}/.envy-cache
```

See [GitHub Actions](../guides/integrations/github-actions.md) for the rest of
that setup, including what to key the cache on.

## Guarantees

- **Concurrent processes are safe.** Each entry is file-locked, so two
  `envy sync` runs in two terminals cooperate rather than corrupt. Locks live in
  `locks/` and are per entry, so unrelated packages still install in parallel.
- **A partial install is never visible.** The `envy-complete` marker is written
  last, after `INSTALL` reports success. An interrupted run leaves an unmarked
  entry, which the next run redoes.
- **Retries are cheap.** A failed attempt keeps `fetch/`, so verified downloads
  survive and the next attempt resumes from bytes already on disk.
- **A finished entry is never re-validated.** No timestamp checks and no
  re-hashing. A package is done until its identity changes or you delete it.

## Reclaiming space

There is no `envy cache clean`. Everything is reconstructible from the manifest,
so deletion is the cleanup tool. [`envy cache`](../reference/cli/cache.md) shows
what is worth deleting:

```console
$ ./bin/envy cache
Cache: /Users/you/Library/Caches/envy

Packages:
  envy.python@r1/darwin-arm64-blake3-f92708b498a20257  257.25MB
  envy.cmake@r0/darwin-arm64-blake3-49a9b2620de8c380   240.93MB
  envy.ninja@r0/darwin-arm64-blake3-268bff6f91bfacc4     2.14MB

Envy deployments:
  0.1.10                                                 5.72MB
  0.1.9                                                  5.69MB

Other:
  specs                                                180.00KB
  shell                                                 32.00KB
  locks                                                      0B

  TOTAL                                                514.36MB
```

Then delete whatever you no longer want, at whatever granularity:

```bash
CACHE="$(envy cache | head -1 | cut -d' ' -f2)"

rm -rf "$CACHE/packages/envy.cmake@r0"   # one identity, every variant
rm -rf "$CACHE/envy/0.1.9"               # an envy version nothing pins now
rm -rf "$CACHE"                          # all of it
```

The next command in any project reinstalls what that project needs. The only cost
is download and build time.

## A note on fetched artifacts

A completed entry usually holds only `pkg/`, because envy deletes the downloads
once the package is installed. An entry for a spec that is not `EXPORTABLE`
keeps its `fetch/` directory instead, so a [depot](./depots.md) can publish the
downloaded artifacts for a package whose install has to run per machine. Seeing
`fetch/` next to `pkg/` is that case, not a leak.

## See also

- [`envy cache`](../reference/cli/cache.md) for the command.
- [The Package Lifecycle](./specs/lifecycle.md) for what writes each directory.
- [Package Depots](./depots.md) for sharing entries between machines.
