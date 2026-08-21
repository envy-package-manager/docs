---
sidebar_position: 6
title: The Cache
---

# The Cache

> **Placeholder content.** Outline for review; verify against sources.

One per-user store serves every project on the machine. Content-addressed,
concurrency-safe, and always safe to delete.

Will cover:

- What lives there: envy's own pinned binaries, fetched specs and bundles,
  installed package trees, durable download caches, shell hooks.
- The user-facing shape (enough to navigate, not an internals spec):

```
<cache-root>/
├── envy/<version>/          # envy binaries, per pinned version
├── specs/<identity>/...     # fetched specs & bundles
└── packages/<identity>/<platform-arch-hash>/pkg/   # installed packages
```

- Content addressing in user terms: the hash covers identity + options (+
  platform), so different option sets coexist and nothing is ever clobbered;
  ten projects pinning the same package share one entry.
- Where the root lives per OS, and every way to move it (`ENVY_CACHE_ROOT`,
  `--cache-root`, `@envy cache-posix`/`cache-win`) with precedence.
- Lifecycle guarantees, stated as behavior: concurrent envy processes are
  safe; interrupted work never leaves a "complete" lie; verified downloads
  survive failed builds so retries are cheap.
- Deleting things: the whole cache is reconstructible — `rm -rf` is the
  supported cleanup tool; `envy cache` shows what's using space.
- What deliberately is NOT in the cache key — setup selections and depot
  configuration ([SETUP](/concepts/specs/setup) explains why).
- Never hardcode cache paths; resolve via `envy product` / `envy package`.
