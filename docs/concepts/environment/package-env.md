---
sidebar_position: 4
title: Package Environment
---

# Package environment

Some tools need more than a `PATH` entry. Rust reads `RUSTUP_HOME` and
`CARGO_HOME`. A JDK expects `JAVA_HOME`. From envy 0.6.0 a spec declares those
variables in its `ENV` global, and envy applies them in three places:

- In a shell you [activate](#activation) in the project, with the
  [shell hook](./shell-hooks.md) or [`envy activate`](../../reference/cli/activate.md).
- In every tool a [product script](./product-scripts.md) runs (envy 0.8.0+).
- In the verbs of every package that [depends](#in-builds) on this one.

## Declaring `ENV`

```lua title="rust.lua"
IDENTITY = "acme.rust@r0"
-- FETCH, INSTALL, ...

ENV = function(pkg_dir, pkg_state_dir, options)
  return {
    RUSTUP_HOME = envy.path.join(pkg_dir, "rustup"),
    CARGO_HOME  = pkg_state_dir,
    PATH        = { prepend = { envy.path.join(pkg_dir, "bin"),
                                envy.path.join(pkg_state_dir, "bin") } },
  }
end
```

Each value says what to do with one variable:

| Value | Effect |
| --- | --- |
| `"text"` | Set the variable. |
| `false` | Unset it. |
| `{ prepend = ..., append = ..., sep = ... }` | Add to the current value. `prepend` and `append` each take a string or a list of strings. `sep` defaults to the platform path separator, `:` or `;`. |
| `nil` | Leave it alone. |

`true` is an error. Names must match `[A-Za-z_][A-Za-z0-9_]*`, and names starting
with `ENVY_` are reserved for envy. On Windows, variable names are
case-insensitive, so `Path` and `PATH` in one table is an error.

A table works for constants, such as `ENV = { RUST_BACKTRACE = "1" }`. envy
checks a table when it loads the spec, so a bad name fails before anything is
fetched. The function form is called once per consumer, with three arguments:

| Argument | Value |
| --- | --- |
| `pkg_dir` | The package's install directory. `nil` for a [user-managed](../specs/user-managed.md) package. |
| `pkg_state_dir` | A directory for the tool's mutable state, `<root>/.envy/state/<namespace.name>/`. In an activated shell and a product script, `<root>` is the project root. In a build it is the dependent package's temporary directory. Requires envy 0.8.0. |
| `options` | The package's validated options. |

Both directories arrive with a trailing separator, like every directory envy
hands to Lua. Build paths with `envy.path.join`. Returning `nil` declares no
variables.

The example shows why `pkg_state_dir` exists. A rustup toolchain is part of the
payload, so `RUSTUP_HOME` points into `pkg_dir`. Cargo's registry cache is state
that cargo writes to, so `CARGO_HOME` is `pkg_state_dir`. Each project gets its
own, and a build gets a private one inside its own work area. Neither writes
into the shared cache entry.

`pkg_state_dir` leaves the revision out of its name, so a spec bump or a version
change keeps the tool's caches. Every option set of one spec shares it. envy
does not create the directory. The tool creates it on first write. `envy init`
already puts `.envy/` in `.gitignore`.

## Activation

An activated shell has every installed package's `ENV` applied, plus two
variables envy always sets:

- The project's bin directory, prepended to `PATH`.
- `ENVY_PROJECT_ROOT`, the project's directory.

The [shell hook](./shell-hooks.md) activates a project when you `cd` into it and
restores your environment when you leave. Without the hook, do the same by hand:

```shell-session
$ eval "$(envy activate zsh)"
envy: entering proj — 4 variables set
$ echo $CARGO_HOME
/Users/you/work/proj/.envy/state/acme.rust/
$ eval "$(envy deactivate zsh)"
envy: leaving proj — environment restored
```

To run one command in the activated environment without changing your shell, use
[`envy run --activate`](../../reference/cli/run.md).

Activation follows these rules:

- **Installed packages only.** Activation never fetches, installs, or waits on
  another envy process. A package that is not installed is skipped without a
  message. Its `ENV` applies at the first prompt after it installs.
- **Dependencies count.** A dependency's `ENV` applies even when the manifest
  does not list it in `PACKAGES`.
- **Earlier wins.** When two packages set the same variable, the one listed
  first in `PACKAGES` wins, and a package wins over its own dependencies. The bin
  directory always lands first on `PATH`.
- **Errors only skip.** An `ENV` function that fails skips that package with a
  warning. A manifest that fails to load still gets the bin directory and
  `ENVY_PROJECT_ROOT`.
- **Exact restore.** Activation records the old value of every variable it
  touches. Deactivating puts each one back byte for byte, or unsets it if it was
  unset. An edit you made to one of those variables inside the project is
  discarded on the way out.
- **One project at a time.** Activating always deactivates first, from any
  project, so switching projects leaves nothing of the first one behind.

## Product scripts

From envy 0.8.0, a [product script](./product-scripts.md) runs its tool in the
project's activation. `./bin/cargo` sees `CARGO_HOME` in CI, in an IDE, and in
another project's shell, the same as in an activated one. The script installs the
tool first if it has to, so its `ENV` is always there.

- **An activated shell stays as it is.** When the caller is already in this
  project's activation, the tool gets the caller's environment unchanged, plus
  any of its own `ENV` that is missing. Edits you made to `PATH` in that shell
  survive.
- **Anything else gets a fresh activation.** Another project's activation, or
  one written by a different envy, is undone first. Then this project's is
  applied for that one tool.
- **The tool's own `ENV` must work.** An `ENV` function that fails in the tool's
  own dependency closure stops the script with an error. Elsewhere it warns, as
  in a shell.

A plain [`envy run`](./envy-run.md) does not apply `ENV`. It puts the bin
directory on `PATH` and sets `ENVY_PROJECT_ROOT`. Use `envy run --activate` for
the full environment.

## In builds

A package's verbs see the `ENV` of its dependencies. That covers string verbs,
`envy.run`, and both halves of a [SETUP](../specs/setup.md) pair.

```lua
-- A's INSTALL runs B's tool. B's tool runs C's cargo.
-- C sets CARGO_HOME = pkg_state_dir.
-- A's INSTALL sees CARGO_HOME inside A's own temporary directory.
```

- **Transitive.** Every package behind the dependency edges the current phase
  waits on contributes, along with everything those packages depend on. A
  dependency with `needed_by = "install"` reaches `INSTALL` but not `BUILD`. See
  [Phase Ordering](../dependencies/ordering.md).
- **Nearer wins.** If A depends on B, B depends on C, and both B and C set a
  variable, A's verbs see B's value.
- **`pkg_state_dir` is the dependent's.** It sits under the dependent package's
  temporary directory, never the project's. A SETUP pair gets a scratch
  directory that goes away when the pair returns.
- **Not its own.** A package's `ENV` does not apply to its own verbs.
- **Processes only.** The variables reach processes that `envy.run` and string
  verbs start. Lua's `os.getenv` inside the phase does not see them.

## Activation never reaches a build

Verbs start from the environment as it was before any activation. envy undoes an
activated shell's changes before it runs a verb, so `envy install` from an
activated shell builds the same thing as from a plain one. Lua's `os.getenv` reads the same
pre-activation environment, in manifests, specs, and `envy lua`.

`os.execute` and `io.popen` are unavailable for the same reason, since they would
start a process with the live environment. Calling either is an error:

```text
os.execute is unavailable; use envy.run
io.popen is unavailable; use envy.run (capture = true)
```

Use [`envy.run`](../../reference/lua-api.md#envyrunscript-opts), with
`capture = true` in place of `io.popen`. A spec that called either one fails
from envy 0.6.0 on.

A dependency's `ENV` is computed from that dependency's install path, options,
and spec. Nothing from the project or your shell reaches it. Keep project layout,
such as a `CARGO_HOME` under the project's `out/` directory, out of package
options. In a shell, `pkg_state_dir` already sits under the project.

## Windows

`ENV` works the same way. `sep` defaults to `;`. `envy activate` emits
PowerShell or, from envy 0.8.0, `cmd`. Variable names are case-insensitive, so an
`ENV` that sets `PATH` edits the `Path` variable Windows already has.

## See also

- [`envy activate`](../../reference/cli/activate.md) and [`envy deactivate`](../../reference/cli/deactivate.md) for the commands.
- [Shell Hooks](./shell-hooks.md) for activation on `cd`.
- [Spec Reference](../../reference/spec-globals.md#env) for the terse form.
