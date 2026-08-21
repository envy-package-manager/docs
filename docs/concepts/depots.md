---
sidebar_position: 7
title: Package Depots
---

# Package Depots

> **Placeholder content.** Outline for review. Verify against sources.

envy is serverless until you choose otherwise. A depot is an optional artifact
store holding prebuilt packages your CI exported, keyed by the same hashes the
cache uses. With a depot, `sync` downloads finished packages instead of fetching
and building them.

Will cover:

- Positioning. Depots are an accelerator, never a requirement. With no depot
  configured, everything builds from source. If a configured depot is
  unavailable, envy warns and falls back to source builds. It never bricks a
  project.
- Consumer configuration, which is one manifest line:

```lua
PACKAGE_DEPOTS = { "s3://acme-envy-packages/packages.txt" }
```

- What a depot is: a flat index file mapping package hashes to archive URLs,
  stored next to the archives. Any file host qualifies. There is no depot server
  software.
- The exact-match rule. A depot hit requires the same identity, options, and
  platform, so a depot can never give you the wrong bits, only save you time.
- Authenticated depots. A depot entry can bootstrap its own access tooling:

```lua
PACKAGE_DEPOTS = {
  { DEPENDS = { "acme.aws@r0" },
    FETCH = function(ctx)
      local aws = envy.path.join(ctx.deps["acme.aws@r0"].pkg_path, "bin", "aws")
      local index = envy.path.join(ctx.tmp_dir, "packages.txt")
      envy.run(aws .. " s3 cp s3://acme-envy-packages/packages.txt " .. index)
      return index
    end },
}
```

  `FETCH(ctx)` receives `ctx.tmp_dir` and `ctx.deps[identity].pkg_path`, and
  returns the index text, a path to it, or a table of `{ url, sha256 }` entries.

  `DEPENDS` names manifest packages that are installed from source before the
  depot index is fetched. It is the depot-flavored sibling of
  [fetch dependencies](/concepts/dependencies/fetch-dependencies).
- Which packages a depot can serve. `EXPORTABLE` specs ship installed trees,
  non-exportable specs ship fetched artifacts, and user-managed packages are
  never served because there is nothing to ship.
- Opting out with `--ignore-depot` or `ENVY_IGNORE_DEPOT=1`, and why CI export
  jobs set it: publishers have to build from source.
- Publishing, covered in
  [Running a Package Depot](/guides/package-depots).
