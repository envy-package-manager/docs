---
sidebar_position: 5
title: Monorepos & Subprojects
---

# Monorepos & Subprojects

One repo with several subprojects, or one repo that vendors another. Both are the
same mechanism: nested manifests, one of which is the root.

## The two roles

| Directive | Meaning |
| --- | --- |
| `@envy root "true"`, or the directive absent | This manifest is a project boundary. Discovery stops here. |
| `@envy root "false"` | This is a subproject. Discovery walks past it, looking for a root above. |

[Discovery](/concepts/projects#manifest-discovery) walks up from where you are,
takes the first root manifest it finds, and stops at a `.git` directory. A
subproject checked out on its own still works, because then it is the only
candidate.

## The layout

A shared subproject carries a real manifest, marked as not a root:

```lua title="libs/common/envy.lua"
-- @envy schema "1"
-- @envy version "0.7.0"
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

The root loads it as a subproject and adds what only the top level needs:

```lua title="envy.lua"
-- @envy schema "1"
-- @envy version "0.7.0"
-- @envy sha256sums "a17e9c4f...c93f"
-- @envy bin "bin"
-- @envy deploy "true"
-- @envy root "true"

local common = envy.subproject("libs/common")

PACKAGES = envy.extend(common.PACKAGES, {
  { spec = "acme.releasetool@r0", source = "envy/acme.releasetool.lua" },
})
```

[`envy.subproject`](../reference/lua-api.md#envysubprojectdir) runs
`libs/common/envy.lua` in a sandbox and returns its globals. Its argument is the
directory that holds the subproject's `envy.lua`. `envy.extend` appends to the
list you inherited. It needs **envy 0.7.0 or newer**.

## Paths and aliases follow the file that wrote them

A subproject's entry keeps resolving against the manifest that declared it:

- `source = "envy/acme.protoc.lua"` in the subproject means
  `libs/common/envy/acme.protoc.lua`, whether you sync it on its own or load it
  from the root.
- `bundle = "envy"` in the subproject resolves against its own `BUNDLES`. The
  root does not re-export it, and it can define its own `envy` alias pointing
  somewhere else.
- A custom fetch in the subproject is cached under the subproject's file, not the
  root's.
- A helper module the subproject loads, with `envy.loadenv` or
  `envy.loadenv_bundle`, reads the subproject's globals, `VENDOR_ROOT` included.

Inside the subproject's manifest, `envy.PROJECT_ROOT` is the subproject's own
directory and `envy.IS_SUBPROJECT` is `true`. Both values stay with the
subproject's code when it runs later. That covers functions the root calls,
modules the subproject loads, and its `source.fetch` and depot `FETCH`
functions. Run on its own, the subproject is the root, so `envy.PROJECT_ROOT` is
the same directory in both cases.

Specs, their phases, and `SETUP` see the superproject's root. `SETUP` verbs run
there too. The subproject supplies declarations, not a second project.

:::note[Why not `envy.loadenv`]

`envy.loadenv` returns a plain table with no tie to the file that wrote it. A
manifest composed that way resolves the subproject's relative `source` paths
against the root manifest, and its `bundle` aliases fail unless the root
re-exports `BUNDLES`. Both mistakes are silent: the manifest loads and builds the
wrong thing. Use `envy.loadenv` to split one project's manifest across files.

:::

## Specs the subproject does not declare

A subproject can keep specs it never declares itself, for a superproject to pin.
The table `envy.subproject` returns carries `PROJECT_ROOT`, the subproject's
directory. Use it to name those files from the root:

```lua title="envy.lua"
local common = envy.subproject("libs/common")

PACKAGES = envy.extend(common.PACKAGES, {
  { spec = "acme.armgcc@r1", source = common.PROJECT_ROOT .. "/envy/acme.armgcc.lua",
    options = { version = "15.2.rel1" } },
})
```

`PROJECT_ROOT` is not one of the subproject's globals, so copying the table with
`pairs` takes only what the subproject assigned. A subproject that assigns a
global named `PROJECT_ROOT` is an error.

A subproject can also offer a function that returns the entry. A relative
`source` in that entry resolves against the manifest whose `PACKAGES` it ends up
in, which here is the root. Build the path from `envy.PROJECT_ROOT` instead:

```lua title="libs/common/envy.lua"
function armgcc(options)
  return { spec = "acme.armgcc@r1",
           source = envy.PROJECT_ROOT .. "/envy/acme.armgcc.lua",
           options = options }
end
```

```lua title="envy.lua"
PACKAGES = envy.extend(common.PACKAGES, {
  common.armgcc({ version = "15.2.rel1" }),
})
```

## Working on a subproject

By default, commands anywhere in the tree act on the root:

```shell-session
$ cd libs/common
$ ./bin/envy sync          # syncs the whole superproject
```

`--subproject` stops discovery at the nearest manifest instead:

```shell-session
$ cd libs/common
$ envy sync --subproject   # syncs only this subproject, into its own bin dir
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
`--project ~/src/monorepo` names. To target the subproject itself from outside,
use `--manifest libs/common/envy.lua`. `--subproject` ignores `--project` by
design: "nearest to where I stand" is defined against your working directory,
not an anchor someone passed in.

This is also why running a subproject's committed `libs/common/bin/envy` from any
directory acts on that subproject's enclosing project. Those scripts inject
`--project` with their own directory. See
[Manifest discovery](/concepts/projects#where-the-walk-starts).

Either way the spec lives with the subproject, so there is one definition. Only
the version choice moves up.

## Standalone-only entries

A subproject sometimes needs a package that the superproject supplies another
way. Gate it on `envy.IS_SUBPROJECT`, which is `true` only when another manifest
loaded this one with `envy.subproject`:

```lua title="libs/common/envy.lua"
if not envy.IS_SUBPROJECT then
  envy.extend(PACKAGES, {
    { spec = "acme.armgcc@r1", source = "envy/acme.armgcc.lua",
      options = { version = "15.2.rel1" } },
  })
end
```

Syncing the subproject on its own takes that branch. So does `--subproject`,
which makes it the root. Loading it from the superproject does not, so the
superproject's own compiler pin applies.

## Each manifest pins its own envy

`@envy version` is per manifest, so a subproject and its superproject can name
different envy versions. Keep them equal in practice, and remember
[`envy use`](../reference/cli/use.md) edits one manifest at a time:

```bash
envy use 0.7.0
cd libs/common && envy use 0.7.0 --subproject
```

When the superproject loads the subproject, envy runs the version the root pins.
It checks the subproject's pin against it:

| Subproject `@envy version` | Result |
| --- | --- |
| Equal to the root pin, or absent | Nothing |
| Older than the root pin | Warning, and the run continues |
| Newer than the root pin | Error |

The check needs a pin on both sides. A root manifest with no `@envy version`
compares against nothing, so the subproject's pin is ignored.

Newer is an error because bootstrap already chose the binary from the root
header, so the request cannot be satisfied by the time the subproject loads.

## The bootstrap boundary

A subproject's manifest is a file the root reads. It is not a second project
envy joins, and its header does nothing:

| Directive in a subproject's manifest | Effect |
| --- | --- |
| `bin`, `deploy` | None. Products deploy into the root's bin directory. |
| `cache-local`, `cache-mode`, `state-dir` | None. One cache tree per run, from the root header. |
| `version`, `sha256sums`, `mirror` | None, beyond the version check above. The launchers read the root header only. |
| `root` | None. Discovery never sees the file. |

One run means one tree, one cache root, and one envy binary, all decided from the
root header before any Lua runs.

The header applies when you sync the subproject on its own. envy ignores it when
the superproject loads the subproject.

Because discovery never resolves a subproject's manifest, it produces no
`manifest_resolved` event. The record that it took part in a run is
`subproject_loaded`:

```shell-session
$ envy --trace=file:t.jsonl sync
$ grep subproject_loaded t.jsonl
{"seq":2,"ts":"2026-11-13T15:51:51.949Z","tid":0,"event":"subproject_loaded","path":"/src/app/libs/common/envy.lua","parent":"/src/app/envy.lua"}
```

See [Logging & Tracing](../reference/observability.md).

## Each manifest has its own bin directory

`@envy bin` is per manifest, so the subproject's wrappers land in
`libs/common/bin` when you sync it with `--subproject`, and the root's land in
`bin`. Both are committed. A subproject needs its own bin directory to be usable
standalone.

Each bin directory also needs its own Windows flavor. `--platform` applies to the
manifest being synced, not to the repo, so a cross-platform monorepo runs it per
manifest:

```bash
envy sync --platform all                                  # root
envy sync --subproject --platform all                     # from inside libs/common
```

Miss one and Windows developers get a working root and a subproject they cannot
bootstrap.

## Vendoring is per repo, not per subproject

[`VENDOR_ROOT`](/concepts/vendoring) is read from the root manifest only, like
`DEFAULT_SHELL`, and every destination is anchored on that manifest's directory.
A subproject that sets it is an error unless the root assigns the same value:

```lua title="envy.lua"
VENDOR_ROOT = common.VENDOR_ROOT
```

Destinations follow the same rule. `vendor = "third_party/nanocobs"` on a
subproject's entry is resolved against whichever manifest is the root of the run,
so it means `libs/common/third_party/nanocobs` when the subproject is synced
standalone and `third_party/nanocobs` when the superproject drives it. Unlike
`source` paths, a `vendor` path does not follow the file that wrote it.

The simple answer is to declare vendoring in the root manifest, where the paths
mean one thing. A subproject that has to vendor standalone as well can gate the
path on `envy.IS_SUBPROJECT`, the same way it gates a standalone-only entry.

## The root manifest picks the depots

A subproject can declare the [depot](/concepts/depots) it uses standalone. When a
superproject loads the subproject, envy ignores that depot. It does not fetch
the index or build the depot's `DEPENDS`.

To use the subproject's depot, assign it in the root manifest. To use it with the
root's own depot, merge the lists:

```lua title="envy.lua"
PACKAGE_DEPOTS = envy.extend({ "s3://acme-envy-packages/packages.txt" },
                             common.PACKAGE_DEPOTS)
```

Using a depot means trusting its prebuilt artifacts.

## See also

- [Manifest Discovery](/concepts/projects#manifest-discovery) for the exact walk.
- [`envy.subproject`](../reference/lua-api.md#envysubprojectdir) for the full signature.
- [Projects & Manifests](/concepts/projects) for the composition helpers.
- [`envy sync --subproject`](../reference/cli/sync.md)
