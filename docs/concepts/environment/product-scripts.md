---
sidebar_position: 1
title: Product Scripts
---

# Product Scripts

> **Placeholder content.** Outline for review; verify against sources.

The default activation story: `envy sync` deploys one tiny wrapper script per
executable product into the project's bin dir. Commit the bin dir once;
everything in it stays correct forever.

Will cover:

- What a wrapper is — four lines that resolve the product at call time:

```bash
#!/usr/bin/env bash
# envy-managed schema "1"
SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
exec "$("$SCRIPT_DIR/envy" product "cmake")" "$@"
```

  Because resolution happens at call time, wrappers never go stale: change a
  version in the manifest, `sync`, same wrapper now runs the new tool.
- The switches: `@envy bin` names the directory; `@envy deploy "true"`
  enables deployment; `--platform` picks posix/windows/both script flavors.
- The command triangle: `envy install` (packages only), `envy deploy`
  (scripts only), `envy sync` (both).
- Ownership discipline: envy only creates, updates, and prunes files carrying
  the `envy-managed` marker. Hand-written scripts in the same directory are
  never touched; name collisions are skipped (or errors under `--strict`).
- The hand-written-wrapper pattern that coexists: a committed `bin/gn` that
  runs `envy sync` then dispatches to resolved products.
- What does *not* get a script: `script = false` products
  ([Products](/concepts/specs/products)) — by design.
