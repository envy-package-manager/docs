---
sidebar_position: 6
title: Logging & Tracing
---

# Logging & Tracing

Two independent output systems. Logs narrate for people. Traces record events for
tools. Neither one touches stdout.

| | Logs | Traces |
| --- | --- | --- |
| Turned on by | always on | `--trace` |
| Levels | `-q`, default, `--verbose` | none, all events always |
| Stream | stderr | stderr or a file |
| Format | prose | `key=value` text, or JSONL |
| Read by | you | tooling, and bug reports |

## Log levels

| Flag | Shows |
| --- | --- |
| `-q`, `--quiet` | warnings and errors only |
| none | one line per package outcome, plus warnings and errors |
| `--verbose` | the decision narrative, timestamped and level-tagged |

`-q` and `--verbose` are mutually exclusive. Both are global flags, so they go
before the subcommand.

Default output is one line per package that did something:

```shell-session
$ envy sync
[envy.ninja@r0] imported from depot (0.4s)
[local.mytool@r1] installed (3.2s)
deploy: 4 product script(s) (4 created, 0 updated, 0 unchanged, 0 removed)
```

## A run with no work is silent

On a terminal, a package that did nothing prints no line. Since envy 0.4.2 a
package only prints one if it fetched, built, installed, imported, vendored, or
ran a [`SETUP`](/concepts/specs/setup) pair. A cache hit that copied no files
and ran no pair did none of those, so a second `envy sync` over a warm cache
prints nothing.

The `deploy:` summary works the same way, and has for longer: it prints only
when a wrapper was created, updated, or removed. So `envy sync` on a project
that is already correct prints nothing at all.

Since envy 0.4.3 it writes no bytes at all. Earlier versions opened the live
region on every run, so one with no work still wrote the escape sequences that
hide the cursor and toggle auto-wrap. Those are invisible on a terminal, but a
test that asserts on empty output would fail.

A silent run is a successful one. To see what envy decided about each package,
use `--verbose`, which prints a line for every one.

**Redirect the output and every package prints again.** Off a terminal the
`cache hit` lines come back, so the log lists every package in the run:

```shell-session
$ envy sync 2> sync.log ; cat sync.log
[envy.cmake@r0] cache hit
[envy.ninja@r0] imported from depot (0.4s)
[local.mytool@r1] installed (3.2s)
deploy: 4 product script(s) (4 created, 0 updated, 0 unchanged, 0 removed)
```

A CI log is therefore complete whether or not the cache was warm. If a pipeline
and a terminal disagree about which packages ran, this is why.

A spec's [`DISPLAY`](./spec-globals.md#display) sits between the identity and
the outcome on both, which is how you tell several instances of one spec apart
in a log.

`--verbose` adds the reasoning behind each of those lines:

```shell-session
$ envy --verbose sync
[2026-08-22 14:58:45.135] [DBG] Loading manifest (123 bytes)
[2026-08-22 14:58:45.135] [DBG] [local.fstr@r1] spec: cache-managed
[2026-08-22 14:58:45.135] [DBG] [local.fstr@r1] check: miss — building
[2026-08-22 14:58:45.135] [DBG] [local.fstr@r1] fetch: downloading 1 file(s)
[2026-08-22 14:58:45.135] [DBG] [local.fstr@r1] stage: extracting to install dir
[2026-08-22 14:58:45.135] [DBG] [local.fstr@r1] stage: extracted 1 file(s) from archives, copied 0
[2026-08-22 14:58:45.135] [DBG] [local.fstr@r1] install: install dir already populated — marking complete
[2026-08-22 14:58:45.135] [INF] [local.fstr@r1] installed (0.0s)
```

That is usually enough. Reach for a trace when you need timings, ordering across
threads, or an exact answer about what waited on what.

## stdout is a contract

Logs, progress, and errors all go to stderr. Only machine-readable answers go to
stdout, so any of these is safe to capture:

