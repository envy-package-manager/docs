---
sidebar_position: 2
title: Getting Started
---

# Getting Started

> **Placeholder content.** Verify against the envy sources before publishing.

envy has no install step of its own. You bootstrap once per project and commit
the result.

## New project

```bash
# 1. Get an envy binary, any way you like. This copy is temporary.
curl -fsSL -o /tmp/envy \
  https://github.com/envy-package-manager/envy/releases/latest/download/envy-darwin-arm64
chmod +x /tmp/envy

# 2. Initialize.
mkdir my-project && cd my-project
/tmp/envy init . ./tools

# 3. Use the committed bootstrap script from here on.
./tools/envy sync

# 4. Throw the temp binary away.
rm /tmp/envy
```

`envy init <project-dir> <bin-dir>` writes:

| Path                | Purpose                                              |
| ------------------- | ---------------------------------------------------- |
| `envy.lua`          | Manifest, including the pinned `@envy version`.       |
| `tools/envy`        | POSIX bootstrap script. Commit it.                    |
| `tools/envy.bat`    | Windows bootstrap script. Commit it too.              |
| `.luarc.json`       | IDE config for editing specs.                         |

## Existing project

```bash
git clone https://github.com/example/my-project && cd my-project
./tools/envy sync
```

The bootstrap script reads `@envy version` from `envy.lua`, checks the cache,
downloads that exact envy build from GitHub releases if it is missing, and
`exec`s it. No global install, no version drift.

## Shell integration

Optional hooks manage `PATH` and `ENVY_PROJECT_ROOT` as you `cd` between
projects. They need no envy binary at shell startup.

```bash
envy shell bash        # add the printed line to ~/.bashrc
envy shell zsh         # ~/.zshrc
envy shell fish        # ~/.config/fish/config.fish
envy shell powershell  # $PROFILE
```

`envy shell` only prints the `source` line; the hook files themselves live at
`$CACHE/shell/hook.{bash,zsh,fish,ps1}` and are written during self-deploy.

Opt out with `ENVY_SHELL_HOOK_DISABLE=1`.

## Cache location

| Platform | Default                            |
| -------- | ---------------------------------- |
| macOS    | `~/Library/Caches/envy`            |
| Linux    | `${XDG_CACHE_HOME:-~/.cache}/envy` |
| Windows  | `%LOCALAPPDATA%\envy`              |

Precedence: `--cache-root` > `ENVY_CACHE_ROOT` > `@envy cache-posix` /
`@envy cache-win` > platform default. The cache is disposable — delete it and
the next `sync` rebuilds it.
