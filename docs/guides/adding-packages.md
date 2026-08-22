---
sidebar_position: 2
title: Adding Packages
---

# Adding Packages

A cookbook of `PACKAGES` entries. Every entry is a table, and the fields are
documented in [Package Entries](/concepts/projects#package-entries).

## From a bundle

The common case once a project has a bundle pinned. One `ref` covers every spec
you take from it:

```lua
BUNDLES = {
  envy = {
    identity = "envy.package-specs@r3",
    source = "https://github.com/envy-package-manager/package-specs.git",
    ref = "ded36a39bbf13744f5a0e539f2f4741fecb61dd0",
  },
}

PACKAGES = {
  { spec = "envy.cmake@r0", bundle = "envy", options = { version = "4.4.0" } },
  { spec = "envy.ninja@r0", bundle = "envy", options = { version = "1.13.2" } },
  { spec = "envy.uv@r0", bundle = "envy", options = { version = "0.11.30" } },
}
```

## From a project-local spec file

For a tool nobody has published a spec for, or one whose spec is specific to your
project:

```lua
local specs = envy.abspath("envy") .. "/"

PACKAGES = {
  { spec = "local.mytool@r0", source = specs .. "local.mytool.lua" },
}
```

`envy.abspath` resolves against the directory of the file that calls it, so the
entry works from any working directory and from a superproject that imports this
manifest. No `sha256` is needed, because the file is already versioned by the
commit you are on.

## From a URL

```lua
{ spec = "acme.protoc-gen-acme@r0",
  source = "https://specs.acme.example/protoc-gen-acme@r0.lua",
  sha256 = "9f2c1d5b8e47a03f6c2d9b1e4a7f0c3d8b5e2a9f4c1d7b0e3a6f9c2d5b8e1a4f",
  options = { version = "2.1.0" } },
```

Pin the hash. Get it with [`envy hash`](../reference/cli/hash.md) after
downloading the file once.

## From git

```lua
{ spec = "acme.jlink@r1",
  source = "https://github.com/acme/envy-specs.git",
  -- envy git-resolve https://github.com/acme/envy-specs refs/heads/main
  ref = "7bc9a0bfe050ef97e1712ff61c6f11952799e951",
  options = { version = "9.30" } },
```

A git source requires a full commit sha. Use
[`envy git-resolve`](../reference/cli/git-resolve.md) to turn a branch or tag into
one, and leave the command in a comment.

## Passing options

Options are ordinary Lua values, and the spec's `OPTIONS` schema decides which
are legal:

```lua
{ spec = "envy.python@r1", bundle = "envy",
  options = {
    version = "3.13.14",        -- string
    release = "20260623",
    provide_python3 = true,     -- boolean
  } },

{ spec = "acme.clang-tools@r0", source = specs .. "acme.clang-tools.lua",
  options = {
    version = "22.1.8",
    tools = { "clang-format", "clang-tidy" },   -- list
  } },
```

Options are part of the package's identity, which is what lets two entries for
one spec coexist:

```lua
{ spec = "envy.python@r1", bundle = "envy",
  options = { version = "3.13.14", release = "20260623", provide_python3 = true } },
{ spec = "envy.python@r1", bundle = "envy",
  options = { version = "3.14.2", release = "20260623" } },
```

Both install. The first claims the `python3` product name, the second does not, so
there is no collision. Each also provides its own `python3.13` or `python3.14`.

## Restricting to platforms

```lua
{ spec = "acme.apt@r0", source = specs .. "acme.apt.lua",
  platforms = { "linux" },
  options = { packages = { "libusb-1.0-0-dev" } } },

{ spec = "acme.dtrace-tools@r0", source = specs .. "acme.dtrace-tools.lua",
  platforms = { "darwin-arm64" } },
```

An entry whose filter excludes the current machine never instantiates, with no
error. Naming it explicitly on the wrong platform *is* an error, so a typo in a
CLI query fails loudly. See [Platforms](/concepts/specs/platforms).

## Opting into setup pairs

Nothing in a spec's [SETUP](/concepts/specs/setup) runs unless an entry names it:

```lua
{ spec = "acme.jlink@r1", source = specs .. "acme.jlink.lua",
  options = { version = "9.30" },
  setup = { "udev_rules" } },
```

Conditional selection is normal, because the manifest is Lua:

```lua
local ci = os.getenv("CI")

{ spec = "acme.apt@r0", source = specs .. "acme.apt.lua",
  platforms = { "linux" },
  options = { packages = { "libusb-1.0-0-dev" } },
  setup = not ci and { "packages" } or nil },
```

Selecting a pair does not change the package's identity, so the same cached
artifact serves a machine that selected it and one that did not.

## Environment-conditional entries

The manifest is a program. `os.getenv` and `envy.extend` are available:

```lua
PACKAGES = {
  { spec = "envy.cmake@r0", bundle = "envy", options = { version = "4.4.0" } },
}

if os.getenv("ACME_ENABLE_COVERAGE") then
  envy.extend(PACKAGES, {
    { spec = "acme.coverage-tools@r0", source = specs .. "acme.coverage-tools.lua" },
  })
end
```

Use this sparingly. An entry that appears only under an environment variable is
an entry most contributors never see.

## Verifying the result

```console
$ envy sync
[envy.cmake@r0] installed (8.2s)
deploy: 3 product script(s) (3 created, 0 updated, 0 unchanged, 0 removed)

$ envy product                 # what the project now offers
cmake   bin/cmake   envy.cmake@r0{version="4.4.0"}
ctest   bin/ctest   envy.cmake@r0{version="4.4.0"}
cpack   bin/cpack   envy.cmake@r0{version="4.4.0"}

$ cmake --version
cmake version 4.4.0
```

If a product you expected is missing, the spec probably declares it
`script = false`, which deploys no wrapper on purpose. Ask for it directly with
`envy product <name>`.

Commit the manifest and the new wrappers together.

## See also

- [Package Entries](/concepts/projects#package-entries) for the full field list.
- [Options](/concepts/specs/options) for what a spec accepts and why.
- [Writing a Spec](./writing-a-spec.md) when no spec exists yet.
