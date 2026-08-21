---
sidebar_position: 5
title: Environment Variables
---

# Environment Variables

> **Placeholder content.** Verify against sources.

| Variable | Direction | Meaning |
| --- | --- | --- |
| `ENVY_CACHE_ROOT` | in | Override the cache root. |
| `ENVY_MIRROR` | in | Override the envy release mirror. Takes precedence over `@envy mirror`. |
| `ENVY_IGNORE_DEPOT` | in | Skip depot lookups and build from source. |
| `ENVY_PROJECT_ROOT` | out | Set by `envy run` and the shell hooks. The governing manifest's directory. |
| `ENVY_SHELL_HOOK_DISABLE` | in | Disable shell-hook activation. |
| `ENVY_SHELL_NO_ENTER_EXIT_ANNOUNCE` | in | Silence project enter/leave messages. |
| `ENVY_SHELL_NO_ICON` | in | No 🦝 prompt marker. |
| `ENVY_NO_REEXEC` | in | Do not re-exec into the manifest-pinned envy version. For debugging. |

Precedence for the cache root and the mirror is documented in
[The Cache](/concepts/cache).
