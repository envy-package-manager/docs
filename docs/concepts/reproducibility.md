---
sidebar_position: 9
title: Reproducibility
---

# Reproducibility

How a clone of a repo becomes the same toolchain on every machine, and where the
edges are.

## There is no lockfile

envy does not solve version ranges, so there is nothing to lock. Every version is
already exact, and every pin lives in the manifest or in a spec that the manifest
pins. The manifest is the lockfile.

That removes a whole class of problems. There is no lockfile to conflict in a
merge, no "regenerate the lockfile" step, and no gap between what the lockfile
says and what the manifest asks for.

## The pin inventory

Four tiers, all visible in one file:

```lua title="envy.lua"
-- @envy schema "1"
-- @envy version "0.2.0"                                          -- 1
-- @envy sha256sums "a17e9c4fbb2d1e07c5a9f0d3e8b47c61f2a09d5e4c3b8a7f6e5d4c3b2a1908f7e"
-- @envy mirror "https://envy-mirror.acme.example"
-- @envy bin "bin"
-- @envy deploy "true"

BUNDLES = {
  envy = {
    identity = "envy.package-specs@r3",
    source = "https://github.com/envy-package-manager/package-specs.git",
    -- envy git-resolve https://github.com/envy-package-manager/package-specs main
    ref = "ded36a39bbf13744f5a0e539f2f4741fecb61dd0",                -- 2
  },
}

PACKAGES = {
  { spec = "envy.cmake@r0", bundle = "envy",
    options = { version = "4.4.0" } },                              -- 4

  { spec = "acme.protoc-gen-acme@r0",
    source = "https://specs.acme.example/protoc-gen-acme@r0.lua",
    sha256 = "9f2c1d5b8e47a03f6c2d9b1e4a7f0c3d8b5e2a9f4c1d7b0e3a6f9c2d5b8e1a4f", -- 2
    options = { version = "2.1.0" } },
}
```

1. **envy itself.** `@envy version` names the release, and `@envy sha256sums`
   attests it.
2. **Specs.** A `sha256` for a spec fetched over https, a full commit `ref` for
   git, and a bundle `ref` for a whole bundle of specs.
