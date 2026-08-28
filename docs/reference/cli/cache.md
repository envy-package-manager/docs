---
sidebar_position: 10
title: envy cache
---

# `envy cache`

Report where the cache lives and what is using space in it, or change which
cache this project uses. The report is one row per installed package variant,
one per cached envy deployment, and one per remaining top-level directory,
largest first, with a total.

There is no `envy cache clean`. Everything in the cache is reconstructible from
the manifest, so reclaiming space is `rm -rf` on whatever row you no longer want.
That can be one package entry, a whole identity, or the entire root. The next
`sync` rebuilds what the project needs.

## Usage

```
envy cache [--root | --local | --shared]
```

| Flag | Effect |
| --- | --- |
| *(none)* | Print the usage report, with the winning precedence tier named. |
| `--root` | Print the resolved cache root and nothing else. No disk scan. |
| `--local` | Use this project's own tree from now on. |
| `--shared` | Use the user-wide cache from now on. |

The flags are mutually exclusive; one action per invocation.

### Reading the root

`--root` prints one line on stdout and skips the usage walk, which makes it the
right thing to script against:

```console
$ envy cache --root
/Users/you/src/firmware/out/.envy
```

The bare report names the tier that decided, because the failure mode worth
catching is two things disagreeing about where the cache is:

```console
$ envy cache | head -1
Cache: /Users/you/src/firmware/out/.envy  (@envy cache-local)
```

The suffix is one of `(--cache-root/ENVY_CACHE_ROOT)`, `(recorded by 'envy
cache')`, `(@envy cache-mode)`, `(@envy cache-local)`, or `(default)`.

### Changing the mode

`--local` and `--shared` record your choice as a zero-byte marker file beside the
manifest, `.envy-cache-local` or `.envy-cache-shared`, which outranks whatever
the manifest declares:

```console
$ envy cache --shared
Cache: /Users/you/Library/Caches/envy  (recorded by 'envy cache')
Previous: /Users/you/src/firmware/out/.envy (no longer used; remove it when convenient)
```

The marker exists only when your choice differs from the project's own default,
so asking for the default clears it rather than restating it. Neither flag moves
an existing tree: relocating a multi-GB cache is slow and would race any other
envy process holding a lock, so the old root is named and deleting it is your
call. Both need a discoverable manifest, and they honor `--project` like every
other manifest-aware command.

### Precedence

The root honors the full chain: `--cache-root` or `ENVY_CACHE_ROOT` (which must
be absolute), then a marker file, then `@envy cache-mode`, then `@envy
cache-local` being present at all, then the platform default —
`~/Library/Caches/envy` on macOS, `$XDG_CACHE_HOME/envy` or `~/.cache/envy` on
Linux, `%LOCALAPPDATA%\envy` on Windows. Directive paths are relative literals
anchored to the manifest's directory, never the working directory. envy reads
them out of the manifest as text, so a broken manifest above your working
directory cannot stop the report — and under `--cache-root` it does not read a
manifest at all.

Measurement is a parallel walk using native directory enumeration. Sizes are
apparent file sizes, and symlinked trees are excluded so nothing is
double-counted.

## Output

```
Cache: /Users/you/Library/Caches/envy  (default)

Packages:
  envy.python@r1/darwin-arm64-blake3-f92708b498a20257  257.25MB
  envy.cmake@r0/darwin-arm64-blake3-49a9b2620de8c380   240.93MB
  envy.ninja@r0/darwin-arm64-blake3-268bff6f91bfacc4     2.14MB

Envy deployments:
  0.2.0                                                  8.23MB
  0.1.9                                                  5.72MB

Other:
  specs                                                202.78KB
  shell                                                 22.66KB
  locks                                                      0B

  TOTAL                                                514.36MB
```

Package rows are `identity/platform-arch-blake3-hash`, one per option variant.
That is why two pythons can appear under one identity, and why bumping an option
leaves the old tree behind until you delete it. Envy deployment rows are the
versions your projects have pinned over time. `Other` is everything else the
cache holds, such as downloaded specs, shell hooks, and lock files, listed so
the total reconciles.

## Examples

### To find out what is using disk

```bash
envy cache
```

Rows are sorted largest first within each section.

### To confirm which cache root is in effect

```bash
envy cache --root
# /Users/you/Library/Caches/envy
envy --cache-root /opt/envy-cache cache --root
# /opt/envy-cache
```

Use the bare report when you want to know *why* it is what it is:

```bash
envy cache | head -1
# Cache: /Users/you/src/firmware/out/.envy  (@envy cache-local)
```

### To delete one package and let envy rebuild it

```bash
rm -rf "$(envy cache --root)/packages/envy.cmake@r0"
envy sync
```

Nothing outside the cache points into it by absolute path, so the only cost is
re-downloading.

### To reclaim everything

```bash
rm -rf "$(envy cache --root)"
```

```powershell
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\envy"
```

This deletes installed packages, cached envy versions, and downloaded specs. The
next `sync` in any project restores what that project needs.

### To keep a project's packages inside the project

```bash
envy cache --local
envy sync
```

Everything the project downloads now lives under its own tree, so deleting the
project reclaims all of it. `envy cache --shared` puts you back on the user-wide
cache. Neither command copies anything; the next `sync` populates the new root.

### To retire old envy versions only

```bash
CACHE="$(envy cache --root)"
rm -rf "$CACHE/envy/0.1.9"
```

This keeps package builds intact while dropping envy binaries no project pins.

## See also

- [The Cache](/concepts/cache) for layout, sharing between projects, and the safety guarantees.
- [Environment Variables](../environment-variables.md) for `ENVY_CACHE_ROOT`.
