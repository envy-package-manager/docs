---
sidebar_position: 7
title: Running a Package Depot
---

# Running a Package Depot

A [depot](/concepts/depots) is a file host with archives on it and one index
file. There is no server to run. This page is the operational path: decide
whether you need one, stand one up by hand, automate it, verify hits, and keep
the storage from growing forever.

## Decide first

A depot only pays for itself where source builds or slow downloads hurt. Measure
before committing:

```bash
ENVY_CACHE_ROOT=/tmp/cold-cache ENVY_IGNORE_DEPOT=1 time envy sync
```

That is the worst case every new checkout and every CI runner pays. If it is
thirty seconds of prebuilt downloads, skip the depot. If it is ten minutes of
compiling, a depot turns it into a download.

There is a second reason that has nothing to do with speed. A depot is an
internal mirror, so upstream deleting a release stops being an outage. Some teams
run one for that alone.

## What you need

- Somewhere to put files. An S3 bucket, a static web server, or an artifact
  repository all work.
- A way to upload. envy reads `s3://` and `https://` natively, but it never
  publishes, so use the AWS CLI, `rclone`, `scp`, or whatever your host expects.
- A CI runner per platform you support. A runner can only build for itself.

## Stand one up by hand

Do it manually once. Automating a pipeline you have never run end to end is how
you end up debugging YAML instead of the depot.

### 1. Check what your specs will publish

| Spec | Archive contains | Consumer skips |
| --- | --- | --- |
| `EXPORTABLE = true` | the installed `pkg/` tree | download, build, and install |
| `EXPORTABLE` absent or false | the fetched `fetch/` bytes | the download only |
| [user-managed](/concepts/specs/user-managed) | nothing, they are skipped | nothing |

Source-built tools are where `EXPORTABLE = true` matters most. Add it to specs
you own, then bump their revision, because it changes what the cache entry
holds.

### 2. Export

```console
$ mkdir -p /tmp/depot
$ envy export -o /tmp/depot > /tmp/depot/packages.txt
[envy.doctest-cpp@r0] cache hit
[envy.ninja@r0] cache hit
[[envy.cmake@r0]] 2/8845 files 1.48MB/309.73MB: 0.5%
[envy.cmake@r0] cache hit
```

The archives land in the output directory and the index goes to stdout:

```console
$ cat /tmp/depot/packages.txt
864655da611af3c9048156db2ee6355d5e62907f5acdb1acac8e762370e8c019  /tmp/depot/envy.cmake@r0-darwin-arm64-blake3-49a9b2620de8c380.tar.zst
08a76597e21dc9f50033668d830d4ecb892f672de0d5d6d0277295463715bb16  /tmp/depot/envy.ninja@r0-darwin-arm64-blake3-846f6979e3402fea.tar.zst
6e6dac60fd224cc77a7b61ad4faf076177031feb338d4f7d8788413f860ace89  /tmp/depot/envy.doctest-cpp@r0-darwin-arm64-blake3-1a46f3b186252763.tar.zst
```

Each archive is named `<identity>-<platform>-<arch>-blake3-<hash>.tar.zst`, which
is the cache entry directory name with the identity in front. envy derives the
lookup key from that filename, so do not rename the files.

For a real depot, `--depot-prefix` rewrites the second column to the URL
consumers will see:

```bash
envy export -o envy-export --depot-prefix s3://acme-envy-packages/
```

The prefix is prepended literally, so keep the trailing slash.

### 3. Publish

```bash
aws s3 sync /tmp/depot/ s3://acme-envy-packages/
```

Whatever your host uses is fine. The only requirement is that the URLs in the
index resolve for consumers.

### 4. Point a consumer at it

```lua title="envy.lua"
PACKAGE_DEPOTS = { "s3://acme-envy-packages/packages.txt" }
```

Then prove it works from a cache that cannot possibly have the packages:

```console
$ ENVY_CACHE_ROOT=/tmp/verify-cache envy sync
[envy.doctest-cpp@r0] imported from depot (0.0s)
[envy.ninja@r0] imported from depot (0.0s)
[[envy.cmake@r0]] verifying SHA256....
[envy.cmake@r0] imported from depot (1.8s)
```

`imported from depot` is the hit. Every archive is verified against the sha256 in
the index before it is unpacked.

## Automate it

The nightly shape below is what a production depot pipeline looks like. Two jobs:
a matrix that exports, and one that merges and publishes.

