---
sidebar_position: 4
title: Fetch Dependencies
---

# Fetch Dependencies

> **Placeholder content.** Outline for review. Verify against sources.

The bootstrap problem. This project's specs live in Artifactory. The Artifactory
CLI is itself an envy package, so it has to be installed before any of those
specs can be fetched. Ordinary dependencies cannot express that. They order
phases of packages whose specs envy already has. Fetch dependencies order the
acquisition of the spec itself.

Will cover:

- The shape. A `source` table carrying both the tools it needs and the custom
  fetch that uses them. Here it is on a manifest `BUNDLES` declaration, fetching
  a bundle of specs out of Artifactory with a `jf` that envy installed:

```lua title="envy.lua"
BUNDLES = {
  corp = {
    identity = "corp.specs@r1",
    source = {
      -- Installed end to end, including setup, before the bundle is fetched.
      dependencies = {
        { spec = "tools.jfrog-cli@r1", product = "jf",
          source = envy.abspath("envy/tools.jfrog-cli.lua") },
      },

      fetch = function(tmp_dir)
        envy.run(envy.template([[
          {{jf}} config add ci --url={{url}} --access-token=$JF_TOKEN --interactive=false
          {{jf}} rt download --flat --fail-no-op '{{repo}}/' '{{dest}}'
        ]], {
          jf = envy.product("jf"),  -- provided by tools.jfrog-cli
          url = "https://acme.jfrog.io/artifactory",
          repo = "envy-specs/corp.specs@r1",
          dest = tmp_dir .. "/",
        }))

        envy.commit_fetch({ "envy-bundle.lua", "specs" })
      end,
    },
  },
}

PACKAGES = {
  { spec = "corp.toolchain@r2", bundle = "corp", options = { version = "15.2" } },
}
```

  The fetch dependency declares `product = "jf"`, so the fetch function resolves
  the tool with `envy.product("jf")` and gets an absolute path into the cache.
  Nothing assumes a `jf` on `PATH`, and nothing hardcodes a cache path. Wrapping
  the command in `envy.template` keeps the two `jf` invocations and the three
  varying values in one place. `envy.package(identity)` is available the same way
  when you need the dependency's whole directory rather than one product.

  `fetch` writes into `tmp_dir` and calls `envy.commit_fetch`, which verifies any
  hashes and moves the files into the durable fetch directory. A bundle commits
  its `envy-bundle.lua` and spec files. A single spec commits one file named
  `spec.lua`.

- Where a source table can be declared: a `BUNDLES` declaration, in a manifest or
  a spec, and a spec `DEPENDENCIES` entry. A manifest `PACKAGES` entry cannot
  carry `source.fetch`. envy fails with `Custom fetch function spec has no
  parent`. The fetch function is looked up in the declaring spec's Lua state, and
  a manifest entry has no declaring spec.

- `opts`. A spec-declared `source.fetch` receives `(tmp_dir, opts)`. Those are
  the declaring spec's options, not the dependency's. One spec can therefore
  route its dependency fetches through whichever server the project configured.
  A bundle's fetch receives `(tmp_dir)` only.

- The ordinary case, for comparison. Once a spec is loaded, its own verbs resolve
  tools the same way, and `needed_by` decides how early that is legal:

```lua title="corp.toolchain@r2.lua"
local hashes -- version -> sha256, at the bottom of this file

DEPENDENCIES = {
  { spec = "tools.jfrog-cli@r1", product = "jf", source = "tools.jfrog-cli.lua",
    needed_by = "fetch" },
}

FETCH = function(tmp_dir, opts)
  envy.run(envy.template([[
    {{jf}} rt download --flat --fail-no-op 'toolchains/{{version}}.tar.zst' '{{dest}}'
  ]], {
    jf = envy.product("jf"),  -- provided by tools.jfrog-cli
    version = opts.version,
    dest = envy.path.join(tmp_dir, "toolchain.tar.zst"),
  }))

  envy.commit_fetch({ filename = "toolchain.tar.zst", sha256 = hashes[opts.version] })
end
```

  `needed_by = "fetch"` is what makes the call legal in `FETCH`. The default,
  `build`, produces `envy.product: product 'jf' needed_by 'build' but accessed
  during 'fetch'`. A fetch dependency needs no `needed_by`, because it is already
  gated on the earliest phase there is.

- The guarantee. Every entry in `source.dependencies` goes through its entire
  lifecycle, install and setup included, before the dependent's spec is fetched.
  Compare `needed_by = "fetch"`, which gates payload fetching only.
- `source.dependencies` requires `source.fetch`. If nothing custom runs, the tool
  was not needed.
- Strong references only, for anything a fetch function resolves by name. A
  fetch dependency with its own `spec` and `source` is wired before the fetch
  runs. A bare product query or a weak reference is deferred to the resolution
  pass. That pass runs after the graph is discovered, too late for a fetch
  function.
- Chains. A fetch dependency's own spec can have fetch dependencies, and
  bootstrap chains resolve bottom-up.
- Where the same machinery appears without being called this: fetching
  [bundles](./bundles.md), and authenticated [depot](/concepts/depots) indexes
  with `DEPENDS`, which hands its fetch function `ctx.deps[identity].pkg_path`.
- Failure modes. Cycles among fetch dependencies are detected and reported.
