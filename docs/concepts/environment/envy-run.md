---
sidebar_position: 3
title: envy run
---

# `envy run`

> **Placeholder content.** Outline for review. Verify against sources.

One-shot activation. Run a single command with the project's bin directory on
`PATH` and no shell integration required.

Will cover:

- Basic use: `envy run ./scripts/build.sh`, `envy run make -j`. The command can
  call `envy` by name, sees any deployed products, and gets
  `ENVY_PROJECT_ROOT`.
- Argument passthrough. Everything after `run` belongs to your command.
- Anchoring. Which project's environment you get, which is manifest discovery
  from the current directory, and how to anchor to a script's location instead.
- Where it fits: CI steps, Makefiles, git hooks, and editor task runners,
  anywhere a login shell and its hooks do not exist.
- Exit-code transparency. Your command's exit status is envy's exit status.
