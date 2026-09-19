---
sidebar_position: 4
title: envy vendor
---

# `envy vendor`

Restore the [vendored](/concepts/vendoring) copies in the project tree. A
destination that is missing, edited, or left over from an older version of its
package is wiped and copied again from the cache. Requires envy 0.4.0.

[`sync`](./sync.md) and [`install`](./install.md) already do this as part of a
normal run, so most days you never type this command. It exists for the three
things they cannot do: repair one package without running anything else,
override a `vendor.auto_sync = false` exemption, and ask what has drifted
without changing it.

## Usage

```
envy vendor <queries>... [--force] [--dry-run] [--threads=<n>] [--manifest=<path>]
envy vendor --all        [--force] [--dry-run] [--threads=<n>] [--manifest=<path>]
```

## Arguments and flags

| Argument or flag | Meaning |
| --- | --- |
| `queries` | Which vendored packages to restore. See [query forms](./index.md#package-queries). |
| `--all` | Every package the manifest vendors. Mutually exclusive with `queries`. |
| `--force` | Repair a destination even where `vendor.auto_sync = false` exempts it. |
| `--dry-run` | Decide the same way, report it, and leave every vendored directory alone. |
| `--threads <n>` | Copy workers. `0`, the default, picks a count from the machine. Does not change what lands. |
| `--manifest <path>` | Use this manifest instead of [discovery](/concepts/projects#manifest-discovery). |

There is no `--subproject`, and there is no default selection. Say what to
restore or say `--all`. A bare `envy vendor` is an error, because the command
deletes directories and "everything" is not a safe thing to assume you meant.

## What it touches

Only what you named. A vendored *dependency* of a target is not swept along, and
keeps whatever it has.

The plan, though, is always resolved over the whole manifest. A destination
collision or a nesting anywhere in `PACKAGES` is still an error before a byte is
written, even when it involves a package you did not name. Restoring one package
can never land on top of another's directory.

Packages are run to completion, exactly as `install` would run them, with the
vendor step as the point. So naming a package that is not in the cache yet
fetches and installs it first. That is also true under `--dry-run`: the flag
holds off the vendored directory, not the rest of the run.

Naming a package with no `vendor` field is an error that says so. `--all` simply
skips those, since "every package that vendors" is what it means. A manifest that
vendors nothing at all is an error whichever way you ask.

## The report

One line per target, after the run, in the order you named them, or in manifest
order under `--all`:

```shell-session
$ envy vendor --all
[local.nanocobs@r3] re-vendored 41 files to /src/app/third_party/nanocobs: contents were dirty
[acme.armgcc@r1] up to date: /src/app/toolchains/armgcc
```

| Line | Meaning |
| --- | --- |
| `vendored N files to <dir>` | The destination was missing, so it was created. |
| `re-vendored N files to <dir>: contents were dirty` | It did not match the package, so it was wiped and copied again. |
| `up to date: <dir>` | It already matched. Nothing was touched. |
| `kept <dir>: contents differ from the package` | It did not match, and `auto_sync = false` said leave it. |
| `would vendor` / `would re-vendor` | `--dry-run`. The same decision, without the copy. |

Two queries that resolve to one package report it once. All of this goes to
stderr, so `envy vendor` writes nothing to stdout.

## Examples

### To put back a directory somebody deleted

```bash
envy vendor nanocobs
```

Also the fix for a directory a build system wrote into, a bad merge, or a
half-applied patch. The command does not care which of those happened, because
the answer is the same.

### To check a whole repo for drift without changing it

```bash
envy vendor --all --dry-run
```

Every destination is hashed and compared, and each one reports what a repair
would do and how many files it would write. Nothing under a vendored directory
is created, deleted, or modified. Worth running in CI on a repo that commits its
vendored trees, where a diff after a real `sync` would be a failing job rather
than a report.

### To discard deliberate edits to an exempt copy

```bash
envy vendor patched --force
```

`vendor = { auto_sync = false }` is how a project says "I edit this one, tell me
when it diverges, do not correct it". `--force` is how that project throws the
edits away when it is finished with them. It lifts the exemption and nothing
else: an already-matching destination is still left alone.

### To see the repair an exemption is holding back

```bash
envy vendor patched --force --dry-run
```

The two flags are independent. This reports the copy `--force` would make,
without making it.

### To restore one component of a monorepo

```bash
envy vendor --all --manifest libs/firmware/envy.lua
```

Vendor destinations are anchored on the root manifest, so which manifest the
command loads decides what the paths mean. See
[Vendoring is per repo](/guides/monorepos#vendoring-is-per-repo-not-per-component).

## See also

- [Vendoring](/concepts/vendoring) for the manifest fields and the drift check
- [`envy sync`](./sync.md) and [`envy install`](./install.md), which vendor as part of a normal run
- [`envy hash --tree`](./hash.md#subtree-hashing) for the digest the drift check compares
