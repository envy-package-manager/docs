---
sidebar_position: 3
title: FETCH
---

# FETCH

Get the bytes. `FETCH` says what to download, as data when data is enough and as
code when it is not. A spec with no `FETCH` is either
[user-managed](./user-managed.md) or an error.

Downloads land in the entry's `fetch/` directory. Several downloads in one
`FETCH` run concurrently.

## The four shapes

| Shape | Meaning |
| --- | --- |
| string | One URL. The filename comes from the URL. |
| table | One download `{ source, sha256?, ref?, dest?, post_data? }`, or an array of URLs and tables. |
| function `FETCH(tmp_dir, opts)` | Compute the download set and return it, or download imperatively with `envy.fetch` and return nothing. |
| omitted | Valid only for [user-managed](./user-managed.md) specs. |

### string

```lua
FETCH = "https://www.colm.net/files/ragel/ragel-6.10.tar.gz"
```

Enough for a tool with one platform-independent artifact. There is no hash, so
see [`sha256` and caching](#sha256-and-caching) below.

### table, one download

```lua
FETCH = {
  source = "https://github.com/Kitware/CMake/releases/download/v4.4.0/cmake-4.4.0-macos-universal.tar.gz",
  sha256 = "c2302d3e2c0dd2f4e0b1e0b3a0e2cd18a51a7c5e9f4d3b8a7f6e5d4c3b2a41b5b",
}
```

| Field | Meaning |
| --- | --- |
| `source` | Required. The URL. |
| `sha256` | Expected hash. Verified on download, and again before reusing a cached file. |
| `ref` | Commit sha, branch, or tag. Required for git sources. |
| `dest` | Override the filename. Must be a plain filename with no path separators and no `..`. |
| `post_data` | Body for a POST request. HTTP and HTTPS only. |

### table, several downloads

```lua
FETCH = {
  { source = "https://www.segger.com/downloads/jlink/JLink_Windows_V930_x86_64.exe",
    post_data = "accept_license_agreement=accepted" },
  { source = "https://github.com/ip7z/7zip/releases/download/26.00/7z2600-x64.exe" },
}
```

Two artifacts, because the installer needs an unpacker to open it. Both download
in parallel. Two entries resolving to the same filename is an error, which is
what `dest` is for.

### function that returns a download

The common case. `FETCH(tmp_dir, opts)` receives the validated options and
returns a string or table, which envy then fetches:

```lua
FETCH = function(tmp_dir, opts)
  local arch = (envy.ARCH == "arm64") and "aarch64" or envy.ARCH
  local ext = (envy.PLATFORM == "windows") and ".zip" or ".gz"
  return "https://github.com/tamasfe/taplo/releases/download/" ..
      opts.version .. "/taplo-" .. envy.PLATFORM .. "-" .. arch .. ext
end
```

With a fingerprint table, the same shape produces a verified download for every
platform and version the spec records:

```lua
local hashes  -- version -> platform key -> sha256, filled in at the bottom of the file

local function platform_key()
  return ({
    darwin = "macos-universal",
    linux = "linux-" .. ((envy.ARCH == "arm64") and "aarch64" or envy.ARCH),
    windows = "windows-x86_64",
  })[envy.PLATFORM]
end

OPTIONS = { version = { required = true } }

FETCH = function(tmp_dir, opts)
  local key = platform_key()
  local hash = hashes[opts.version] and hashes[opts.version][key]
  if not hash then
    error("no recorded hash for " .. opts.version .. " on " .. key)
  end
  return {
    source = "https://github.com/Kitware/CMake/releases/download/v" .. opts.version ..
        "/cmake-" .. opts.version .. "-" .. key .. ".tar.gz",
    sha256 = hash,
  }
end

hashes = {
  ["4.4.0"] = {
    ["macos-universal"] = "c2302d3e...41b5b",
    ["linux-x86_64"] = "8f1a90bd...7c3e2",
  },
}
```

Returning a table lets one branch handle a platform that needs two files:

```lua
FETCH = function(tmp_dir, opts)
  local jlink = { source = base .. jlink_filename(opts),
                  post_data = "accept_license_agreement=accepted" }
  if envy.PLATFORM == "windows" then
    return { jlink, { source = "https://github.com/ip7z/7zip/releases/download/26.00/7z2600-x64.exe" } }
  end
  return jlink
end
```

### function that fetches imperatively

Return nothing and do the work directly when the download can only be identified
by looking at something else. An index, a manifest, or an API response has to be
fetched first.

This is the two-step pattern, and the split is a security boundary.
`envy.fetch(source, { dest = <dir> })` downloads into `tmp_dir`, which is
scratch, and returns the filename it wrote. `envy.commit_fetch` moves files from
`tmp_dir` into the durable `fetch/` directory and verifies a `sha256` on the
way. Nothing becomes part of the package until it passes through
`commit_fetch`.

```lua
FETCH = function(tmp_dir, opts)
  -- Step 1: pull the index into scratch space.
  local index = envy.fetch("https://vendor.example/builds/index.txt", { dest = tmp_dir })

  -- Step 2: read it in tmp_dir and decide.
  local url, hash = pick_build(tmp_dir .. index, opts.channel)   -- your own parsing

  -- Step 3: fetch what it named, and commit that, verified.
  local artifact = envy.fetch(url, { dest = tmp_dir })
  envy.commit_fetch({ filename = artifact, sha256 = hash })
end
```

`envy.fetch` requires `dest`, a directory, and returns the basename it wrote, or
an array of basenames for an array of sources. `envy.commit_fetch` accepts
`"name"`, `{ "a", "b" }`, a single `{ filename, sha256 }` table, or an array of
them. `envy.verify_hash(path, hash)` checks a file without committing it.

Returning anything other than nil, a string, or a table is an error. A `FETCH`
that accidentally returns a number reports it rather than downloading nothing.

## `sha256` and caching

| Situation | Behavior |
| --- | --- |
| Hash given, file absent | Download, then verify. A mismatch fails the package. |
| Hash given, file present | Re-hash the file. On a match envy reuses it with no network access. On a mismatch envy deletes it and downloads again. |
| No hash, file present | Delete and download again, every time. |

So `sha256` is not only about integrity. It also makes a retry cheap. Pin hashes
on anything you fetch repeatedly.

This applies while an entry is incomplete. A completed package skips `FETCH`
entirely.

## git sources

```lua
FETCH = { source = "https://github.com/org/tool.git",
          ref = "7bc9a0bfe050ef97e1712ff61c6f11952799e951" }
```

A `ref` is required. Use
[`envy git-resolve`](../../reference/cli/git-resolve.md) to turn a tag or branch
into the sha you pin. Record the command in a comment so the next person can
advance it.

Two things differ from a file download. A clone lands in the staging tree rather
than `fetch/`. And a fetch containing a git source is not marked cacheable,
because a repository is a working tree rather than a verifiable artifact.

## Supported transports

`https`, `http`, `ftp`, `ftps`, `s3://bucket/key` using ambient AWS credentials,
`git://`, `git+ssh://`, `https://host/repo.git`, and local paths. To test one
outside a spec, use [`envy fetch`](../../reference/cli/fetch.md), which uses the
same code path.

## When a tool must exist before fetching

That is not a `FETCH` problem. It is a
[fetch dependency](../dependencies/fetch-dependencies.md), declared by the entry
that requests this spec, so `FETCH` never has to bootstrap its own downloader.

## See also

- [STAGE](./stage.md) for what happens to what you downloaded.
- [`envy fetch`](../../reference/cli/fetch.md) for the same transports from the CLI.
- [Reproducibility](../reproducibility.md) for why hashes live in specs rather than a lockfile.