| Command | stdout |
| --- | --- |
| [`product <name>`](./cli/product.md) | one absolute path |
| [`product --json`](./cli/product.md) | a JSON object of every product |
| [`package <query>`](./cli/package.md) | one package directory |
| [`hash`](./cli/hash.md) | `<sha256>  <name>` lines |
| [`export`](./cli/export.md) | depot index lines |
| [`merge-depot`](./cli/merge-depot.md) | the merged index |
| [`git-resolve`](./cli/git-resolve.md) | one commit sha |
| [`import`](./cli/import.md) | the imported package directory |
| [`cache`](./cli/cache.md) | the usage report |

Everything else prints nothing to stdout. `envy product cmake > path.txt` gets a
path and nothing else, with the progress narrative still visible on your
terminal.

On Windows, `>` in PowerShell writes UTF-16, which most parsers reject. Pipe
through `Out-File` with an explicit encoding instead:

```powershell
envy product --json | Out-File -FilePath products.json -Encoding utf8
envy export -o out --depot-prefix s3://bucket/ | Out-File -FilePath index.txt -Encoding ascii
```

`cmd.exe` redirection needs no such care, and neither does any POSIX shell.

## Traces

```bash
envy --trace sync                          # human-readable, to stderr
envy --trace=file:trace.jsonl sync         # JSONL, to a file
envy --trace=stderr,file:trace.jsonl sync  # both
```

