---
sidebar_position: 6
title: INSTALL
---

# INSTALL

> **Placeholder content.** Outline for review; verify against sources.

Produce the final package directory — the tree that gets cached, shared, and
resolved by products.

Will cover — the three shapes:

| Shape | Meaning |
| --- | --- |
| omitted | The staged tree *becomes* the package. Right for "download, unpack, done" specs. |
| string | A shell script (e.g. `INSTALL = "make install"`), run in the staging directory. |
| function `INSTALL(install_dir, stage_dir, fetch_dir, tmp_dir, opts)` | File surgery: copy/rename binaries, run platform installers, assemble the tree by hand. May return a string to run as a shell script. |

- The contract: after INSTALL, the package directory is immutable — consumers
  resolve into it forever; never mutate it post-hoc (that's what
  [SETUP](./setup.md) is for).
- `EXPORTABLE` and what it changes: exportable packages ship their installed
  tree to [depots](/concepts/depots); non-exportable packages keep their
  *fetched* artifacts instead (for tools whose installers must run per
  machine).
- Small real examples: rename-a-platform-suffixed-binary; run
  `installer` / `msiexec` per platform.
