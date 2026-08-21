---
sidebar_position: 11
title: envy git-resolve
---

# `envy git-resolve`

> **Placeholder content.** Verify flags and semantics against sources.

Resolve a remote branch or tag to its full commit hash — without cloning.
The authoring-time tool behind every pinned `ref`: turn a mutable name into
an immutable pin, and record the command as a comment so future updaters know
how to re-resolve.

## Usage

```
envy git-resolve <url> <ref>
```

## Arguments

| Argument | Meaning |
| --- | --- |
| `url` | Remote repository URL. |
| `ref` | Branch, tag, or ref name (e.g. `main`, `tags/v1.5.25`). |

Prints the full commit hash to stdout.

## Examples

```bash
envy git-resolve https://github.com/envy-package-manager/package-specs main
# 9bdb0a11cefa3e83418cff37dc68ea755c07a237
```

```lua title="the convention in a manifest"
BUNDLES = {
  envy = {
    identity = "envy.package-specs@r1",
    source = "https://github.com/envy-package-manager/package-specs.git",
    -- envy git-resolve https://github.com/envy-package-manager/package-specs main
    ref = "9bdb0a11cefa3e83418cff37dc68ea755c07a237",
  },
}
```

## See also

- [Pinning & Updating](/guides/pinning)
