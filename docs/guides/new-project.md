---
sidebar_position: 1
title: Starting a Project
---

# Starting a Project

From an empty repo to a committed, self-bootstrapping toolchain. You need one
throwaway envy binary, once.

## Initialize

Download any envy release to a scratch location and run
[`envy init`](../reference/cli/init.md):

```console
$ /tmp/envy init . ./bin --deploy=true --pin-sums
Fetching SHA256SUMS for https://github.com/envy-package-manager/envy/releases/download/v0.2.0/SHA256SUMS
Created envy
Created ./envy.lua
Created ./.luarc.json
Initialized envy project.
Next steps:
  1. Edit ./envy.lua to add packages
  2. Run envy sync
```

Two positional arguments: where the manifest goes, and where the bin directory
goes. Then delete the scratch binary. It is never needed again, because
`bin/envy` will download the pinned version on demand.

The version `init` stamps is the version of the binary you ran. To pin a
different one, run [`envy use <version>`](../reference/cli/use.md) afterwards.

## Choosing init options

| Flag | When you want it |
| --- | --- |
| `--deploy=true` | Almost always. It enables [product wrappers](/concepts/environment/product-scripts), so `cmake` works. |
| `--pin-sums` | Anything shared. It stamps `@envy sha256sums`, so bootstrap verifies the envy binary it downloads. |
| `--platform all` | A repo with both POSIX and Windows developers. Writes `bin/envy` and `bin/envy.bat`. |
| `--mirror <url>` | A network that cannot reach GitHub releases. See [`envy mirror-envy`](../reference/cli/mirror-envy.md). |
| `--root=false` | A component manifest inside a larger tree. See [Monorepos](./monorepos.md). |

`--pin-sums` does its download before creating anything, so a typo or an
unpublished version fails with an untouched directory.

## What it wrote

```text
envy.lua        the manifest, header stamped from your flags
bin/envy        POSIX bootstrap script
bin/envy.bat    Windows bootstrap script, with --platform windows or all
.luarc.json     editor config for spec authoring
```

The manifest starts nearly empty:

```lua title="envy.lua"
-- envy.lua - Project manifest
-- @envy schema "1"
-- @envy version "0.2.0"
-- @envy sha256sums "a17e9c4f...c93f"
-- @envy bin "bin"
-- @envy deploy "true"
-- @envy root "true"

PACKAGES = {
}
```

See [Projects & Manifests](/concepts/projects) for what each directive means.

## Add the first package

Point at a bundle of published specs and take cmake from it:

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
  { spec = "envy.cmake@r0", bundle = "envy", options = { version = "4.4.0" } },
}
```

Then sync:

```console
$ envy sync
[envy.package-specs@r3] fetched (1.4s)
[envy.cmake@r0] installed (8.2s)
deploy: 3 product script(s) (3 created, 0 updated, 0 unchanged, 0 removed)
$ cmake --version
cmake version 4.4.0
```

The three wrappers are cmake, ctest, and cpack, because that is what the spec
declares as products.

## What to commit

Commit all of it:

```text
envy.lua
.luarc.json
bin/envy
bin/envy.bat
bin/cmake        the deployed wrappers
bin/ctest
bin/cpack
```

Committing the wrappers is the point. A colleague clones the repo and runs
`cmake` with nothing installed. See
[Product Scripts](/concepts/environment/product-scripts).

Worth adding to `.gitignore`:

```gitignore
# only if you point ENVY_CACHE_ROOT into the workspace, as CI often does
.envy-cache/
```

The cache lives outside the repo by default, so usually there is nothing to
ignore.

## Conventions worth adopting early

- **Record the resolve command next to every pinned ref.** The comment above
  `ref =` in the example is not decoration. It is how the next person advances
  the pin without guessing which command produced it.
- **Keep project-local specs in one directory**, named after their identity:
  `envy/local.mytool.lua`. Reference them with
  `source = envy.abspath("envy/local.mytool.lua")` so the path works from any
  working directory, and from a superproject that includes this manifest.
- **Turn on `--pin-sums` from the start.** Adding it later is one `envy use`
  away, but a repo that never had it tends never to get it.
- **Sync and commit the bin directory in the same commit as a manifest change.**
  A manifest that adds a product and a bin directory that lacks its wrapper are
  an inconsistent tree.

## Next

- [Adding Packages](./adding-packages.md) for the manifest cookbook.
- [Writing a Spec](./writing-a-spec.md) when no spec exists for the tool you need.
- [Pinning & Updating](./pinning.md) for moving the pins on purpose.
