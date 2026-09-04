---
sidebar_position: 7
title: envy init
---

# `envy init`

Turn a directory into an envy project: write the manifest, the committed
bootstrap scripts, and the editor config. Run it once with any envy binary you
can get. After that the project bootstraps itself, and nobody who clones it
needs envy installed.

Everything `init` writes is stamped from the running binary's version, so the
`@envy version` it pins is the envy you ran. `--envy-version` initializes at a
different release instead, and [`envy use`](./use.md) retargets afterwards.

## Usage

```
envy init <project-dir> <bin-dir> [--envy-version=<x.y.z>] [--mirror=<url>]
          [--pin-sums] [--deploy=true|false] [--root=true|false]
          [--platform=posix|windows|all]
```

## Arguments and flags

| Argument or flag | Meaning |
| --- | --- |
| `project-dir` | Where `envy.lua` and `.luarc.json` go. Created if missing. Required. |
| `bin-dir` | Where the bootstrap scripts go. Recorded as `@envy bin`, relative to the manifest. Created if missing. Required. |
| `--envy-version <x.y.z>` | Initialize the project at this release instead of the running binary's. See [below](#initializing-at-another-version). |
| `--mirror <url>` | Stamp `@envy mirror`, an `https://` or `s3://` prefix to download envy releases from instead of GitHub. Validated before anything is written. Also where `--envy-version` downloads from, since the flag's value is the mirror the project is about to get. |
| `--pin-sums` | Fetch the release's `SHA256SUMS`, hash it, and stamp `@envy sha256sums`, so bootstrap verifies every envy binary it downloads. Runs after the `--envy-version` handoff, so the pin describes the version actually stamped. |
| `--deploy true\|false` | Stamp `@envy deploy`. `true` enables [product script](/concepts/environment/product-scripts) deployment. Defaults to `true`, so a bare `init` stamps `@envy deploy "true"`. Pass `false` for a project that reaches its tools some other way. |
| `--root true\|false` | Stamp `@envy root`. Defaults to `true`. Use `false` for a component manifest inside a larger tree. |
| `--platform posix\|windows\|all` | Which bootstrap flavors to write. Defaults to the current OS. |

## What it writes

| Path | Purpose | Commit |
| --- | --- | --- |
| `<project-dir>/envy.lua` | Manifest, header stamped from the flags above. | yes |
| `<bin-dir>/envy` | POSIX bootstrap script. | yes |
| `<bin-dir>/envy.bat` | Windows bootstrap script. | yes |
| `<project-dir>/.luarc.json` | Points lua-language-server at envy's type definitions for spec authoring. | yes |
| `<project-dir>/.gitignore` | Gets `.envy/` and `.envy-cache-*` appended, so a [cache mode marker](/concepts/cache#picking-the-other-one) and a default local cache tree stay out of commits. Created if absent. | yes |

Both `@envy deploy` and `@envy root` are always stamped, because both default
to `true`. A hand-written manifest that omits them behaves differently: an absent
`deploy` means deployment is off, and an absent `root` is treated as a root.

Nothing you already have is overwritten. An existing `envy.lua` is left alone
with a note, and an existing `.luarc.json` is left alone with the library paths
to add printed for you. The bootstrap scripts are always rewritten, which makes
re-running `init` a safe way to add a script flavor. `--pin-sums` runs its
download before anything is created, so a typo or an unpublished version fails
with an untouched directory.

`.gitignore` is the one file `init` appends to rather than skipping, and only
when `project-dir` holds a `.git` directory. Into a plain directory it writes
nothing, and into a subdirectory of a repo a nested `.gitignore` would be a
surprise. An entry already present in any spelling git treats as equivalent,
including a `!` negation, is left alone, so re-running `init` never duplicates
one. Later commands never touch the file.

## Initializing at another version

`--envy-version` re-execs into the requested release and lets *that* binary do
the init, so the manifest pin, the version stamped into the bootstrap scripts,
and the extracted type definitions all come from it rather than from whichever
envy happened to be on `PATH`:

```bash
/tmp/envy init . ./bin --envy-version 0.2.0 --pin-sums
```

The release is downloaded to a temp directory if the cache lacks it. The flag is
handled by the parent and stripped from the child's arguments, so the child
stamps its own version, which is the requested one. That also keeps the flag
usable with releases that predate it, which would reject it as an unknown
option.

A dev build (version `0.0.0`) and `ENVY_NO_REEXEC` cannot hand off. `init` warns
and stamps itself instead.

## Examples

### To start a new project with the standard layout

```bash
/tmp/envy init . ./bin
```

```powershell
C:\Temp\envy.exe init . .\bin
# then: bin\envy.bat sync
```

Then edit `envy.lua`, add packages, and run `envy sync`. The throwaway
binary in `/tmp` is never needed again.

### To make bootstrap downloads verified

```bash
/tmp/envy init . ./bin --pin-sums
```

This stamps `@envy sha256sums`, so every machine that bootstraps the project
verifies the envy binary it downloads against a hash in your git history.
Recommended for anything shared.

### To bootstrap from a private mirror

```bash
/tmp/envy init . ./tools --mirror s3://acme-envy-mirror --pin-sums
```

For networks that cannot reach GitHub releases. Populate the mirror with
[`envy mirror-envy`](./mirror-envy.md). The mirror lands only in the manifest.
The bootstrap scripts carry no project config and read the directive back out at
run time.

### To turn on wrapper scripts from the start

```bash
/tmp/envy init . ./bin --deploy=true --pin-sums
```

With `@envy deploy "true"`, `sync` writes a `bin/<tool>` per product, so
`./bin/cmake` works with no `PATH` setup.

### To set up a cross-platform repo

```bash
/tmp/envy init . ./bin --platform all --deploy=true
```

This writes both `bin/envy` and `bin/envy.bat`. Commit both, and Windows and
POSIX developers clone the same repo.

### To add a component manifest inside an existing project

```bash
envy init libs/firmware libs/firmware/bin --root=false --deploy=true
```

`@envy root "false"` marks it as a subproject.
[Discovery](/concepts/projects#manifest-discovery) walks past it to the real
root by default, and `envy sync --subproject` targets it directly.

### To add the Windows bootstrap script to a project that lacks it

```bash
envy init . ./bin --platform windows
```

The manifest is left as-is, and only `bin/envy.bat` appears.

## See also

- [Starting a Project](/guides/new-project) for the full walkthrough, including what to commit.
- [Projects & Manifests](/concepts/projects) and the [Manifest Reference](../manifest.md).
- [`envy use`](./use.md) for changing the pinned version afterwards.
