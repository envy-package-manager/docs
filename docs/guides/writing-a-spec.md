---
sidebar_position: 3
title: Writing a Spec
---

# Writing a Spec

A tutorial. Start with the smallest spec that works, then grow it until it is
something worth publishing.

The reference companion is [Anatomy of a Spec](/concepts/specs).

## 1. The smallest thing that works

Two globals. `IDENTITY`, and a `FETCH` that names a URL:

```lua title="envy/local.ripgrep.lua"
-- @envy schema "1"
IDENTITY = "local.ripgrep@r0"

FETCH = "https://github.com/BurntSushi/ripgrep/releases/download/14.1.1/ripgrep-14.1.1-aarch64-apple-darwin.tar.gz"
STAGE = { strip = 1 }
PRODUCTS = { rg = "rg" }
```

```lua title="envy.lua"
PACKAGES = {
  { spec = "local.ripgrep@r0", source = envy.abspath("envy/local.ripgrep.lua") },
}
```

```console
$ ./bin/envy sync
[local.ripgrep@r0] installed (1.9s)
deploy: 1 product script(s) (1 created, 0 updated, 0 unchanged, 0 removed)
$ ./bin/rg --version
ripgrep 14.1.1
```

envy downloaded the archive, extracted it, and the extracted tree *is* the
package. There is no `BUILD` and no `INSTALL`, because the defaults already do
the right thing. `strip = 1` removes the wrapper directory the tarball has, so
`rg` lands at the top of the package.

Iterate with a `local.*` identity like this. That namespace is reserved for
project-local specs, and nothing published can depend on it.

## 2. Make it work on every platform

Hardcoding one platform's URL is fine for an afternoon. Compute it instead:

```lua
local function triple()
  if envy.PLATFORM == "darwin" then
    return (envy.ARCH == "arm64") and "aarch64-apple-darwin" or "x86_64-apple-darwin"
  elseif envy.PLATFORM == "linux" then
    return (envy.ARCH == "x86_64") and "x86_64-unknown-linux-musl"
        or "aarch64-unknown-linux-musl"
  end
  return "x86_64-pc-windows-msvc"
end

local ARCHIVE_EXT = (envy.PLATFORM == "windows") and ".zip" or ".tar.gz"

FETCH = function(tmp_dir, opts)
  return "https://github.com/BurntSushi/ripgrep/releases/download/14.1.1/ripgrep-14.1.1-"
      .. triple() .. ARCHIVE_EXT
end
```

A spec runs on the machine doing the install, so `envy.PLATFORM` and `envy.ARCH`
describe that machine. There is no cross-building to account for.

## 3. Add integrity

An unhashed download is a reproducibility hole, and it is also slow: envy
re-fetches an unverified file on every attempt rather than trusting it. Get the
hashes and put them in a table:

```console
$ envy fetch https://github.com/BurntSushi/ripgrep/releases/download/14.1.1/ripgrep-14.1.1-aarch64-apple-darwin.tar.gz /tmp/rg.tar.gz
$ envy hash /tmp/rg.tar.gz
9f2c1d5b8e47a03f6c2d9b1e4a7f0c3d8b5e2a9f4c1d7b0e3a6f9c2d5b8e1a4f  rg.tar.gz
```

```lua
local hashes -- version -> triple -> sha256, filled in at the bottom of this file

FETCH = function(tmp_dir, opts)
  local t = triple()
  local hash = hashes[opts.version] and hashes[opts.version][t]
  if not hash then
    error("no recorded hash for " .. opts.version .. " on " .. t)
  end
  return {
    source = "https://github.com/BurntSushi/ripgrep/releases/download/"
        .. opts.version .. "/ripgrep-" .. opts.version .. "-" .. t .. ARCHIVE_EXT,
    sha256 = hash,
  }
end

-- https://github.com/BurntSushi/ripgrep/releases
hashes = {
  ["14.1.1"] = {
    ["aarch64-apple-darwin"] = "9f2c1d5b...1a4f",
    ["x86_64-unknown-linux-musl"] = "023fdd3b...4c70c",
  },
}
```

