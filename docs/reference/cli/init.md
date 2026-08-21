---
sidebar_position: 7
title: envy init
---

# `envy init`

> **Placeholder content.** Verify flags and semantics against sources.

Initialize a project: write the manifest, the committed bootstrap scripts,
and editor config. Run once with any envy binary — the project is
self-bootstrapping from then on.

## Usage

```
envy init <project-dir> <bin-dir> [--mirror=<url>] [--pin-sums]
          [--deploy=true|false] [--root=true|false]
          [--platform=posix|windows|all]
```

## Arguments & flags

| Argument / flag | Meaning |
| --- | --- |
| `project-dir` | Where `envy.lua` and `.luarc.json` are written. |
| `bin-dir` | Where the `envy` / `envy.bat` bootstrap scripts go (becomes `@envy bin`). |
| `--mirror <url>` | Stamp `@envy mirror` (https or s3) for air-gapped/private networks. |
| `--pin-sums` | Also stamp `@envy sha256sums` (checksum-pin the envy release). |
| `--deploy true\|false` | Stamp `@envy deploy` (product-script deployment). |
| `--root true\|false` | Stamp `@envy root` (subproject manifests use `false`). |
| `--platform posix\|windows\|all` | Which bootstrap script flavors to write. |

## What it writes

| Path | Purpose | Commit? |
| --- | --- | --- |
| `envy.lua` | Manifest with pinned `@envy version`. | yes |
| `<bin>/envy` | POSIX bootstrap script. | yes |
| `<bin>/envy.bat` | Windows bootstrap script. | yes |
| `.luarc.json` | Editor config for spec authoring. | yes |

## Examples

```bash
/tmp/envy init . ./bin                       # typical layout
/tmp/envy init . ./tools --pin-sums --deploy=true
```

## See also

- [Starting a Project](/guides/new-project)
- [The Manifest](/concepts/projects/manifest)
