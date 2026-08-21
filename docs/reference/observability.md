---
sidebar_position: 6
title: Logging & Tracing
---

# Logging & Tracing

> **Placeholder content.** Outline for review. Verify against sources.

Will cover:

- The two output systems, and when to use each:
  - Logs, a human narrative on stderr. The default is one line per package
    outcome. `--verbose` adds the reasoning: cache hit, depot hit, and what
    waited on what. `-q` prints problems only.
  - Traces, enabled with `--trace[=stderr|file:<path>]`, are structured JSONL
    machine events for tooling and bug reports.
- The stdout contract. Only machine-readable answers go there, from `product`,
  `package`, `hash`, and `export`, so stdout is always safe to pipe.
- Reading `--verbose` output to answer the common questions: why did this
  rebuild, what blocked on what, and where did this file come from.
- The trace event catalog, as a table, either generated or hand-maintained.
- What to attach to a bug report.
