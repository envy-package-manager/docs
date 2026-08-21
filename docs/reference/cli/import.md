---
sidebar_position: 17
title: envy import
---

# `envy import`

Put exported package archives into the cache by hand. During a normal
[`sync`](./sync.md) a configured depot does this automatically. `import` is the
manual path, for sneakernet transfers, pre-seeding a build machine, air-gapped
networks, and checking that an artifact you published is usable.

## Usage

```
envy import <archive.tar.zst>
envy import <index.txt> [--manifest=<path>]
envy import --dir <dir> [--checksums=<file>] [--manifest=<path>]
```

## Arguments and flags

| Argument or flag | Meaning |
| --- | --- |
| `archive` | A single `.tar.zst` package archive, or a `.txt` depot index. Mutually exclusive with `--dir`, and one of the two is required. |
| `--dir <dir>` | Treat a directory of `.tar.zst` archives as a depot. |
| `--checksums <file>` | Attach expected hashes to the directory's archives, by filename, from an index file. |
| `--manifest <path>` | Use this manifest instead of [discovery](/concepts/projects#manifest-discovery). |

## Three modes

**A single archive** needs no manifest and no project. The
`<identity>-<platform>-<arch>-blake3-<hash>.tar.zst` filename tells envy where
the bytes belong. It unpacks them into that cache entry, marks it complete, and
prints the resulting package path to stdout. An archive of a non-`EXPORTABLE` spec
restores its `fetch/` tree instead and prints `fetch-only import: <path>`. A
cache entry that already exists is left alone and reported as `cached`.

**An index file or a directory** is treated as a depot for one run. envy builds
an index from it, then installs the manifest's packages through it. Both modes
therefore perform a full `install`. Packages whose artifacts match are satisfied
locally, and the rest build from source.

Hash verification follows the index. A `.txt` index always carries a sha256 per
entry, so those imports are always verified. `--dir` alone carries none, and
`--dir --checksums` restores them. A mismatch is a warning rather than a failure.
envy declines the artifact and builds that package normally, so a corrupt
archive costs time rather than correctness. A single-archive import is
unverified, because its filename is the only claim made about it.

## Examples

### To load one artifact into the cache

```bash
./bin/envy import exports/envy.cmake@r0-darwin-arm64-blake3-49a9b2620de8c380.tar.zst
# /Users/you/Library/Caches/envy/packages/envy.cmake@r0/darwin-arm64-blake3-49a9b2620de8c380/pkg
```

No manifest is consulted, so this works on a machine with no envy project at all.
Use it to pre-warm a shared cache or a container image.

### To install a whole project from a USB stick

```bash
./bin/envy import --dir /media/usb/envy-artifacts
```

Every archive on the stick becomes an available depot entry, and the manifest's
packages install from it. Anything not on the stick falls back to a normal build,
so a partial artifact set still produces a working project.

### To check artifacts as they are imported

```bash
./bin/envy import --dir ./exports --checksums exports/packages.txt
```

`--checksums` supplies the expected sha256 per filename, so an archive corrupted
in transit is rejected and rebuilt from source with a warning instead of landing
in the cache. Use it for anything that travelled by USB stick.

### To install from a published index without configuring a depot

```bash
curl -O https://packages.acme.example/envy/packages.txt
./bin/envy import packages.txt
```

A one-off equivalent of adding the depot to `PACKAGE_DEPOTS`, useful for testing
a depot before committing it to the manifest.

### To confirm an export round-trips

```bash
ENVY_IGNORE_DEPOT=1 ./bin/envy export -o /tmp/x
rm -rf "$(envy cache | head -1 | cut -d' ' -f2)/packages"
./bin/envy import --dir /tmp/x
```

Clear, import, and confirm nothing rebuilds from source. Run this before pointing
a team at a new depot.

## See also

- [Package Depots](/concepts/depots) for how a configured depot does this automatically.
- [`envy export`](./export.md) for the producer end.
- [Running a Package Depot](/guides/package-depots)
