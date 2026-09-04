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

## The layout

A shared component carries a real manifest, marked as a component:

```lua title="libs/common/envy.lua"
-- @envy schema "1"
-- @envy version "0.3.0"
-- @envy sha256sums "a17e9c4f...c93f"
-- @envy bin "bin"
-- @envy deploy "true"
-- @envy root "false"

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
  { spec = "acme.protoc@r0", source = "envy/acme.protoc.lua",
    options = { version = "33.5" } },
}
```

The root imports it and adds what only the top level needs:

```lua title="envy.lua"
-- @envy schema "1"
-- @envy version "0.3.0"
-- @envy sha256sums "a17e9c4f...c93f"
-- @envy bin "bin"
-- @envy deploy "true"
-- @envy root "true"

local common = envy.import("libs/common")

PACKAGES = envy.extend(common.PACKAGES, {
  { spec = "acme.releasetool@r0", source = "envy/acme.releasetool.lua" },
})
```

[`envy.import`](../reference/lua-api.md#envyimportpath) runs
`libs/common/envy.lua` in a sandbox and returns its globals. `envy.extend`
appends to the list you inherited. It needs **envy 0.3.0 or newer**.

## Paths and aliases follow the file that wrote them

An imported entry keeps resolving against the manifest that declared it:

- `source = "envy/acme.protoc.lua"` in the component means
  `libs/common/envy/acme.protoc.lua`, whether you sync the component on its own
  or import it from the root.
- `bundle = "envy"` in the component resolves against the component's own
  `BUNDLES`. The root does not re-export it, and it can define its own `envy`
  alias pointing somewhere else.

Everything else names the superproject: the project root, the `SETUP` working
directory, and custom-fetch cache keys. The component supplies declarations, not
a second project.

:::note[Upgrading from `envy.loadenv`]

Before 0.3.0, composing manifests meant `envy.loadenv`, which returns a plain
table with no such tie. Two things were needed to make it work, and both go away:

- Component spec paths had to be wrapped in `envy.abspath`, because a plain
  relative string would resolve against the root manifest. Now `"envy/x.lua"` is
  enough.
- The root had to re-export `BUNDLES = common.BUNDLES`, or every
  `bundle = "alias"` in the component failed to resolve. Now it does not.

Both traps were silent in the direction that matters: the manifest loaded and
built the wrong thing.

:::

## Working on a component

By default, commands anywhere in the tree act on the root:

```shell-session
$ cd libs/common
$ ./bin/envy sync          # syncs the whole superproject
```

`--subproject` stops discovery at the nearest manifest instead:

```shell-session
$ cd libs/common
$ envy sync --subproject   # syncs only this component, into its own bin dir
```

That is available on [`sync`](../reference/cli/sync.md),
[`deploy`](../reference/cli/deploy.md), and [`use`](../reference/cli/use.md).
`--manifest <path>` names one outright from anywhere.

The global `--project <dir>` starts the walk somewhere other than your current
directory, so you can act on the superproject from outside the tree without a
`cd`:

```shell-session
$ envy --project ~/src/monorepo/libs/common sync   # syncs the superproject
```

The walk still climbs to the root from there, so that is the same project
`--project ~/src/monorepo` names. To target the component itself from outside,
use `--manifest libs/common/envy.lua`. `--subproject` ignores `--project` by
design: "nearest to where I stand" is defined against your working directory,
not an anchor someone passed in.

This is also why running a component's committed `libs/common/bin/envy` from any
directory acts on that component's enclosing project. Those scripts inject
`--project` with their own directory. See
[Manifest discovery](/concepts/projects#where-the-walk-starts).

## Leaving a package out on purpose

The shared component can omit a package so each consumer pins its own.

```lua title="libs/common/envy.lua"
-- No compiler entry, on purpose. Each superproject pins the version it ships.
PACKAGES = {
  { spec = "envy.cmake@r0", bundle = "envy", options = { version = "4.4.0" } },
}
```

```lua title="envy.lua"
PACKAGES = envy.extend(common.PACKAGES, {
  { spec = "acme.armgcc@r1", source = "libs/common/envy/acme.armgcc.lua",
    options = { version = "15.2.rel1" } },
})
```

The spec still lives with the component, so there is one definition. Only the
version choice moves up. This entry is the root's own, so its `source` anchors on
the root manifest.

## Standalone-only entries

A component sometimes needs a package that the superproject supplies another way.
Gate it on `ENVY_IMPORTER`, which is set only when another manifest imported this
one:

```lua title="libs/common/envy.lua"
if not ENVY_IMPORTER then
  envy.extend(PACKAGES, {
    { spec = "acme.armgcc@r1", source = "envy/acme.armgcc.lua",
      options = { version = "15.2.rel1" } },
  })
end
```

Syncing the component on its own takes that branch. Importing it from the root
does not, so the root's own compiler pin stands. `ENVY_IMPORTER` holds the
absolute path of the importing manifest, and is `nil` otherwise.

Before 0.3.0 this needed an environment variable that CI had to set, which made
the component's package list depend on the caller's environment.

## Each manifest pins its own envy

`@envy version` is per manifest, so a component and its superproject can name
different envy versions. Keep them equal in practice, and remember
[`envy use`](../reference/cli/use.md) edits one manifest at a time:

```bash
envy use 0.3.0
cd libs/common && envy use 0.3.0 --subproject
```

Under `envy.import` the root pin is what runs, and envy checks the two against
each other:

| Imported `@envy version` | Result |
| --- | --- |
| Equal to the root pin, or absent | Nothing |
| Older than the root pin | Warning, and the run continues |
| Newer than the root pin | Error |

The check needs a pin on both sides. A root manifest with no `@envy version`
compares against nothing, so an imported pin is ignored.

Newer is an error because bootstrap already chose the binary from the root
header, so the request cannot be satisfied by the time the import runs.

## The bootstrap boundary

An imported manifest is a file the root reads. It is not a second project envy
joins, and its header does nothing:

| Directive in an imported manifest | Effect |
| --- | --- |
| `bin`, `deploy` | None. Products deploy into the root's bin directory. |
| `cache-local`, `cache-mode`, `state-dir` | None. One cache tree per run, from the root header. |
| `version`, `sha256sums`, `mirror` | None, beyond the version check above. The launchers read the root header only. |
| `root` | None. Discovery never sees the file. |

One run means one tree, one cache root, and one envy binary, all decided from the
root header before any Lua runs.

That header still matters when the component is synced on its own, which is the
point of a component carrying a full manifest rather than a fragment. Both roles
read the same file, and which directives apply is what changes.

Because discovery never resolves an imported manifest, it produces no
`manifest_resolved` event. The record that it took part in a run is
`manifest_imported`:

```shell-session
$ envy --trace=file:t.jsonl sync
$ grep manifest_imported t.jsonl
{"seq":2,"ts":"2026-09-04T00:33:52.167Z","tid":0,"event":"manifest_imported","path":"/src/app/libs/common/envy.lua","importer":"/src/app/envy.lua"}
```

See [Logging & Tracing](../reference/observability.md).

## Each manifest has its own bin directory

`@envy bin` is per manifest, so the component's wrappers land in
`libs/common/bin` when you sync it with `--subproject`, and the root's land in
`bin`. Both are committed. A component needs its own bin directory to be usable
standalone.

Each bin directory also needs its own Windows flavor. `--platform` applies to the
manifest being synced, not to the repo, so a cross-platform monorepo runs it per
manifest:

```bash
envy sync --platform all                                  # root
envy sync --subproject --platform all                     # from inside libs/common
```

Miss one and Windows developers get a working root and a component they cannot
bootstrap.

## See also

- [Manifest Discovery](/concepts/projects#manifest-discovery) for the exact walk.
- [`envy.import`](../reference/lua-api.md#envyimportpath) for the full signature.
- [Projects & Manifests](/concepts/projects) for the composition helpers.
- [`envy sync --subproject`](../reference/cli/sync.md)
