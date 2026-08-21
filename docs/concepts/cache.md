---
sidebar_position: 6
title: The Cache
---

# The Cache

> **Placeholder content.** Outline for review. Verify against sources.

One per-user store serves every project on the machine. It is
content-addressed, concurrency-safe, and always safe to delete.

Will cover:

- What lives there: envy's own pinned binaries, fetched specs and bundles,
  installed package trees, durable download caches, and shell hooks.
- The user-facing shape, enough to navigate rather than an internals spec:

```
<cache-root>/
├── envy/<version>/          # envy binaries, per pinned version
├── specs/<identity>/...     # fetched specs and bundles
└── packages/<identity>/<platform-arch-hash>/pkg/   # installed packages
```

- Content addressing in user terms. The hash covers identity, options, and
  platform, so different option sets coexist and nothing is clobbered. Ten
  projects pinning the same package share one entry.
- Where the root lives per OS, and every way to move it: `ENVY_CACHE_ROOT`,
  `--cache-root`, `@envy cache-posix`, `@envy cache-win`, with precedence.
- Lifecycle guarantees, stated as behavior. Concurrent envy processes are safe.
  Interrupted work never leaves an entry marked complete. Verified downloads
  survive failed builds, so retries are cheap.
- Deleting things. The whole cache is reconstructible, so `rm -rf` is the
  supported cleanup tool, and `envy cache` shows what is using space.
- What is not in the cache key: setup selections and depot configuration.
  [SETUP](/concepts/specs/setup) explains why.
- Never hardcode cache paths. Resolve them with `envy product` or
  `envy package`.
