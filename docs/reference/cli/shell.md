---
sidebar_position: 9
title: envy shell
---

# `envy shell`

Print the line to add to your shell profile to enable
[shell hooks](/concepts/environment/shell-hooks), which manage `PATH` per
project as you `cd` around.

This command does not create the hook file. envy maintains it in the cache during
self-deploy, so any earlier envy command has already put it there. `shell` finds
the one for your shell and prints how to source it. The hook is
pure shell: no envy process runs on `cd`, and it updates itself across envy
versions.

## Usage

```
envy shell <bash|zsh|fish|powershell>
```

## Arguments

| Argument | Meaning |
| --- | --- |
| `shell` | One of `bash`, `zsh`, `fish`, `powershell`. Required. Anything else is rejected with the list. |

Output is instructions on stderr, naming the profile file and the line to add.
It is not a bare line for redirection, so copy it rather than appending the
command's output to your profile. The path uses `$HOME`, or PowerShell's
`${env:...}` syntax, so it stays portable across machines.

If the hook file is missing, `shell` says so and tells you to run any envy
command first, which triggers self-deploy.

## Examples

### To enable automatic project activation in your shell

```bash
envy shell zsh
# Add this line to ~/.zshrc:
#
#   source "$HOME/Library/Caches/envy/shell/hook.zsh"
#
# Then restart your shell or run the command directly.
```

Paste that line into `~/.zshrc`, restart, and `cd` into any envy project. Its
tools are on `PATH`, with a 🦝 marker in the prompt. `cd` out and they are gone.

### To set up the other supported shells

```bash
envy shell bash          # ~/.bashrc
envy shell fish          # ~/.config/fish/config.fish
```

On Windows, PowerShell gets a dot-source line for `$PROFILE`, pointing at the
`.ps1` hook in `%LOCALAPPDATA%\envy`:

```powershell
envy shell powershell
# Add this line to $PROFILE:
#
#   . "${env:USERPROFILE}/AppData/Local/envy/shell/hook.ps1"
#
# Then restart your shell or run the command directly.
```

The `${env:...}` form is native PowerShell syntax, so the line stays valid on
any machine regardless of where the profile directory lives.

### To find the hook path when your cache is not in the default place

```bash
envy --cache-root /opt/envy-cache shell zsh
```

The printed path points into whichever cache root is in effect. envy also warns
that moving or deleting that cache breaks shell integration, because the hook
lives inside it.

## See also

- [Shell Integration](/getting-started/shell-integration) for setup, the prompt marker, and the opt-out variables.
- [Shell Hooks](/concepts/environment/shell-hooks) for what the hook does on `cd`.
- [`envy run`](./run.md) for one-shot activation with no profile edit.
