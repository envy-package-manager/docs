---
sidebar_position: 20
title: envy version
---

# `envy version`

Print envy's version, the path of the running binary, and the version of every
third-party library compiled into it. With `--licenses`, also print the full
license text of every bundled component, which is the canonical source for
compliance exports.

## Usage

```
envy version [--licenses]
```

Also reachable as `envy -v` and `envy --version`.

## Flags

| Flag | Meaning |
| --- | --- |
| `--licenses` | After the version report, print envy's license followed by every bundled third-party license. |

Streams split as they do elsewhere. The version report is human output on stderr,
and `--licenses` writes the license text to stdout. So
`envy version --licenses > LICENSES.txt` captures the licenses and nothing else.

`version` does not read a manifest and does not re-exec, so it reports the binary
you invoked. Running it through a project's bootstrap script reports the pinned
version, because the script downloads and runs that envy.

## Examples

### To check which envy a project is pinned to

```bash
./bin/envy version
# envy version 0.2.0 (/Users/you/Library/Caches/envy/envy/0.2.0/envy)
```

The path points into the cache, at the version the manifest pins, rather than at
whatever is on your `PATH`.

### To check the envy on your `PATH`

```bash
envy -v
```

Useful right before an [`envy init`](./init.md), because `init` stamps the running
binary's version into the new manifest.

### To report a bug

```bash
envy version 2>&1 | tee /tmp/envy-version.txt
```

The third-party component list, covering libgit2, libcurl, libarchive, Lua, zstd,
and the rest, is what turns "download failed" into a diagnosable report.

### To produce a compliance artifact

```bash
./bin/envy version --licenses > third-party-licenses.txt
```

Everything statically linked into the binary, in one file, generated from the
binary rather than from a hand-maintained list.

### To confirm a build has the transport you expect

```bash
envy version 2>&1 | grep -i curl
#   libcurl: 8.11.0 (zstd, brotli, zlib)
```

Windows builds report `HTTP: WinINet (system)` instead. They use the OS stack, so
there is no libcurl or mbedTLS line to find.

## See also

- [`envy use`](./use.md) for changing the pinned version.
- [Pinning & Updating](/guides/pinning)
- [Getting Help](/getting-started/getting-help)
