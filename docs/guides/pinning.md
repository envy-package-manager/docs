---
sidebar_position: 4
title: Pinning & Updating
---

# Pinning & Updating

There is no lockfile. Every pin is a value in the manifest or in a spec, which
means updating anything is an edit somebody reviews.

This guide is the workflow. [Reproducibility](/concepts/reproducibility) is the
reasoning behind it.

## What to pin

| What | Where | Looks like |
| --- | --- | --- |
| envy itself | manifest header | `-- @envy version "0.2.0"` plus `-- @envy sha256sums "a17e..."` |
| A tool's version | package entry | `options = { version = "4.4.0" }` |
| A spec fetched over https | package entry | `sha256 = "9f2c..."` |
| A spec or bundle from git | package entry or `BUNDLES` | `ref = "ded36a39..."`, a full commit sha |
| A downloaded artifact | inside the spec's `FETCH` | `sha256 = versions.lookup(hashes, ...)` |

## Resolving a git ref

Never pin a branch or a tag. Resolve it to a sha at authoring time:

```console
$ envy git-resolve https://github.com/envy-package-manager/package-specs main
ded36a39bbf13744f5a0e539f2f4741fecb61dd0
```

Then record the command next to the pin, so the next person advances it the same
way:

```lua
BUNDLES = {
  envy = {
    identity = "envy.package-specs@r3",
    source = "https://github.com/envy-package-manager/package-specs.git",
    -- envy git-resolve https://github.com/envy-package-manager/package-specs main
    ref = "ded36a39bbf13744f5a0e539f2f4741fecb61dd0",
  },
}
```

`git-resolve` needs no clone and no `git` binary. A full sha passed in is echoed
back lowercased with no network access, so it is safe to call unconditionally in
a script.

## Updating a tool version

Edit the option and sync:

```diff
-  { spec = "envy.cmake@r0", bundle = "envy", options = { version = "4.4.0" } },
+  { spec = "envy.cmake@r0", bundle = "envy", options = { version = "4.5.0" } },
```

```console
$ envy sync
[envy.cmake@r0] installed (8.4s)
deploy: 3 product script(s) (0 created, 0 updated, 3 unchanged, 0 removed)
```

The old version is still in the cache under its own entry, so a revert is
instant. Nothing was overwritten, because the version is part of the identity.

If the spec keeps a fingerprint table, a version it has no hash for is rejected
before anything downloads, and the error lists the versions it does know. That is
usually the signal to update the spec, not the manifest.

## Updating a bundle

Advance the ref, and every spec from that bundle moves together:

```console
$ envy git-resolve https://github.com/envy-package-manager/package-specs main
c1a4f9f2c1d5b8e47a03f6c2d9b1e4a7f0c3d8b5e
```

That atomicity is the reason to prefer a bundle over ten spec URLs. It is also
the reason to read the bundle's changes before advancing: one ref moves every
spec you take from it.

## Updating envy

[`envy use`](../reference/cli/use.md) rewrites the version and refreshes the
checksum pin in one step:

```console
$ envy use 0.2.1
envy.lua: @envy version "0.2.0" -> "0.2.1"
envy.lua: @envy sha256sums "a17e9c4f..." -> "3f9c2d1b..."
run 'envy sync' to restamp the bootstrap scripts and .luarc.json for 0.2.1

$ envy sync
Updated bootstrap script
Updated .luarc.json types paths
```

The `sync` is not optional bookkeeping. The bootstrap scripts and `.luarc.json`
are stamped from the running binary, so only the newly pinned envy can restamp
them. Commit the manifest and the scripts together.

Downgrades are the same command. In a [superproject](./monorepos.md), run `use`
once per manifest that carries its own version.

## Repairing a stale pin

The one failure `use` exists for: a manifest naming a version whose checksum pin
is wrong. Nothing else can fix it, because everything else re-execs into the envy
that cannot be downloaded.

```console
$ envy use 0.2.0
envy.lua: @envy sha256sums "0000..." -> "a17e9c4f..."
```

`use` reads the header as text and never re-execs, so it works even when the
pinned envy is unreachable.

## Starting and stopping verification

```bash
envy use 0.2.0 --pin-sums      # add @envy sha256sums
envy use 0.2.0 --no-pin-sums   # remove it
```

Otherwise pinning follows the manifest: pinned stays pinned, unpinned stays
unpinned. Gaining or losing verification is never a side effect of changing
versions.

## Team discipline

- **One pin change per commit**, or at least per reviewable unit. "Bump cmake"
  and "bump the bundle" are different risks.
- **Let CI prove the source path still works.** A nightly job with
  `ENVY_IGNORE_DEPOT=1` catches a spec that only builds because someone published
  an artifact months ago.
- **Bump spec revisions when behavior changes.** A cache entry is named by
  identity plus options, not by spec contents, so editing a spec in place reuses
  the existing package. `@r0` to `@r1` is how you say "this is different now".
- **Prefer `--pin-sums` everywhere.** It is one line and it makes a mirror
  untrusted infrastructure rather than trusted infrastructure.

## See also

- [`envy use`](../reference/cli/use.md) and [`envy git-resolve`](../reference/cli/git-resolve.md).
- [Reproducibility](/concepts/reproducibility) for the trust chain and the honest limits.
- [Writing a Spec](./writing-a-spec.md) for fingerprint tables.
