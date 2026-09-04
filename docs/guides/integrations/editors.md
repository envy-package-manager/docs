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

```shell-session
$ envy init . bin
Created bin/envy
Created ./envy.lua
Created ./.luarc.json
Updated ./.gitignore

Initialized envy project.
```

```json title=".luarc.json"
{
  "$schema": "https://raw.githubusercontent.com/LuaLS/vscode-lua/master/setting/schema.json",
  "runtime.version": "Lua 5.4",
  "workspace.library": [
    ".envy/cache/envy/0.3.0",
    "~/Library/Caches/envy/envy/0.3.0",
    "~/.cache/envy/envy/0.3.0",
    "${env:USERPROFILE}/AppData/Local/envy/envy/0.3.0"
  ],
  "diagnostics.globals": [
    "envy", "IDENTITY", "PACKAGES", "DEPENDENCIES", "PRODUCTS",
    "FETCH", "STAGE", "BUILD", "INSTALL", "SETUP", "ENVY_IMPORTER"
  ],
  "completion.enable": true
}
```

Four library paths: the [project-local cache tree](/concepts/cache#where-the-root-lives)
first, then one per platform's default cache location, with
`${env:USERPROFILE}/AppData/Local/envy` covering Windows. It is a union rather
than a choice, because `.luarc.json` is committed while the cache root is
per-user state: the same manifest is local for whoever ran `envy cache --local`
and shared for everyone else. Only one path exists on any given machine and the
language server ignores the rest, which is why this file can be committed and
shared. If your project sets `@envy cache-local`, that path replaces the default
`.envy/cache` entry, relative rather than absolute so the file names no machine.

`${env:VAR}` is the language server's own placeholder syntax, so it is expanded
by the server rather than by a shell, and forward slashes are correct on Windows
too. Each path points at `envy/<version>` in the cache, where envy extracts
`envy.lua`, a few hundred lines of
[LuaCATS](https://luals.github.io/wiki/annotations/) annotations covering
`envy.run`, `envy.path`, `envy.commit_fetch`, the phase globals, and the rest of
the API.

Commit `.luarc.json`. It is machine-independent and version-matched to the envy
the project pins.

## Keeping it current

The library paths name an exact envy version, so they go stale when the project
moves. [`sync`](../../reference/cli/sync.md) and
[`deploy`](../../reference/cli/deploy.md) fix them:

```shell-session
$ envy use 0.3.0
$ envy sync
Updated .luarc.json types paths
```

The rewrite removes any `workspace.library` entry that ends in `envy/<semver>`
and appends the current four. Everything else in the file is left alone, so your
own settings and library paths survive:

```json
{
  "workspace.library": [
    "/my/other/lua/lib",
    ".envy/cache/envy/0.3.0",
    "~/Library/Caches/envy/envy/0.3.0",
    "~/.cache/envy/envy/0.3.0",
    "${env:USERPROFILE}/AppData/Local/envy/envy/0.3.0"
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

```shell-session
$ envy init . bin
.luarc.json already exists at ./.luarc.json
To enable envy autocompletion, add the following to workspace.library:
  ".envy/cache/envy/0.3.0"
  "~/Library/Caches/envy/envy/0.3.0"
  "~/.cache/envy/envy/0.3.0"
  "${env:USERPROFILE}/AppData/Local/envy/envy/0.3.0"
```

It prints the same four paths it would have written, so pasting them in gets you
the same result.

## Globals

`diagnostics.globals` is what stops the language server from reporting
`undefined-global` on the names envy assigns meaning to:

| Global | Where |
| --- | --- |
| `envy` | everywhere, the API table |
| `IDENTITY`, `DEPENDENCIES`, `PRODUCTS`, `PLATFORMS` | specs |
| `FETCH`, `STAGE`, `BUILD`, `INSTALL`, `SETUP` | specs, the [phase verbs](/concepts/specs/lifecycle) |
| `OPTIONS`, `USER_MANAGED`, `EXPORTABLE` | specs |
| `PACKAGES`, `DEFAULT_SHELL`, `PACKAGE_DEPOTS` | manifests |
| `ENVY_IMPORTER` | an imported manifest, set by [`envy.import`](/reference/lua-api#envyimportpath) |
| `ENVY_SHELL` | both, the shell constants |

The list `init` writes covers the common ones. Add what your project uses, for
example `BUNDLES` in a manifest with a bundle, or `BUNDLE` and `SPECS` in a
bundle repo:

```json
"diagnostics.globals": [
  "envy", "IDENTITY", "PACKAGES", "BUNDLES", "DEPENDENCIES", "PRODUCTS",
  "FETCH", "STAGE", "BUILD", "INSTALL", "SETUP", "ENVY_IMPORTER"
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
