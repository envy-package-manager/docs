---
sidebar_position: 3
title: Editor Setup
---

# Editor Setup

> **Placeholder content.** Outline for review. Verify against sources.

Get completion, hover docs, and diagnostics while editing manifests and specs.

Will cover:

- What `envy init` and `envy sync` maintain. A `.luarc.json` configured for the
  Lua language server, with envy's typed API definitions on the workspace library
  path. The definitions are version-matched, from the cache.
- The merge behavior. envy appends to `.luarc.json` without destroying your own
  settings.
- Recognized globals such as `IDENTITY`, `PACKAGES`, and `FETCH`, and why your
  editor stops flagging them.
- Pointers for enabling lua-language-server in VS Code, Neovim, and JetBrains
  editors.
