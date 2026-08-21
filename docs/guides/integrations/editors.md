---
sidebar_position: 3
title: Editor Setup
---

# Editor Setup

> **Placeholder content.** Outline for review; verify against sources.

Get completion, hover docs, and diagnostics while editing manifests and specs.

Will cover:

- What `envy init` / `envy sync` maintain for you: a `.luarc.json` configured
  for the Lua language server, with envy's typed API definitions
  (version-matched, from the cache) on the workspace library path.
- The merge behavior: envy appends to `.luarc.json` non-destructively — your
  own settings survive.
- Recognized globals (`IDENTITY`, `PACKAGES`, `FETCH`, ...) and why your
  editor stops flagging them.
- VS Code / Neovim / JetBrains pointers for enabling lua-language-server.
