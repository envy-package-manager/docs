---
sidebar_position: 10
title: envy cache
---

# `envy cache`

Report where the cache lives and what is using space in it. One row per
installed package variant, one per cached envy deployment, and one per remaining
top-level directory, largest first, with a total.

There is no `envy cache clean`. Everything in the cache is reconstructible from
the manifest, so reclaiming space is `rm -rf` on whatever row you no longer want.
That can be one package entry, a whole identity, or the entire root. The next
`sync` rebuilds what the project needs.

## Usage

```
envy cache
```

This command has no flags of its own. The cache root it reports honors the full
precedence chain: `--cache-root` or `ENVY_CACHE_ROOT`, then a discovered
manifest's `@envy cache-posix` or `@envy cache-win` directive with relative paths
anchored to the manifest's directory, then the platform default. The defaults
are `~/Library/Caches/envy` on macOS, `$XDG_CACHE_HOME/envy` or `~/.cache/envy`
on Linux, and `%LOCALAPPDATA%\envy` on Windows. envy reads the manifest as text
for that directive. A broken manifest above your working directory cannot stop
the report.

Measurement is a parallel walk using native directory enumeration. Sizes are
apparent file sizes, and symlinked trees are excluded so nothing is
double-counted.

## Output

```
Cache: /Users/you/Library/Caches/envy

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
envy cache | head -1
# Cache: /Users/you/Library/Caches/envy
envy --cache-root /opt/envy-cache cache | head -1
# Cache: /opt/envy-cache
```

Useful when a project sets `@envy cache-posix` and you want to know whether you
are looking at the shared cache or your own.

### To delete one package and let envy rebuild it

```bash
rm -rf "$(envy cache | head -1 | cut -d' ' -f2)/packages/envy.cmake@r0"
envy sync
```

Nothing outside the cache points into it by absolute path, so the only cost is
re-downloading.

### To reclaim everything

```bash
rm -rf "$(envy cache | head -1 | cut -d' ' -f2)"
```

```powershell
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\envy"
```

This deletes installed packages, cached envy versions, and downloaded specs. The
next `sync` in any project restores what that project needs.

### To retire old envy versions only

```bash
CACHE="$(envy cache | head -1 | cut -d' ' -f2)"
rm -rf "$CACHE/envy/0.1.9"
```

This keeps package builds intact while dropping envy binaries no project pins.

## See also

- [The Cache](/concepts/cache) for layout, sharing between projects, and the safety guarantees.
- [Environment Variables](../environment-variables.md) for `ENVY_CACHE_ROOT`.
