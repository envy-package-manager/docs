---
sidebar_position: 3
title: envy run
---

# `envy run`

One-shot activation. `envy run <command>` runs one command with the project's bin
directory on `PATH` and `ENVY_PROJECT_ROOT` set, then gets out of the way.

It is the third way to reach a project's tools, alongside
[product scripts](./product-scripts.md) and [shell hooks](./shell-hooks.md), and
the only one that needs no prior setup of any kind. Nothing is committed for it,
and nothing is configured in your profile.

## The shape

```bash
envy run make -j
envy run ./scripts/build.sh --release
envy run "$SHELL"
```

Everything after `run` belongs to your command. envy stops parsing there, so
flags that look like envy's are passed through:

```bash
envy run cmake --version        # --version goes to cmake
envy --verbose run cmake --build build   # global flags go before `run`
```

Your command's exit status becomes envy's, with no translation. On POSIX envy
`exec`s the child, so there is not even an extra process in the tree.

## What the child gets

| | |
| --- | --- |
| `PATH` | The manifest's `@envy bin` directory, prepended. |
| `ENVY_PROJECT_ROOT` | The governing manifest's directory. |
| envy version | The one the manifest pins, because `run` re-execs first. |

That is deliberately small. `run` installs nothing itself and deploys nothing.
What it does is make `envy` callable by name and tell the child where the project
is, so the child can resolve what it needs:

```bash title="scripts/build.sh"
#!/usr/bin/env bash
set -euo pipefail
CMAKE="$(envy product cmake)"
NINJA="$(envy product ninja)"
"$CMAKE" -G Ninja -DCMAKE_MAKE_PROGRAM="$NINJA" -S "$ENVY_PROJECT_ROOT" -B build
"$CMAKE" --build build
```

```bash
envy run ./scripts/build.sh
```

Those `envy product` calls install what they name, on demand. A project can
therefore deploy no wrappers at all and still have a working entry point, which
is why `run` is the natural fit for projects that leave
`@envy deploy` off.

If a project *does* deploy wrappers, `run` makes them visible too, since they
live in the same bin directory. `envy run make -j` then lets a Makefile call
`cmake` by name.

## Anchoring

Which project you get is [discovery](/concepts/projects#manifest-discovery), with
one addition: if the first argument is an existing file, discovery starts from
that file's directory rather than from your working directory.

```bash
cd ~
envy run ~/work/firmware/scripts/build.sh    # firmware's project, not $HOME's
```

Use `--` to be explicit, which also handles the case where the script is not the
first argument:

```bash
envy run -- ./scripts/build.sh --release
```

If a bare `envy run` cannot find a manifest, the error suggests `--` for exactly
this reason.

## Where it fits

`run` is the right answer wherever a login shell and its hooks do not exist:

- **CI steps.** One line, no setup action, and the exit code propagates.
- **Makefiles and build scripts.** `$(shell envy product cmake)` also works, but
  `envy run` covers a whole script at once.
- **Git hooks.** A `pre-commit` that runs the project's formatter.
- **Editor task runners**, which usually spawn a non-login shell.

```bash
envy run ./scripts/test.sh || exit $?
```

## Requirements and failure modes

- `@envy bin` must be present, and the directory must exist. Both are errors
  rather than warnings, since `run` has nothing to put on `PATH` otherwise.
- Windows has no `execvp`, so envy spawns the child, waits, and forwards the
  code. Observable behavior is identical, with one extra process while it runs.

## See also

- [`envy run`](../../reference/cli/run.md) for the full CLI reference.
- [Product Scripts](./product-scripts.md) and [Shell Hooks](./shell-hooks.md) for the other two activation paths.
- [`envy product`](../../reference/cli/product.md) for what your scripts call.
