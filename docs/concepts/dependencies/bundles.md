---
sidebar_position: 6
title: Bundles
---

# Bundles

A bundle is a versioned container of specs: one pin that delivers a whole toolbox
of package definitions. Instead of pinning ten spec URLs, a project pins one
commit.

## Consuming a bundle

```lua title="envy.lua"
BUNDLES = {
  envy = {
    identity = "envy.package-specs@r3",
    source = "https://github.com/envy-package-manager/package-specs.git",
    -- envy git-resolve https://github.com/envy-package-manager/package-specs main
    ref = "ded36a39bbf13744f5a0e539f2f4741fecb61dd0",
  },
}

PACKAGES = {
  { spec = "envy.uv@r0", bundle = "envy", options = { version = "0.11.30" } },
  { spec = "envy.python@r1", bundle = "envy",
    options = { version = "3.13.14", release = "20260623" } },
  { spec = "envy.cmake@r0", bundle = "envy", options = { version = "4.4.0" } },
}
```

`BUNDLES` maps an alias to a declaration, and an entry uses `bundle = "<alias>"`
in place of `source`. One `ref` covers every spec taken from that bundle, so the
whole toolbox upgrades atomically: advance the ref, run `sync`, and every spec
moves together.

| Field | Meaning |
| --- | --- |
| `identity` | Required. The bundle's own identity, which the bundle file must declare. |
| `source` | Required. A git URL, an https URL, a local path, or a `{ fetch, dependencies }` table. |
| `ref` | Required for a git source. A full commit sha. |
| `sha256` | Integrity pin for an archive source. |

