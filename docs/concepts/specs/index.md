---
sidebar_position: 1
title: Anatomy of a Spec
slug: /concepts/specs
---

# Anatomy of a Spec

A spec is a Lua file that teaches envy how to acquire one kind of package. It
sets UPPERCASE globals. Everything else in the file is ordinary Lua: locals,
helper functions, tables of hashes.

Only `IDENTITY` is required. Everything else is optional or has a default, so a
useful spec can be four lines long:

```lua title="the whole spec"
-- @envy schema "1"
IDENTITY = "acme.ripgrep@r0"
FETCH = "https://github.com/BurntSushi/ripgrep/releases/download/14.1.1/ripgrep-14.1.1-aarch64-apple-darwin.tar.gz"
STAGE = { strip = 1 }
PRODUCTS = { rg = "rg" }
```

## The global roster

| Global | Type | Purpose |
| --- | --- | --- |
| `IDENTITY` | string | Required. `namespace.name@revision`. |
| [`FETCH`](./fetch.md) | string \| table \| function | Get the bytes. Required unless the spec is [user-managed](./user-managed.md). |
| [`STAGE`](./stage.md) | string \| table \| function | Arrange a working tree. Defaults to extracting every fetched archive. |
| [`BUILD`](./build.md) | string \| function | Transform the tree. Defaults to nothing. |
| [`INSTALL`](./install.md) | string \| function | Produce the final package directory. Defaults to promoting the staged tree. |
| [`SETUP`](./setup.md) | table of named `CHECK`/`INSTALL` pairs | Adjust the host machine. Runs only when a manifest entry selects a pair by name. |
| [`OPTIONS`](./options.md) | table \| function | Declare and validate the options this spec accepts. |
| [`PRODUCTS`](./products.md) | table \| function | Name what the package offers consumers. |
| [`DEPENDENCIES`](../dependencies/declaring.md) | array | Other packages this one needs, and how early. |
| [`PLATFORMS`](./platforms.md) | array of string | Where this package exists at all. |
| [`USER_MANAGED`](./user-managed.md) | boolean \| function | Orchestrate host state instead of owning files. |
| `EXPORTABLE` | boolean | Whether the installed tree may be published to a [depot](../depots.md). See [INSTALL](./install.md#exportable). |
| `BUNDLES` | table | Alias to bundle declaration, for specs whose dependencies live in a bundle. |

A top-level `CHECK` is an error. `CHECK` is half of a `SETUP` pair, and the
error message says so.

## Every verb takes several shapes

Each verb accepts a string for the simple case, a table for the declarative
case, a function for the programmatic case, or nothing for the default. A
two-line spec and a two-hundred-line spec are both idiomatic. A spec can grow one
verb at a time.

| Verb | omitted | string | table | function |
| --- | --- | --- | --- | --- |
| `FETCH` | error, unless user-managed | one URL | one download, or an array of them | compute the download set, or fetch imperatively |
| `STAGE` | extract every fetched archive | shell script | extract options (`strip`, `only`) | full control |
| `BUILD` | no build step | shell script | not accepted | script generator or imperative build |
| `INSTALL` | staged tree becomes the package | shell script | not accepted | file surgery, platform installers |

Function verbs receive their directories as arguments, with a trailing
separator already applied, so specs concatenate rather than join:

```lua
INSTALL = function(install_dir, stage_dir, fetch_dir, tmp_dir, opts)
  envy.run("pkgutil --expand-full " .. fetch_dir .. "JLink.pkg " .. install_dir .. "jlink")
end
```

A function verb that returns a string has that string run as a shell script.
See [Shells & Scripts](./shells.md). Computing a script and returning it is a
normal pattern:

```lua
BUILD = function(install_dir, stage_dir, fetch_dir, tmp_dir, opts)
  return envy.template([[
    ./configure --prefix={{prefix}}
    make -j
  ]], { prefix = install_dir })
end
```

## Three real specs, smallest to largest

### A header-only library

```lua title="doctest-cpp.lua"
-- @envy schema "1"
IDENTITY = "envy.doctest-cpp@r0"
EXPORTABLE = true

local hashes = { ["2.5.3"] = "cfd518a3ef90f67e1f3ba514df23fb3627437de1a2feeba78cf5062a40021421" }

OPTIONS = { version = { required = true, choices = { "2.5.3" } } }

FETCH = function(tmp_dir, opts)
  return {
    source = "https://raw.githubusercontent.com/doctest/doctest/v" ..
        opts.version .. "/doctest/doctest.h",
    sha256 = hashes[opts.version],
  }
end

PRODUCTS = {
  doctest_cpp_dir = { value = ".", script = false },
  doctest_cpp_h = { value = "doctest.h", script = false },
}
```

No `STAGE`, no `BUILD`, no `INSTALL`. One downloaded file is the package. Both
products set `script = false`, because a header is not executable. No wrapper is
deployed, and consumers ask
[`envy product doctest_cpp_h`](../../reference/cli/product.md) for the path.

### A prebuilt binary that needs renaming

```lua title="taplo.lua"
-- @envy schema "1"
IDENTITY = "acme.taplo@r1"
EXPORTABLE = true

OPTIONS = { version = { required = true } }

FETCH = function(tmp_dir, opts)
  local arch = (envy.ARCH == "arm64") and "aarch64" or envy.ARCH
  local ext = (envy.PLATFORM == "windows") and ".zip" or ".gz"
  return "https://github.com/tamasfe/taplo/releases/download/" ..
      opts.version .. "/taplo-" .. envy.PLATFORM .. "-" .. arch .. ext
end

INSTALL = function(install_dir, stage_dir, fetch_dir, tmp_dir, opts)
  local bin = envy.path.join(install_dir, "taplo" .. envy.EXE_EXT)
  if envy.PLATFORM == "windows" then
    envy.copy(envy.path.join(stage_dir, "taplo.exe"), bin)
  else
    local arch = (envy.ARCH == "arm64") and "aarch64" or envy.ARCH
    envy.copy(envy.path.join(stage_dir, "taplo-" .. envy.PLATFORM .. "-" .. arch), bin)
    envy.run("chmod +x " .. bin)
  end
end

PRODUCTS = { taplo = "taplo" .. envy.EXE_EXT }
```

`FETCH` computes a per-platform URL. `INSTALL` exists only because the vendor
ships a platform-suffixed filename and the product should be plain `taplo`.
Everything else is default behavior.

### A setup-only spec that installs Homebrew

```lua title="brew.lua"
-- @envy schema "1"
IDENTITY = "acme.brew@r0"
PLATFORMS = { "darwin" }
USER_MANAGED = true

SETUP = {
  brew = {
    CHECK = "brew --version",
    INSTALL = function(pkg_dir, opts)
      envy.run({
        "sudo -v",
        'curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh | bash',
      }, { env = { NONINTERACTIVE = "1" }, interactive = true })
    end,
  },
}
```

No fetch, no build, nothing cached. The package is host state. See
[User-Managed Packages](./user-managed.md).

## Where specs live

| Location | Manifest entry | Notes |
| --- | --- | --- |
| In the project | `source = envy.abspath("envy/acme.gn.lua")` | Versioned by your git history. |
| At a URL | `source = "https://...", sha256 = "..."` | envy verifies the hash. |
| In git | `source = "https://...git", ref = "<sha>"` | A full commit sha is required. |
| In a [bundle](../dependencies/bundles.md) | `bundle = "envy"` | One pin covers every spec the bundle ships. |

Specs from a bundle can `require()` sibling modules. envy prefixes
`package.path` with the bundle root, which is how published specs share a `lib/`
of helpers. A standalone single-file spec has no such path and keeps its helpers
as locals.

## Specs run on the host

A spec executes on the machine doing the install. `envy.PLATFORM`, `envy.ARCH`,
`envy.PLATFORM_ARCH`, and `envy.EXE_EXT` describe that machine, and there is no
cross-building. Platform switching is ordinary Lua, and it can go as far as
defining different verbs per platform:

```lua
if envy.PLATFORM == "windows" then
  FETCH = "https://.../Ragel.zip"
  PRODUCTS = { ragel = "Ragel.exe" }
else
  FETCH = "https://www.colm.net/files/ragel/ragel-6.10.tar.gz"
  STAGE = { strip = 1 }
  BUILD = function(install_dir) return "./configure --prefix=" .. install_dir .. "\nmake -j" end
  INSTALL = "make install"
  PRODUCTS = { ragel = "bin/ragel" }
end
```

Cross-platform coverage comes from a CI matrix, not from one machine building
for another.

## See also

- [The Package Lifecycle](./lifecycle.md) for the order verbs run in and the directories they see.
- [Writing a Spec](../../guides/writing-a-spec.md) for the authoring workflow.
- [Spec Reference](../../reference/spec-globals.md) for the same roster, terser.
