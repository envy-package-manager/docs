---
sidebar_position: 3
title: envy run
---

# `envy run`

> **Placeholder content.** Outline for review; verify against sources.

One-shot activation: run a single command with the project's bin dir on
`PATH`, no shell integration required.

Will cover:

- Basic use: `envy run make -j`, `envy run python3 tools/gen.py` — the
  command sees every deployed product and `ENVY_PROJECT_ROOT`.
- Argument passthrough: everything after `run` belongs to your command.
- Anchoring: which project's environment you get (manifest discovery from
  the current directory), and anchoring to a script's location instead.
- Where it shines: CI steps, Makefiles, git hooks, editors' task runners —
  anywhere a login shell (and its hooks) doesn't exist.
- Exit-code transparency: your command's exit status is envy's exit status.
