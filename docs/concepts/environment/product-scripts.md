---
sidebar_position: 1
title: Product Scripts
---

# Product Scripts

The default way to reach a project's tools. `envy sync` deploys one small
wrapper script per executable [product](/concepts/specs/products) into the
project's bin directory, so `./bin/cmake` runs the cmake the manifest pins.

A wrapper is four lines, and it resolves the product when called rather than
when it was written:

```bash title="bin/cmake"
#!/usr/bin/env bash
# envy-managed schema "1"
SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
exec "$("$SCRIPT_DIR/envy" product "cmake")" "$@"
```

Because resolution happens at call time, wrappers never go stale. Change a
version in the manifest, run `sync`, and the same wrapper runs the new tool. The
first call on a fresh machine installs the package.

Deployment needs `@envy deploy "true"` in the manifest header, and `@envy bin`
names the directory. `--platform posix|windows|all` picks which flavors get
written.

## Commit the bin directory

The expected workflow is to check the whole bin directory into the repo:

| File | Written by | Commit |
| --- | --- | --- |
| `bin/envy` | `envy init`, restamped by `sync` and `deploy` | yes |
| `bin/envy.bat` | same, for Windows | yes |
| `bin/cmake`, `bin/ctest`, `bin/python3`, ... | `sync` and `deploy`, one per `script` product | yes |
| `bin/cmake.bat`, ... | same, under `--platform windows` or `all` | yes |

That is the whole point of the design. Someone clones the repo and runs
`./bin/cmake --version` with nothing installed. The wrapper calls `bin/envy`.
That downloads the pinned envy, which installs cmake, which runs. There is no
bootstrap sequence to document and no setup step to forget.

A wide toolchain produces a lot of these files. A firmware project with a
compiler, a debugger suite, Python, and a formatter set can commit a hundred
wrappers. They are small and they are stable text. A diff over them reads as a
summary of what the project's tool surface gained or lost.

### The Windows twin

Each wrapper has a `.bat` counterpart that does the same job through `cmd`:

```bat title="bin\cmake.bat"
@echo off
rem envy-managed schema "1"
for /f "delims=" %%i in ('call "%~dp0envy.bat" product "cmake"') do set "PRODUCT_PATH=%%i"
if not defined PRODUCT_PATH (
    echo envy: failed to resolve product 'cmake' 1>&2
    exit /b 1
)
call "%PRODUCT_PATH%" %*
exit /b %ERRORLEVEL%
```

`%~dp0` is the script's own directory, so it finds `envy.bat` beside itself the
way the POSIX wrapper finds `envy`. The exit code is forwarded.

Deploy both flavors from whatever machine you are on:

```console
$ envy deploy --platform all
deploy: 8 product script(s) (4 created, 0 updated, 4 unchanged, 0 removed)
```

A later `deploy` without `--platform all` writes only the host flavor and leaves
the other one alone, so the Windows wrappers a macOS developer committed are not
pruned by their colleagues' syncs. They do stop being restamped, though, so run
`--platform all` in whatever job or hook keeps the bin directory current. See
[`envy deploy`](../../reference/cli/deploy.md).

## What envy owns

envy touches only files that contain the `envy-managed` marker. On every `sync`
or `deploy`:

| File in the bin directory | What happens |
| --- | --- |
| Marked, and still backed by a product | Rewritten if its content changed, otherwise left alone |
| Marked, and no longer backed by a product | Removed |
| Not marked | Skipped, or an error under `--strict` |
| `envy` and `envy.bat` | Always restamped, never pruned |

Pruning is why a filtered `sync` needs care. `sync envy.cmake@r0` resolves only
that subgraph, so every other marked wrapper looks unbacked and is removed. A
bare `sync` puts them back.

## Taking ownership of a name

A file with no marker belongs to you, permanently. envy will not update it, will
not prune it, and will not overwrite it. That makes hand-written wrappers a
supported pattern rather than a hack.

The usual reason is that one command needs several products, or a step before
the tool runs. This is a real `bin/gn` from a firmware repo, replacing the
generated one:

```bash title="bin/gn"
#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

"${SCRIPT_DIR}/envy" sync --platform all
PYTHON3="$($SCRIPT_DIR/envy product python3)"
NINJA="$($SCRIPT_DIR/envy product ninja)"
GN="$($SCRIPT_DIR/envy product gn)"

"${PYTHON3}" "${SCRIPT_DIR}/../src/gntools/run_gn.py" \
  --gn="$GN" --ninja="$NINJA" -- "$@"
```

It syncs first, so a stale checkout repairs itself before the build runs. It
resolves three products instead of one. And it dispatches through a project
script rather than exec'ing the tool directly. None of that fits a generated
four-line wrapper, and none of it has to.

To take a name over, write the file. Either start from scratch or delete the
marker line from the deployed wrapper. Commit it like any other script.

Two things to know:

- **`--strict` will fail on it.** A name you own that a product also provides is
  exactly the collision `--strict` reports. Use a plain `sync`, or give the
  product a different name in its spec.
- **The marker is a substring match.** Any file containing `envy-managed`
  anywhere counts as envy's. Do not mention the marker in a comment in a script
  you intend to own.

## Line endings and file modes

envy writes every script with LF endings on every platform, and gives POSIX
scripts mode 755. Both matter to Git:

- The POSIX bootstrap and wrappers need the executable bit. `git ls-files
  --stage bin/envy` should show `100755`.
- Git line-ending conversion fights envy. Check out a repo with
  `core.autocrlf=true` and the `.bat` files arrive as CRLF, which envy sees as
  changed content and rewrites on the next deploy:

  ```console
  $ envy deploy --platform all
  deploy: 8 product script(s) (0 created, 1 updated, 7 unchanged, 0 removed)
  ```

  That churn is harmless but noisy. Turn conversion off for the directory:

  ```text title=".gitattributes"
  bin/** -text
  ```

LF `.bat` files work in `cmd.exe`. envy generates them that way on purpose, so
the same bytes are correct in the repo whichever platform wrote them.

## What gets no script

Products declared `script = false` deploy nothing. A header path, a library
file, and a data directory are not things to execute. Consumers ask
[`envy product <name>`](/reference/cli/product) or `envy.product(name)` for the
value instead. See [Products](/concepts/specs/products).

## See also

- [`envy deploy`](/reference/cli/deploy) and [`envy sync`](/reference/cli/sync)
- [Shell Hooks](./shell-hooks.md) and [`envy run`](./envy-run.md), the two alternatives to wrappers
- [Starting a Project](/guides/new-project) for what else to commit