A file sink survives a [re-exec](/concepts/reproducibility#re-exec-running-the-version-the-manifest-pins).
envy closes the file and hands it to the pinned binary, so one trace covers the
whole run instead of two versions writing over each other. Requires envy 0.4.4.
Before that, on Windows, the parent kept the file open across the hand-off and
its records landed over the child's.

Bare `--trace` means `stderr`. Tracing does not change the log level, so pair it
with `-q` when you want events without the narrative.

A Windows path after `file:` is fine, including the drive letter:
`--trace=file:C:\temp\trace.jsonl`. envy disables `/flag` style options, so a
POSIX-looking path is never mistaken for a flag either.

The stderr form is one event per line:

```shell-session
$ envy --trace sync
trace_start schema=2
spec_registered spec=local.fstr@r1 key=local.fstr@r1
phase_start spec=local.fstr@r1 phase=check
lock_acquired spec=local.fstr@r1 lock_path=/tmp/v2/locks/packages.local.fstr@r1-darwin-arm64-blake3-0a7dd66fdc26e664.lock wait_duration_ms=0
cache_miss spec=local.fstr@r1 cache_key=local.fstr@r1-darwin-arm64-blake3-0a7dd66fdc26e664
phase_complete spec=local.fstr@r1 phase=check duration_ms=0
phase_start spec=local.fstr@r1 phase=fetch
download_start spec=local.fstr@r1 url=/tmp/payload.tar.gz destination=/tmp/v2/packages/local.fstr@r1/darwin-arm64-blake3-0a7dd66fdc26e664/fetch/payload.tar.gz
download_complete spec=local.fstr@r1 url=/tmp/payload.tar.gz bytes=445 duration_ms=0
```

The file form is one JSON object per line:

```json
{"seq":41,"ts":"2026-08-22T18:59:00.426Z","tid":1,"event":"phase_blocked","spec":"local.user@r1","blocked_at_phase":"build","waiting_for":"local.tool@r1","target_phase":"export"}
```

Every event carries `seq`, `ts`, `tid`, `event`, and usually `spec`. `seq` is a
monotonic counter, so ordering survives interleaving from the worker threads that
`tid` distinguishes. The first event is always `trace_start` with the schema
version.

## Event catalog

**Scheduler**

| Event | Fields |
| --- | --- |
| `trace_start` | `schema` |
| `spec_registered` | `key` |
| `dependency_added` | `dependency`, `needed_by`. `spec` is the parent. |
| `phase_start` | `phase` |
| `phase_complete` | `phase`, `duration_ms` |
| `phase_blocked` | `blocked_at_phase`, `waiting_for`, `target_phase` |
| `phase_unblocked` | `unblocked_at_phase`, `dependency` |
| `target_extended` | `old_target`, `new_target` |
| `pkg_outcome` | `outcome`, `duration_ms`. Terminal result, one of `cache_hit`, `imported`, `installed`, `setup_complete`, `bundle_fetched`, `bundle_local`. |
| `manifest_resolved` | `path`, `anchor`, `mode`, `nearest`. Which project the command decided it was operating on. `mode` is `explicit` (`--manifest`), `project` (`--project`), or `cwd`. `anchor` is the directory the walk started from, empty for an explicit path. `nearest` is `--subproject`. [`envy run`](./cli/run.md) emits nothing, because it replaces its own process before the trace drains. |
| `manifest_imported` | `path`, `importer`. One [`envy.import`](./lua-api.md#envyimportpath): the manifest read, and the file that read it. Discovery never sees an imported manifest, so this is the only record that it took part in the run. |

**Cache and locking**

| Event | Fields |
| --- | --- |
| `cache_hit` | `cache_key`, `pkg_path`, `fast_path` |
| `cache_miss` | `cache_key` |
| `lock_acquired` | `lock_path`, `wait_duration_ms` |
| `lock_released` | `lock_path`, `hold_duration_ms` |
| `cache_entry_finalized` | `entry_dir`, `disposition`, one of `completed`, `purged_user_managed`, `cleaned_failure`, `kept_partial` |

**Lua sandbox access**

| Event | Fields |
| --- | --- |
| `lua_ctx_package_access` | `target`, `current_phase`, `needed_by`, `allowed`, `reason` |
| `lua_ctx_product_access` | `target`, `provider`, `current_phase`, `needed_by`, `allowed`, `reason` |
| `lua_ctx_loadenv_spec_access` | `target`, `subpath`, `current_phase`, `needed_by`, `allowed`, `reason` |
| `lua_ctx_loadenv_bundle` | `alias`, `target`, `subpath`, `root`. A manifest reaching into a bundle before its own global scope has finished, via [`envy.loadenv_bundle`](./lua-api.md#envyloadenv_bundlealias-module). `alias` is the `BUNDLES` key it named, `root` where the payload landed. Requires envy 0.4.6. |

**Depot, products, deploy**

| Event | Fields |
| --- | --- |
| `depot_check` | `sha`, `result`, one of `hit`, `miss`, `sha_mismatch` |
| `depot_wait` | `duration_ms`, `result`, one of `ready`, `bootstrap`, `failed`. One package's block on the merged depot index, closed out. `bootstrap` means the wait ended because the package joined the depot's own `DEPENDS` closure, which exempts it from consulting the index. |
| `default_shell_resolving` | `depends`. The `#default_shell` task starting, and how many packages it must install before the `SHELL` function can name one. The subject is the synthetic consumer. |
| `default_shell_resolved` | `shell`, one of `bash`, `sh`, `cmd`, `powershell` for a built-in, or `file`/`inline` for a custom shell naming an interpreter. Emitted once for the run. |
| `product_resolved` | `product`, `provider`, `via`, one of `registry`, `fallback` |
| `deploy_script` | `product`, `platform`, `action`, one of `created`, `updated`, `unchanged`, `removed` |

**IO**

| Event | Fields |
| --- | --- |
| `download_start` | `url`, `destination` |
| `download_complete` | `url`, `bytes`, `duration_ms` |
| `download_failed` | `url`, `error` |
| `download_retry` | `url`, `attempt` (1-based, the attempt that failed), `delay_ms`, `reason`, `error`. `reason` is the transport classification: `connect`, `transfer`, `timeout`, or `http_status`. |
| `download_skipped` | `url`, `reason` |
| `git_resolve` | `url`, `ref`, `sha`, `method`, either `sha` or `ls-remote` |
| `extract_start` | `archive`, `destination`, `strip_components` |
| `extract_complete` | `archive`, `files_extracted`, `duration_ms` |

**[Vendoring](/concepts/vendoring)**

| Event | Fields |
| --- | --- |
| `vendor_resolved` | `path`, `origin`, either `derived` or `override`. One per destination, emitted before any package runs, because the whole plan is resolved and checked up front. |
| `vendor_result` | `path`, `action`, `reason`, `dry_run`, `files`, `bytes`, `hash_ms`, `wipe_ms`, `copy_ms`, `duration_ms`. `action` is `copied`, `redeployed`, `kept`, or `up_to_date`. `reason` is `absent` (nothing was there), `mismatch` (the destination is not what the package holds), or `current`. `kept` is a mismatch under `auto_sync = false`, where envy reports and leaves it. `files` and `bytes` count what was written, so anything but a copy reports zeroes. `dry_run` marks [`envy vendor --dry-run`](./cli/vendor.md), where the decision is the real one and `files`/`bytes` are what a copy *would* have written. The three stage timings split `duration_ms` into hashing, deleting, and copying. |

## Recipes

**Why did this rebuild?**

```bash
envy --trace=file:t.jsonl sync && grep -E 'cache_(hit|miss)' t.jsonl
```

A `cache_miss` names the key that was not found. Compare it to the key in a
previous trace and the difference tells you which option or dependency moved.
`--verbose` answers the same question in prose with `check: miss — building`.

**What waited on what?**

```shell-session
$ grep -E 'phase_(blocked|unblocked)' t.jsonl
{"seq":41,...,"event":"phase_blocked","spec":"local.user@r1","blocked_at_phase":"build","waiting_for":"local.tool@r1","target_phase":"export"}
{"seq":48,...,"event":"phase_unblocked","spec":"local.user@r1","unblocked_at_phase":"build","dependency":"local.tool@r1"}
```

That line says `local.user@r1` reached `build`, needed `local.tool@r1`, and
resumed when that package got there. Subtract the timestamps for the stall.

**Where did this file come from?**

`download_start` and `download_complete` carry the URL and the destination, and
`depot_check` says whether a depot answered first. Together they account for every
byte that entered the cache.

**Was my `envy.product` call legal?**

```shell-session
$ grep lua_ctx_product_access t.jsonl
{...,"target":"hello_txt","provider":"local.tool@r1","current_phase":"build","needed_by":"build","allowed":true,"reason":"/tmp/cache/packages/local.tool@r1/darwin-arm64-blake3-7d319775cb50aa49/pkg/hello.txt"}
```

`allowed` is the verdict and `reason` is the resolved path, or the explanation
when it is `false`. A denial is also a hard error, so you will see it without the
trace:

```shell-session
$ envy install
error: Lua error in local.user@r1:
  envy.product: pkg 'local.user@r1' does not declare product dependency on 'nope_txt'
Stack traceback:
  /tmp/project/user.lua:11: in function 'base.BUILD'

Spec file: /tmp/project/user.lua:11
Declared in: /tmp/project/envy.lua
```

**Why did a vendored directory get rewritten?**

```shell-session
$ grep vendor_result t.jsonl
{...,"event":"vendor_result","spec":"local.nanocobs@r3","path":"third_party/nanocobs","action":"redeployed","reason":"mismatch","dry_run":false,"files":41,"bytes":8192,"hash_ms":7,"wipe_ms":2,"copy_ms":3,"duration_ms":12}
```

`mismatch` says the directory's contents are not what the package holds, which
covers an edit, a stray file, and a package that moved on. Reproduce the
comparison with [`envy hash --tree`](./cli/hash.md#subtree-hashing) on that path,
or ask for the same report without a repair with
[`envy vendor --all --dry-run`](./cli/vendor.md).

**What did deploy actually change?**

```shell-session
$ grep deploy_script t.jsonl
{...,"event":"deploy_script","product":"cmake","platform":"posix","action":"unchanged"}
```

One event per script per platform, which is how the summary line's counts are
produced.

## Filing a bug report

Attach these:

1. The manifest, and the spec if you wrote it.
2. `envy version`.
3. `envy --verbose <command>` output.
4. `envy --trace=file:trace.jsonl <command>` and the file.

The trace has paths and URLs in it. Nothing else, but read it before pasting it
into a public issue.

## See also

- [Global flags](./cli/index.md)
- [Troubleshooting](./troubleshooting.md)
- [Dependency Resolution](/concepts/dependencies/resolution) for what the phase events describe
