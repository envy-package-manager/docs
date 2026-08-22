---
sidebar_position: 3
title: Shell Integration
---

# Shell Integration

Optional. Teach your shell to put each project's bin directory on `PATH` as you
`cd` around, so `cmake` means the project's cmake without a path or a wrapper
prefix.

## Setup

Ask envy for the line, then paste it into your profile:

```console
$ envy shell zsh
Add this line to ~/.zshrc:

  source "$HOME/Library/Caches/envy/shell/hook.zsh"

Then restart your shell or run the command directly.
```

Supported shells and their profiles:

| Shell | Profile |
| --- | --- |
| `bash` | `~/.bashrc` |
| `zsh` | `~/.zshrc` |
| `fish` | `~/.config/fish/config.fish` |
| `powershell` | `$PROFILE` |

The output is instructions on stderr, not a bare line, so copy the line rather
than redirecting the command into your profile.

envy maintains the hook file itself, in the cache. Any earlier envy command has
already created it. If it is missing, `envy shell` says so and tells you to run
any envy command first.

## What it does

```console
$ cd ~/work/firmware
envy: entering firmware — tools added to PATH
$ which cmake
/Users/you/work/firmware/bin/cmake
$ echo $ENVY_PROJECT_ROOT
/Users/you/work/firmware
$ cd ~/work/webapp
envy: leaving firmware — PATH restored
envy: entering webapp — tools added to PATH
$ cd ~
envy: leaving webapp — PATH restored
```

On every directory change the hook finds the governing `envy.lua`, prepends its
bin directory to `PATH`, sets `ENVY_PROJECT_ROOT`, and adds a 🦝 marker to the
prompt. Leaving undoes all of it. Switching between projects does both in one
step.

The messages go to stderr, so a piped command is unaffected.

## It costs nothing

The hook is pure shell. envy is never invoked at shell startup or on `cd`, and
the hook avoids subshells deliberately, so entering a directory does not fork
anything.

It also resolves manifests by the same rules envy itself uses, so the tools on
your `PATH` always belong to the project envy would act on. See
[Shell Hooks](/concepts/environment/shell-hooks).

## Turning parts off

| Variable | Effect |
| --- | --- |
| `ENVY_SHELL_HOOK_DISABLE=1` | Disable the hook entirely. |
| `ENVY_SHELL_NO_ENTER_EXIT_ANNOUNCE=1` | Keep the `PATH` management, drop the messages. |
| `ENVY_SHELL_NO_ICON=1` | Keep everything, drop the prompt marker. |

The marker also stays off outside a UTF-8 locale, where the enter and leave
messages use `--` in place of the em dash.

Powerlevel10k users get a `prompt_envy` segment instead of a prepended marker, so
it can be positioned deliberately.

## Updating

envy rewrites the hook file during self-deploy, so it tracks envy's version
without you touching your profile. Restart your shell when a new envy version
ships a new hook.

The `source` line points into the cache, so moving or deleting the cache breaks
it. `envy shell` warns about this when you are on a non-default cache root.

## When to skip it

CI and scripts should not depend on an interactive shell having been configured.
Use `./bin/<tool>` or [`envy run`](../reference/cli/run.md) there. Hooks are a
convenience for humans at a terminal.

## See also

- [`envy shell`](../reference/cli/shell.md) for the command.
- [Shell Hooks](/concepts/environment/shell-hooks) for the mechanism and its guarantees.
- [First Steps](./first-steps.md) for the other two activation paths.
