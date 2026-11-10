---
sidebar_position: 2
title: Shell Hooks
---

# Shell Hooks

The convenience layer. Your shell activates envy projects as you `cd` into them
and restores your own environment as you leave.

This is optional. [Product scripts](./product-scripts.md) already work with no
shell setup, and [`envy run`](./envy-run.md) covers one-shot activation. Hooks
are for the case where you want `cmake` to mean the project's cmake without
typing a path, and `cargo` to find the project's `CARGO_HOME`.

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
- Every installed package's [`ENV`](./package-env.md) is applied (envy 0.6.0+).
- The prompt gains a 🦝 marker.

Outside, every variable the project changed goes back to what it was, byte for
byte, and the marker goes away. Switching directly between two projects leaves
the first and enters the second in one step.

```shell-session
$ cd ~/work/firmware
envy: entering firmware — 3 variables set
$ which cmake
/Users/you/work/firmware/bin/cmake
$ cd ~/work/webapp
envy: leaving firmware — environment restored
envy: entering webapp — 2 variables set
$ cd ~
envy: leaving webapp — environment restored
```

Those messages go to stderr, so they never contaminate a piped command.

### How it activates

When you enter a project, the hook runs that project's own launcher,
`<bin>/envy activate <shell>`, and evaluates what it prints. When you leave the
last project, it runs `envy deactivate <shell>` with the binary that activated.
Both are [CLI commands](../../reference/cli/activate.md) you can also run by
hand. The launcher re-execs into the envy the project pins, so each project is
activated by its own version.

`envy install` and `envy sync` mark the project when they finish. At the next
prompt, every shell activated in that project refreshes and picks up what was
installed:

```text
envy: refreshed proj — 4 variables set
```

Activation skips packages that are not installed yet, with a warning to run
`envy install`. It never installs anything itself.

A project pinned to an envy older than 0.6.0 has no `activate` command. There
the hook falls back to what it did before: the bin directory on `PATH` and
`ENVY_PROJECT_ROOT`, with the messages `tools added to PATH` and `PATH
restored`. A bin directory without an `envy` launcher in it gets the same
fallback.

### Nested shells

Activation lives in exported variables, so a subshell, a tmux pane, or an editor
launched from an activated shell inherits it without activating again. The
variables are listed under
[Activation state](../../reference/environment-variables.md#activation-state).

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

## What it costs

Shell startup outside a project runs no envy. Neither does a `cd` between
directories of the same project. The hook finds the project without shelling out
to `head` or `grep`. bash, zsh and PowerShell each parse the manifest header with
their own regex support, over one pass of the file. The zsh hook goes furthest
and returns through `REPLY`, so a `cd` inside a project forks nothing at all.
bash uses a handful of `$(...)` substitutions, and fish calls `sed` and
`realpath`.

Entering or leaving a project runs one envy process. The first time you enter a
project whose pinned envy is not in the cache yet, the launcher downloads it.

The check for a finished `envy install` runs at every prompt. It is one builtin
`read` of a small file, with no fork.

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
| `ENVY_SHELL_HOOK_DISABLE=1` | The hook returns immediately. Nothing is activated or restored. |
| `ENVY_SHELL_NO_ENTER_EXIT_ANNOUNCE=1` | No entering, leaving, or refreshed messages. |
| `ENVY_SHELL_NO_ICON=1` | No prompt marker. |

`ENVY_PROJECT_ROOT` is the hook's output rather than its input. Scripts can read
it to find the project without walking the tree themselves.

Restoring on leave is wholesale. A variable activation touched returns to its
value from before you entered, including any edit you made to it inside the
project. envy never applies activation to its own builds, so `envy install` from
an activated shell builds the same thing as from a plain one. See
[Package Environment](./package-env.md#activation-never-reaches-a-build).

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

The hook file lives in the user-wide cache, and envy rewrites it when its
contents no longer match the copy the running binary carries. Restart your shell
to pick up a new one. Nothing in your profile changes.

Each hook file carries a stamp naming its writer and a digest of its own text:

```text
_ENVY_HOOK_STAMP=0.3.2:8d9dde49c42c
```

Every envy command compares that digest to its own copy. A hook it wrote itself
is repaired whenever it differs, so a fix to a hook ships with the binary that
carries it. A byte-identical hook from another version is left labeled as it is,
and a hook a *newer* envy wrote is never overwritten. That last rule is what
keeps a version-pinned project and a newer envy from rewriting each other's
hooks on every command, since all versions share one `shell/` directory.

Before envy 0.3.2 the stamp was a hand-bumped integer, so a hook change that
shipped without a bump never reached a shell that already had a hook.

A refresh announces itself once, naming every shell whose hook changed, because
one restart covers all of them:

```text
Shell hooks updated (bash, zsh, fish) — restart your shell
```

A hook written for the first time is not an update and says nothing.

Moving or deleting that cache breaks the `source` line, since that is where the
hook lives. `envy shell` warns about this when you are on a `--cache-root` or
`ENVY_CACHE_ROOT` override. To force a refresh, delete `<user-wide
cache>/shell/` and run an envy command in a project that is not on a local tree.

## When not to use hooks

- **In CI.** A job should call `./bin/<tool>` or `envy run` explicitly, so the
  build does not depend on a login shell having been configured. Use
  `envy run --activate` where a tool needs its package's `ENV`.
- **In scripts.** Same reason. A script that relies on an interactive shell's
  `PATH` works on your machine and nowhere else.
- **In editors and task runners.** Many spawn a non-login shell.
  [`envy run`](./envy-run.md) is deterministic there.

## See also

- [`envy shell`](../../reference/cli/shell.md) for the command and its output.
- [`envy activate`](../../reference/cli/activate.md) and [`envy deactivate`](../../reference/cli/deactivate.md) for what the hook runs.
- [Package Environment](./package-env.md) for `ENV`.
- [Shell Integration](../../getting-started/shell-integration.md) for the setup walkthrough.
- [Product Scripts](./product-scripts.md) for the mechanism hooks put on `PATH`.
