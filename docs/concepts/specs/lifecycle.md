---
sidebar_position: 2
title: The Package Lifecycle
---

# The Package Lifecycle

> **Placeholder content.** Outline for review; verify against sources.

What happens to a package between "listed in the manifest" and "ready to
use" — the pipeline every verb plugs into.

Will cover:

- The user-visible pipeline:

```
spec acquired → (depot check) → FETCH → STAGE → BUILD → INSTALL → SETUP pairs
```

  - envy first acquires and reads the spec, checks whether the finished
    package already exists (cache hit) or can be downloaded prebuilt
    ([depot](/concepts/depots) hit) — and only otherwise runs the verbs.
- What each verb is *for* (one paragraph each, links to per-verb pages):
  fetch bytes → arrange a working tree → transform it → produce the final
  package directory → optionally adjust the host machine.
- The directories a spec sees and their lifetimes: `fetch_dir` (durable
  download cache), `stage_dir` / `tmp_dir` (scratch, discarded), the package
  install directory (the final product).
- Packages build in parallel; dependencies control ordering
  ([Phase Ordering](/concepts/dependencies/ordering)).
- Completed packages are never re-validated or re-run — a package is done
  until its identity/options change or the cache is deleted.
- Failure behavior: what's kept (downloads), what's cleaned (partial
  installs), what re-runs on the next attempt.
