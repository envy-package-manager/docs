---
sidebar_position: 3
title: Phase Ordering & needed_by
---

# Phase Ordering & `needed_by`

> **Placeholder content.** Outline for review; verify against sources.

A dependency edge in envy has a *time* attached: the phase of the dependent
that must wait. That's `needed_by`.

Will cover:

- The intuition with three examples:
  - A **build tool** (cmake for a source build): `needed_by = "build"` — the
    dependent can fetch and stage its own sources while cmake installs.
  - A **fetch tool** (the AWS CLI for a spec whose FETCH shells out to
    `aws s3 cp`): `needed_by = "fetch"`.
  - A **runtime companion** (something INSTALL invokes):
    `needed_by = "install"`.
- Valid values: `check`, `import`, `fetch`, `stage`, `build`, `install` —
  the phases of the dependent that can wait on a dependency.
- **The default is `build`.** If a verb *earlier* than BUILD uses a
  dependency (most commonly FETCH), you must say so explicitly — otherwise
  the dependency may not exist yet when your FETCH runs.
- What "ready" means: the dependency is fully installed (through its own
  setup) before the gated phase starts; ungated phases of the dependent run
  concurrently with it.
- Where `needed_by` can appear: on `DEPENDENCIES` entries in specs, and on
  dependency-shaped fields in manifest entries.
- The limit of `needed_by`: it cannot gate *acquiring the dependent's own
  spec* — that's earlier than any phase you can name. For that, see
  [Fetch Dependencies](./fetch-dependencies.md).
- Parallelism consequences: why envy installs are fast, and how to read
  `--verbose` output to see what waited on what.
