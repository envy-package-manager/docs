---
sidebar_position: 6
title: envy run
---

# `envy run`

> **Placeholder content.** Verify flags and semantics against sources.

Run one command with the project's bin dir prepended to `PATH` and
`ENVY_PROJECT_ROOT` set — one-shot activation, no shell integration needed.
Everything after `run` belongs to your command, and its exit status becomes
envy's exit status.

## Usage

```
envy run <command> [args...]
envy run -- <script-path> [args...]     # anchor manifest discovery at the script
```

## Behavior

| Aspect | Meaning |
| --- | --- |
| PATH | Project bin dir prepended; deployed wrappers all visible. |
| `ENVY_PROJECT_ROOT` | Set to the governing manifest's directory. |
| Discovery | Walks up from the current directory (or the `--` script's directory). |
| Exit code | Transparent passthrough from your command. |

## Examples

```bash
envy run make -j
envy run python3 tools/codegen.py
envy run -- ./scripts/build.sh --release
```

## See also

- [envy run (concepts)](/concepts/environment/envy-run)
- [Shell Integration](/getting-started/shell-integration) — the persistent
  alternative.
