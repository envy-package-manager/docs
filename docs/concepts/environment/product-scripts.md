---
sidebar_position: 1
title: Product Scripts
---

# Product Scripts

> **Placeholder content.** Outline for review. Verify against sources.

The default activation story. `envy sync` deploys one small wrapper script per
executable product into the project's bin directory. Commit the bin directory
once, and everything in it stays correct.

Will cover:

- What a wrapper is: four lines that resolve the product when called.

```bash
#!/usr/bin/env bash
# envy-managed schema "1"
SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
exec "$("$SCRIPT_DIR/envy" product "cmake")" "$@"
```

  Because resolution happens at call time, wrappers never go stale. Change a
  version in the manifest, run `sync`, and the same wrapper runs the new tool.
- The switches. `@envy bin` names the directory, `@envy deploy "true"` enables
  deployment, and `--platform` picks POSIX, Windows, or both script flavors.
- The command triangle: `envy install` for packages only, `envy deploy` for
  scripts only, `envy sync` for both.
- Ownership. envy creates, updates, and prunes only files carrying the
  `envy-managed` marker. Hand-written scripts in the same directory are never
  touched, and name collisions are skipped, or reported as errors under
  `--strict`.
- The hand-written wrapper pattern that coexists with deployment: a committed
  `bin/gn` that runs `envy sync` and then dispatches to resolved products.
- What does not get a script: `script = false` products. See
  [Products](/concepts/specs/products).
