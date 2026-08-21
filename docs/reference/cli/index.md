---
sidebar_position: 0
title: CLI Reference
slug: /reference/cli
---

# CLI Reference

`envy` is one binary with one subcommand per workflow. Most days you need one of
them, [`sync`](./sync.md). The rest exist for spec authors, depot publishers,
and CI.

## Conventions

These hold for every command, so the per-command pages do not repeat them.

**Global flags go before the subcommand.** Write `envy --verbose sync`. The
reverse, `envy sync --verbose`, is a parse error. Per-command flags go after the
subcommand.

**stdout is for machines, stderr is for you.** Progress, summaries, warnings,
and errors go to stderr. The commands whose output is the answer write it to
stdout: [`product`](./product.md), [`package`](./package.md),
[`hash`](./hash.md), [`export`](./export.md),
[`merge-depot`](./merge-depot.md), [`git-resolve`](./git-resolve.md),
[`import`](./import.md) for a single archive, [`cache`](./cache.md), and
`version --licenses`. Piping never captures decoration.

**Manifest-aware commands find the manifest by
[discovery](/concepts/projects#manifest-discovery)**, walking up from the current
directory to the project root. `--manifest` names one directly, and
`--subproject` stops the walk at the nearest one.

**Manifest-aware commands re-exec into the pinned envy.** If the manifest's
`@envy version` names a version other than the running binary, envy downloads
that version and hands off to it before doing any work. You get the version the
project pins, not the one you typed. `sync`, `install`, `deploy`, `product`,
`package`, `run`, `export`, and `import` do this. [`use`](./use.md) and
[`cache`](./cache.md) do not. They read the manifest header as text, so they keep
working when the pinned version cannot run. Set `ENVY_NO_REEXEC` to suppress the
hand-off while debugging.

**Exit status is 0 on success and non-zero on failure.** The exception is
[`envy run`](./run.md), which returns its child's exit code.

**Every command works the same on Windows.** Examples here use POSIX shell for
brevity. The Windows equivalents differ in the shell, not in envy:

| POSIX | Windows |
| --- | --- |
| `./bin/envy sync` | `bin\envy.bat sync` |
| `./bin/cmake` (deployed wrapper) | `bin\cmake.bat` |
| `~/Library/Caches/envy`, `~/.cache/envy` | `%LOCALAPPDATA%\envy` |
| `PATH` separated by `:` | separated by `;` |
| `envy shell zsh` prints `source "…/hook.zsh"` | `envy shell powershell` prints `. "…/hook.ps1"` |

The `--platform` flag on `sync`, `deploy`, and `init` selects which script
flavors to write, not which OS you are on. A repo synced on macOS with
`--platform all` commits working Windows wrappers. envy also disables
Windows-style `/flag` option prefixes. A POSIX-looking absolute path is never
mistaken for a flag.

## Package queries

`sync`, `install`, `deploy`, `export`, and `package` take queries that select
manifest entries. A query matches an entry's identity by dropping components,
not by substring:

| Query form | Matches |
| --- | --- |
| `cmake` | any namespace, any revision, so `envy.cmake@r0` and `local.cmake@r3` |
| `envy.cmake` | that namespace, any revision |
| `cmake@r0` | that revision, any namespace |
| `envy.cmake@r0` | that identity |
| `envy.cmake@r0{version="4.2.3"}` | one option variant, the full canonical key |

Each query resolves to the first matching entry in manifest order, and its
dependencies come along automatically. A query that matches nothing is an error.
So is one that matches an entry excluded on the current platform. A filter typo
fails instead of silently doing less.

## Global flags

| Flag | Effect |
| --- | --- |
| `--verbose` | DEBUG logging: per-package decision narrative, with timestamp and level. Excludes `-q`. |
| `-q`, `--quiet` | Warnings and errors only. |
| `--trace[=<sinks>]` | Structured machinery events for the scheduler, cache, locks, and IO. Comma-separated sinks: `stderr` for human-readable text, `file:<path>` for JSONL. Bare `--trace` means `stderr`. Independent of log level. See [Logging & Tracing](../observability.md). |
| `--cache-root <path>` | Override the cache root. Env: `ENVY_CACHE_ROOT`. |
| `-v`, `--version` | Print version info. Alias for [`envy version`](./version.md). |
| `-h`, `--help` | Print help. Works per subcommand: `envy sync --help`. |

## Commands

### Everyday

| Command | Purpose |
| --- | --- |
| [`envy sync`](./sync.md) | Install packages and deploy product scripts. The everyday command. |
| [`envy install`](./install.md) | Install packages only. |
| [`envy deploy`](./deploy.md) | Deploy product scripts only. |
| [`envy product`](./product.md) | Resolve a product to its path or value, or list all. |
| [`envy package`](./package.md) | Install one package and print its directory. |
| [`envy run`](./run.md) | Run your own script with `envy` resolvable and the project root known. |

### Project management

| Command | Purpose |
| --- | --- |
| [`envy init`](./init.md) | Initialize a project: manifest, bootstrap scripts, editor config. |
| [`envy use`](./use.md) | Retarget the manifest's pinned envy version. |
| [`envy shell`](./shell.md) | Print the shell-profile line that enables shell hooks. |
| [`envy cache`](./cache.md) | Show cache location and disk usage. |

### Spec authoring

| Command | Purpose |
| --- | --- |
| [`envy git-resolve`](./git-resolve.md) | Resolve a remote branch or tag to a full commit hash. |
| [`envy hash`](./hash.md) | Print `sha256` lines for fingerprint tables and depot indexes. |
| [`envy fetch`](./fetch.md) | Download one resource the way `FETCH` would. |
| [`envy extract`](./extract.md) | Extract an archive the way `STAGE` would. |
| [`envy lua`](./lua.md) | Run a Lua script inside envy's runtime. |

### Depot publishing

| Command | Purpose |
| --- | --- |
| [`envy export`](./export.md) | Export cached packages as depot artifacts. |
| [`envy import`](./import.md) | Import exported artifacts into the cache. |
| [`envy merge-depot`](./merge-depot.md) | Merge per-platform depot indexes. |

### Administration

| Command | Purpose |
| --- | --- |
| [`envy mirror-envy`](./mirror-envy.md) | Mirror an envy release to a directory or S3. |
| [`envy version`](./version.md) | Print version info and bundled licenses. |
