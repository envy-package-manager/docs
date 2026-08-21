---
sidebar_position: 5
title: BUILD
---

# BUILD

> **Placeholder content.** Outline for review; verify against sources.

Transform the staged tree — compile, configure, generate. Most prebuilt
packages skip it entirely.

Will cover — the three shapes:

| Shape | Meaning |
| --- | --- |
| omitted | No build step. The norm for prebuilt binaries. |
| string | A shell script run in the staging directory. |
| function `BUILD(install_dir, stage_dir, fetch_dir, tmp_dir, opts)` | Programmatic build. **If it returns a string, that string runs as a shell script** — compute your script, hand it back. |

- The `envy.template` idiom for readable generated scripts:

```lua
BUILD = function(install_dir, stage_dir, fetch_dir, tmp_dir, opts)
  return envy.template([[
    ./configure --prefix={{prefix}}
    make -j
  ]], { prefix = install_dir })
end
```

- Which shell runs your strings, and how to change it project-wide
  ([Shells & Scripts](./shells.md)).
- Using dependency products inside BUILD (`envy.product("cmake")`) — and why
  the dependency must be declared ([Dependencies](/concepts/dependencies)).
- Conditionally defining BUILD at all (source build on one platform, prebuilt
  on the others).
