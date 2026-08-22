---
sidebar_position: 1
title: The Dependency Model
slug: /concepts/dependencies
---

# The Dependency Model

envy dependencies answer a different question than most package managers'. There
is no version solver and no registry to solve against. Every version is already
exact, so the questions left are provisioning and ordering: what has to exist,
and by when, for this package to make progress.

## The model in one page

A spec declares what it needs:

```lua title="specs/clang-tools.lua"
DEPENDENCIES = { { product = "ninja" }, { product = "cmake" } }

BUILD = function(install_dir, stage_dir, fetch_dir, tmp_dir, opts)
  return envy.template([[
    {{cmake}} -G Ninja -DCMAKE_MAKE_PROGRAM={{ninja}} -S . -B build
    {{ninja}} -C build
  ]], { cmake = envy.product("cmake"), ninja = envy.product("ninja") })
end
```

Four things follow from that declaration:

1. **The project decides who provides `cmake`.** The spec names a capability, not
   a package, so a project can satisfy it with any spec that offers that product.
2. **Everything installs in parallel except where an edge says otherwise.**
   cmake and ninja install concurrently with this package's own fetch and stage.
3. **The edge has a phase attached.** `cmake` is needed by `build`, so this
   package can fetch and stage while cmake is still installing.
4. **`envy.product("cmake")` is legal only because the edge was declared.** An
   undeclared name is an error rather than a lookup, and the edge is what
   guarantees cmake is installed before `BUILD` runs.

## The four pages

- **[Declaring dependencies](./declaring.md)** covers the four kinds: strong,
  product, weak, and reference-only. Who insists, who defers, and who provides.
- **[Phase ordering and `needed_by`](./ordering.md)** covers the time attached to
  an edge. A build tool is needed by `build`, a download tool by `fetch`.
- **[Fetch dependencies](./fetch-dependencies.md)** covers the extreme case,
  where a tool has to be installed before another package's *spec* can be
  fetched.
- **[Resolution](./resolution.md)** covers how the graph settles: what is
  discovered when, how weak references are decided, and what counts as an error.
- **[Bundles](./bundles.md)** covers spec distribution, which rides the same
  machinery.

## What envy does not do

- **No version-range solving.** `options = { version = "4.4.0" }` is a value, not
  a constraint. There is nothing to solve and nothing to backtrack over.
- **No diamond mediation.** Two packages that want different cmake versions get
  two cmake packages, side by side in the cache, because the version is part of
  the identity. Nobody has to lose.
- **No lockfile.** Every pin is already exact and already in the manifest. See
  [Reproducibility](/concepts/reproducibility).

What that removes is a whole category of failure: the unsolvable constraint set,
the surprise upgrade of a transitive dependency, and the lockfile that disagrees
with the manifest. What it costs is that nobody picks versions for you.

## The graph is discovered, not declared

envy reads the manifest, fetches those specs, finds their `DEPENDENCIES`, fetches
*those* specs, and keeps going until nothing new appears. A spec you have never
heard of can enter the graph three levels down, and its own dependencies come
with it.

That is why [resolution](./resolution.md) has a settling phase at all, and why
weak references are decided late: envy cannot know whether the project already
provides something until the picture stops changing.

## See also

- [Anatomy of a Spec](/concepts/specs) for where `DEPENDENCIES` sits.
- [Products](/concepts/specs/products) for the capability names dependencies target.
- [Package Entries](/concepts/projects#package-entries) for the manifest-side fields.
