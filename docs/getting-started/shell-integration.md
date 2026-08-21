---
sidebar_position: 3
title: Shell Integration
---

# Shell Integration

> **Placeholder content.** Outline for review; verify against sources.

Optional: teach your shell to put each project's bin dir on `PATH`
automatically as you `cd` around.

Will cover:

- One-time setup: `envy shell <bash|zsh|fish|powershell>` prints the `source`
  line to add to your shell profile.
- What the hook does on every directory change: finds the governing
  `envy.lua`, prepends its bin dir to `PATH`, sets `ENVY_PROJECT_ROOT`, and
  adds the 🦝 prompt marker; undoes all of it when you leave.
- No performance tax: the hook is pure shell — the envy binary is never
  invoked at shell startup or on `cd`.
- Hooks update themselves when envy updates (restart your shell when told).
- Opt-outs: `ENVY_SHELL_HOOK_DISABLE=1`, `ENVY_SHELL_NO_ENTER_EXIT_ANNOUNCE=1`,
  `ENVY_SHELL_NO_ICON=1`.
- When *not* to bother: CI and scripts should use `./bin/<tool>` wrappers or
  `envy run` instead.
