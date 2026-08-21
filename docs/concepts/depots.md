---
sidebar_position: 7
title: Package Depots
---

# Package Depots

> **Placeholder content.** Outline for review; verify against sources.

envy is serverless — until you *choose* otherwise. A depot is an optional,
dumb artifact store: prebuilt packages your CI exported, keyed by the same
hashes the cache uses. With a depot, `sync` downloads finished packages
instead of fetching and building.

Will cover:

- Positioning first: depots are an accelerator, never a requirement. No
  depot configured → everything builds from source, exactly as documented
  everywhere else. Depot unavailable → envy warns and falls back to source
  builds; it never bricks a project.
- Consumer configuration — one manifest line:

```lua
PACKAGE_DEPOTS = { "s3://acme-envy-packages/packages.txt" }
```

- What a depot actually is: a flat index file mapping package hashes to
  archive URLs, next to the archives. Any file host qualifies; there is no
  depot server software.
- The exact-match rule: a depot hit requires the same identity, options, and
  platform — a depot can never give you the *wrong* bits, only save you
  time.
- Authenticated depots — a depot entry can bootstrap its own access tooling:

```lua
PACKAGE_DEPOTS = {
  { DEPENDS = { "fi.aws@r0" },
    FETCH = function(...) --[[ fetch index via the aws CLI ]] end },
}
```

  `DEPENDS` names manifest packages installed (from source) before the
  depot index is fetched — the depot-flavored sibling of
  [fetch dependencies](/concepts/dependencies/fetch-dependencies).
- Which packages can be served: `EXPORTABLE` specs ship installed trees;
  non-exportable specs ship fetched artifacts; user-managed packages are
  never depot-served (nothing to ship).
- Opting out: `--ignore-depot` / `ENVY_IGNORE_DEPOT=1` — and why CI export
  jobs set it (publishers must build from source).
- Publishing — pointer to the
  [Running a Package Depot](/guides/package-depots) guide.
