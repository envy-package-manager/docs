---
sidebar_position: 5
title: Environment Variables
---

# Environment Variables

> **Placeholder content.** Verify against sources.

| Variable | Direction | Meaning |
| --- | --- | --- |
| `ENVY_CACHE_ROOT` | in | Override the cache root. |
| `ENVY_MIRROR` | in | Override the envy release mirror (beats `@envy mirror`). |
| `ENVY_IGNORE_DEPOT` | in | Skip depot lookups; build from source. |
| `ENVY_PROJECT_ROOT` | out | Set by `envy run` / shell hooks: the governing manifest's directory. |
| `ENVY_SHELL_HOOK_DISABLE` | in | Disable shell-hook activation. |
| `ENVY_SHELL_NO_ENTER_EXIT_ANNOUNCE` | in | Silence project enter/leave messages. |
| `ENVY_SHELL_NO_ICON` | in | No 🦝 prompt marker. |
| `ENVY_NO_REEXEC` | in | Don't re-exec into the manifest-pinned envy version (debugging). |

Precedence interactions (cache root, mirror) documented in
[Concepts](/concepts/cache).
