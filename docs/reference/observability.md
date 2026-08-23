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

Default output is one line per package:

```console
$ envy sync
[envy.cmake@r0] cache hit
[envy.ninja@r0] imported from depot (0.4s)
[local.mytool@r1] installed (3.2s)
deploy: 4 product script(s) (4 created, 0 updated, 0 unchanged, 0 removed)
```

`--verbose` adds the reasoning behind each of those lines:

```console
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

Bare `--trace` means `stderr`. Tracing does not change the log level, so pair it
with `-q` when you want events without the narrative.

A Windows path after `file:` is fine, including the drive letter:
`--trace=file:C:\temp\trace.jsonl`. envy disables `/flag` style options, so a
POSIX-looking path is never mistaken for a flag either.

The stderr form is one event per line:

```console
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

**Depot, products, deploy**

| Event | Fields |
| --- | --- |
| `depot_check` | `sha`, `result`, one of `hit`, `miss`, `sha_mismatch` |
| `product_resolved` | `product`, `provider`, `via`, one of `registry`, `identity`, `fallback` |
| `deploy_script` | `product`, `platform`, `action`, one of `created`, `updated`, `unchanged`, `removed` |

**IO**

| Event | Fields |
| --- | --- |
| `download_start` | `url`, `destination` |
| `download_complete` | `url`, `bytes`, `duration_ms` |
| `download_failed` | `url`, `error` |
| `download_skipped` | `url`, `reason` |
| `git_resolve` | `url`, `ref`, `sha`, `method`, either `sha` or `ls-remote` |
| `extract_start` | `archive`, `destination`, `strip_components` |
| `extract_complete` | `archive`, `files_extracted`, `duration_ms` |

## Recipes

**Why did this rebuild?**

```bash
envy --trace=file:t.jsonl sync && grep -E 'cache_(hit|miss)' t.jsonl
```

A `cache_miss` names the key that was not found. Compare it to the key in a
previous trace and the difference tells you which option or dependency moved.
`--verbose` answers the same question in prose with `check: miss — building`.

**What waited on what?**

```console
$ grep -E 'phase_(blocked|unblocked)' t.jsonl
{"seq":41,...,"event":"phase_blocked","spec":"local.user@r1","blocked_at_phase":"build","waiting_for":"local.tool@r1","target_phase":"export"}
{"seq":48,...,"event":"phase_unblocked","spec":"local.user@r1","unblocked_at_phase":"build","dependency":"local.tool@r1"}
```

Read it as: `local.user@r1` reached `build`, needed `local.tool@r1`, and resumed
when that package got there. Subtract the timestamps for the stall.

**Where did this file come from?**

`download_start` and `download_complete` carry the URL and the destination, and
`depot_check` says whether a depot answered first. Together they account for every
byte that entered the cache.

**Was my `envy.product` call legal?**

```console
$ grep lua_ctx_product_access t.jsonl
{...,"target":"hello_txt","provider":"local.tool@r1","current_phase":"build","needed_by":"build","allowed":true,"reason":"/tmp/cache/packages/local.tool@r1/darwin-arm64-blake3-7d319775cb50aa49/pkg/hello.txt"}
```

`allowed` is the verdict and `reason` is the resolved path, or the explanation
when it is `false`. A denial is also a hard error, so you will see it without the
trace:

```console
$ envy sync
error: Lua error in local.user@r1:
  envy.product: pkg 'local.user@r1' does not declare product dependency on 'nope_txt'
Stack traceback:
  /tmp/project/user.lua:11: in function 'base.BUILD'

Spec file: /tmp/project/user.lua:11
Declared in: /tmp/project/envy.lua
```

**What did deploy actually change?**

```console
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
