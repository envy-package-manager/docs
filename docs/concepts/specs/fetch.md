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
| table | One download `{ source, sha256?, ref?, submodules?, dest?, post_data? }`, or an array of URLs and tables. |
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
| `ref` | Required for git sources. A full commit sha, or a branch or tag name. See [git sources](#git-sources). |
| `submodules` | Git sources only. `true` for every submodule, or a list of path selectors. See [submodules](#submodules). Requires envy 0.5.0. |
| `dest` | Override the filename. Must be a plain filename with no path separators and no `..`. |
| `post_data` | Body for a POST request. HTTP and HTTPS only. |

From envy 0.5.0 any other key is an error that lists the accepted ones. Earlier
releases ignored it:

```text
error: local.grpc-src@r0: unknown key 'submodule'; allowed keys are dest, post_data, ref, sha256, source, submodules
```

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
FETCH = {
  source = "https://github.com/grpc/grpc.git",
  -- envy git-resolve https://github.com/grpc/grpc v1.85.1
  ref = "558b7e3b09e42e2160018732acbbf56c9094c84d",
}
```

A `ref` is required. Pin a full commit sha, and use
[`envy git-resolve`](../../reference/cli/git-resolve.md) to turn a tag or branch
into one. Record the command in a comment so the next person can advance it.

A branch or tag name also works, because envy looks it up in the remote's ref
list. It is not a pin, though, since the name can move. From envy 0.5.0 a short
sha or an expression such as `HEAD~1` is an error:

```text
error: Fetch failed for local.grpc-src@r0:
  https://github.com/grpc/grpc.git: git-resolve: ref not found: 558b7e3b09e4; a git ref must be a full commit sha or an advertised branch or tag (`envy git-resolve` pins one)
```

envy fetches only the pinned commit, with no history, when the server allows
it. A commit that a branch or tag points at comes shallow from any server. Any
other commit comes shallow from servers that accept a fetch by commit id, which
GitHub, GitLab, and googlesource do. Otherwise envy falls back to the full
history. A repository on a local path is always fetched in full.

The only tag that comes along is one that names the pinned commit. So
`git describe --tags` works on a tagged release and fails on other commits. A
spec that needs a version string should build it from its options.

Two things differ from a file download. The checkout lands in the stage
directory rather than `fetch/`, in a directory named after the URL's last
component (`grpc.git` here) unless `dest` renames it. The default `STAGE` and
`INSTALL` carry it into the package as is, `.git` included. And a fetch
containing a git source is not marked cacheable, because a repository is a
working tree rather than a verifiable artifact.

### Submodules

From envy 0.5.0, `submodules = true` checks out every submodule at the commit
its parent records, and their submodules in turn:

```lua
FETCH = {
  source = "https://github.com/grpc/grpc.git",
  -- envy git-resolve https://github.com/grpc/grpc v1.85.1
  ref = "558b7e3b09e42e2160018732acbbf56c9094c84d",
  submodules = true,
}
```

For gRPC v1.85.1 that is 39 submodules and about 150 MB of download. No extra
pin is needed. The parent's commit records each submodule's commit, and every
object is checked against its hash. One `ref` pins the whole tree.

To take only some of them, list selectors instead. A selector is a path from the
top of the parent repository, written in envy's selector language (see
[`STAGE`](./stage.md)). A leading `!` excludes:

```lua
FETCH = {
  source = "https://github.com/grpc/grpc.git",
  -- envy git-resolve https://github.com/grpc/grpc v1.85.1
  ref = "558b7e3b09e42e2160018732acbbf56c9094c84d",
  submodules = { "!third_party/bloaty", "!third_party/opentelemetry-cpp" },
}
```

That skips two submodules and the 19 nested inside them, which leaves 18
submodules and about 108 MB.

| Selector | Effect |
| --- | --- |
| `"!third_party/bloaty"` | Skip that submodule and everything nested in it. |
| `"third_party/protobuf"` | Take that submodule and everything nested in it. With any include present, unlisted submodules are skipped. |
| `"third_party/bloaty/third_party/re2"` | Take a nested submodule. envy also fetches each submodule on its path, because fetching one is the only way to learn what it holds. |

An include that matches nothing is an error, since it is almost always a typo.
An exclude that matches nothing is fine. `submodules = {}` is an error, so write
`true` to take them all. `false` is the same as leaving the key out.

The result has the layout `git clone --recurse-submodules` produces: each
submodule's git directory under `.git/modules/<name>`, and its URL in
`.git/config`. `git submodule status` reads clean. envy also follows git on
these points:

- A relative URL such as `../lib.git` resolves against the parent's URL.
- A submodule marked `update = none` in `.gitmodules` is skipped.
- The `branch` and `shallow` settings in `.gitmodules` are ignored. The commit
  the parent records is the one checked out.

A submodule with no URL in `.gitmodules` is an error. So is a submodule whose URL
is a local path when its parent came from a server.

Up to eight repositories download at once. Each one retries on its own after a
transport failure, so one dropped connection does not restart the tree. The
package row shows the parent's fetch first, then counts repositories across the
whole tree, with a row for each submodule in flight:

```text
[local.grpc-src@r0] 17/18 submodules 107.54MB grpc.git: 94.4%
  third_party/boringssl-with-bazel checkout 8153/8601 files: 94.8%
```

The total grows as nested submodules turn up, so the bar can move backward.

`submodules` in `FETCH` is part of the spec. A spec's contents are not part of
its packages' cache key, so an installed package keeps its old tree when you edit
the key. Bump the spec's revision, `@r0` to `@r1`, as for any change to what a
spec fetches. See [Reproducibility](../reproducibility.md#known-limits).

To check a repository's submodules before writing the spec, run
[`envy fetch --submodules`](../../reference/cli/fetch.md#to-check-a-repositorys-submodules-before-pinning-it).

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
