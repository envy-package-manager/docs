---
sidebar_position: 2
title: Projects & Manifests
slug: /concepts/projects
---

# Projects & Manifests

A project is a directory containing an `envy.lua` manifest. The manifest pins
the version of envy that runs, names every package the project needs, and sets
the project's bin directory. There is no lockfile and no state directory. Every
pin lives in the manifest or in the specs it references. See
[Reproducibility](./reproducibility.md).

`envy.lua` is real Lua, executed by envy's interpreter. Conditionals, locals,
functions, and file composition all work, so one manifest can serve a laptop, a
CI runner, and a Docker build.

## The `@envy` header

The file starts with comment directives. Two readers parse them. One is envy
itself. The other is the committed bootstrap scripts. Those are plain shell and
batch, and they read the directives as text to learn which envy to download.

```lua title="envy.lua"
-- @envy schema "1"
-- @envy version "0.2.0"
-- @envy sha256sums "a17e9c4f...c93f"
-- @envy mirror "https://envy-mirror.acme.example"
-- @envy bin "bin"
-- @envy deploy "true"
-- @envy root "true"
```

| Directive | Required | Meaning |
| --- | --- | --- |
| `schema "N"` | no | Manifest/spec schema version. |
| `version "x.y.z"` | recommended | The envy release this project runs. If absent, the project floats to the latest release. |
| `sha256sums "<64 hex>"` | no | The sha256 of that release's `SHA256SUMS` file. Bootstrap verifies every envy binary it downloads against it. Requires `version`. A pin names one release, so envy rejects the combination rather than stop verifying when the version is resolved dynamically. |
| `bin "<relpath>"` | yes, for `sync`, `deploy`, and `run` | The project's bin directory, relative to the manifest. Holds the committed bootstrap scripts and any deployed wrappers. |
| `deploy "true\|false"` | no (default: off) | Whether `sync`/`deploy` write [product wrapper scripts](./environment/product-scripts.md) into the bin dir. |
| `root "true\|false"` | no (default: true) | Superproject boundary. `false` means discovery keeps searching upward. See [discovery](#manifest-discovery). |
| `mirror "<url>"` | no | Where to download envy releases from, `https://` or `s3://`. `ENVY_MIRROR` overrides it. |
| `cache-local "<path>"` | no | Keep this project's packages in a tree inside it, relative to the manifest. See [The Cache](./cache.md#where-the-root-lives). |
| `cache-mode "local\|shared"` | no | Override what `cache-local`'s presence implies. |
| `state-dir "<path>"` | no | Where `envy cache --local/--shared` records your override. |

Header rules:

- A directive is a comment: optional whitespace, `--`, optional whitespace,
  `@envy`, a space or tab, the key, then a quoted value.
- The first line of Lua code ends the header. Blank lines and ordinary comments
  do not. A directive-shaped comment below the first statement is only a
  comment, and envy will not read it.
- The last occurrence of a key wins.
- Directives are data, not code. `envy use` and `envy cache` read them as text
  without executing the manifest, so they still work when the pinned envy cannot
  be downloaded.

## Globals

| Global | Type | Meaning |
| --- | --- | --- |
| `PACKAGES` | table | **Required.** The array of [package entries](#package-entries). |
| `BUNDLES` | table | Alias → [bundle](./dependencies/bundles.md) declaration. Lets many entries share one pin. |
| `PACKAGE_DEPOTS` | table | Prebuilt-artifact indexes. URI strings, or `{ DEPENDS, FETCH }` tables for depots that need credentials or a tool to reach. See [Depots](./depots.md). |
| `DEFAULT_SHELL` | constant, table, or function | Which shell runs string verbs project-wide ([Shells & Scripts](./shells.md)). |

Three helpers are available in manifest code:

| Helper | What it does |
| --- | --- |
| `envy.abspath("p")` | Resolves `p` against the directory of the file that calls it, not the current directory. A subproject manifest uses it to name its own spec files, so the paths still work when a superproject includes the file. |
| `envy.loadenv("a.b")` | Loads `<caller's dir>/a/b.lua` in a sandbox and returns its globals as a table. Used to reuse one manifest from another. |
| `envy.extend(t, ...)` | Appends the array items of each argument onto `t`. Use it to add entries to an inherited `PACKAGES` list. |

## Package entries

Every element of `PACKAGES` is a table describing one requested package. A bare
identity string is an error: an entry always has to say where the spec comes
from.

| Field | Type | Meaning |
| --- | --- | --- |
| `spec` | string | **Required.** The spec identity: `namespace.name@revision`. |
| `source` | string \| table | Where the spec file comes from. A URL, a local path, a git URL, or a table `{ fetch = function, dependencies = { ... } }` for a spec that has to be fetched by code. See [fetch dependencies](./dependencies/fetch-dependencies.md). Mutually exclusive with `bundle` and with `weak`. |
| `bundle` | string \| table | Take the spec from a [bundle](./dependencies/bundles.md). Either a `BUNDLES` alias or an inline declaration table. Mutually exclusive with `source`. |
| `ref` | string | Commit sha. **Required** when `source` is a git URL. |
| `sha256` | string | Integrity pin for a downloaded spec file. |
| `options` | table | The settings this package is built with. Part of its identity. Functions are rejected, because options have to hash. |
| `platforms` | array of string | Restrict this entry to some platforms, for example `"linux"` or `"darwin-arm64"`. See [Platforms](./specs/platforms.md). |
| `setup` | array of string | Which of the spec's [SETUP](./specs/setup.md) pairs to run. Nothing runs unless named here. |
| `needed_by` | string | How early this package must be ready. One of `check`, `import`, `fetch`, `stage`, `build`, `install`. Defaults to `build`. See [Phase Ordering](./dependencies/ordering.md). |
| `product` | string | Depend on a product name rather than an identity. See [Declaring Dependencies](./dependencies/declaring.md). |
| `weak` | table | A fallback entry, used when this one cannot resolve. Mutually exclusive with `source`. |

### Identity syntax

All three parts of `namespace.name@revision` are required. The revision
versions the spec, not the tool the spec installs:

```lua
PACKAGES = {
  { spec = "envy.cmake@r0", bundle = "envy", options = { version = "4.4.0" } }
  --       ^^^^ ^^^^^ ^^                                        ^^^^^^^
  --    namespace name spec revision                    the tool's version
}
```

Going from `@r0` to `@r1` means the spec changed shape, for example new options
or renamed products, in a way that is not backward compatible.

The `local.*` namespace is reserved for project-local specs. A spec outside
`local.*` cannot depend on a `local.*` spec, so a published spec can never reach
into a particular project.

### One spec, several packages

Two entries for the same spec with different `options` are two independent
packages. Both install, and both are usable at once:

```lua
PACKAGES = {
  { spec = "envy.python@r1", bundle = "envy",
    options = { version = "3.13.14", release = "20260623", provide_python3 = true } },

  { spec = "envy.python@r1", bundle = "envy",
    options = { version = "3.14.2", release = "20260623" } },
}
```

The first entry claims the `python3` product name and the second does not, so
the two coexist. Each also provides its own `python3.13` or `python3.14`.

## A complete manifest

Everything above in one file: a firmware project that pulls published specs
from a bundle, project-local specs from disk, and one spec from a URL.

```lua title="envy.lua"
-- @envy schema "1"
-- @envy version "0.2.0"
-- @envy sha256sums "a17e9c4fbb2d1e07c5a9f0d3e8b47c61f2a09d5e4c3b8a7f6e5d4c3b2a1908f7e"
-- @envy mirror "https://envy-mirror.acme.example"
-- @envy bin "bin"
-- @envy deploy "true"
-- @envy root "true"

-- Prebuilt artifacts, when the depot has them for this platform. Optional.
-- If the depot is unreachable, every package still builds from its spec.
PACKAGE_DEPOTS = { "s3://acme-envy-packages/packages.txt" }

local ci = os.getenv("CI")

-- Spec files that live in this repo, named relative to *this file*.
local specs = envy.abspath("envy") .. "/"

BUNDLES = {
  -- One pin covering every spec the bundle ships.
  envy = {
    identity = "envy.package-specs@r3",
    source = "https://github.com/envy-package-manager/package-specs.git",
    -- envy git-resolve https://github.com/envy-package-manager/package-specs main
    ref = "ded36a39bbf13744f5a0e539f2f4741fecb61dd0",
  },
}

PACKAGES = {
  -- Bundle entries: the spec comes from the bundle above, options are ours.
  { spec = "envy.cmake@r0", bundle = "envy", options = { version = "4.4.0" } },

  { spec = "envy.ninja@r0", bundle = "envy", options = { version = "1.13.2" } },

  { spec = "envy.python@r1", bundle = "envy",
    options = { version = "3.13.14", release = "20260623",
                provide_python = true, provide_python3 = true } },

  { spec = "envy.doctest-cpp@r0", bundle = "envy", options = { version = "2.5.3" } },

  -- Standalone entry, spec file in this repo. No pin needed, because the file
  -- is already versioned by the commit you are on.
  { spec = "acme.armgcc@r1", source = specs .. "acme.armgcc.lua",
    options = { version = "15.2.rel1" } },

  -- Standalone entry, spec fetched over https and hash-pinned.
  { spec = "acme.protoc-gen-acme@r0",
    source = "https://specs.acme.example/protoc-gen-acme@r0.lua",
    sha256 = "9f2c1d5b8e47a03f6c2d9b1e4a7f0c3d8b5e2a9f4c1d7b0e3a6f9c2d5b8e1a4f",
    options = { version = "2.1.0" } },

  -- Standalone entry, spec from git. A git source requires a commit sha.
  { spec = "acme.jlink@r1", source = "https://github.com/acme/envy-specs.git",
    ref = "7bc9a0bfe050ef97e1712ff61c6f11952799e951",
    options = { version = "9.30" },
    -- Host state, opted into per project: install udev rules on Linux, but
    -- never on a CI runner nobody owns.
    setup = not ci and { "udev_rules" } or nil },

  -- Linux-only entry driving the host package manager. Nothing is cached; the
  -- SETUP pair adjusts the machine (see User-Managed Packages).
  { spec = "acme.apt@r0", source = specs .. "acme.apt.lua",
    platforms = { "linux" },
    options = { packages = { "libudev-dev", "libusb-1.0-0-dev" } },
    setup = { "packages" } },
}

-- Extra packages only CI needs. `envy.extend` appends to the list above.
if ci then
  envy.extend(PACKAGES, {
    { spec = "acme.coverage-tools@r0", source = specs .. "acme.coverage-tools.lua" },
  })
end
```

The file makes three decisions. The header selects the envy version. `BUNDLES`
and `PACKAGE_DEPOTS` say where things come from. `PACKAGES` says what the
project needs. Nothing else is implied. There is no global install and no
ambient state, and nothing is shared with the next project on the machine except
the [cache](./cache.md).

## Manifest discovery

Commands that need a manifest walk up from where they start: the current
directory, or the directory of the script passed to
[`envy run`](../reference/cli/run.md). At each level:

1. If `envy.lua` exists, envy reads its header. `@envy root "true"`, or no
   `root` directive, stops the walk. That manifest is the project.
2. `@envy root "false"` marks a component. envy remembers it and keeps climbing.
3. A `.git` directory stops the walk. If only `root = false` manifests were
   found, the one closest to the top wins.
4. Reaching the filesystem root ends the walk the same way.

A subproject checked out on its own therefore still works, because its manifest
is the only candidate. Checked out inside a superproject, the superproject's
manifest wins, and the component's packages arrive through composition instead
of a second project.

`--subproject` on `sync`, `deploy`, and `use` skips the walk and uses the
nearest `envy.lua`. `--manifest <path>` names one directly.

One rule keeps everything consistent. The shell hook, the bootstrap script in
the bin directory, and envy itself all resolve the same manifest from the same
directory. The `PATH` you get therefore belongs to the project envy is about to
act on.

## Superprojects and subprojects

A superproject is one root manifest that imports its components' package lists
instead of letting each component form its own project.

```lua title="libs/firmware-common/envy.lua"
-- @envy schema "1"
-- @envy version "0.2.0"
-- @envy bin "bin"
-- @envy deploy "true"
-- @envy root "false"          -- a component, not a project boundary

local specs = envy.abspath("envy") .. "/"

BUNDLES = { envy = { identity = "envy.package-specs@r3",
                     source = "https://github.com/envy-package-manager/package-specs.git",
                     ref = "ded36a39bbf13744f5a0e539f2f4741fecb61dd0" } }

PACKAGES = {
  { spec = "envy.cmake@r0", bundle = "envy", options = { version = "4.4.0" } },
  { spec = "acme.armgcc@r1", source = specs .. "acme.armgcc.lua",
    options = { version = "15.2.rel1" } },
}
```

```lua title="envy.lua (the superproject root)"
-- @envy schema "1"
-- @envy version "0.2.0"
-- @envy bin "bin"
-- @envy deploy "true"
-- @envy root "true"

local fwc = envy.loadenv("libs.firmware-common.envy")

BUNDLES = fwc.BUNDLES
PACKAGES = fwc.PACKAGES

-- Same toolchain as the component, plus one thing only the top level needs.
envy.extend(PACKAGES, {
  { spec = "acme.releasetool@r0", source = envy.abspath("envy/acme.releasetool.lua") },
})
```

The component's `envy.lua` works both as a manifest on its own and as a module
the root imports. `envy.abspath` anchors its spec paths to its own directory in
either case. From inside `libs/firmware-common`, `envy sync` syncs the whole
superproject, and `envy sync --subproject` syncs only that component into only
its bin directory.

## One manifest, three platforms

A manifest is meant to be byte-identical on macOS, Linux, and Windows. Nothing in
it is per-platform except where you say so:

| Concern | Where it belongs |
| --- | --- |
| A package only some platforms need | `platforms = { "windows" }` on the entry, or `PLATFORMS` in the spec |
| Packages kept inside the project rather than the user-wide cache | `@envy cache-local` |
| A different interpreter for string verbs | [`DEFAULT_SHELL`](./shells.md), usually a function that branches on `envy.PLATFORM` |
| A per-platform download URL or hash | inside the spec's `FETCH`, keyed on `envy.PLATFORM_ARCH` |

The bin directory is the one place both platforms appear side by side. It holds
`envy` and `envy.bat`, plus a POSIX and a `.bat` wrapper per product, and all of
it is committed:

```text
bin/
├── envy          bash bootstrap
├── envy.bat      batch bootstrap
├── cmake
├── cmake.bat
├── ninja
└── ninja.bat
```

Both bootstrap scripts parse the `@envy` header themselves, in bash and in batch,
using the same rules as envy. Both walk up the directory tree for the root
manifest, and both honor `ENVY_CACHE_ROOT` and `ENVY_MIRROR`. A Windows developer
cloning the repo runs `bin\envy.bat` and gets the same pinned envy from
`%LOCALAPPDATA%\envy`.

Write both flavors from whatever machine you have with
`envy sync --platform all`. See
[Product Scripts](./environment/product-scripts.md#the-windows-twin).

One Lua detail: `envy.abspath` returns a native path, so it produces backslashes
on Windows. Pass its result around, and use
[`envy.path.join`](../reference/lua-api.md#paths) to extend it, rather than
concatenating `"/"` yourself.

## See also

- [Manifest Reference](../reference/manifest.md) for the same tables, terser.
- [Anatomy of a Spec](./specs/index.md) for what a `spec` field points at.
- [Bundles](./dependencies/bundles.md) for one pin covering many specs.
- [Monorepos & Subprojects](../guides/monorepos.md) for the superproject workflow.
- [Starting a Project](../guides/new-project.md) for how this file gets written.
