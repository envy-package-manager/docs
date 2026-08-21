---
sidebar_position: 2
title: First Steps
---

# First Steps

> **Placeholder content.** Outline for review; verify against sources.

A guided five-minute tour from a fresh clone to running project tools.

Will cover:

- `./bin/envy sync` — the everyday command: installs everything in the
  manifest and deploys product wrapper scripts into the project's bin dir.
- The command triangle — three distinct verbs, not synonyms:
  - `envy install` — install packages into the cache; touch nothing in the
    project.
  - `envy deploy` — (re)generate product wrapper scripts in the bin dir from
    already-resolved products.
  - `envy sync` = install + deploy.
- What just happened: a look at the bin dir (wrapper per product), and at the
  one-line-per-package output.
- Three ways to run project tools:
  1. `./bin/<tool>` — deployed product wrappers, zero setup.
  2. `envy run <command...>` — one-shot PATH activation.
  3. [Shell integration](./shell-integration.md) — automatic PATH management
     on `cd`.
- Asking envy questions: `envy product` (list products), `envy product cmake`
  (resolve one), `envy package <identity>` (where is this package installed).
- Syncing a subset: `envy sync <query>` with partial-match queries.
- What's safe: the cache can always be deleted; `sync` is idempotent and
  incremental.
