---
sidebar_position: 13
title: envy fetch
---

# `envy fetch`

Download one resource the way a spec's [`FETCH`](/concepts/specs/fetch) verb
would: same transports, same TLS handling, same credentials, same progress bar.
Use it to prove a URL works before wiring it into a spec. A vendor CDN that
needs a redirect follow, or a wrong S3 prefix, shows up here rather than mid-sync.

## Usage

```
envy fetch <source> <destination> [--ref=<ref>] [--manifest-root=<path>]
```

## Arguments and flags

| Argument or flag | Meaning |
| --- | --- |
| `source` | The URI to fetch. Required. |
| `destination` | File path to write, or a directory path for a git clone. Required. `fetch` never guesses a filename. |
| `--ref <ref>` | Branch, tag, or commit sha. Required for git sources and meaningless for others. |
| `--manifest-root <path>` | Root that relative local-file sources resolve against. Defaults to the current directory. |

Supported transports, matching `FETCH`:

| Scheme | Notes |
| --- | --- |
| `https://`, `http://` | TLS verified against the system trust store. |
| `ftp://`, `ftps://` | |
| `s3://bucket/key` | Uses your ambient AWS credentials and region config. |
| `git://`, `git+ssh://`, `https://host/repo.git` | Clone at `--ref`. SSH keys come from your agent. |
| local paths | Absolute, or relative to `--manifest-root`. |

## Examples

### To check a release URL before pinning it in a spec

```bash
envy fetch https://github.com/Kitware/CMake/releases/download/v4.2.3/cmake-4.2.3-macos-universal.tar.gz \
  /tmp/cmake.tar.gz
envy hash /tmp/cmake.tar.gz
```

`fetch` then [`hash`](./hash.md) is the whole authoring loop for a fingerprint
table entry.

### To confirm a git source and ref resolve

```bash
envy fetch https://github.com/org/tool.git /tmp/tool --ref v1.5.23
```

Git sources require `--ref`, exactly as in a spec. A fetch without one is an
error rather than an implicit default branch. Combine with
[`git-resolve`](./git-resolve.md) to pin the sha you got.

### To verify an internal artifact store is reachable

```bash
envy fetch s3://acme-artifacts/toolchains/gcc-14.3.tar.zst /tmp/gcc.tar.zst
```

This uses the same AWS credential chain a real `FETCH` would. It is the fastest
way to tell a credentials problem from a spec problem.

### To test a local source the way a spec sees it

```bash
envy fetch vendor/blob.bin /tmp/blob.bin --manifest-root ~/work/firmware
```

Relative sources in a spec resolve against the manifest root rather than your
working directory. `--manifest-root` reproduces that, so a path that works here
works in the spec.

### To debug a download that hangs or returns 403

```bash
envy --verbose --trace fetch https://vendor.example/tool.tgz /tmp/tool.tgz
```

## On Windows

Local sources take either separator, so `envy fetch C:\vendor\tool.zip` and a
`file:///C:/vendor/tool.zip` URL both work, and so does a UNC path such as
`\\fileserver\share\tool.zip`. Transports are compiled in, so nothing here needs
`curl`, `git`, or `tar` on the machine.

## See also

- [FETCH](/concepts/specs/fetch) for the spec verb this mirrors.
- [`envy extract`](./extract.md) for the next step.
- [`envy hash`](./hash.md) for fingerprinting what you downloaded.
