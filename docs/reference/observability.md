---
sidebar_position: 6
title: Logging & Tracing
---

# Logging & Tracing

> **Placeholder content.** Outline for review; verify against sources.

Will cover:

- The two output systems and when to reach for each:
  - **Logs** — human narrative on stderr. Default: one line per package
    outcome. `--verbose`: the reasoning (cache hit? depot hit? why did this
    wait?). `-q`: problems only.
  - **Traces** — `--trace[=stderr|file:<path>]`: structured JSONL machine
    events for tooling and bug reports.
- The stdout contract: only machine-readable answers (`product`, `package`,
  `hash`, `export`) — safe to pipe, always.
- Reading `--verbose` output to answer the classic questions: why did this
  rebuild? what blocked on what? where did this file come from?
- Trace event catalog (table, generated or hand-maintained — TBD).
- What to attach to a bug report.
