---
sidebar_position: 8
title: envy use
---

# `envy use`

Retarget a manifest at a different envy version. `use` rewrites `@envy version`
and refreshes `@envy sha256sums` to match, in one step. Upgrades and downgrades
are the same operation.

Despite the name, this is not a shell-session switch. It is a durable edit to a
checked-in file, which is why it prints what it changed. It splices new
values into the existing header lines, so comments, indentation, and CRLF
survive.

`use` reads the manifest header as text. No Lua runs, and it does not re-exec
into the pinned version. That is what lets it repair the one state nothing else
can: a manifest naming a version whose checksum pin is stale, which therefore
cannot download its own binary.

## Usage

```
envy use <version> [--manifest=<path>] [--subproject] [--mirror=<url>]
         [--pin-sums | --no-pin-sums] [--force]
```

## Arguments and flags

| Argument or flag | Meaning |
| --- | --- |
| `version` | The envy version to target, for example `0.2.0`. Required. |
| `--manifest <path>` | Target this manifest instead of [discovery](/concepts/projects#manifest-discovery). |
| `--subproject` | Target the nearest manifest instead of walking to the project root. Mutually exclusive with `--manifest`. |
| `--mirror <url>` | Fetch `SHA256SUMS` from this mirror instead of the manifest's. Precedence otherwise: `ENVY_MIRROR`, then `@envy mirror`, then envy's GitHub releases. |
| `--pin-sums` | Add a `@envy sha256sums` pin even if the manifest had none. |
| `--no-pin-sums` | Drop the pin, leaving bootstrap downloads unverified. Mutually exclusive with `--pin-sums`. |
| `--force` | Skip the `SHA256SUMS` fetch that proves the release exists. Refused when a pin is in play, because the pin's value can only come from that file. |

Pinning follows the manifest by default. Pinned stays pinned, unpinned stays
unpinned, so gaining or losing verification is never a side effect of changing
versions.

The `SHA256SUMS` fetch happens even when there is no pin to write. That fetch is
the point: a typo'd or unmirrored version becomes an error here rather than a
failed bootstrap on someone else's machine. Network comes before file, so a
failed run leaves the manifest byte for byte unchanged.

A manifest with no `@envy version` is an error rather than a conversion. That
project floats to `latest` on purpose, and adding the directive is the author's
call.

`use` edits the manifest and nothing else. The bootstrap scripts and
`.luarc.json` are stamped from the running binary, so only the newly targeted
envy can restamp them. That happens on the next [`sync`](./sync.md), one re-exec
away. `use` prints the reminder.

## Examples

### To change the version of envy a project uses

```bash
envy use 0.2.0
# envy.lua: @envy version "0.1.9" -> "0.2.0"
# envy.lua: @envy sha256sums "3f9c..." -> "a17e..."
# run 'envy sync' to restamp the bootstrap scripts and .luarc.json for 0.2.0
envy sync
```

The `sync` is not optional bookkeeping. It re-execs into 0.2.0, which rewrites
`bin/envy`, `bin/envy.bat`, and the `.luarc.json` type paths. Commit the manifest
and the scripts together.

### To roll back after a bad upgrade

```bash
envy use 0.1.9 && envy sync
```

Identical mechanics. A downgrade is not a special case.

### To repair a stale or wrong checksum pin

```bash
envy use 0.1.9
# envy.lua: @envy sha256sums "0000..." -> "3f9c..."
```

Targeting the version already named refreshes only the pin. Because `use` never
re-execs, this works even when the pinned envy cannot be downloaded at all. That
is the failure mode that would otherwise leave a project stuck.

### To start verifying envy downloads

```bash
envy use 0.2.0 --pin-sums
```

This adds a `@envy sha256sums` line directly below `@envy version`. A directive
lower in the file is read by nothing. To stop verifying:

```bash
envy use 0.2.0 --no-pin-sums
```

which removes the line and its terminator, leaving no blank gap.

### To pin a version published only on a private mirror

```bash
envy use 0.2.0 --mirror s3://acme-envy-mirror
```

This reads `SHA256SUMS` from that mirror. The flag decides only where the
checksum comes from now. Where bootstrap downloads from is `@envy mirror` in the
manifest.

### To retarget one component of a superproject

```bash
cd libs/firmware && envy use 0.2.0 --subproject
# or, from anywhere:
envy use 0.2.0 --manifest libs/firmware/envy.lua
```

Each manifest that carries its own `@envy version` needs its own `use`.

### To target an internal build with no published SHA256SUMS

```bash
envy use 0.2.0-rc1 --no-pin-sums --force
```

`--force` skips the existence check. It is refused alongside a pin, because
there would be no file to compute the pin from.

## See also

- [Pinning & Updating](/guides/pinning) for the upgrade workflow.
- [Reproducibility](/concepts/reproducibility) for the envy trust chain.
- [`envy mirror-envy`](./mirror-envy.md) for publishing the release you are pinning.
