---
sidebar_position: 6
title: Bundles
---

# Bundles

> **Placeholder content.** Outline for review. Verify against sources.

A bundle is a versioned container of specs: one pin that delivers a whole
toolbox of package definitions.

Will cover:

- The consumer side:

```lua
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
}
```

- One `ref` pin covers every spec taken from the bundle, so the whole toolbox
  upgrades atomically.
- The producer side, meaning `envy-bundle.lua` with its `BUNDLE` and `SPECS`
  globals. See [Creating a Bundle](/guides/creating-bundles).
- How bundles arrive. envy materializes the bundle through the
  [fetch-dependency](./fetch-dependencies.md) machinery before reading any spec
  out of it. A bundle can therefore live behind the same bootstrap tooling as
  anything else.
- Inline bundle references on a single entry, using `bundle = { ... }` in place
  of an alias.
- Identity integrity. A spec fetched from a bundle has to declare the identity
  the bundle promised for it.

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
and returns that sandbox, not the module's return value, so a module meant for
this path assigns a global. Do both, and one module serves both callers:

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

jfrog = M   -- global, for envy.loadenv_spec callers
return M    -- return value, for require callers
```

A project-local spec then reads as one call:

```lua title="envy/local.toolchain.lua"
-- @envy schema "1"
IDENTITY = "local.toolchain@r0"

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
  local jfrog = envy.loadenv_spec("acme.cmake@r0", "lib.jfrog").jfrog

  return jfrog.artifact {
    base = "https://acme.jfrog.io",
    repo = "toolchains",
    path = "gcc-" .. opts.version .. ".tar.zst",
    sha256 = hashes[opts.version],
  }
end
```

Four rules govern that call:

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
  manifest's. A spec that pulls from a bundle declares that bundle itself.

## See also

- [Anatomy of a Spec](/concepts/specs) for the globals a factory module returns.
- [Creating a Bundle](/guides/creating-bundles) for the producer-side layout.
- [Fetch Dependencies](./fetch-dependencies.md) for the bootstrap ordering that
  makes the jfrog case work.
