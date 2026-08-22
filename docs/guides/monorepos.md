---
sidebar_position: 5
title: Monorepos & Subprojects
---

# Monorepos & Subprojects

One repo with several components, or one repo that vendors another. Both are the
same mechanism: nested manifests, one of which is the root.

## The two roles

| Directive | Meaning |
| --- | --- |
| `@envy root "true"`, or the directive absent | This manifest is a project boundary. Discovery stops here. |
| `@envy root "false"` | This is a component. Discovery walks past it, looking for a root above. |

[Discovery](/concepts/projects#manifest-discovery) walks up from where you are,
takes the first root manifest it finds, and stops at a `.git` directory. A
component checked out on its own still works, because then it is the only
candidate.

## The shape that works

A shared component carries a real manifest, marked as a component:

```lua title="libs/common/envy.lua"
-- @envy schema "1"
-- @envy version "0.2.0"
-- @envy sha256sums "a17e9c4f...c93f"
-- @envy bin "bin"
-- @envy deploy "true"
-- @envy root "false"

local specs = envy.abspath("envy") .. "/"

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
  { spec = "acme.protoc@r0", source = specs .. "acme.protoc.lua",
    options = { version = "33.5" } },
}
```

The root imports it and adds what only the top level needs:

```lua title="envy.lua"
-- @envy schema "1"
-- @envy version "0.2.0"
-- @envy sha256sums "a17e9c4f...c93f"
-- @envy bin "bin"
-- @envy deploy "true"
-- @envy root "true"

local common = envy.loadenv("libs.common.envy")

BUNDLES = common.BUNDLES
PACKAGES = common.PACKAGES

envy.extend(PACKAGES, {
  { spec = "acme.releasetool@r0", source = envy.abspath("envy/acme.releasetool.lua") },
})
```

`envy.loadenv("libs.common.envy")` loads `libs/common/envy.lua` in a sandbox and
returns its globals. `envy.extend` appends to the list you inherited.

## Why `envy.abspath` matters here

The component's spec paths use `envy.abspath`, which resolves against the
directory of the file that calls it. That is what lets one file serve two roles:

- Run `envy sync` inside `libs/common` and it is a manifest, resolving
  `envy/acme.protoc.lua` inside `libs/common`.
- Import it from the root and it is a module, still resolving that same path.

A plain relative string would resolve against the working directory and break in
one of those two cases.

## Working on a component

By default, commands anywhere in the tree act on the root:

```console
$ cd libs/common
$ ../../bin/envy sync            # syncs the whole superproject
```

`--subproject` stops discovery at the nearest manifest instead:

```console
$ cd libs/common
$ ./bin/envy sync --subproject   # syncs only this component, into its own bin dir
```

That is available on [`sync`](../reference/cli/sync.md),
[`deploy`](../reference/cli/deploy.md), and [`use`](../reference/cli/use.md).
`--manifest <path>` names one outright from anywhere.

## The deliberate hole

A useful pattern: the shared component omits a package on purpose, so each
consumer pins its own.

```lua title="libs/common/envy.lua"
-- Deliberately no compiler entry. Each superproject pins the version it ships.
PACKAGES = {
  { spec = "envy.cmake@r0", bundle = "envy", options = { version = "4.4.0" } },
}
```

```lua title="envy.lua"
PACKAGES = common.PACKAGES

envy.extend(PACKAGES, {
  { spec = "acme.armgcc@r1", source = envy.abspath("libs/common/envy/acme.armgcc.lua"),
    options = { version = "15.2.rel1" } },
})
```

The spec still lives with the component, so there is one definition. Only the
version choice moves up.

## Standalone-only entries

A component sometimes needs a package that the superproject supplies another way.
Gate it on an environment variable rather than duplicating the manifest:

```lua title="libs/common/envy.lua"
if os.getenv("ACME_COMMON_STANDALONE") then
  envy.extend(PACKAGES, {
    { spec = "acme.armgcc@r1", source = specs .. "acme.armgcc.lua",
      options = { version = "15.2.rel1" } },
  })
end
```

CI for the component sets it, and the superproject does not.

## Each manifest pins its own envy

`@envy version` is per manifest, so a component and its superproject can name
different envy versions. Keep them equal in practice, and remember
[`envy use`](../reference/cli/use.md) edits one manifest at a time:

```bash
./bin/envy use 0.2.1
cd libs/common && ./bin/envy use 0.2.1 --subproject
```

A CI check that greps every `envy.lua` for the version is cheap and catches
drift.

## Each manifest has its own bin directory

`@envy bin` is per manifest, so the component's wrappers land in
`libs/common/bin` when you sync it with `--subproject`, and the root's land in
`bin`. Both are committed. A component's bin directory is what makes it usable
standalone.

## See also

- [Manifest Discovery](/concepts/projects#manifest-discovery) for the exact walk.
- [Projects & Manifests](/concepts/projects) for the composition helpers.
- [`envy sync --subproject`](../reference/cli/sync.md)
