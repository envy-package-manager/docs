---
sidebar_position: 13
title: envy hash
---

# `envy hash`

Print `sha256sum`-style lines, `<hash>  <filename>`, to stdout. Use it to build
the fingerprint tables specs use to pin downloads, and to write the index files
a [package depot](/concepts/depots) serves.

`--tree` switches to a different question: one BLAKE3 digest for a whole
directory, which is what [vendoring](/concepts/vendoring) compares to decide
whether a copy is still current.

## Usage

```
envy hash <paths...> [--prefix=<url>]
envy hash --tree <dirs...> [--only=<pattern>]... [--threads=<n>] [--json] [--stats]
```

## Arguments and flags

| Argument or flag | Meaning |
| --- | --- |
| `paths` | Files and directories to hash. At least one is required. A missing path is an error. |
| `--prefix <url>` | Prepend this string to each filename, turning bare names into depot URLs. Excluded by `--tree`. |
| `--tree` | Hash each argument as a whole subtree with BLAKE3 instead of per file. Every argument has to be a directory. |
| `--only <pattern>` | Which entries the subtree digest covers. Repeatable, `--tree` only. |
| `--threads <n>` | Hashing threads. `0`, the default, means one per performance core. `--tree` only. |
| `--json` | Emit one JSON object per directory instead of a text line. `--tree` only. |
| `--stats` | Report where the time went and how evenly it was spread. `--tree` only. |

`--only`, `--threads`, `--json`, and `--stats` without `--tree` are an error
rather than silently ignored.

envy prints only the filename, never the path you passed. The output is meant to
be pasted into a spec or a depot index, where your working directory is
irrelevant. `--prefix` puts a real location back.

A directory argument contributes its `*.tar.zst` entries, non-recursively, which
is the shape [`envy export`](./export.md) writes. Other files in that directory
are ignored.

## Subtree hashing

Requires envy 0.4.0.

```shell-session
$ envy hash --tree third_party/nanocobs
b3a1f2c07d4e8915ab6c3f20e7d8149c5b0a2e6f3d19c847a25b0f6e3c81d492  third_party/nanocobs
```

Unlike per-file mode, `--tree` prints the path you passed. It folds one digest
over every selected entry: relative path, kind, the owner-execute bit, and either
the file's own BLAKE3 or a symlink's stored target. Directories count, so adding
or removing an empty one changes the answer. Symlinks are never followed, so the
digest does not depend on where the tree sits. Timestamps are not part of it, so
touching a file is not a change.

`--only` takes the same selector language as
[`envy extract --only`](./extract.md) and a spec's
[`VENDOR`](../spec-globals.md#vendor-selectors) list, `!` exclusions included. A
selection always carries the directories holding what it names, which is what
makes the digest of a selection equal the digest of a copy of that selection.
That equality is what vendoring rests on.

`--stats` prints to stderr, so stdout stays the digest line alone and still pipes
into a file or a diff. Under `--json` the same numbers ride inside the JSON
object instead. `-q` suppresses `--stats`, as it does every other informational
line.

## Examples

### To pin a download in a spec's fingerprint table

```bash
curl -LO https://github.com/Kitware/CMake/releases/download/v4.2.3/cmake-4.2.3-macos-universal.tar.gz
envy hash cmake-4.2.3-macos-universal.tar.gz
# c2302d3e...41b5b  cmake-4.2.3-macos-universal.tar.gz
```

```lua title="specs/cmake.lua"
hashes = {
  ["4.2.3"] = {
    ["macos-universal"] = "c2302d3e...41b5b",
  },
}
```

### To fingerprint every platform's archive in one pass

```bash
envy hash dist/*.tar.gz
```

One line per file, in the order given, which is easy to reshape into a
per-platform table.

### To build a depot index from an export directory

```bash
envy hash exports --prefix https://packages.acme.example/envy/ > packages.txt
```

`exports` is a directory, so only its `.tar.zst` archives are hashed, and
`--prefix` turns each name into the URL a consuming project fetches. The result
drops into a depot's `packages.txt`.

### To match `envy export`'s own index lines

```bash
envy hash exports --prefix s3://acme-envy-packages/
```

This is equivalent to what `export --depot-prefix` emits, which is why the two
are interchangeable when you re-hash a directory after moving files around.

### To verify a downloaded artifact against a published sum

```bash
envy hash cmake-4.2.3-macos-universal.tar.gz | diff - expected.txt
```

### To check whether a vendored tree still matches its package

```bash
envy hash --tree third_party/nanocobs
```

Run it before and after an `envy sync` that reported a package as re-vendored.
The digest that changed is the one whose directory somebody edited. See
[Vendoring](/concepts/vendoring#staying-in-sync).

### To see what a spec's `VENDOR` list would select

```bash
envy hash --tree "$(envy package local.nanocobs@r3)" \
  --only 'include/**' --only '!include/internal/**'
```

Same selectors, same code, so a digest matching the vendored copy's means the
list is the one that produced it.

### To find out where a big hash is spending its time

```shell-session
$ envy hash --tree --stats out/artifacts
9f2c...c481  out/artifacts
  threads 6  dirs 73  files 50001  bytes 204800038  wall 1136.4ms
  scan    132.9ms   2.0%   read   6472.3ms  96.3%
  hash    104.7ms   1.6%   wait      9.5ms   0.1%   fold      4.1ms
  files/worker 8301..8355 (ideal 8333)   bytes/worker 34000896..34222080 (ideal 34133339)
```

Stage times are summed across workers, so they exceed wall time on a parallel
run. The ratios are the useful part, and the per-worker spread says whether the
work divided evenly.

## On Windows

Output is the same `sha256sum` format. Redirecting it with PowerShell's `>` gives
UTF-16, which nothing downstream parses, so pipe it instead:

```powershell
bin\envy.bat hash *.tar.zst | Out-File -FilePath index.txt -Encoding ascii
```

## See also

- [Writing a Spec](/guides/writing-a-spec) for fingerprint tables in context.
- [Running a Package Depot](/guides/package-depots)
- [`envy export`](./export.md) and [`envy merge-depot`](./merge-depot.md)
- [Vendoring](/concepts/vendoring) for what `--tree` digests are compared against
