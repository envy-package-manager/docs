---
sidebar_position: 6
title: Creating a Bundle
---

# Creating a Bundle

Distribute a family of specs as one versioned, pinnable unit. Consumers pin one
commit instead of ten URLs.

## When a bundle is worth it

- **A shared toolchain.** One organization, many repos, the same twelve tools.
- **Atomic upgrades.** One `ref` advance moves every spec together, so a
  consumer cannot end up with half of a coordinated change.
- **Shared helpers.** Specs in a bundle can `require()` Lua modules that ship
  beside them, which is how a bundle becomes a library rather than a folder. See
  [Shipping an API with your specs](/concepts/dependencies/bundles#shipping-an-api-with-your-specs).

For one or two specs, a URL with a `sha256` is simpler. Reach for a bundle when
the specs start sharing code or need to move together.

## Layout

A bundle is a git repo or an archive with a manifest at its root:

```text
envy-bundle.lua
lib/
├── github.lua
├── platform.lua
└── versions.lua
specs/
├── cmake.lua
├── ninja.lua
└── uv.lua
```

```lua title="envy-bundle.lua"
-- @envy schema "1"
BUNDLE = "acme.specs@r1"

SPECS = {
  ["acme.cmake@r0"] = "specs/cmake.lua",
  ["acme.ninja@r0"] = "specs/ninja.lua",
  ["acme.uv@r0"] = "specs/uv.lua",
}
```

`BUNDLE` is the identity consumers pin. `SPECS` maps each spec identity to a file
inside the bundle.

## The identity-match rule

A spec file's `IDENTITY` has to equal its `SPECS` key. `specs/cmake.lua` must
declare `IDENTITY = "acme.cmake@r0"`, and a mismatch is an error rather than a
warning.

That rule is what makes a bundle trustworthy: a bundle cannot promise one
identity and deliver a spec that claims another.

## Consuming it

```lua title="envy.lua"
BUNDLES = {
  acme = {
    identity = "acme.specs@r1",
    source = "https://github.com/acme/envy-specs.git",
    -- envy git-resolve https://github.com/acme/envy-specs refs/heads/main
    ref = "ded36a39bbf13744f5a0e539f2f4741fecb61dd0",
  },
}

PACKAGES = {
  { spec = "acme.cmake@r0", bundle = "acme", options = { version = "4.4.0" } },
  { spec = "acme.ninja@r0", bundle = "acme", options = { version = "1.13.2" } },
}
```

The bundle is itself a package. It gets a cache entry, reports its own row in the
output, and is fetched once no matter how many specs are taken from it.

## Shared helpers

Specs from the bundle `require()` modules by path, because envy prefixes
`package.path` with the bundle root:

The helper most bundles end up with first is platform naming, because every spec
in the bundle needs the same answer:

```lua title="lib/platform.lua"
-- Platform naming shared by the specs in this bundle.
local M = {}

M.WINDOWS = envy.PLATFORM == "windows"

-- Windows release artifacts are almost always zips, everything else tarballs.
M.ARCHIVE_EXT = M.WINDOWS and ".zip" or ".tar.gz"

-- Rust-style target triple, matching how Rust projects name their release
-- artifacts. Linux picks musl so the binaries do not depend on the host glibc.
function M.rust_triple()
  if envy.PLATFORM == "darwin" then
    return (envy.ARCH == "arm64") and "aarch64-apple-darwin" or "x86_64-apple-darwin"
  elseif envy.PLATFORM == "linux" then
    return (envy.ARCH == "x86_64") and "x86_64-unknown-linux-musl"
        or "aarch64-unknown-linux-musl"
  end
  return "x86_64-pc-windows-msvc"
end

return M
```

Getting this wrong in one spec is a bug in one spec. Getting it right in
`lib/platform.lua` fixes it for the whole bundle, which is most of the argument
for bundling in the first place.

```lua title="lib/github.lua"
local M = {}

---@param repo string "owner/name"
---@param tag string release tag
---@param filename string release asset filename
---@return string url
function M.release_url(repo, tag, filename)
  return "https://github.com/" .. repo .. "/releases/download/" .. tag .. "/" .. filename
end

return M
```

```lua title="specs/cmake.lua"
local github = require("lib.github")

FETCH = function(tmp_dir, opts)
  return {
    source = github.release_url("Kitware/CMake", "v" .. opts.version, asset(opts)),
    sha256 = hashes[opts.version][platform_key()],
  }
end
```

Write the LuaCATS annotations. Consumers of your bundle get completion and hover
docs on your helpers through the `.luarc.json` that `envy init` maintains.

The pattern worth aiming for is a helper that returns whole verb sets, so a spec
becomes a name, a repo, and a hash table. That is covered in
[Shipping an API with your specs](/concepts/dependencies/bundles#shipping-an-api-with-your-specs).

## Testing a bundle before publishing

Point a scratch manifest at your working copy. A local path needs no ref:

```lua title="envy.lua"
BUNDLES = {
  acme = { identity = "acme.specs@r1", source = envy.abspath("../envy-specs") },
}
```

That is the fastest edit-and-run loop, because there is nothing to commit or push
between attempts. Switch to the git source with a pinned ref before anyone else
consumes it.

## Migrating loose specs into a bundle

Consumers keep their identities, so the change is small:

1. Move the spec files into the bundle and list them in `SPECS`. Identities do
   not change.
2. Publish the bundle and resolve a ref.
3. In each consumer, add the `BUNDLES` entry and change `source = "..."` to
   `bundle = "acme"` on the affected entries.

Nothing about the packages changes, so no cache entry is invalidated and no
version moves. That is worth doing as its own commit, separate from any version
bump, so a bisect can tell the two apart.

## Versioning discipline

Two identities move independently, and the distinction matters:

| Change | Bump |
| --- | --- |
| A spec gains an option, renames a product, or changes its install layout | that spec's revision, `acme.cmake@r0` to `@r1` |
| The bundle adds, removes, or renames specs, or reorganizes `lib/` in a way consumers can see | the bundle identity, `acme.specs@r1` to `@r2` |
| A spec gains a new version in its hash table | neither. That is a normal commit consumers pick up by advancing the ref. |

Bumping the bundle identity is a consumer-visible break, because `BUNDLES` pins
it by name. Bumping a spec revision is narrower: only entries naming that spec
change.

Declaring the same bundle identity twice with different sources or refs is an
error, so a superproject and a component cannot disagree silently about which
bundle they mean.

## See also

- [Bundles](/concepts/dependencies/bundles) for the consumer-side concepts and the API section.
- [Writing a Spec](./writing-a-spec.md) for the specs that go inside.
- [`envy git-resolve`](../reference/cli/git-resolve.md) for the ref consumers pin.
