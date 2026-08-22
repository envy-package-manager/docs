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

Paste the line into your profile and restart. envy maintains the hook file in the
cache, one per supported shell: bash, zsh, fish, and PowerShell. See
[`envy shell`](../../reference/cli/shell.md).

## The contract

Inside a project:

- The project's `@envy bin` directory is prepended to `PATH`.
- `ENVY_PROJECT_ROOT` is set to the manifest's directory.
- The prompt gains a 🦝 marker.

Outside, all three are removed. Switching directly between two projects removes
the first project's bin directory and adds the second's, in one step.

```console
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
coincidence or a reimplementation-by-eye. The three readers of a manifest header,
the hook, the bootstrap script, and envy, deliberately share one rule, so a
directive-shaped comment down inside `PACKAGES` cannot make the hook put one
project's bin directory on `PATH` while envy resolves another's.

## No performance cost

The hook never runs envy. It is shell script all the way down, and it avoids
subshells on purpose: the manifest header is parsed with the shell's own regex
support rather than `head` and `grep`, and results come back through `REPLY`
rather than through `$(...)`, because a fork costs a millisecond or two and a
`cd` should not.

That is why the hook can afford to run on every directory change without anyone
noticing.

## The prompt marker

The 🦝 prefix appears only in a UTF-8 locale. In anything else the hook skips it,
and the enter and leave messages use `--` in place of the em dash.

If your prompt is managed by a theme that rewrites `PROMPT` on every command, the
hook re-applies the marker before each prompt and reorders itself to run last.
Powerlevel10k users get a real segment instead, `prompt_envy`, so the marker can
be placed deliberately rather than prepended.

## Environment variables

| Variable | Effect |
| --- | --- |
| `ENVY_SHELL_HOOK_DISABLE=1` | The hook returns immediately. Nothing is added or removed. |
| `ENVY_SHELL_NO_ENTER_EXIT_ANNOUNCE=1` | No entering and leaving messages. |
| `ENVY_SHELL_NO_ICON=1` | No prompt marker. |

`ENVY_PROJECT_ROOT` is the hook's output rather than its input. Scripts can read
it to find the project without walking the tree themselves.

## Updating

The hook file lives in the cache, and envy rewrites it during self-deploy, so it
follows envy's version without you editing your profile. When a new envy version
ships a new hook, restart your shell to pick it up.

Moving or deleting the cache breaks the `source` line, since that is where the
hook lives. `envy shell` warns about this when you are using a non-default cache
root.

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