An alias is scoped to the manifest that wrote it. An entry pulled in with
[`envy.import`](/reference/lua-api#envyimportpath) resolves `bundle = "envy"`
against the imported manifest's `BUNDLES` first, then the importing one's. A
superproject does not re-export a component's `BUNDLES`, and two components can
use the same alias for different bundles. An alias that matches neither table
reports both:

```text
Bundle alias 'envy' not found in the BUNDLES table of this manifest or of the
manifest that declared it, for spec 'acme.tool@r0'
```

An entry can also carry an inline declaration instead of an alias, which is worth
it only for a one-off:

```lua
PACKAGES = {
  { spec = "acme.tool@r0",
    bundle = { identity = "acme.specs@r1", source = envy.abspath("vendor/specs") } }
}
```

## Producing a bundle

A bundle is a directory or repo with a manifest of its own:

```lua title="envy-bundle.lua"
-- @envy schema "1"
BUNDLE = "envy.package-specs@r3"

SPECS = {
  ["envy.cmake@r0"] = "specs/cmake.lua",
  ["envy.python@r1"] = "specs/python.lua",
  ["envy.uv@r0"] = "specs/uv.lua",
}
```

`BUNDLE` is the identity consumers pin. `SPECS` maps each identity to a file
inside the bundle. The identities have to match: a spec file whose `IDENTITY`
disagrees with its `SPECS` key is an error, so a bundle cannot promise one thing
and deliver another.

See [Creating a Bundle](../../guides/creating-bundles.md) for the authoring
workflow.

## How a bundle arrives

envy materializes the bundle through the
[fetch-dependency](./fetch-dependencies.md) machinery before reading any spec out
of it. The bundle is itself a package, with its own cache entry under `specs/`,
and it reports its own row in the output.

Two consequences. A bundle can live behind the same bootstrap tooling as anything
else, including a `source` table with its own `dependencies` and `fetch`. And
several specs pulled from one bundle share a single fetch, because they share the
bundle package.

Declaring the same bundle identity twice with different sources or refs is an
error rather than a silent winner.

## Shipping an API with your specs

A bundle is a directory, so it can carry Lua modules next to the specs. envy
prefixes `package.path` with the bundle root before running a spec from that
bundle. Those specs `require()` the modules like any other Lua module. This is
how a bundle stops being a pile of files and becomes a small library.

### Shared helpers

Start with the boring kind. One module holds the naming rules every spec in the
bundle repeats:

```lua title="lib/platform.lua"
local M = {}

M.WINDOWS = envy.PLATFORM == "windows"

-- Windows release artifacts are almost always zips, everything else tarballs.
M.ARCHIVE_EXT = M.WINDOWS and ".zip" or ".tar.gz"

---Rust-style target triple, matching how Rust projects name their release
---artifacts. Linux picks musl so the binaries are static.
---@return string triple
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

```lua title="specs/ripgrep.lua"
local github = require("lib.github")
local platform = require("lib.platform")

FETCH = function(tmp_dir, opts)
  return {
    source = github.release_url("BurntSushi/ripgrep", opts.version,
      "ripgrep-" .. opts.version .. "-" .. platform.rust_triple() .. platform.ARCHIVE_EXT),
    sha256 = hashes[opts.version],
  }
end
```

The LuaCATS annotations are worth writing. `envy init` and `envy sync` maintain a
`.luarc.json`, so a bundle author gets completion and hover docs on their own
helpers.

### A factory for a whole verb set

The interesting version returns the verbs themselves. Several tools published as
one release archive per target triple differ only in name, repo, and hashes. One
module can implement all of them:

```lua title="lib/rust_binary.lua"
local github = require("lib.github")
local platform = require("lib.platform")
local versions = require("lib.versions")

local M = {}

---Spec globals for one such tool.
---@param tool table `{ name, repo, hashes, binaries? }`
---@return table globals `{ OPTIONS, FETCH, STAGE, PRODUCTS }`
function M.tool(tool)
  local products = {}
  for _, binary in ipairs(tool.binaries or { tool.name }) do
    products[binary] = binary .. envy.EXE_EXT
  end

  return {
    OPTIONS = function() versions.validate(tool.hashes()) end,

    FETCH = function(tmp_dir, opts)
      local triple = platform.rust_triple()
      return {
        source = github.release_url(tool.repo, opts.version,
          tool.name .. "-" .. triple .. platform.ARCHIVE_EXT),
        sha256 = versions.lookup(tool.hashes(), opts.version, triple),
      }
    end,

    STAGE = { strip = platform.WINDOWS and 0 or 1 },

    PRODUCTS = products,
  }
end

return M
```

A spec is then a name, a repo, and a hash table:

```lua title="specs/uv.lua"
-- @envy schema "1"
IDENTITY = "envy.uv@r0"
EXPORTABLE = true

local hashes -- version -> triple -> sha256, at the bottom of this file

local uv = require("lib.rust_binary").tool {
  name = "uv",
  repo = "astral-sh/uv",
  binaries = { "uv", "uvx" },
  hashes = function() return hashes end,
}

OPTIONS = uv.OPTIONS
FETCH = uv.FETCH
STAGE = uv.STAGE
PRODUCTS = uv.PRODUCTS

hashes = {
  ["0.11.30"] = {
    ["aarch64-apple-darwin"] = "9bed3567...dc357",
    ["x86_64-unknown-linux-musl"] = "023fdd3b...4c70c",
  },
}
```

Adding the fourth tool of that shape is a hash table, and fixing the extraction
rule fixes it for all of them. `hashes` is passed as a function rather than a
value. That lets each spec keep its table at the bottom of the file, where it
does not bury the interesting lines.

### Reaching a bundle's API from outside the bundle

`require` only works for specs the bundle ships. A spec that lives elsewhere,
including a project-local one, reaches the same modules with
`envy.loadenv_spec(identity, module)`.

The motivating case is fetch bootstrap. A project whose artifacts live in
Artifactory would otherwise repeat the same shell in every spec:

```lua
-- What you do not want in ten specs.
envy.run(envy.product("jf") .. " rt download --flat --fail-no-op '" ..
         repo .. "/" .. path .. "' '" .. dest .. "'")
```

Put it in the bundle once. `envy.loadenv_spec` executes the module in a sandbox
and hands back what it returned, the same rule `require` follows, so one module
serves both callers unchanged:

```lua title="lib/jfrog.lua"
local M = {}

---A declarative fetch for an artifact in an Artifactory generic repo.
---@param opts table `{ base, repo, path, sha256 }`
---@return table fetch a FETCH table
function M.artifact(opts)
  return {
    source = opts.base .. "/artifactory/" .. opts.repo .. "/" .. opts.path,
    sha256 = opts.sha256,
  }
end

---The same artifact through the CLI, for repos that need it to authenticate.
---Commits the file, so a FETCH that calls this returns nothing.
---@param opts table `{ jf, repo, path, dest, tmp_dir, sha256 }`
function M.download(opts)
  envy.run(envy.template([[
    {{jf}} rt download --flat --fail-no-op '{{repo}}/{{path}}' '{{dest}}'
  ]], {
    jf = opts.jf,
    repo = opts.repo,
    path = opts.path,
    dest = envy.path.join(opts.tmp_dir, opts.dest),
  }))
  envy.commit_fetch({ filename = opts.dest, sha256 = opts.sha256 })
end

return M
```

Before envy 0.4.6, `envy.loadenv_spec` returned the sandbox globals whatever the
module returned, so a module on this path had to assign `jfrog = M` as well and
callers reached it as `envy.loadenv_spec(...).jfrog`. That assignment is now
dead weight. Both forms still work, because a module that returns nothing still
hands back its globals, but there is no reason to write both.

A project-local spec then reads as one call:

```lua title="envy/local.toolchain.lua"
-- @envy schema "1"
IDENTITY = "local.toolchain@r0"

local hashes -- version -> sha256, at the bottom of this file

OPTIONS = { version = { required = true } }

BUNDLES = {
  acme = {
    identity = "acme.specs@r1",
    source = "https://github.com/acme/envy-specs.git",
    ref = "ded36a39bbf13744f5a0e539f2f4741fecb61dd0",
  },
}

DEPENDENCIES = {
  { spec = "acme.cmake@r0", bundle = "acme", needed_by = "fetch" },
}

FETCH = function(tmp_dir, opts)
  local jfrog = envy.loadenv_spec("acme.cmake@r0", "lib.jfrog")

  return jfrog.artifact {
    base = "https://acme.jfrog.io",
    repo = "toolchains",
    path = "gcc-" .. opts.version .. ".tar.zst",
    sha256 = hashes[opts.version],
  }
end

hashes = { ["15.2"] = "9f2c1d5b...1a4f" }
```

`jfrog.artifact` returns a table, and `FETCH` hands that table back unchanged, so
envy performs the download and verifies the hash. No `envy.commit_fetch` is
involved. That call belongs to the imperative path, where a fetch function
downloads into `tmp_dir` itself and has to move the result somewhere durable.
`jfrog.download` above is that path, which is why it commits and why a `FETCH`
calling it returns nothing.

Four rules govern `envy.loadenv_spec`:

- **It needs a declared dependency.** `envy.loadenv_spec` resolves the module
  relative to a dependency you named. When that dependency came from a bundle,
  the path resolves inside the bundle root, which is how `lib.jfrog` is found
  through a dependency on `acme.cmake@r0`.
- **`needed_by` applies.** The default is `build`, so calling from `FETCH`
  without `needed_by = "fetch"` reports `dependency 'acme.cmake@r0' needed_by
  'build' but accessed during 'fetch'`.
- **Phase functions only.** At file scope there is no phase context, and envy
  says so.
- **Bundle aliases are file-scoped.** A spec's `DEPENDENCIES` resolves
  `bundle = "acme"` against that spec's own `BUNDLES` table rather than the
  manifest's. A spec that pulls from a bundle declares that bundle itself. The
  same rule covers imported manifests, where an entry resolves against the
  `BUNDLES` of the manifest that declared it.

### Reaching a bundle's API from a manifest

`envy.loadenv_spec` needs a phase to run in, so a manifest cannot use it. From
envy 0.4.6,
[`envy.loadenv_bundle(alias, module)`](/reference/lua-api#envyloadenv_bundlealias-module)
is the manifest-scope version. It names a `BUNDLES` alias, fetches that bundle
on the spot, and returns the module.

That is what lets a bundle ship the helper that writes its own consumers'
entries. One generic spec plus a builder that knows how to call it, and a
consumer writes a line per dependency instead of restating the spec, the alias,
and the vendor path every time:

```lua title="lib/github.lua, in the bundle"
local M = {}

---One source tree from GitHub, vendored into the project for the build to compile.
---@param name string leaf directory name under the consumer's VENDOR_ROOT
---@param repo string "owner/name"
---@param ref string full commit sha
---@return table entry a PACKAGES entry
function M.repo(name, repo, ref)
  return {
    spec = "acme.github@r0",
    bundle = ENVY_BUNDLE.alias,
    vendor = (VENDOR_ROOT or "vendor") .. "/" .. name,
    options = { repo = repo, ref = ref },
  }
end

return M
```

```lua title="envy.lua, in the consuming project"
BUNDLES = {
  tools = {
    identity = "acme.specs@r1",
    source = "https://github.com/acme/envy-specs.git",
    ref = "ded36a39bbf13744f5a0e539f2f4741fecb61dd0",
  },
}

VENDOR_ROOT = "third_party"

local gh = envy.loadenv_bundle("tools", "lib.github")

PACKAGES = {
  gh.repo("libb64", "libb64/libb64", "ce864b1d3f4b9e0e2b0a4e5f0c9d8a7b6c5d4e3f"),
  gh.repo("hidapi", "libusb/hidapi", "4ebce6b0dcdd9eb9b8d8d0a0d0b9f8e7d6c5b4a3"),
}
```

`BUNDLES` has to be assigned above the call, because a manifest is read top to
bottom.

An entry the builder returns is parsed exactly like one written out in the
manifest. Its `bundle` resolves against the *consuming* manifest's `BUNDLES`, so
a helper may name any alias its consumer declared, including one pointing at a
different bundle. It may also carry [`vendor`](/concepts/vendoring), which
before envy 0.4.6 was rejected on any entry that named a bundle.

[`ENVY_BUNDLE`](/reference/lua-api#envy_bundle), from envy 0.4.7, is what spares
the builder from being handed a name its caller already typed. A module loaded
out of a bundle sees the bundle's `identity`, its materialized `root`, and the
`alias` the caller reached it by. Under `envy.loadenv_spec` the `alias` is `nil`,
since that call names the dependency by identity. It is `nil` altogether where no
bundle is involved.

The builder reads `VENDOR_ROOT` out of the consuming manifest, because
[a module reads the globals of the file that loaded it](/reference/lua-api#what-a-module-can-read).
The two entries above land in `third_party/libb64` and `third_party/hidapi`.
Spelling the leaf out matters here. Every entry the builder writes shares the
identity `acme.github@r0`, so `vendor = true` would derive names that escalate
to an options hash.

When the consuming manifest is an [imported component](/guides/monorepos), the
builder sees the component's globals. That needs envy 0.4.8. Before it, a
builder loaded by an imported manifest saw the root manifest's globals instead.
Unless the root had already assigned `VENDOR_ROOT`, the builder read `nil` and
every entry fell back to `vendor/`.

A bundle with a [custom fetch](./fetch-dependencies.md) is refused here by name.
Its fetch function needs a phase to run in, and its `source.dependencies` cannot
be ordered this early.

## See also

- [Anatomy of a Spec](/concepts/specs) for the globals a factory module returns.
- [Creating a Bundle](/guides/creating-bundles) for the producer-side layout.
- [Fetch Dependencies](./fetch-dependencies.md) for the bootstrap ordering that
  makes the jfrog case work.
