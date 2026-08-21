---
sidebar_position: 1
title: CLI Reference
---

# CLI Reference

> **Placeholder content.** Command list verified against sources at skeleton
> time; every section below needs its full flag table and examples filled in.

Conventions: human output goes to stderr; stdout is reserved for
machine-readable results. Commands that need a manifest find it by
[discovery](/concepts/projects/discovery) unless `--manifest` overrides.

## Global flags

| Flag | Effect |
| --- | --- |
| `--verbose` | Decision-level narrative (why, not just what). |
| `-q`, `--quiet` | Warnings and errors only. |
| `--trace[=stderr\|file:<path>]` | Structured JSONL event stream ([Logging & Tracing](./observability.md)). |
| `--cache-root <path>` | Override the cache root (env: `ENVY_CACHE_ROOT`). |
| `-v`, `--version` | Print version. |
| `-h`, `--help` | Print help. |

## Everyday

- ### `envy sync [queries...]`
  Install manifest packages and deploy product scripts. Equal to `install` +
  `deploy`. Flags: `--manifest`, `--strict`, `--subproject`, `--platform`,
  `--ignore-depot`.
- ### `envy install [queries...]`
  Install packages only; the project directory is untouched.
- ### `envy deploy [identities...]`
  Deploy/refresh product wrapper scripts only.
- ### `envy product [name] [--json]`
  Resolve one product to its path/value, or list all.
- ### `envy package <identity>`
  Ensure a package (plus dependencies) is installed; print its directory.
- ### `envy run <command...>`
  Run a command with the project bin dir on `PATH`.

## Project management

- ### `envy init <project-dir> <bin-dir>`
  Create a manifest, bootstrap scripts, and editor config. Flags:
  `--mirror`, `--pin-sums`, `--deploy`, `--root`, `--platform`.
- ### `envy use <version>`
  Retarget the manifest's pinned envy version (and checksum pin). Flags:
  `--manifest`, `--subproject`, `--mirror`, `--pin-sums`/`--no-pin-sums`,
  `--force`.
- ### `envy shell <bash|zsh|fish|powershell>`
  Print the shell-profile line enabling [shell hooks](/concepts/environment/shell-hooks).
- ### `envy cache`
  Show the cache root and disk usage.

## Spec authoring utilities

- ### `envy git-resolve <url> <ref>`
  Resolve a remote branch/tag to a full commit hash (no clone) — for pinning.
- ### `envy hash <paths...> [--prefix <url>]`
  Print `sha256` lines suitable for fingerprint tables and depot indexes.
- ### `envy fetch <source> <destination>`
  Download one resource the way FETCH would.
- ### `envy extract <archive> [destination] [--only <glob>]`
  Extract an archive the way STAGE would.
- ### `envy lua <script>`
  Run a Lua script inside envy's runtime (test spec helpers directly).

## Depot publishing

- ### `envy export [queries...] -o <dir> [--depot-prefix <url>]`
  Export cached packages as depot artifacts; print their index lines.
- ### `envy import [archive|--dir <dir>]`
  Import exported artifacts into the cache by hand.
- ### `envy merge-depot <manifests...>`
  Merge per-platform depot indexes, with retention policy flags.

## Administration

- ### `envy mirror-envy <version> <destination>`
  Mirror an envy release (all platforms + checksums) to a directory or S3.
- ### `envy version [--licenses]`
  Print version; optionally all bundled third-party licenses.