```yaml title=".github/workflows/envy-package-depot.yml"
name: Envy Package Depot
on:
  schedule:
    - cron: "0 4 * * *"
  workflow_dispatch:

env:
  ENVY_CACHE_ROOT: ${{ github.workspace }}/.envy-cache
  ENVY_IGNORE_DEPOT: 1

jobs:
  export:
    name: export (${{ matrix.name }})
    timeout-minutes: 30
    runs-on: ${{ matrix.runner }}
    strategy:
      matrix:
        include:
          - { name: linux-x64,   runner: ubuntu-latest,   envy: ./bin/envy }
          - { name: linux-arm64, runner: ubuntu-24.04-arm, envy: ./bin/envy }
          - { name: mac-arm64,   runner: macos-latest,    envy: ./bin/envy }
    steps:
      - uses: actions/checkout@v6
      - name: Export
        run: |
          mkdir -p envy-export
          ${{ matrix.envy }} export -o envy-export \
            --depot-prefix s3://acme-envy-packages/ \
            > envy-export/${{ matrix.name }}-packages.txt
      - uses: actions/upload-artifact@v7
        with:
          name: envy-export-${{ matrix.name }}
          path: envy-export/

  publish:
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
          aws s3 cp s3://acme-envy-packages/packages.txt existing.txt || true
          aws s3 ls s3://acme-envy-packages/ > retain.txt
          EXISTING=""
          if [ -f existing.txt ]; then EXISTING="--existing existing.txt"; fi
          ./bin/envy merge-depot envy-export/*-packages.txt $EXISTING \
            --retain-s3-ls retain.txt \
            --retain-prefix s3://acme-envy-packages/ \
            > envy-export/packages.txt
      - name: Publish
        run: aws s3 sync envy-export/ s3://acme-envy-packages/ --exclude "*-packages.txt"
```

Why each piece is there:

- **`ENVY_IGNORE_DEPOT: 1` at the workflow level.** A publisher that reads its own
  depot republishes what it already has and never notices a spec that stopped
  building. This job exists to build from source.
- **Windows in the matrix, if you support it.** Use `bin\envy.bat` and a
  PowerShell redirect, since `>` in PowerShell writes UTF-16 by default:
  `... | Out-File -FilePath envy-export/win-x64-packages.txt -Encoding ascii`.
- **Per-platform index filenames.** Every runner writes its own, and the merge job
  globs them.
- **`|| true` on the existing index.** The first run has nothing to merge with.
- **`--exclude "*-packages.txt"` on the upload.** Publish the merged index and the
  archives, never the per-platform intermediates.

Nightly is a reasonable default. Trigger it on manifest changes instead if your
versions move rarely and you want hits the same day.

## Verify and debug

Four ways to answer "why did that not hit":

**Compare the key.** The cache entry directory name is the archive name:

```console
$ envy -q package cmake
/Users/you/Library/Caches/envy/packages/envy.cmake@r0/darwin-arm64-blake3-49a9b2620de8c380/pkg
```

So the depot needs `envy.cmake@r0-darwin-arm64-blake3-49a9b2620de8c380.tar.zst`.
Grep the index for that name. A different hash means the options, the spec
revision, or a weak dependency changed since the export.

**Read the trace.** Every lookup is recorded:

```console
$ envy --trace=file:trace.jsonl sync
$ grep depot_check trace.jsonl
{"seq":12,"ts":"...","tid":1,"event":"depot_check","spec":"local.demo@r1","sha":"4b80ccd91d719bdb","result":"miss"}
```

`result` is `hit`, `miss`, or `sha_mismatch`.

**Expect silence on a miss.** A miss just builds:

```console
$ ENVY_CACHE_ROOT=/tmp/c3 envy sync
[local.demo@r1] installed (0.0s)
```

**Expect a warning on a broken depot.** An unreachable index, a failed download,
or a hash mismatch all warn and fall back:

```console
$ envy sync
warning: depot: failed to fetch manifest https://depot.invalid/packages.txt: curl_easy_perform failed: Couldn't resolve host name
[local.demo@r1] installed (0.1s)
```

A depot can never break a build, only fail to accelerate it.

One thing that surprises people: with a warm cache, a misconfigured depot is
completely silent. The index is only fetched when something actually needs
installing.

## Keep storage bounded

Every version bump adds artifacts and nothing removes them. The index is the
place to enforce policy, and
[`envy merge-depot`](../reference/cli/merge-depot.md) does it with a retain list:

```bash
aws s3 ls s3://acme-envy-packages/ > retain.txt
envy merge-depot envy-export/*-packages.txt \
  --existing existing.txt \
  --retain-s3-ls retain.txt \
  --retain-prefix s3://acme-envy-packages/ \
  > packages.txt
```

The retain list is what the bucket actually holds. Any index entry whose object
is gone is dropped, so consumers never chase a 404. That inverts the usual
ordering: delete objects however you like, with a lifecycle rule or by hand, and
the next merge reconciles the index.

`--retain-prefix` exists because the two sides name things differently. `aws s3
ls` prints keys and the index holds full URLs.

Add `--strict` if you want a non-reproducible rebuild to fail the pipeline rather
than warn. The same artifact path with different bytes usually means a spec is
capturing a timestamp or a path.

## Access control

The index and the archives are fetched the same way, so they need the same
access:

- **Public read.** Simplest. Nothing to configure on the consumer side.
- **`s3://` with credentials.** envy has the AWS SDK compiled in and uses ambient
  credentials, so a normal profile or CI role works with no AWS CLI installed.
- **Behind a token or a registry API.** Use the `{ DEPENDS, FETCH }` form of
  `PACKAGE_DEPOTS`, which lets a depot entry install a CLI and fetch the index
  through it. See [Depots behind something envy cannot speak](/concepts/depots#depots-behind-something-envy-cannot-speak).

## See also

- [Package Depots](/concepts/depots) for the concepts and the exact-match rule.
- [`envy export`](../reference/cli/export.md), [`envy merge-depot`](../reference/cli/merge-depot.md), [`envy import`](../reference/cli/import.md).
- [GitHub Actions](./integrations/github-actions.md) for caching the cache instead, which is the cheaper first move.
