---
sidebar_position: 3
title: Shell Integration
---

# Shell Integration

> **Placeholder content.** Outline for review. Verify against sources.

Optional. Teach your shell to put each project's bin directory on `PATH` as you
`cd` around.

Will cover:

- One-time setup. `envy shell <bash|zsh|fish|powershell>` prints the line to add
  to your shell profile.
- What the hook does on every directory change. It finds the governing
  `envy.lua`, prepends its bin directory to `PATH`, sets `ENVY_PROJECT_ROOT`, and
  adds the 🦝 prompt marker. Leaving the project undoes all of it.
- No performance cost. The hook is pure shell, and the envy binary is never
  invoked at shell startup or on `cd`.
- Hooks update themselves when envy updates. Restart your shell when told.
- Opt-outs: `ENVY_SHELL_HOOK_DISABLE=1`,
  `ENVY_SHELL_NO_ENTER_EXIT_ANNOUNCE=1`, `ENVY_SHELL_NO_ICON=1`.
- When not to bother. CI and scripts should use `./bin/<tool>` wrappers or
  `envy run`.
