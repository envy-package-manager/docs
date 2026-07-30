---
sidebar_position: 5
title: CLI Reference
---

# CLI Reference

> **Placeholder content.** Covers the commands most users need, not the full
> surface. Verify against the envy sources before publishing.

## Global flags

Accepted by every subcommand.

| Flag                     | Effect                                            |
| ------------------------ | ------------------------------------------------- |
| `--verbose`              | DEBUG narrative: why each decision was made.      |
| `-q`, `--quiet`          | Warnings and errors only.                         |
| `--trace[=stderr\|file:<path>]` | Structured JSONL machinery events.          |
| `--cache-root=<path>`    | Override the cache root (env: `ENVY_CACHE_ROOT`).  |
| `-v`, `--version`        | Print version.                                    |
| `-h`, `--help`           | Print help.                                       |

## `envy init`

```
envy init <project-dir> <bin-dir> [--mirror=URL] [--pin-sums]
                                  [--deploy=true|false] [--root=true|false]
```

Bootstrap a project: writes `envy.lua`, `.luarc.json`, and the `envy` /
`envy.bat` bootstrap scripts.

## `envy sync`

```
envy sync [<queries>...] [--manifest=<path>] [--strict] [--subproject]
          [--platform=posix|windows|all] [--ignore-depot]
```

Install packages and deploy product scripts. The everyday command. Syncs
everything in the manifest when given no queries.

## `envy install`

```
envy install [<queries>...] [--manifest=<path>] [--ignore-depot]
```

Install packages without deploying product scripts.

## `envy product`

```
envy product [<product>] [--manifest=<path>] [--json]
```

Print a named product's resolved value or path. Omit the name to list all
products.

## `envy package`

```
envy package <identity> [--manifest=<path>] [--ignore-depot]
```

Install that package plus its transitive dependencies, then print its absolute
package directory to stdout. Exits 0 with the path, or 1 with `not found`.

## `envy shell`

```
envy shell <bash|zsh|fish|powershell>
```

Print the `source` line to add to your shell profile for automatic `PATH`
management. See [Getting Started](./getting-started.md#shell-integration).

## `envy cache`

```
envy cache
```

Print the cache root and its disk usage, largest entry first, with a total.
