---
sidebar_position: 8
title: Package Depots
---

# Package Depots

envy is serverless until you decide otherwise. A depot is an optional store of
prebuilt packages, keyed by the same hashes the [cache](./cache.md) uses. With
one configured, a `sync` that would have built a compiler downloads it instead.

Depots are an accelerator and never a requirement. With no depot configured
everything builds from source. With one configured but unreachable, envy warns
and builds from source. A depot cannot change what you get, only how long it
takes.

## Consuming a depot

One line in the manifest:

```lua title="envy.lua"
PACKAGE_DEPOTS = { "s3://acme-envy-packages/packages.txt" }
```

That is the whole consumer side. The next `sync` checks the index before
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
schema beyond that naming. Lines it cannot parse are skipped with a warning, and
so is an index it cannot download, which is what makes an unreachable depot a
slowdown rather than a failure.

## The exact-match rule

A hit requires the identity, the options, and the platform to match exactly,
because the key is the same content hash that names the cache entry. There is no
"close enough" and no version negotiation.

That is worth internalizing in both directions. A depot can never hand you the
wrong bits. And a depot miss is not a bug: bump one option and you have named a
package nobody has published yet, so it builds locally.

## Which packages a depot can serve

| Spec | What ships |
| --- | --- |
| [`EXPORTABLE = true`](./specs/install.md#exportable) | The installed `pkg/` tree, so consumers skip the build entirely. |
| `EXPORTABLE` absent or false | The `fetch/` artifacts, so consumers skip the download but still run the install. |
| [User-managed](./specs/user-managed.md) | Nothing. There is no cache tree to publish. |

## Publishing

The producer side is three commands, and the shape is stable enough to copy.
This is a nightly workflow, trimmed from a production repo:

```yaml title=".github/workflows/envy-package-depot.yml"
on:
  schedule: [{ cron: "0 4 * * *" }]
  workflow_dispatch:

env:
  ENVY_CACHE_ROOT: ${{ github.workspace }}/.envy-cache
  ENVY_IGNORE_DEPOT: 1          # publishers must build from source

jobs:
  export:
    runs-on: ${{ matrix.runner }}
    strategy:
      matrix:
        include:
          - { name: linux-x64,   runner: ubuntu-latest,  envy: ./bin/envy }
          - { name: linux-arm64, runner: ubuntu-arm64,   envy: ./bin/envy }
          - { name: mac-arm64,   runner: macos-latest,   envy: ./bin/envy }
          - { name: win-x64,     runner: windows-latest, envy: bin\envy.bat }
    steps:
      - uses: actions/checkout@v6
      - name: Export
        run: |
          mkdir -p envy-export
          ${{ matrix.envy }} export -o envy-export \
            --depot-prefix s3://acme-envy-packages/ > envy-export/${{ matrix.name }}-packages.txt
      - uses: actions/upload-artifact@v7
        with:
          name: envy-export-${{ matrix.name }}
          path: envy-export/

  upload:
    needs: export
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v6
      - uses: actions/download-artifact@v8
        with:
          pattern: envy-export-*
          path: envy-export
          merge-multiple: true
      - uses: aws-actions/configure-aws-credentials@v6
        with:
          role-to-assume: arn:aws:iam::111122223333:role/AcmeDeploymentRole
          aws-region: us-east-1
      - name: Merge indexes
        run: |
          aws s3 cp s3://acme-envy-packages/packages.txt existing-packages.txt || true
          aws s3 ls s3://acme-envy-packages/ > retain.txt
          EXISTING=""
          if [ -f existing-packages.txt ]; then EXISTING="--existing existing-packages.txt"; fi
          ./bin/envy merge-depot envy-export/*-packages.txt $EXISTING \
            --retain-s3-ls retain.txt --retain-prefix s3://acme-envy-packages/ \
            > envy-export/packages.txt
      - name: Publish
        run: aws s3 sync envy-export/ s3://acme-envy-packages/ --exclude "*-packages.txt"
```

Five things in there are deliberate:

- **`ENVY_IGNORE_DEPOT: 1` at the workflow level.** A publisher that reads the
  depot would republish its own artifacts and never notice a spec that stopped
  building.
- **One export job per platform.** A runner can only build for itself, so the
  matrix is the coverage.
- **One merge job for all of them.** Each runner sees only its own artifacts, and
  [`envy merge-depot`](../reference/cli/merge-depot.md) combines them with what is
  already published.
- **`|| true` on the existing index.** The first run has nothing to merge with.
- **`--exclude "*-packages.txt"` on the upload.** Only the merged index and the
  archives get published, never the per-platform intermediates.

The `aws s3 ls` and `--retain-s3-ls` pair is the garbage collector. The retain
list is what the bucket actually holds, so an index entry whose object is gone is
pruned instead of sent to consumers as a 404.

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
