---
sidebar_position: 16
title: envy export
---

# `envy export`

Install packages, then write each one to a `.tar.zst` archive and print its depot
index line, `<sha256>  <path-or-url>`, to stdout. This is the producer end of the
[package depot](/concepts/depots) loop, normally run by CI once per platform.

Export is fused into the install pipeline rather than being a separate pass. Each
package is archived and hashed as soon as its install finishes. A wide manifest
therefore exports concurrently instead of building everything and then
compressing everything.

## Usage

```
envy export [<queries>...] [-o <dir>] [--manifest=<path>]
            [--depot-prefix=<url>] [--ignore-depot]
```

## Arguments and flags

| Argument or flag | Meaning |
| --- | --- |
| `queries` | Which manifest entries to export. See [query forms](./index.md#package-queries). None means every entry available on this platform. |
| `-o`, `--output-dir <dir>` | Where archives are written. Defaults to the current directory. Created if missing. |
| `--manifest <path>` | Use this manifest instead of [discovery](/concepts/projects#manifest-discovery). |
| `--depot-prefix <url>` | Emit index lines with this prefix plus filename instead of the local path, which is the form a depot's index file needs. |
| `--ignore-depot` | Ignore the depot when installing, so packages build from source rather than being re-exported from someone else's artifacts. Publishers should always set this. Env: `ENVY_IGNORE_DEPOT`. |

## What gets exported

| Spec | Archive contents |
| --- | --- |
| [`EXPORTABLE = true`](/concepts/specs/install#exportable) | The installed `pkg/` tree, the built result. |
| `EXPORTABLE` absent or false | The `fetch/` tree, the downloaded artifacts, so consumers skip the download but still run the spec's install. |
| [User-managed](/concepts/specs/user-managed) | Nothing. Skipped silently, or with a `skipped non-cache-managed package ...` line if you named it explicitly. |

Archive names are `<identity>-<platform>-<arch>-blake3-<hash>.tar.zst`, the same
encoding [`envy import`](./import.md) parses back and [`envy hash`](./hash.md)
expects in a directory.

## Examples

### To publish a platform's artifacts from CI

```bash
ENVY_IGNORE_DEPOT=1 envy export -o exports \
  --depot-prefix s3://acme-envy-packages/ > exports/macos-packages.txt
aws s3 cp --recursive exports/ s3://acme-envy-packages/
```

One job per platform, each producing an archive set and an index file. The index
goes to stdout, so it redirects cleanly while progress stays on your terminal.
envy reads from S3 itself but does not upload, so publishing uses whatever
storage CLI you already have.

### To export one package you just fixed

```bash
envy export envy.cmake@r0 -o exports --depot-prefix s3://acme-envy-packages/
```

Dependencies install as needed, but only the queried entry is archived.

### To seed a machine that has no network

```bash
envy export -o /media/usb/envy-artifacts
```

With no `--depot-prefix`, index lines carry local paths, the form
[`envy import`](./import.md) expects on the other side.

### To check what an export would produce

```bash
envy export -o /tmp/exports | tee /tmp/index.txt
```

Every line is `sha256  path`, so a missing package is a missing line and `wc -l`
against your manifest is a cheap sanity check.

### To rebuild the index after moving archives

```bash
envy hash exports --prefix s3://acme-envy-packages/ > exports/packages.txt
```

`hash` on a directory produces the same lines from the archives themselves, with
no re-export.

## On Windows

`export` runs on the machine whose packages it is exporting, so a Windows depot
needs a Windows runner. Redirect through `Out-File`, because PowerShell's `>`
writes UTF-16 and [`merge-depot`](./merge-depot.md) will not parse it:

```powershell
bin\envy.bat export -o envy-export --depot-prefix s3://acme-envy-packages/ |
  Out-File -FilePath envy-export/win-x64-packages.txt -Encoding ascii
```

The archive names carry the platform, so a Windows export never collides with a
macOS one and both live in the same index.

## See also

- [Running a Package Depot](/guides/package-depots) for the full CI loop.
- [`envy merge-depot`](./merge-depot.md) for combining per-platform indexes.
- [`envy import`](./import.md) for the consumer end.
