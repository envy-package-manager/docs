---
sidebar_position: 10
title: envy cache
---

# `envy cache`

> **Placeholder content.** Verify flags and semantics against sources.

Show where the cache lives and what's using space — per package, largest
first, with a total.

## Usage

```
envy cache
```

## Behavior

- Prints the resolved cache root (after `--cache-root` / `ENVY_CACHE_ROOT` /
  `@envy cache-*` / platform-default precedence).
- Disk usage breakdown: installed packages, envy's own deployed versions,
  totals.
- Cleanup is `rm -rf` on entries (or the whole root) — everything is
  reconstructible; there is no separate GC command.

## Examples

```bash
./bin/envy cache                     # where is it, what's big
rm -rf "$(./bin/envy cache | head -1)"   # placeholder: exact scriptable form TBD
```

## See also

- [The Cache](/concepts/cache) — layout, sharing, safety guarantees.
