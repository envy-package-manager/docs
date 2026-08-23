---
sidebar_position: 4
title: STAGE
---

# STAGE

Turn fetched files into a working tree. That usually means unpacking an archive,
and the default already does it, so most specs never write this verb.

## The four shapes

| Shape | Meaning |
| --- | --- |
| omitted | Extract every archive in `fetch/`. |
| table | Extraction options: `{ strip = N, only = { ... } }`. |
| string | A shell script, run in the staging destination. |
| function `STAGE(fetch_dir, stage_dir, tmp_dir, opts)` | Full control: conditional extraction, per-platform handling, `envy.extract` and `envy.extract_all`. |

### omitted

```lua
FETCH = "https://vendor.example/tool-1.2.tar.gz"
-- no STAGE: the archive is extracted, and that is the package
```

If `fetch/` holds no files, staging does nothing. That happens with an
imperative `FETCH` that committed nothing, and with a git clone, which lands in
the staging tree already.

### table

```lua
STAGE = { strip = 1 }
```

Most release tarballs nest everything under one directory such as
`cmake-4.4.0-macos-universal/`. `strip = 1` removes it, so `bin/cmake` lands at
the top of the package.

```lua
STAGE = { strip = 1, only = { "bin/clang-format", "lib/**/include/*.h", "LICENSE*" } }
```

`only` extracts just what you name. Unselected entries are never written.
Pulling two binaries out of a 10 GB toolchain tarball costs one streaming pass
instead of 10 GB of disk.

| Field | Meaning |
| --- | --- |
| `strip` | Leading path components to remove. Must be 0 or greater. |
| `only` | Archive-relative paths or globs. Must list at least one entry if present. |

Glob rules:

- A selector that matches nothing is an error, and so is a malformed pattern.
- A selector naming a directory takes its whole subtree.
- `*` and `?` stay inside one path component. `**` spans components and must
  occupy a component by itself, so `lib/**/include` is valid and `lib/**x` is
  not.
- `[a-z]` and `[!a-z]` are character classes. Write `[*]`, `[?]`, and `[[]` for
  literals.
- Matching is case-sensitive on every platform, including Windows.
- Paths are archive-relative. No leading `/`, no `..`.

To test a selector list outside a spec, use
[`envy extract --only`](../../reference/cli/extract.md), which runs the same
code.

### string

```lua
STAGE = "unzip -q payload.zip && rm payload.zip"
```

The script runs in the staging destination. It replaces the default extraction
rather than following it, so if you write `STAGE`, unpacking is your job.

### function

```lua
-- The prebuilt archives carry a whole toolchain, but only the requested tools
-- are wanted. macOS builds from source, so it needs the full tree.
STAGE = function(fetch_dir, stage_dir, tmp_dir, opts)
  local only
  if envy.PLATFORM ~= "darwin" then
    only = {}
    for i, tool in ipairs(opts.tools) do
      only[i] = "bin/" .. tool .. envy.EXE_EXT
    end
  end
  envy.extract_all(fetch_dir, stage_dir, { strip = 1, only = only })
end
```

`envy.extract_all(src_dir, dest_dir, opts?)` extracts every archive in a
directory. `envy.extract(archive, dest_dir, opts?)` extracts one and returns the
file count. Both accept the same `{ strip, only }` options as the table form.

A function `STAGE` can also do nothing, which is how a spec says "this platform
needs no staging":

```lua
STAGE = function(fetch_dir, stage_dir, tmp_dir, opts)
  if envy.PLATFORM ~= "windows" then return end
  -- Windows ships an installer that has to be unpacked by a tool we also fetched
  envy.run('Start-Process -Wait -FilePath "' .. fetch_dir .. '7z2600-x64.exe" ' ..
           '-ArgumentList "/S","/D=' .. stage_dir .. '7z"')
end
```

## Where staging writes

The destination depends on whether anything downstream needs to inspect the
tree:

| Spec | Extraction goes to |
| --- | --- |
| No function verbs, so `STAGE` is a table or string and `BUILD`/`INSTALL` are strings or absent | `pkg/`, the final package, with no copy |
| `STAGE`, `BUILD`, or `INSTALL` is a function | `work/stage/`, scratch, discarded afterwards |

A download-and-unpack spec therefore never pays for a second copy of the tree. A
spec that assembles its package by hand gets a scratch area to work in. See
[The Package Lifecycle](./lifecycle.md#where-extraction-lands).

## Archive formats

Everything libarchive reads: `tar`, `tar.gz`, `tar.xz`, `tar.bz2`, `tar.zst`,
`zip`, `7z`, `rar`, `iso`, and bare compressed streams. envy detects the format
from content rather than the filename. A `.tgz` that is really a zip still works.
Permissions, timestamps, and symlinks are preserved.

## See also

- [FETCH](./fetch.md) for where the bytes come from.
- [BUILD](./build.md) for what happens to the staged tree next.
- [`envy extract`](../../reference/cli/extract.md) for the same extractor from the CLI.
