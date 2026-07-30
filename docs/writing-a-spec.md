---
sidebar_position: 4
title: Writing a Spec
---

# Writing a Spec

> **Placeholder content.** Verify against the envy sources before publishing.

A spec is a Lua file that declares an `IDENTITY` and a pipeline:

```
FETCH → STAGE → BUILD → INSTALL
```

plus optional `SETUP` pairs. Everything is optional except `IDENTITY`; a spec
that only downloads and unpacks a tarball needs `FETCH` and `STAGE`.

## Fetch and install a prebuilt release

```lua title="local.cmake@r0.lua"
-- @envy schema "1"
IDENTITY = "local.cmake@r0"
EXPORTABLE = true

OPTIONS = { version = { required = true } }

local sha256_fingerprints = {
  ["4.2.3-macos-universal"] =
  "c2302d3e9c48daabee5ea7c4db4b2b93b989bcc89dae8b760880e00120641b5b",
  ["4.2.3-linux-x86_64"] =
  "5bb505d5e0cca0480a330f7f27ccf52c2b8b5214c5bba97df08899f5ef650c23",
  ["4.2.3-windows-x86_64"] =
  "eb4ebf5155dbb05436d675706b2a08189430df58904257ae5e91bcba4c86933c",
}

FETCH = function(tmp_dir, opts)
  local platform_arch = ({
    darwin = "macos-universal",
    linux = "linux-" .. envy.ARCH,
    windows = "windows-x86_64",
  })[envy.PLATFORM]

  local ext = (envy.PLATFORM == "windows") and ".zip" or ".tar.gz"
  local filename = "cmake-" .. opts.version .. "-" .. platform_arch .. ext
  local fingerprint = sha256_fingerprints[opts.version .. "-" .. platform_arch]
  assert(fingerprint,
    "unsupported version/platform: " .. opts.version .. "-" .. platform_arch)

  return {
    source = "https://github.com/Kitware/CMake/releases/download/v" ..
        opts.version .. "/" .. filename,
    sha256 = fingerprint,
  }
end

STAGE = { strip = 1 }

local bin = (envy.PLATFORM == "darwin") and "CMake.app/Contents/bin/" or "bin/"

PRODUCTS = { cmake = bin .. "cmake" .. envy.EXE_EXT }
```

Every artifact is pinned by SHA-256. An unpinned fetch is a bug, not a
convenience.

## Setup pairs

Some things cannot live in the cache — they mutate the host. Model those with a
`SETUP` pair: `CHECK` reports whether the host is already in the desired state,
and `INSTALL` returns the command that gets it there.

```lua title="local.brew_package@r0.lua"
-- @envy schema "1"
IDENTITY = "local.brew_package@r0"
PLATFORMS = { "darwin" }
USER_MANAGED = true

DEPENDENCIES = {
  { spec = "local.brew@r0", source = "local.brew@r0.lua", setup = { "brew" } },
}

local missing_packages = {}

SETUP = {
  packages = {
    CHECK = function(pkg_dir, opts)
      local res = envy.run("brew list", { capture = true, quiet = true, check = false })
      if res.exit_code ~= 0 then return false end

      local installed = {}
      for pkg in res.stdout:gmatch("%S+") do installed[pkg] = true end

      missing_packages = {}
      for _, pkg in pairs(opts.packages) do
        if not installed[pkg] then table.insert(missing_packages, pkg) end
      end
      return #missing_packages == 0
    end,

    INSTALL = function(pkg_dir, opts)
      return "brew install " .. table.concat(missing_packages, " ")
    end,
  },
}
```

Setup pairs are opt-in per manifest entry (`setup = { "packages" }`) and are
never hashed into the package key.
