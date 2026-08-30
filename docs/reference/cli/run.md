---
sidebar_position: 6
title: envy run
---

# `envy run`

Run your own scripts and let them ask envy for what they need. This is the
activation mode for projects that deploy no product wrapper scripts and rely on
no `PATH` setup. Nothing is committed to the bin directory except the `envy`
bootstrap script, and every entry point is `envy run <your thing>`.

`run` gives the child process three things:

- The project's bin directory on `PATH`, so `envy` is callable by name from
  inside your script, however deeply nested.
- `ENVY_PROJECT_ROOT`, pointing at the manifest's directory, so a script never
  has to compute where the project is.
- The envy version the manifest pins, because `run` re-execs first.

Your script does the resolving from there: `envy product cmake` for a path,
`envy package <identity>` for a tree. Those calls install what they name, on
demand. The tool chain is described in one place, the manifest, and reached one
way. There are no generated wrappers to commit, no `PATH` ordering to reason
about, and nothing left behind in your shell.

If a project does deploy wrappers, `run` makes those visible too, because they
live in the same bin directory. That is a convenience rather than the purpose.

Everything after `run` belongs to your command, and your command's exit status
becomes envy's. On POSIX envy `exec`s the child, so there is no extra process in
the tree. On Windows it spawns, waits, and forwards the code.

## Usage

```
envy run <command> [args...]
envy run -- <script-path> [args...]
```

## Behavior

| Aspect | Detail |
| --- | --- |
| `PATH` | The manifest's `@envy bin` directory, prepended. A missing `@envy bin`, or a bin directory that does not exist, is an error. |
| `ENVY_PROJECT_ROOT` | The governing manifest's directory. |
| Discovery | Anchored at the first argument's directory if that argument is an existing file, otherwise at the current directory. `--` forces the anchor to the path that follows it. A global `--project <dir>` outranks both. |
| Flags | None of its own. `envy run --verbose make` passes `--verbose` to `make`. [Global flags](./index.md#global-flags) go before `run`. |
| Tracing | `run` emits no `manifest_resolved` event: it replaces its own process with the child before the trace drains. What it resolved is visible in the child's `PATH`. |
| Installs | Nothing directly. Whatever the child asks envy for is installed then. |
| Exit code | Whatever the child returned. |

## Examples

### To drive a project that deploys no wrappers

```lua title="envy.lua"
-- @envy bin "bin"
-- no '@envy deploy' directive, so nothing is generated into bin/
```

```bash title="scripts/build.sh"
#!/usr/bin/env bash
set -euo pipefail
CMAKE="$(envy product cmake)"          # envy is on PATH; project root is known
NINJA="$(envy product ninja)"
"$CMAKE" -G Ninja -DCMAKE_MAKE_PROGRAM="$NINJA" -S "$ENVY_PROJECT_ROOT" -B build
"$CMAKE" --build build
```

```bash
envy run ./scripts/build.sh
```

The only committed artifact is `bin/envy`. Tools install the first time the
script asks for them, and the script behaves the same for every developer and in
CI.

### To let a build system resolve its own tools

```makefile title="Makefile"
CC  := $(shell envy product arm-none-eabi-gcc)
GEN := $(shell envy product protoc)
```

```bash
envy run make -j
```

`PATH` and `ENVY_PROJECT_ROOT` are inherited by the whole process subtree, so
sub-makes and anything they shell out to can call `envy` too.

### To run a repo script that must resolve its own project

```bash
envy run -- ./scripts/build.sh --release
envy run -- ~/work/firmware/scripts/flash.sh
```

`--` names the script explicitly, and discovery starts from the script's
directory. Use it when the script lives in a different project than the shell
you are calling from. The error message points at this if a bare `envy run`
fails to find a manifest.

### To invoke a tool directly, without writing a script

```bash
envy run "$(envy product python3)" tools/codegen.py --out generated/
```

Explicit, and it works with no wrappers deployed. If the project does deploy
them, the shorter `envy run python3 tools/codegen.py` finds the wrapper on
`PATH`.

### To pass flags that would otherwise look like envy's

```bash
envy run cmake --version         # --version goes to cmake
envy --verbose run cmake --build build
```

### To run the same thing on Windows

```powershell
bin\envy.bat run .\scripts\build.ps1
```

envy has no `execvp` there, so it spawns the child, waits, and forwards its exit
code. The observable behavior is identical, with one extra process in the tree
while it runs.

### To get an interactive shell with the project active

```bash
envy run "$SHELL"
```

A subshell where `envy` resolves to the pinned version and the project root is
already set. Exit it and your environment is untouched. The persistent
alternative is [shell integration](/getting-started/shell-integration).

### To propagate exit codes in CI

```bash
envy run ./scripts/test.sh || exit $?
```

The child's status passes straight through, so no `if` wrapper is needed to
avoid swallowing failures.

## See also

- [`envy run` (concepts)](/concepts/environment/envy-run) for how it compares to wrappers and hooks.
- [`envy product`](./product.md) for what your scripts call to resolve a tool.
- [Product Scripts](/concepts/environment/product-scripts) for the alternative you are opting out of.
- [Shell Integration](/getting-started/shell-integration) for the other alternative.
