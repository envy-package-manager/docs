---
sidebar_position: 11
title: Platforms
---

# Platforms

envy installs for the machine it is running on. There is no cross-building and
no target triple. A cross-platform repo gets its coverage from a CI matrix, and
every machine resolves its own packages.

Platform filters decide which packages a given machine instantiates.

## Vocabulary

| Form | Example | Matches |
| --- | --- | --- |
| OS | `"linux"` | that OS, any architecture |
| OS and arch | `"darwin-arm64"` | that pair only |

The OS names are `darwin`, `linux`, and `windows`. The architectures are `arm64`
and `x86_64`. In Lua:

| Name | Value on an Apple-silicon Mac |
| --- | --- |
| `envy.PLATFORM` | `"darwin"` |
| `envy.ARCH` | `"arm64"` |
| `envy.PLATFORM_ARCH` | `"darwin-arm64"` |
| `envy.EXE_EXT` | `""`, and `".exe"` on Windows |

An empty or absent filter means everywhere. A filter list matches if any entry
matches.

## The four places filters apply

| # | Where | Meaning |
| --- | --- | --- |
| 1 | Manifest entry `platforms = { ... }` | This project only needs it here. |
| 2 | Spec `PLATFORMS = { ... }` | This package only exists here. |
| 3 | [SETUP](./setup.md) pair `PLATFORMS = { ... }` | This host tweak only applies here. |
| 4 | [Product](./products.md) `platforms = { ... }` | This tool only ships here. |

```lua title="envy.lua: (1) the project only wants apt on Linux"
PACKAGES = {
  { spec = "acme.apt@r0", source = specs .. "acme.apt.lua",
    platforms = { "linux" },
    options = { packages = { "libudev-dev" } },
    setup = { "packages" } },
}
```

```lua title="acme.jlink.lua: (2), (3) and (4)"
PLATFORMS = { "darwin", "linux", "windows" }     -- (2) all three, explicitly

SETUP = {
  udev_rules = {
    PLATFORMS = { "linux" },                     -- (3) kernel rules are Linux-only
    CHECK = ..., INSTALL = ...,
  },
}

PRODUCTS = function(opts)
  local products = { JLinkExe = exe("JLink") }
  if envy.PLATFORM == "linux" then
    products.jlink_udev_rules = { value = "99-jlink.rules", script = false }  -- (4)
  end
  return products
end
```

### How (1) and (2) combine

envy intersects the entry's list with the spec's list. If both are non-empty and
share nothing, the package never instantiates: no error, no scripts, no work.

| Entry `platforms` | Spec `PLATFORMS` | Result |
| --- | --- | --- |
| absent | absent | everywhere |
| `{ "linux" }` | absent | Linux only |
| absent | `{ "darwin" }` | macOS only |
| `{ "linux", "darwin" }` | `{ "darwin" }` | macOS only |
| `{ "linux" }` | `{ "darwin" }` | nowhere |

Naming an excluded package explicitly is different. `envy sync acme.apt@r0` on
macOS is an error, because you asked for something specific that cannot happen.
A filter that does less is fine. A query that silently does nothing is not.

## Switching inside a spec

Platform logic is ordinary Lua, and it can define different verbs per platform:

```lua
if envy.PLATFORM == "windows" then
  FETCH = "https://github.com/PolarGoose/Ragel-for-Windows/releases/download/ragel-6.10/Ragel.zip"
  PRODUCTS = { ragel = "Ragel.exe" }
else
  FETCH = "https://www.colm.net/files/ragel/ragel-6.10.tar.gz"
  STAGE = { strip = 1 }
  BUILD = function(install_dir) return "./configure --prefix=" .. install_dir .. "\nmake -j" end
  INSTALL = "make install"
  PRODUCTS = { ragel = "bin/ragel" }
end
```

Two smaller patterns:

```lua
-- Fail loudly on a platform the vendor does not publish for.
FETCH = function(tmp_dir, opts)
  local key = ({ darwin = "macos", linux = "linux", windows = "win64" })[envy.PLATFORM]
  assert(key, "unsupported platform: " .. envy.PLATFORM)
  return base .. "tool-" .. opts.version .. "-" .. key .. ".tar.gz"
end

-- Vendor arch naming rarely matches envy's, so normalize once.
local arch = (envy.ARCH == "arm64") and "aarch64" or envy.ARCH
```

## Not the same thing: `--platform`

[`envy init`](../../reference/cli/init.md),
[`sync`](../../reference/cli/sync.md), and
[`deploy`](../../reference/cli/deploy.md) take a `--platform` flag. It selects
which script flavors get written into the bin directory: POSIX shell scripts,
Windows `.bat` files, or both.

```bash
envy sync --platform all      # commit wrappers for POSIX and Windows
```

It says nothing about which packages install. A macOS machine still installs
macOS packages. The flag exists so a cross-platform repo can commit working
wrappers for colleagues on other systems.

## See also

- [Anatomy of a Spec](./index.md#specs-run-on-the-host) for why everything is host-relative.
- [Package Entries](../projects#package-entries) for the `platforms` field.
- [SETUP](./setup.md) and [Products](./products.md) for the other two filter sites.
