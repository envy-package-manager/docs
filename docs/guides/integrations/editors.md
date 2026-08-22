---
sidebar_position: 3
title: Editor Setup
---

# Editor Setup

Manifests and specs are Lua, so any editor with a
[lua-language-server](https://luals.github.io/) client gives you completion,
hover documentation, and diagnostics on envy's API. envy ships the type
definitions and writes the configuration that points the server at them.

## What envy sets up

[`envy init`](../../reference/cli/init.md) creates `.luarc.json` next to the
manifest:

```console
$ envy init . bin
Created bin/envy
Created ./envy.lua
Created ./.luarc.json
Initialized envy project.
```

```json title=".luarc.json"
{
  "$schema": "https://raw.githubusercontent.com/LuaLS/vscode-lua/master/setting/schema.json",
  "runtime.version": "Lua 5.4",
  "workspace.library": [
    "~/Library/Caches/envy/envy/0.1.10",
    "~/.cache/envy/envy/0.1.10",
    "${env:USERPROFILE}/AppData/Local/envy/envy/0.1.10"
  ],
  "diagnostics.globals": [
    "envy", "IDENTITY", "PACKAGES", "DEPENDENCIES", "PRODUCTS",
    "FETCH", "STAGE", "BUILD", "INSTALL", "SETUP"
  ],
  "completion.enable": true
}
```

Three library paths, one per platform's default cache location. Only one exists
on any given machine and the language server ignores the rest, which is why this
file can be committed and shared. Each points at `envy/<version>` in the cache,
where envy extracts `envy.lua`, a few hundred lines of
[LuaCATS](https://luals.github.io/wiki/annotations/) annotations covering
`envy.run`, `envy.path`, `envy.commit_fetch`, the phase globals, and the rest of
the API.

Commit `.luarc.json`. It is machine-independent and version-matched to the envy
the project pins.

## Keeping it current

The library paths name an exact envy version, so they go stale when the project
moves. [`sync`](../../reference/cli/sync.md) and
[`deploy`](../../reference/cli/deploy.md) fix them:

```console
$ envy use 0.1.10
$ envy sync
Updated .luarc.json types paths
```

The rewrite removes any `workspace.library` entry that ends in `envy/<semver>`
and appends the current three. Everything else in the file is left alone, so your
own settings and library paths survive:

```json
{
  "workspace.library": [
    "/my/other/lua/lib",
    "~/Library/Caches/envy/envy/0.1.10",
    "~/.cache/envy/envy/0.1.10",
    "${env:USERPROFILE}/AppData/Local/envy/envy/0.1.10"
  ],
  "custom.setting": "preserved"
}
```

Two opt-outs, both by omission:

- Delete `.luarc.json` and envy stops creating or touching it. `sync` and
  `deploy` only update a file that already exists.
- Remove the `workspace.library` key and the rewrite skips the file entirely.

`init` will not overwrite an existing `.luarc.json` either. It prints the paths
instead:

```console
$ envy init . bin
.luarc.json already exists at ./.luarc.json
To enable envy autocompletion, add the following to workspace.library:
  "~/Library/Caches/envy/envy/0.1.10"
  "~/.cache/envy/envy/0.1.10"
  "${env:USERPROFILE}/AppData/Local/envy/envy/0.1.10"
```

If your project sets a custom cache root with `@envy cache-posix` or
`@envy cache-win`, the generated paths follow it.

## Globals

`diagnostics.globals` is what stops the language server from reporting
`undefined-global` on the names envy assigns meaning to:

| Global | Where |
| --- | --- |
| `envy` | everywhere, the API table |
| `IDENTITY`, `DEPENDENCIES`, `PRODUCTS`, `PLATFORMS` | specs |
| `FETCH`, `STAGE`, `BUILD`, `INSTALL`, `SETUP` | specs, the [phase verbs](/concepts/specs/lifecycle) |
| `OPTIONS`, `USER_MANAGED`, `EXPORTABLE` | specs |
| `PACKAGES`, `DEFAULT_SHELL` | manifests |
| `ENVY_SHELL` | both, the shell constants |

The list `init` writes covers the common ones. Add what your project uses, for
example `BUNDLES` in a manifest with a bundle, or `BUNDLE` and `SPECS` in a
bundle repo:

```json
"diagnostics.globals": [
  "envy", "IDENTITY", "PACKAGES", "BUNDLES", "DEPENDENCIES", "PRODUCTS",
  "FETCH", "STAGE", "BUILD", "INSTALL", "SETUP"
]
```

Nothing breaks without them. The names are still resolved at run time by envy,
and the only cost is a warning squiggle.

## Per editor

The language server reads `.luarc.json` from the workspace root, so open the
directory holding the manifest.

- **VS Code**: install the
  [Lua extension](https://marketplace.visualstudio.com/items?itemName=sumneko.lua).
  It picks up `.luarc.json` with no further configuration.
- **Neovim**: enable `lua_ls`, through `nvim-lspconfig` or `vim.lsp.config` on
  0.11 and later. It finds `.luarc.json` by root marker.
- **Zed**: Lua support is built in and uses the same server.
- **Anything else**: run `lua-language-server` over the workspace. The
  configuration is in the file, not in the editor.

In a [monorepo](../monorepos.md), each manifest directory gets its own
`.luarc.json` from `init`, but the language server only reads the one at the
workspace root. Open a component directory directly when editing its specs, or
keep the root file authoritative and let the others be redundant.

## See also

- [`envy init`](../../reference/cli/init.md)
- [Lua API](../../reference/lua-api.md) for the same API in prose
- [Writing a Spec](../writing-a-spec.md)
