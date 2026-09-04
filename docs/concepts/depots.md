---
sidebar_position: 8
title: Package Depots
---

# Package Depots

envy is serverless until you decide otherwise. A depot is an optional store of
prebuilt packages, keyed by the same hashes the [cache](./cache.md) uses. With
one configured, an install that would have built a compiler downloads it
instead.

![A terminal session. The depot index is three lines of sha256 and URL, and envy
install reports each package as imported from depot rather than
built.](/screencasts/depot.svg)

Depots are an accelerator and never a requirement. With no depot configured
everything builds from source. With one configured but unreachable, envy warns
and builds from source. A depot cannot change what you get, only how long it
takes.

## Consuming a depot

One line in the manifest:

```lua title="envy.lua"
PACKAGE_DEPOTS = { "s3://acme-envy-packages/packages.txt" }
```

That is the whole consumer side. The next install checks the index before
building anything, and a hit is downloaded, verified against its recorded
sha256, and unpacked.

`https://` works the same way. envy has the AWS SDK compiled in, so an `s3://`
index uses your ambient credentials with no AWS CLI installed anywhere.

## What a depot actually is

Two things on any file host:

1. A flat index file, one line per artifact, in `sha256sum` format:

   ```text title="packages.txt"
   9f2c1d5b8e47a03f6c2d9b1e4a7f0c3d8b5e2a9f4c1d7b0e3a6f9c2d5b8e1a4f  s3://acme-envy-packages/envy.cmake@r0-darwin-arm64-blake3-49a9b2620de8c380.tar.zst
   5f2ac91d8b47a03f6c2d9b1e4a7f0c3d8b5e2a9f4c1d7b0e3a6f9c2d5b8e1a4f  s3://acme-envy-packages/envy.cmake@r0-linux-x86_64-blake3-8f1a90bd7c3e2114.tar.zst
   ```

2. The `.tar.zst` archives those URLs point at.

There is no depot server software, no API, and no registration. An S3 bucket, a
static web server, or a directory on a file share all qualify.

envy derives the lookup key from the archive filename, so the index needs no
schema beyond that naming. The platform and architecture are part of that name,
which is why one index serves every platform: a Windows machine looks for
`...-windows-x86_64-blake3-<hash>.tar.zst` and never sees the macOS entry. Lines it cannot parse are skipped with a warning, and
so is an index it cannot download, so an unreachable depot is a slowdown rather
than a failure.

## The exact-match rule

A hit requires the identity, the options, and the platform to match exactly,
because the key is the same content hash that names the cache entry. There is no
"close enough" and no version negotiation.

That cuts both ways. A depot can never hand you the wrong bits. And a depot miss
is not a bug: bump one option and you have named a package nobody has published
yet, so it builds locally.

## Which packages a depot can serve

| Spec | What ships |
| --- | --- |
| [`EXPORTABLE = true`](./specs/install.md#exportable) | The installed `pkg/` tree, so consumers skip the build entirely. |
| `EXPORTABLE` absent or false | The `fetch/` artifacts, so consumers skip the download but still run the install. |
| [User-managed](./specs/user-managed.md) | Nothing. There is no cache tree to publish. |

## Publishing

Three commands, and only the first two are envy's:

1. [`envy export`](../reference/cli/export.md) archives cache entries as
   `.tar.zst` and prints index lines for them. One run per platform, because a
   runner can only build for itself.

   ```bash
   envy export -o envy-export --depot-prefix s3://acme-envy-packages/ \
     > envy-export/linux-x64-packages.txt
   ```

2. [`envy merge-depot`](../reference/cli/merge-depot.md) combines the per-platform
   indexes with the one already published, and prunes entries whose objects are
   gone.

   ```bash
   envy merge-depot envy-export/*-packages.txt --existing existing.txt > packages.txt
   ```

3. Upload the archives and the merged index with whatever your host uses. envy
   reads a depot but never writes one.

Publish jobs should set `ENVY_IGNORE_DEPOT=1`. A publisher that reads its own
depot republishes what it already has and never notices a spec that stopped
building.

[Running a Package Depot](../guides/package-depots.md) has the full nightly
workflow, the retention policy, and how to debug a miss.

## Depots behind something envy cannot speak

An `https://` or `s3://` index needs no tooling. For an index behind a registry
API or a token-minting CLI, a depot entry can bootstrap its own access:

```lua title="envy.lua"
PACKAGE_DEPOTS = {
  { DEPENDS = { "tools.jfrog-cli@r1" },
    FETCH = function(ctx)
      local jf = envy.path.join(ctx.deps["tools.jfrog-cli@r1"].pkg_path, "bin", "jf")
      local index = envy.path.join(ctx.tmp_dir, "packages.txt")
      envy.run(jf .. " rt download --flat envy-packages/packages.txt " .. index)
      return index
    end },
}
```

`DEPENDS` names manifest packages that are installed from source before the index
is fetched. `FETCH(ctx)` receives `ctx.tmp_dir` and
`ctx.deps[identity].pkg_path`, and returns the index text, a path to it, or a
table of `{ url, sha256 }` entries. This is the depot-flavored sibling of
[fetch dependencies](./dependencies/fetch-dependencies.md).

## Opting out

`--ignore-depot` on any command, or `ENVY_IGNORE_DEPOT=1` in the environment,
skips the layer entirely and builds from source. Use it in publish jobs, in the
nightly that proves your specs still build, and when you suspect a bad artifact.

## See also

- [Running a Package Depot](../guides/package-depots.md) for the operational guide.
- [`envy export`](../reference/cli/export.md), [`envy merge-depot`](../reference/cli/merge-depot.md), and [`envy import`](../reference/cli/import.md).
- [The Cache](./cache.md) for the hash the depot is keyed on.