3. **Artifacts.** A `sha256` inside each spec's `FETCH`, usually from a
   fingerprint table keyed by version and platform. See
   [FETCH](./specs/fetch.md#sha256-and-caching).
4. **Tool versions.** `options`, which are part of the package's identity, so
   changing one names a different package rather than mutating an existing one.

Use [`envy git-resolve`](../reference/cli/git-resolve.md) to turn a branch or tag
into the sha you pin, and leave the command in a comment so the next person knows
how to advance it.

## envy verifies itself

The committed bootstrap script is plain shell and batch, and it does the
verification before running anything:

1. It reads `@envy version` and `@envy sha256sums` out of the manifest header as
   text.
2. It downloads `<mirror>/v<version>/SHA256SUMS` and hashes that file. A mismatch
   against the pin aborts.
3. It looks up the platform archive's entry inside that now-trusted `SHA256SUMS`,
   downloads the archive, and verifies it too.

One pin therefore covers all six platform archives, so a single
`@envy sha256sums` value works in a cross-platform repo. It also means a
mirror cannot tamper undetected: republishing requires producing a `SHA256SUMS`
whose hash matches a value already committed to your git history.

Two details that keep this from degrading quietly. `@envy sha256sums` without
`@envy version` is rejected, by envy and by the bootstrap script, because a pin
that names one release is meaningless when the version is resolved dynamically.
And if the pin is set but the machine has no `sha256sum`, `shasum`, or `openssl`,
bootstrap fails rather than skipping verification.

### What happens without a version pin

An unpinned project resolves a version at run time, in this order: a `latest`
marker in the local cache, then a `latest` file at the mirror, then GitHub's
redirect for the newest release, then the fallback version stamped into the
script when `envy init` wrote it.

That is convenient and it is not reproducible. Pin the version for anything
shared.

### Mirrors

`@envy mirror` and `ENVY_MIRROR` redirect where releases come from.
[`envy mirror-envy`](../reference/cli/mirror-envy.md) populates one, copying
`SHA256SUMS` byte for byte so an existing pin keeps verifying.

Prefer the `https://` form of a bucket, for example
`https://acme-envy-mirror.s3.us-east-1.amazonaws.com`. envy itself speaks
`s3://` natively, but the bootstrap script is plain shell with no AWS SDK, so an
`s3://` mirror makes it require the AWS CLI on every machine that bootstraps.

## The same pins on every platform

One manifest covers all three platforms, and the pins are shared where they can
be:

| Pin | Scope |
| --- | --- |
| `@envy version` | all platforms. One release, one version number. |
| `@envy sha256sums` | all platforms. It pins the release's `SHA256SUMS` file, which lists every platform's archive, so one value verifies the macOS, Linux, and Windows binaries. |
| A spec's `sha256` | per artifact. A spec that downloads per-platform archives records one hash each. |
| A bundle `ref` | all platforms. Git commits are not platform-specific. |

So a Windows machine and a Linux machine reading the same manifest install the
same envy, the same specs, and the same tool versions. What differs is only the
artifact each spec picks for the host, and each of those is hashed.

Two things to keep in the checklist for a cross-platform repo:

- Commit the Windows bootstrap and wrappers, not just the POSIX ones. Run
  `envy sync --platform all` so both flavors exist even if nobody on the team
  uses Windows today.
- Cover each platform in CI. A spec's Windows branch is only proven by a Windows
  runner, and a per-platform hash table is only proven where it is used.

## Known limits

Stated plainly, because each one is a place where "reproducible" needs a
qualifier.

- **Verification is opt-in per artifact.** A `FETCH` with no `sha256` is a
  reproducibility hole, and a performance one: an unverified download is
  re-fetched on every attempt rather than trusted from cache.
- **Spec contents are not part of the cache key.** An entry is named by identity
  plus options, so editing a spec in place, changing its URL or its build, reuses
  the existing package. Bump the spec revision, `@r0` to `@r1`, when behavior
  changes. That is what revisions are for.
- **User-managed packages are as reproducible as the host.**
  [Those specs](./specs/user-managed.md) run `apt` or `brew` against a machine
  envy does not own. envy guarantees the ordering and the idempotence check, not
  the resulting version.
- **Depots guarantee equivalent inputs, not bit-identical rebuilds.** A depot hit
  means an artifact was built from the same identity, options, and platform. If
  you need to prove a build reproduces, run it with
  [`--ignore-depot`](../reference/cli/index.md#global-flags) and compare, and use
  [`merge-depot --strict`](../reference/cli/merge-depot.md) in publishing so a
  changed hash fails the pipeline instead of quietly winning.
- **`envy run` and shell hooks inherit your environment.** Package resolution is
  hermetic, but a build script that reads `CC` or `PATH` for something envy did
  not provide is not.

## A checklist for teams

- `@envy version` and `@envy sha256sums` in every manifest, including
  subproject manifests.
- Every git source pinned to a full commit sha, never a branch or tag.
- Every remote spec pinned with `sha256`.
- Every `FETCH` pinned with `sha256`, in a fingerprint table so adding a version
  is a reviewable diff.
- A nightly CI job that builds with `ENVY_IGNORE_DEPOT=1`, so a spec that stopped
  building from source is caught before someone needs it.
- Spec revisions bumped when behavior changes, not just when content does.

See [Pinning & Updating](../guides/pinning.md) for the workflow that moves these
pins on purpose.

## See also

- [`envy use`](../reference/cli/use.md) for retargeting the envy pin.
- [The Cache](./cache.md) for what the identity hash covers.
- [Package Depots](./depots.md) for the accelerator and its trade-off.
