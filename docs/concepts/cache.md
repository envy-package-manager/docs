---
sidebar_position: 7
title: The Cache
---

# The Cache

One content-addressed store, safe under concurrent use and always safe to delete.
By default it is per-user and serves every project on the machine, so ten projects
that want the same cmake install it once. A project can instead keep its packages
inside its own tree, and you can override that choice per project. See
[Where the root lives](#where-the-root-lives).

Nothing outside the cache points into it by absolute path. Projects resolve paths
through [`envy product`](../reference/cli/product.md) and
[`envy package`](../reference/cli/package.md) at call time, so the cache can be
deleted, moved, or rebuilt without touching a single project.

## What is in it

```
~/Library/Caches/envy/
├── envy/
│   ├── 0.1.9/
│   ├── 0.1.10/
│   │   ├── envy          # the binary itself
│   │   └── envy.lua      # Lua type definitions, what .luarc.json points at
│   └── latest            # a bare version string, no newline
├── locks/                # per-entry lock files, empty between runs
├── packages/
│   └── envy.cmake@r0/
│       └── darwin-arm64-blake3-49a9b2620de8c380/
│           ├── envy-complete
│           └── pkg/      # the installed package
├── shell/                    # user-wide tree only, never a project-local one
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

Five things live there. envy's own binaries, one directory per version, so
several projects can pin several versions. Fetched specs and bundles. Installed
package trees. The shell hook files
[`envy shell`](../reference/cli/shell.md) points your profile at. And lock files,
which exist only while work is in flight.

Two of those are worth a note:

- **`envy/latest`** is written by whichever envy last ran, and only when that
  version is newer than what the file already says. It is how an unpinned project
  gets a version without going to the network: the bootstrap script reads it
  first, and uses it when the matching binary is present. A project with
  `@envy version` ignores it entirely. See
  [what happens without a version pin](./reproducibility.md#what-happens-without-a-version-pin).
- **`shell/`** holds one hook per shell, not one per envy version. Each file
  carries its own version number internally, and any envy command rewrites a
  hook that is older than the one it ships:

  ```shell-session
  $ envy install
  Shell hook updated (zsh) — restart your shell
  ```

  So the hook your profile sources keeps up with envy without you editing
  anything. `shell/` exists only in the user-wide tree. A project on its own
  cache tree writes no hooks at all, for the reasons in
  [Shell Hooks](./environment/shell-hooks.md#hooks-are-a-user-wide-feature).

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

Left out of the hash on purpose: [setup-pair selections](./specs/setup.md) and
depot configuration. The same artifact serves a machine that selected `udev_rules` and
one that did not.

## Where the root lives

There are two answers, and a project picks which one is its default.

**Shared** is the user-wide store, and what you get when a manifest says nothing:

| Platform | Default |
| --- | --- |
| macOS | `~/Library/Caches/envy` |
| Linux | `$XDG_CACHE_HOME/envy`, or `~/.cache/envy` |
| Windows | `%LOCALAPPDATA%\envy` |

**Local** is a tree inside the project, so deleting the project deletes every
package it downloaded. A manifest asks for it by naming where the tree goes:

```lua
-- @envy cache-local "out/.envy"
```

Naming the tree is what turns local mode on. A `cache-local` that needed a
second directive to take effect would sit in a manifest doing nothing. Point it
at whatever directory your build already deletes, and `rm -rf out` becomes a
complete teardown. If you want local mode but do not care where, omit it and
envy uses `.envy/cache` beside the manifest.

### Picking the other one

Whichever the project declares, you can override it for your own checkout:

```shell-session
$ envy cache --local     # keep this project's packages inside the project
$ envy cache --shared    # use the shared cache instead
```

That writes a zero-byte marker file next to the manifest, `.envy-cache-local`
or `.envy-cache-shared`, and the marker outranks the manifest from then on. The
marker exists only when your choice *differs* from what the project declares, so
`envy cache --local` on a project that already defaults local just clears it.
Both markers present at once is an error. envy never writes that state.

`envy init` adds `.envy/` and `.envy-cache-*` to `.gitignore`, so a marker is
yours alone and never travels in a commit.

`envy cache --local` and `--shared` deploy envy into the tree the project is
about to use, not the one still recorded, so switching a fresh clone to the
shared cache costs no download when you already have that version.

### A local tree reads the user-wide one

A local tree never writes outside the project, which is the whole point of
asking for one. It does *read* the user-wide tree for exactly one thing: an envy
binary of the pinned version that is already sitting there. A version-pinned
envy is the same bytes in every project, so re-downloading it per checkout is
pure waste.

The bootstrap scripts and the re-exec path try candidates in this order:

1. `<this project's cache>/envy/<version>/envy`
2. `<user-wide cache>/envy/<version>/envy`, only for a local tree, and only when
   the manifest has no `@envy sha256sums`

A candidate that is not a regular, non-empty, executable file is skipped rather
than run. If neither exists, envy is downloaded to a temp directory and exec'd
from there.

Three properties are worth knowing:

- **It is read-only.** The binary that ends up running still self-deploys into
  the project's own tree, so a populated local cache stays runnable after being
  tarred to a machine with no user-wide cache at all.
- **A sums pin turns it off.** The lock-free fast path never re-hashes what it
  finds, and every other project on the machine writes to the user-wide tree, so
  a project that pins `@envy sha256sums` must not run bytes it never attested.
  It downloads instead.
- **It never goes the other way.** A project on the shared cache does not look
  inside a project-local tree. A hostile clone shipping its own
  `envy/<version>/envy` would otherwise be arbitrary code execution on the first
  run.

Everything a local run *writes* stays inside the project: package entries, spec
entries, `envy/`, `envy/latest`, and `locks/`. Shell hooks are not written at
all. `envy cache --shared` is the one command that writes to the user-wide tree
on a local project's behalf, and only because it is the command that stops the
project being local.

[`envy cache --user-wide-root`](../reference/cli/cache.md) prints the second
tree, the way `--root` prints the first.

Two more directives exist for projects that need them:

| Directive | Default | What it does |
| --- | --- | --- |
| `cache-local "<path>"` | none | Where the local tree goes. Declaring it makes local the project's default. |
| `cache-mode "local"` / `"shared"` | implied by `cache-local` | Overrides that implication. Use `"shared"` to declare where `--local` *would* put the tree while still defaulting to the user-wide cache. |
| `state-dir "<path>"` | the manifest's directory | Where the override markers live. |

Point `state-dir` at your build directory and one `rm -rf` erases the cache and
your mode choice together, at the cost that `envy cache --shared` no longer
survives a clean. Left alone, the markers sit beside the manifest and a cache
wipe cannot silently revert you.

### The rules those paths follow

`cache-local` and `state-dir` are **relative literals**: one or more path
components, no `..`, no leading separator, no drive letter, and no `~`, `$VAR`
or `%VAR%`. Nothing is expanded, on any platform. That is on purpose. The two
bootstrap launchers and the envy binary each have to resolve the cache root
independently, and a shell-expansion grammar is not something `bash` and
`cmd.exe` can be made to agree on. One relative literal reads the same
everywhere, which is also why there is a single `cache-local` rather than the
per-platform `cache-posix`/`cache-win` pair it replaced.

An absolute cache root is `ENVY_CACHE_ROOT`'s job, not a directive's.

### Full precedence

Highest first:

1. `--cache-root <path>` or `ENVY_CACHE_ROOT`. Must be absolute.
2. A `.envy-cache-local` / `.envy-cache-shared` marker in the state directory.
3. `@envy cache-mode`.
4. `@envy cache-local` being present at all, which means local.
5. Otherwise shared: the platform default.

Tiers 2 through 5 all resolve relative to the manifest's directory, never the working
directory, so one manifest names one cache tree from wherever you run. envy reads
the directives out of the manifest as text and never runs its Lua to get them, so
a broken manifest above your working directory cannot break a cache lookup. Under
`--cache-root` envy does not read a manifest at all.

`envy cache` tells you which tier won:

```shell-session
$ envy cache | head -1
Cache: /Users/you/src/firmware/out/.envy  (@envy cache-local)
```

### The first time a local tree is used

A project-local tree gets a notice before any packages land:

```shell-session
$ envy install
Caching packages in /Users/you/src/firmware/out/.envy
  These packages live inside the project, so deleting it deletes them.
  To share one cache across all your projects, run: ./bin/envy cache --shared
```

The shared cache gets no notice. It is the default and it outlives any one
project, so naming it tells you nothing you can act on.

It is a notice, not a prompt. Nothing blocks, and CI is unaffected. It goes to
stderr, which keeps `envy cache --root` parseable and lets `-q` silence it. It
stops once the tree holds packages and comes back after you delete the tree, so
it is always telling you something true.

### Moving it for CI

The most common reason to override is CI, where the cache has to sit somewhere
the runner's cache action can archive:

```yaml
env:
  ENVY_CACHE_ROOT: ${{ github.workspace }}/.envy-cache
```

An environment variable is the right tool there: it is absolute, it applies to
the whole job, and it leaves no marker behind in the checkout. See
[GitHub Actions](../guides/integrations/github-actions.md) for the rest of that
setup, including what to key the cache on.

### Version requirement

`cache-local`, `cache-mode` and `state-dir` require **envy 0.2.0 or newer**. An
older envy ignores directives it does not know, so it would quietly use the
shared cache for a project asking for a hermetic tree. Rather than let that
happen silently, the bootstrap launchers and the re-exec path both refuse to run
an envy older than 0.2.0 against a manifest using them. If your manifest pins an
earlier `@envy version`, raise it.

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

## Windows specifics

The cache works the same way, with three details that only exist there:

- **Long paths.** Cache trees nest deeply, and a content-addressed entry
  directory name is long. envy opts out of `MAX_PATH` at the cache root by
  prefixing its own scans, so a deep entry is not a problem even without the
  system-wide long-path policy enabled. The prefixed form is internal and never
  printed.
- **Antivirus.** Defender and the Search indexer hold handles on freshly written
  files, which makes a delete fail for a moment. envy retries deletions with
  backoff rather than failing the run. A directory that will not go away after
  the retries is usually an open handle in another process.
- **Paths in output.** Everything envy prints or hands to a Lua phase uses the
  platform separator, so cache paths look like
  `C:\Users\you\AppData\Local\envy\packages\envy.cmake@r0\windows-x86_64-blake3-...\pkg`.
  Build `.bat` and PowerShell strings with
  [`envy.path.join`](../reference/lua-api.md#paths) rather than hardcoding a
  separator.

## Reclaiming space

There is no `envy cache clean`. Everything is reconstructible from the manifest,
so deletion is the cleanup tool. [`envy cache`](../reference/cli/cache.md) shows
what is worth deleting:

```shell-session
$ envy cache
Cache: /Users/you/Library/Caches/envy  (default)

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
CACHE="$(envy cache --root)"

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
