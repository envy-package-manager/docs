---
sidebar_position: 8
title: Vendoring
---

# Vendoring

Copy a package's installed files out of the [cache](./cache.md) and into the
project tree, so a build system that can only read inputs from inside the project
can find them. Requires envy 0.4.0.

Most builds do not need this. Make and CMake take an absolute path to a header or
a library and never ask where it came from, so
[`envy product`](../reference/cli/product.md) is the whole integration. GN and
Bazel are the other kind: every input is a label relative to the workspace root,
`//third_party/nanocobs/include`, and a path in `~/Library/Caches/envy` has no
spelling in that language. Vendoring is the copy-in step that gives those builds
a path they can name.

It is a copy, not a move and not a link. The cache entry stays where it is and
stays authoritative. What lands in the project is a duplicate that envy keeps
matching the package it came from.

## Asking for it

Vendoring is requested by the manifest. A spec never decides that it should be
vendored, because whether a copy is wanted depends on the project's build system
rather than on the package.

```lua title="envy.lua"
VENDOR_ROOT = "third_party"

PACKAGES = {
  { spec = "local.nanocobs@r3", source = envy.abspath("envy/nanocobs.lua"),
    vendor = true },
}
```

That copies the package into `third_party/nanocobs/` under the manifest's
directory. [`envy sync`](../reference/cli/sync.md) and
[`envy install`](../reference/cli/install.md) do the copying as part of the
normal run, so nothing extra has to be typed to keep a vendored tree current.
[`envy vendor`](../reference/cli/vendor.md) runs the same step on its own, for
[repairing one package](#restoring-a-copy-on-demand) or asking what has drifted.

`VENDOR_ROOT` is read from the root manifest only, like `PACKAGE_DEPOTS` and
`DEFAULT_SHELL`. An [imported](./projects.md#superprojects-and-subprojects)
manifest that sets it has to be spliced into the root by hand, or the import is
an error.

Destinations follow the same rule. Unlike an entry's `source`, which anchors on
the file that wrote it, a `vendor` path is always relative to the root manifest's
directory. See
[Vendoring is per repo](../guides/monorepos.md#vendoring-is-per-repo-not-per-component).

## Where a package lands

| `vendor` value | Destination |
| --- | --- |
| absent, or `false` | nothing is copied |
| `true` | a derived name under `VENDOR_ROOT` |
| `"tools/armgcc"` | exactly that directory, relative to the root manifest |
| `{ path = "...", auto_sync = ... }` | the same two settings written out |
| `{}` | the same as `true` |

A derived name spells out only as much of the identity as it needs to stay
unique. `local.nanocobs@r3` becomes `nanocobs`, and only if a second package
would claim that name does either of them escalate:

```text
nanocobs  →  local.nanocobs  →  local.nanocobs@r3  →  local.nanocobs@r3-1f04c8e1a9b23d7c
```

The last step appends a hash of the options, which is what lets two option
variants of one spec both vendor. Escalation runs over the whole manifest and
repeats until nothing moves, because raising one colliding group can collide it
with another.

An explicit path is fixed and never escalates. It also needs no `VENDOR_ROOT`, so
a manifest that vendors one package to one named directory can skip the global
entirely. A derived name that wanted a directory an explicit path already claimed
steps aside.

Destination paths are validated the same way [`@envy cache-local`](./cache.md#where-the-root-lives)
is. They must be relative, with no leading separator, no drive letter, no `.` or
`..` component, and no `~`, `$` or `%`.

Only vendored entries take part in any of this. A package with no `vendor` key
never claims a name, and an entry whose
[`platforms`](./specs/platforms.md) filter excludes the current machine is
dropped before names are assigned, so a Linux-only and a macOS-only package may
name the same directory.

## What gets copied

By default, everything in the package's install directory. A spec narrows that
with `VENDOR`:

```lua title="nanocobs.lua"
VENDOR = { "include/**", "LICENSE", "!include/internal/**" }
```

This is the same selector language as
[`STAGE`'s `only`](./specs/stage.md) and
[`envy extract --only`](../reference/cli/extract.md), matched by the same code. A
leading `!` excludes, and an exclusion beats an inclusion. An empty or absent
list selects the whole install directory.

`VENDOR` is checked when the spec loads, so a malformed pattern fails before
anything is fetched or built.

This is the only thing a spec says about vendoring, and it is a statement about
the package rather than about any project. A toolchain's headers and license are
worth copying into a repo. Its debug symbols are not.

## Staying in sync

A vendored tree sits in the repo, where people edit it, merge it, and revert it.
envy checks it on every run rather than assuming it is still correct.

Each run hashes the destination directory whole and compares that digest against
the one the package recorded in its cache entry when it was installed. Equal
means the copy is exactly what the package holds. Anything else means it is not,
and envy deletes the destination and copies it again.

An edited file, a stray file, a deleted file, an added empty directory, a
repointed symlink, and a package whose version moved on are all the same fact:
this is not what the package holds. They all get the same repair. Touching a
file without changing its contents is not drift, because the digest covers
contents, names, the executable bit and symlink targets, and not timestamps.

The wipe is why nesting is refused. Two destinations where one contains the
other would mean the outer package's recopy deletes the inner one, so envy
rejects that manifest before it writes a single file. Duplicate destinations are
rejected the same way, and so is a destination that resolves outside the project
through a symlinked path component.

A destination that is itself a symlink to somewhere else in the project is not
refused, but it does not survive. The wipe removes the link and leaves whatever
it pointed at untouched, and the copy then creates a real directory in its place.
A vendored destination is a directory envy owns, so pointing one at a directory
you own is not a way to share them.

envy keeps no record of any of this on the project side. The vendored tree's own
contents are the record. So a vendored tree committed to git is adopted as-is on
a machine that has never run envy, provided its contents match the package. A
fresh clone is quiet rather than recopying everything.

A run that copies draws a progress bar on the package's row, counting files, and
its last line names what happened: `vendored 41 files to third_party/nanocobs`
for a first copy, or `re-vendored 41 files to ...: contents were dirty` for a
repair. Destinations are named relative to the project root. A package whose
copy already matched draws nothing, because nothing was copied.

That outcome is the whole row. It replaces what the payload did — `cache hit`,
or `installed (2.5s)` — rather than appearing alongside it, because vendoring is
the last phase to run and the payload verdict says nothing about what was
written into the project. The
[`pkg_outcome` trace event](../reference/observability.md) is unaffected and
still records `cache_hit` or `installed`, since a machine reader wants the
payload's verdict. Under [`envy vendor`](../reference/cli/vendor.md) the command
prints its own report, so the destination is not named twice.

## Keeping your own edits

A project that patches its vendored copy on purpose wants to be told it has
diverged, not corrected:

```lua
{ spec = "local.patched@r1", source = envy.abspath("envy/patched.lua"),
  vendor = { path = "third_party/patched", auto_sync = false } },
```

With `auto_sync = false`, a destination that no longer matches the package is
reported as a warning and left exactly as it is:

```text
warning: vendored copy at third_party/patched no longer matches the package; left as it is (vendor.auto_sync = false; 'envy vendor --force' restores it)
```

A missing destination is still copied, because there is nothing to preserve, and
a matching one is still quiet. The exemption applies to one entry and does not
affect its neighbours.

The exemption is a default, not a lock. When the edits have served their purpose,
[`envy vendor --force`](../reference/cli/vendor.md#to-discard-deliberate-edits-to-an-exempt-copy)
throws them away and copies the package back over them.

## Restoring a copy on demand

[`envy vendor`](../reference/cli/vendor.md) runs the vendor step by itself:

```bash
envy vendor nanocobs           # put this one back
envy vendor --all --dry-run    # what has drifted, without changing anything
envy vendor patched --force    # repair a destination auto_sync exempts
```

It decides exactly as a `sync` would, and repairs the same way. What it adds is
control over *which* packages and *whether*: name one package and its vendored
neighbours are left alone, `--force` overrides an exemption, and `--dry-run`
reports the decision while touching no vendored file.

Naming what to restore is required. A bare `envy vendor` is an error rather than
an implied `--all`, because the repair deletes directories.

## Committing the tree, or not

Both work, and the choice is about what the build needs rather than about envy.

Commit it when a consumer has to build without running envy first: a CI job that
only runs the build system, an IDE opening the tree cold, or a downstream
consumer that vendors your repo in turn. A committed tree is adopted rather than
recopied, so it does not churn.

Add it to `.gitignore` when everyone building the project runs `envy sync` first.
The tree is then a build artifact, one `sync` away from existing, and it stays
out of diffs.

A vendored tree is reproducible either way. The bytes come from the package, and
the package is pinned by the manifest.

## What envy will not do

- **Prune.** Changing a destination copies afresh into the new location and
  leaves the old directory alone. Delete it yourself.
- **Sweep up a dependency.** [`envy vendor`](../reference/cli/vendor.md) restores
  what you named and nothing else, so a vendored dependency of a target keeps
  whatever it has. `--all` is how you ask for every one of them.
- **Vendor a `USER_MANAGED` package.** Its state lives on the host, not in a
  cache entry, so there is no payload to copy. Asking is an error naming the
  package.
- **Vendor a bundled spec.** `vendor` belongs to the `source` entry shape. An
  entry that takes its spec from a `bundle` cannot carry the key, and says so.
- **Accept `vendor` in a spec.** It is a manifest `PACKAGES` key only. A
  `DEPENDENCIES` entry that carries it is an error.

## Checking a copy by hand

[`envy hash --tree`](../reference/cli/hash.md#subtree-hashing) prints the same
digest the vendor step compares, so a report that something drifted is
reproducible:

```shell-session
$ envy hash --tree third_party/nanocobs
b3a1f2c07d4e8915ab6c3f20e7d8149c5b0a2e6f3d19c847a25b0f6e3c81d492  third_party/nanocobs
```

`envy vendor --all --dry-run` answers the same question in envy's own terms, for
every vendored package at once, and names what a repair would cost.

For the machinery underneath, [`--trace`](../reference/observability.md) records
one `vendor_resolved` event per destination and one `vendor_result` per package,
carrying what envy did and why.

## See also

- [`envy vendor`](../reference/cli/vendor.md) for restoring a copy on demand
- [Manifest Reference](../reference/manifest.md) for `VENDOR_ROOT` and the `vendor` field
- [Spec Reference](../reference/spec-globals.md) for the `VENDOR` list
- [Build Systems](../guides/integrations/build-systems.md#builds-that-need-files-in-the-tree) for wiring it into GN and Bazel
- [The Cache](./cache.md) for where the original lives
