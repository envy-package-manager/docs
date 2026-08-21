---
sidebar_position: 2
title: First Steps
---

# First Steps

> **Placeholder content.** Outline for review. Verify against sources.

A five-minute tour from a fresh clone to running project tools.

Will cover:

- `./bin/envy sync`, the everyday command. It installs everything in the
  manifest and deploys product wrapper scripts into the project's bin
  directory.
- The command triangle, three distinct verbs rather than synonyms:
  - `envy install` installs packages into the cache and touches nothing in the
    project.
  - `envy deploy` regenerates product wrapper scripts in the bin directory from
    already-resolved products.
  - `envy sync` does both.
- What just happened: a look at the bin directory, which holds one wrapper per
  product, and at the one-line-per-package output.
- Three ways to run project tools:
  1. `./bin/<tool>`, the deployed product wrappers, with no setup.
  2. `envy run <command...>`, one-shot activation.
  3. [Shell integration](./shell-integration.md), automatic `PATH` management on
     `cd`.
- Asking envy questions: `envy product` to list products, `envy product cmake`
  to resolve one, `envy package <identity>` to find where a package is
  installed.
- Syncing a subset with `envy sync <query>`.
- What is safe: the cache can always be deleted, and `sync` is idempotent and
  incremental.
