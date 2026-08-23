---
sidebar_position: 14
title: envy extract
---

# `envy extract`

Extract an archive the way a spec's [`STAGE`](/concepts/specs/stage) verb would:
everything libarchive reads, permissions and symlinks preserved, and the same
selective-extraction globs. Use it to look inside a vendor tarball before
writing a spec, and to test `only` patterns before committing them.

Formats come from libarchive, so the list is long: `tar`, `tar.gz`, `tar.xz`,
`tar.bz2`, `tar.zst`, `zip`, `7z`, `rar`, `iso`, and bare compressed streams.
envy detects the format from content rather than the filename.

## Usage

```
envy extract <archive> [<destination>] [--only=<path|glob>]...
```

## Arguments and flags

| Argument or flag | Meaning |
| --- | --- |
| `archive` | Archive to extract. Required, and it must exist. |
| `destination` | Output directory. Defaults to the current directory. Created if missing. |
| `--only <path\|glob>` | Extract just this archive-relative path or glob. Repeatable. Defaults to everything. |

`--only` keeps large archives cheap. Unselected entries are never decompressed to
disk. Pulling two binaries out of a 10 GB toolchain tarball costs one streaming
pass instead of 10 GB. A selector naming a directory takes its whole subtree.

Selector rules:

- An `--only` entry that matches nothing is an error, and so is a malformed
  pattern.
- Patterns are archive-relative: no leading `/`, no `..`. envy normalizes `\` to
  `/` and ignores a leading `./` and trailing slashes.
- `*` and `?` stay within one path component. `**` spans components and must
  occupy a component by itself, so `lib/**/include` is valid and `lib/**x` is
  not.
- `[a-z]` and `[!a-z]` are character classes. Write `[*]`, `[?]`, and `[[]` for
  literals. An unterminated `[` is an error.
- Matching is case-sensitive on every platform, including Windows.
- A selected hard link needs its target selected too.

## Examples

### To see what is inside a vendor archive

```bash
envy extract vendor-sdk-3.1.tar.xz /tmp/peek
find /tmp/peek -maxdepth 2
```

This is the first thing you need when writing a spec: the real top-level
directory name, which is what `STAGE`'s `strip` has to account for.

### To pull two tools out of a large toolchain tarball

```bash
envy extract clang+llvm-20.1.0.tar.xz out \
  --only 'clang+llvm-20.1.0/bin/clang-*' \
  --only 'clang+llvm-20.1.0/lib/**/include/*.h'
```

Seconds instead of minutes, and the disk cost is what you asked for rather than
what the vendor shipped.

### To test a spec's `only` list before committing it

```bash
envy extract sdk.zip /tmp/try --only 'sdk/bin' --only 'sdk/LICENSE'
```

`sdk/bin` is a directory, so its whole subtree comes along. If either selector is
wrong you get an error here, rather than a spec that stages nothing.

### To extract into the current directory

```bash
envy extract packages/envy.cmake@r0-darwin-arm64-blake3-49a9b2620de8c380.tar.zst
```

Omitting the destination means here, which is convenient for inspecting a depot
artifact from [`envy export`](./export.md).

### To unpack something envy just downloaded

```bash
envy fetch https://vendor.example/sdk-3.1.tar.zst /tmp/sdk.tar.zst
envy extract /tmp/sdk.tar.zst /tmp/sdk
```

## See also

- [STAGE](/concepts/specs/stage) for `strip`, `only`, and how staging feeds `BUILD`.
- [`envy fetch`](./fetch.md)
- [Writing a Spec](/guides/writing-a-spec)
