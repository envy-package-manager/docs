---
sidebar_position: 2
title: Shell Hooks
---

# Shell Hooks

The convenience layer. Your shell notices envy projects as you `cd`, and manages
`PATH` for you.

This is optional. [Product scripts](./product-scripts.md) already work with no
shell setup, and [`envy run`](./envy-run.md) covers one-shot activation. Hooks
are for the case where you want `cmake` to mean the project's cmake without
typing a path.

## Setup

```bash
envy shell zsh
# Add this line to ~/.zshrc:
#
#   source "$HOME/Library/Caches/envy/shell/hook.zsh"
#
# Then restart your shell or run the command directly.
```

Paste the line into your profile and restart. envy maintains the hook file in
the user-wide cache, one per supported shell: bash, zsh, fish, and PowerShell.
See [`envy shell`](../../reference/cli/shell.md).

## The contract

Inside a project:

- The project's `@envy bin` directory is prepended to `PATH`.
- `ENVY_PROJECT_ROOT` is set to the manifest's directory.
- The prompt gains a 🦝 marker.

Outside, all three are removed. Switching directly between two projects removes
the first project's bin directory and adds the second's, in one step.

```shell-session
$ cd ~/work/firmware
envy: entering firmware — tools added to PATH
$ which cmake
/Users/you/work/firmware/bin/cmake
$ cd ~/work/webapp
envy: leaving firmware — PATH restored
envy: entering webapp — tools added to PATH
$ cd ~
envy: leaving webapp — PATH restored
```

Those messages go to stderr, so they never contaminate a piped command.

## It agrees with envy

The hook applies the same [discovery](/concepts/projects#manifest-discovery)
rules envy itself uses. It walks up from the current directory, skips manifests
marked `@envy root "false"`, and stops at the first root manifest.

It also applies the same header grammar: directives are comments before the first
line of Lua code, and the last occurrence of a key wins. That is not a
coincidence or a reimplementation-by-eye. A manifest header has three readers: the hook, the
bootstrap script, and envy. They share one rule. A directive-shaped comment down
inside `PACKAGES` therefore cannot make the hook put one project's bin
directory on `PATH` while envy resolves another's.

## Almost no performance cost

The hook never runs envy, and it never shells out to `head` or `grep` to read a
manifest header. bash, zsh and PowerShell each parse it with their own regex
support, over one pass of the file. The zsh hook goes furthest and returns
through `REPLY`, so a `cd` forks nothing at all. bash uses a handful of `$(...)`
substitutions, and fish calls `sed` and `realpath`. A fork costs a millisecond
or two either way.

So the hook can run on every directory change without anyone noticing.

## The prompt marker

The 🦝 prefix appears only where the terminal can render it: a UTF-8 locale on
bash, zsh and fish, or a UTF-8 locale *or* console output encoding under
PowerShell. In anything else the hook skips the marker, and the enter and leave
messages use `--` in place of the em dash.

PowerShell says so once per session rather than leaving you to guess, because
that is the case with something to do about it:

```text
envy: raccoon icon hidden -- console is not UTF-8. Add [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new() above the hook line in your profile, or set ENVY_SHELL_NO_ICON=1 to silence.
```

The nudge fires on the first project you enter and not again, and never at all
when `ENVY_SHELL_NO_ICON=1` says you did not want the marker. The PowerShell
hook re-checks the encoding on every prompt, so flipping it takes effect without
re-sourcing anything.

If your prompt is managed by a theme that rewrites `PROMPT` on every command, the
hook re-applies the marker before each prompt and reorders itself to run last.
Powerlevel10k users get a real segment instead, `prompt_envy`, so the marker can
be placed anywhere rather than prepended.

## Environment variables

| Variable | Effect |
| --- | --- |
| `ENVY_SHELL_HOOK_DISABLE=1` | The hook returns immediately. Nothing is added or removed. |
| `ENVY_SHELL_NO_ENTER_EXIT_ANNOUNCE=1` | No entering and leaving messages. |
| `ENVY_SHELL_NO_ICON=1` | No prompt marker. |

`ENVY_PROJECT_ROOT` is the hook's output rather than its input. Scripts can read
it to find the project without walking the tree themselves.

## Hooks are a user-wide feature

Your profile sources one path for every directory the shell ever visits, so no
per-project setting moves it. The hook root is `--cache-root` or
`ENVY_CACHE_ROOT` if set, otherwise the platform default. It is never a
project's own cache tree.

A project on a local cache tree (`@envy cache-local`, or
[`envy cache --local`](../../reference/cli/cache.md)) therefore does not merely
put its hooks somewhere else. It writes **no** hooks at all. A copy inside the
project would never be the one your shell loads, and `rm -rf` on the build
directory would take it. Writing to the user-wide tree instead would break the
one promise a local cache makes, which is that running the project touches
nothing outside it.

So if every project you have is local, you have no hooks, and `envy shell` says
so rather than suggesting a command that cannot produce them. Run any envy
command in a project on the user-wide cache, or set `ENVY_CACHE_ROOT`.

## Updating

The hook file lives in the user-wide cache, and envy rewrites it during
self-deploy, so it follows envy's version without you editing your profile. When
a new envy version ships a new hook, restart your shell to pick it up.

Moving or deleting that cache breaks the `source` line, since that is where the
hook lives. `envy shell` warns about this when you are on a `--cache-root` or
`ENVY_CACHE_ROOT` override. To force a refresh, delete `<user-wide
cache>/shell/` and run an envy command in a project that is not on a local tree.

## When not to use hooks

- **In CI.** A job should call `./bin/<tool>` or `envy run` explicitly, so the
  build does not depend on a login shell having been configured.
- **In scripts.** Same reason. A script that relies on an interactive shell's
  `PATH` works on your machine and nowhere else.
- **In editors and task runners.** Many spawn a non-login shell.
  [`envy run`](./envy-run.md) is deterministic there.

## See also

- [`envy shell`](../../reference/cli/shell.md) for the command and its output.
- [Shell Integration](../../getting-started/shell-integration.md) for the setup walkthrough.
- [Product Scripts](./product-scripts.md) for the mechanism hooks put on `PATH`.
