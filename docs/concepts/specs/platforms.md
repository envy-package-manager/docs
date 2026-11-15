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

| # | Where | Decides |
| --- | --- | --- |
| 1 | Manifest entry `platforms = { ... }` | Whether this machine installs the package. |
| 2 | Spec `PLATFORMS = { ... }` | Which wrapper flavors the package's products get. |
| 3 | [SETUP](./setup.md) pair `PLATFORMS = { ... }` | Whether this machine runs the pair. |
| 4 | [Product](./products.md) `platforms = { ... }` | Which wrapper flavors one product gets. |

Only (1) and (3) look at the machine envy runs on. A spec's `PLATFORMS` does not
stop the package from installing, and it does not stop a selected SETUP pair
from running. To keep a package off a machine, filter the manifest entry.

```lua title="envy.lua: (1) the project only wants apt on Linux"
PACKAGES = {
  { spec = "acme.apt@r0", source = specs .. "acme.apt.lua",
    platforms = { "linux" },
    options = { packages = { "libudev-dev" } },
    setup = { "packages" } },
}
```

```lua title="acme.jlink.lua: (2) and (3)"
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
    products.jlink_udev_rules = { value = "99-jlink.rules", script = false }  -- Linux hosts only
  end
  return products
end
```

### How (1), (2) and (4) combine

envy intersects the entry's list, the spec's list, and the product's list. The
result decides which wrappers [`sync`](../../reference/cli/sync.md) and
[`deploy`](../../reference/cli/deploy.md) write for that product: the POSIX
script if it names `darwin` or `linux`, the `.bat` if it names `windows`. If the
lists share nothing, the product gets no wrapper, with no error.

An OS entry covers its architectures, so lists of different granularity meet at
the narrower entry. Since envy 0.7.1.

| Entry `platforms` | Spec `PLATFORMS` | Intersection |
| --- | --- | --- |
| absent | absent | every platform |
| `{ "linux" }` | absent | `linux` |
| absent | `{ "windows" }` | `windows` |
| `{ "linux", "darwin" }` | `{ "darwin" }` | `darwin` |
| `{ "darwin", "linux" }` | `{ "darwin-arm64", "linux-x86_64" }` | `darwin-arm64`, `linux-x86_64` |
| `{ "linux" }` | `{ "darwin" }` | none, so no wrappers |

Wrappers come in two flavors, so the result only chooses between POSIX and
Windows. A spec limited to `linux` still gets its POSIX wrapper on a Mac.
`envy product` ignores (2) and (4), and resolves the product on any machine that
installs the package. To offer a product on some machines only, compute
`PRODUCTS` from `envy.PLATFORM`, as the jlink example does.

Naming a package that its entry excludes is different. `envy install acme.apt@r0`
on macOS is an error, because you asked for something specific that cannot
happen.
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