Declaring `local hashes` at the top and assigning at the bottom keeps the table
out of the way of the interesting lines. Adding a version becomes a reviewable
diff of hashes.

## 4. Accept options

`OPTIONS` is what turns one spec into a spec many projects can use:

```lua
OPTIONS = {
  version = { required = true },
}
```

Now `options = { version = "14.1.1" }` in the manifest is validated before
anything downloads, and an undeclared option is rejected with the list of ones
that exist. Two entries with different versions are two packages, cached side by
side.

To reject a version the spec has no hash for, use the function form:

```lua
OPTIONS = function(opts)
  envy.options({ version = { required = true } })
  if not hashes[opts.version] then
    return "unrecorded version '" .. opts.version .. "'"
  end
end
```

Returning a string is the good error. It becomes the message the user sees.

## 5. Advertise products

Everything a consumer should reach goes in `PRODUCTS`:

```lua
PRODUCTS = { rg = "rg" .. envy.EXE_EXT }
```

Executable products get [wrapper scripts](/concepts/environment/product-scripts)
deployed. Anything not executable takes `script = false`:

```lua
PRODUCTS = {
  mylib_h = { value = "include/mylib.h", script = false },
  mylib_dir = { value = "include", script = false },
}
```

Both shapes are common, because a build system usually wants the directory and a
dependency edge wants the file.

## 6. Build from source when you must

If no prebuilt archive exists, add `BUILD` and `INSTALL`:

```lua
STAGE = { strip = 1 }

BUILD = function(install_dir, stage_dir, fetch_dir, tmp_dir, opts)
  return envy.template([[
    ./configure --prefix={{prefix}}
    make -j
  ]], { prefix = install_dir })
end

INSTALL = "make install"
```

`install_dir` matters: an autotools package bakes its prefix into the binaries, so
it has to be configured with its final location rather than moved afterward.

If the build needs other tools, declare them and resolve them by product name:

```lua
DEPENDENCIES = { { product = "cmake" }, { product = "ninja" } }

BUILD = function(install_dir, stage_dir, fetch_dir, tmp_dir, opts)
  return envy.template([[
    {{cmake}} -G Ninja -DCMAKE_INSTALL_PREFIX={{prefix}} -S . -B build
    {{ninja}} -C build install
  ]], {
    cmake = envy.product("cmake"),
    ninja = envy.product("ninja"),
    prefix = install_dir,
  })
end
```

The dependency edge is what makes `envy.product` legal, and what guarantees cmake
is installed before `BUILD` runs.

## 7. Mark it exportable

If the installed tree is relocatable, say so:

```lua
EXPORTABLE = true
```

That lets a [depot](/concepts/depots) publish the built result, so nobody else has
to build it. Leave it off when the install has to happen per machine, such as a
platform installer, and the depot will publish the downloaded artifacts instead.

## 8. Promote it

While iterating, keep the spec at `local.*` in your own repo. When it is worth
sharing:

1. Rename the identity out of `local.*`, for example `acme.ripgrep@r0`.
2. Move the file into a [bundle](./creating-bundles.md), or publish it at a URL
   and have consumers pin its `sha256`.
3. Consumers change `source` to `bundle`, and nothing else.

Bump the revision, `@r0` to `@r1`, whenever the spec's shape changes in a way
that is not backward compatible: a renamed product, a new required option, a
different install layout. A cache entry is keyed on identity plus options and not
on spec contents, so the revision is how you tell envy and your users that this is
a different thing.

## Debugging while you write

| Want | Command |
| --- | --- |
| Check a URL and get its hash | `envy fetch <url> /tmp/x && envy hash /tmp/x` |
| See what is inside an archive | `envy extract /tmp/x /tmp/peek` |
| Test an `only` glob list | `envy extract /tmp/x /tmp/peek --only 'bin/*'` |
| Try a Lua helper | `envy lua /tmp/probe.lua` |
| See why a package rebuilt | `envy --verbose sync <query>` |

## See also

- [Anatomy of a Spec](/concepts/specs) and the per-verb pages.
- [Options](/concepts/specs/options), [Products](/concepts/specs/products).
- [Creating a Bundle](./creating-bundles.md) for shipping several specs together.
