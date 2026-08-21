---
sidebar_position: 2
title: The Package Lifecycle
---

# The Package Lifecycle

What happens between "listed in the manifest" and "ready to use". Every verb
plugs into one slot of this pipeline, and most slots are usually empty.

```
spec acquired → check cache → depot import → FETCH → STAGE → BUILD → INSTALL → SETUP pairs
                     │             │
                     │             └─ prebuilt artifact found: skip to SETUP
                     └─ finished package already in cache: skip everything
```

The two short circuits matter more than the verbs. On a warm machine most
packages are cache hits, and in a project with a [depot](../depots.md) most
misses are downloads rather than builds.

## The phases

| Phase | What it does |
| --- | --- |
| **spec fetch** | Acquire the spec from disk, a URL, git, or a [bundle](../dependencies/bundles.md), then execute it and validate its globals. `OPTIONS` runs here, so a bad option fails before anything is downloaded. |
| **check** | Hash the package identity: `identity`, serialized `options`, and any resolved [weak](../dependencies/resolution.md) dependency keys, as blake3. The hash names the cache entry. A completed entry ends the run for this package. |
| **import** | Ask the depot for a prebuilt artifact matching that hash. A hit is downloaded, verified against its sha256, and unpacked. No fetch, no build. |
| **FETCH** | [Get the bytes.](./fetch.md) |
| **STAGE** | [Arrange a working tree.](./stage.md) |
| **BUILD** | [Transform it.](./build.md) |
| **INSTALL** | [Produce the final package directory.](./install.md) |
| **SETUP** | [Adjust the host machine](./setup.md), for the pairs a manifest entry selected, and only when their `CHECK` reports the host is not already correct. |
| **export** | Only during [`envy export`](../../reference/cli/export.md): archive the finished package and print its index line. |

## The directories a spec sees

envy creates one cache entry per package, at
`<cache>/packages/<identity>/<platform>-<arch>-blake3-<hash>/`:

| Directory | Passed to verbs as | Lifetime |
| --- | --- | --- |
| `fetch/` | `fetch_dir` | Downloads. Survives a failed attempt so a retry does not re-download. Deleted once the package completes, unless the spec is not `EXPORTABLE`, in which case the artifacts are kept for a depot to publish. |
| `work/stage/` | `stage_dir` | Scratch working tree. Deleted on success and on failure. |
| `work/tmp/` | `tmp_dir` | Scratch space for anything a verb writes and does not keep. Deleted with `work/`. |
| `pkg/` | `install_dir` | The package. Products resolve into it, other projects share it, and a depot ships it. |

Paths arrive with a trailing separator applied, so `fetch_dir .. "JLink.pkg"` is
correct. `envy.path.join` is available when you prefer it.

### Where extraction lands

Default staging extracts fetched archives straight into `pkg/`. A spec that only
downloads and unpacks pays for no intermediate copy. envy uses `work/stage/`
instead when `STAGE`, `BUILD`, or `INSTALL` is a function. That is the case where
a spec inspects the tree before deciding what the package should be.

```lua
-- Extracts into pkg/ directly: nothing here is a function.
STAGE = { strip = 1 }
INSTALL = "make install"

-- Extracts into work/stage/, because INSTALL is a function that copies out of it.
STAGE = { strip = 1 }
INSTALL = function(install_dir, stage_dir) envy.copy(stage_dir .. "bin/tool", install_dir) end
```

### Where scripts run

A string verb, or a string returned from a function verb, is a shell script.
Each verb starts it in a specific directory:

| Verb | Script's working directory |
| --- | --- |
| `STAGE` | the staging destination: `work/stage/`, or `pkg/` per the rule above |
| `BUILD` | `work/stage/` |
| `INSTALL` | `work/stage/` |
| `SETUP` `CHECK` and `INSTALL` | the project root, because they act on host state |

## Parallelism and ordering

Packages run concurrently, each on its own thread. Only a declared dependency
serializes them. A dependency can demand readiness as early as "before I can
fetch", which is how a spec that needs a download tool gets one. See
[Phase Ordering](../dependencies/ordering.md) and
[`needed_by`](../projects#package-entries).

Concurrent envy processes are also safe. Cache entries are file-locked, so two
`envy sync` runs in two terminals cooperate.

## Completion is final

A completed entry carries an `envy-complete` marker, and envy never
re-validates it. No timestamps, no re-hashing, no revalidation pass. A package
stays done until either its identity changes, which names a different entry, or
you delete the cache.

That is why [`envy sync`](../../reference/cli/sync.md) is cheap to run
repeatedly, and why deleting the [cache](../cache.md) is always safe.

## When something fails

| Outcome | What happens to the entry |
| --- | --- |
| Success | `work/` is removed and the marker is written. `fetch/` is removed too, unless the spec is not `EXPORTABLE`. |
| A verb fails | `pkg/` and `work/` are removed. `fetch/` is kept, so the next attempt resumes from downloaded bytes. The entry stays unmarked, so the next run redoes the work. |
| Nothing had happened yet | The whole entry is removed. |
| A `SETUP` pair | Its lock entry is ephemeral and always purged. Host state has no cache, and the pair's `CHECK` is the only re-run gate. |

A partially installed package is never left where a consumer can resolve into
it. envy writes the marker last, after `INSTALL` reports success.

## See also

- [Anatomy of a Spec](./index.md) for the verbs themselves.
- [The Cache](../cache.md) for entry layout and why deletion is safe.
- [Package Depots](../depots.md) for how the import phase gets a hit.
