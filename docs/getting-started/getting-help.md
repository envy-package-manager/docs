---
sidebar_position: 4
title: Getting Help
---

# Getting Help

envy is quiet by default: one line per package, and a summary. When that is not
enough, there are two dials and one contract.

## Make envy talk

```shell-session
$ envy --verbose sync
[2026-08-22 14:36:54.734] [DBG] Loading manifest (221 bytes)
[2026-08-22 14:36:54.734] [DBG] [envy.cmake@r0] spec: cache-managed
[2026-08-22 14:36:54.734] [DBG] [envy.cmake@r0] check: miss — building
[2026-08-22 14:36:54.734] [DBG] [envy.cmake@r0] fetch: running fetch function
[2026-08-22 14:36:54.734] [DBG] [envy.cmake@r0] stage: extracting to install dir
[2026-08-22 14:36:54.734] [INF] [envy.cmake@r0] installed (8.2s)
```

`--verbose` is a decision narrative rather than more noise. It answers the
questions you actually have:

| Question | The line that answers it |
| --- | --- |
| Why did this rebuild? | `check: miss — building`, or `check: hit` |
| Did the depot help? | the import phase's hit or miss |
| Where did this file come from? | `fetch:` lines, including cache reuse |
| Why is staging in a different place? | `stage: extracting to install dir` versus `to stage dir` |

`-q` goes the other way and prints warnings and errors only.

Both are [global flags](../reference/cli/index.md#global-flags), so they go
before the subcommand. `envy sync --verbose` is a parse error.

## Traces, for machines and bug reports

```bash
envy --trace=file:/tmp/sync.jsonl sync
```

One JSON object per line:

```json
{"seq":0,"ts":"2026-08-22T18:36:54.739Z","tid":0,"event":"trace_start","schema":2}
{"seq":1,"ts":"2026-08-22T18:36:54.745Z","tid":1,"event":"spec_registered","spec":"local.hello@r0"}
{"seq":2,"ts":"2026-08-22T18:36:54.745Z","tid":1,"event":"phase_start","spec":"local.hello@r0","phase":"spec_fetch"}
```

Every event carries a sequence number, a timestamp, and a thread id, so a trace
answers ordering questions that a log cannot: what waited on what, and what ran
concurrently. `--trace` on its own writes human-readable events to stderr
instead, and the sinks combine: `--trace=stderr,file:/tmp/t.jsonl`.

Tracing is independent of log level. Turning it on does not change what `--verbose`
prints. See [Logging & Tracing](../reference/observability.md).

## The stdout contract

Human output goes to stderr. stdout carries only machine-readable answers, from
`product`, `package`, `hash`, `export`, `merge-depot`, `git-resolve`, `cache`, and
`version --licenses`.

That separation is what lets this work:

```bash
CMAKE="$(envy product cmake)"     # never captures progress or warnings
```

## Reading an error

envy errors name the thing and the context. A few shapes worth recognizing:

| Error | What it means |
| --- | --- |
| `query 'x' not found in manifest` | A CLI query matched no entry. Check [query forms](../reference/cli/index.md#package-queries). |
| `'x' is not available on this platform` | You named an entry excluded by a `platforms` filter. |
| `Reference 'x' in spec 'y' was not found` | An unsatisfied [weak or reference-only dependency](/concepts/dependencies/resolution). |
| `Product 'x' provided by multiple specs: a, b` | Two specs claim one product name. |
| `envy.product: product 'x' needed_by 'build' but accessed during 'fetch'` | A [`needed_by`](/concepts/dependencies/ordering) gate. |
| `SHA256SUMS does not match the pinned '@envy sha256sums'` | The envy release does not match the manifest's pin. |

A failing verb includes the script text and the captured output, so a build that
dies inside a generated script shows you the script.

## Filing a good report

Attach three things:

1. `envy version` output, which includes every third-party library version.
2. The manifest, and the spec if the failure is in one.
3. A trace file: `envy --trace=file:/tmp/envy.jsonl <the failing command>`.

That combination usually makes a failure diagnosable without a reproduction,
because the trace carries the ordering and the version output carries the
transports.

## See also

- [Troubleshooting](../reference/troubleshooting.md) for specific symptoms.
- [Logging & Tracing](../reference/observability.md) for the event catalog.
- [CLI Reference](../reference/cli) for the conventions every command shares.
