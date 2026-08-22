---
sidebar_position: 12
title: envy hash
---

# `envy hash`

Print `sha256sum`-style lines, `<hash>  <filename>`, to stdout. Use it to build
the fingerprint tables specs use to pin downloads, and to write the index files
a [package depot](/concepts/depots) serves.

## Usage

```
envy hash <paths...> [--prefix=<url>]
```

## Arguments and flags

| Argument or flag | Meaning |
| --- | --- |
| `paths` | Files and directories to hash. At least one is required. A missing path is an error. |
| `--prefix <url>` | Prepend this string to each filename, turning bare names into depot URLs. |

envy prints only the filename, never the path you passed. The output is meant to
be pasted into a spec or a depot index, where your working directory is
irrelevant. `--prefix` puts a real location back.

A directory argument contributes its `*.tar.zst` entries, non-recursively, which
is the shape [`envy export`](./export.md) writes. Other files in that directory
are ignored.

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
