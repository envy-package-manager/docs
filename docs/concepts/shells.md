---
sidebar_position: 4
title: Shells & Scripts
---

# Shells & Scripts

Whenever a verb is a string, or a function returns one, envy runs it as a shell
script. This page covers which interpreter runs it, how the script reaches that
interpreter, and how to make the interpreter itself a package the project pins.

## Where scripts come from

| Source | Example |
| --- | --- |
| A string verb | `INSTALL = "make install"` |
| A function verb returning a string | `BUILD = function(...) return "make -j" end` |
| A [`SETUP`](./specs/setup.md) pair's `CHECK` or `INSTALL` | `CHECK = "brew --version"` |
| An explicit call | `envy.run("make -j")` |

All four go through the same machinery, so everything below applies equally to
each.

## The default interpreter

| Platform | Default |
| --- | --- |
| macOS, Linux | `bash` |
| Windows | PowerShell |

The built-in choices are constants rather than strings:

| Constant | Valid on |
| --- | --- |
| `ENVY_SHELL.BASH` | macOS, Linux |
| `ENVY_SHELL.SH` | macOS, Linux |
| `ENVY_SHELL.CMD` | Windows |
| `ENVY_SHELL.POWERSHELL` | Windows |

Asking for one on the wrong platform is an error, not a silent fallback. A
manifest that wants a per-platform choice makes it explicitly, with a
[function](#a-function).

## Working directories

A script always starts somewhere useful, so relative paths work:

| Verb | Working directory |
| --- | --- |
| [`STAGE`](./specs/stage.md) | the staging destination: `work/stage/`, or `pkg/` for a fully declarative spec |
| [`BUILD`](./specs/build.md) | `work/stage/` |
| [`INSTALL`](./specs/install.md) | `work/stage/` |
| [`SETUP`](./specs/setup.md) `CHECK` and `INSTALL` | the project root, because they act on host state |

## `DEFAULT_SHELL`

`DEFAULT_SHELL` is a manifest global. It sets the interpreter for the whole
project, and it takes four shapes.

### A built-in constant

```lua title="envy.lua"
DEFAULT_SHELL = ENVY_SHELL.SH
```

### A file-based interpreter

envy writes the script to a temporary file and runs the interpreter on it:

```lua title="envy.lua"
DEFAULT_SHELL = { file = "/usr/bin/tclsh", ext = ".tcl" }
```

`file` is the interpreter. A string is shorthand for a one-element argv array,
and the array form carries flags:

```lua
DEFAULT_SHELL = { file = { "/usr/bin/python3", "-u" }, ext = ".py" }
```

`ext` is required. It names the temporary script's extension. That matters on
Windows, where interpreters and the shell often key on it.

### An inline interpreter

The script is passed as the final command-line argument instead of a file:

```lua title="envy.lua"
DEFAULT_SHELL = { inline = { "/usr/bin/python3", "-c" } }
```

### A function

Called lazily, the first time something needs a shell:

```lua title="envy.lua"
DEFAULT_SHELL = function()
  if envy.PLATFORM == "windows" then return ENVY_SHELL.POWERSHELL end
  return ENVY_SHELL.BASH
end
```

A bare function cannot name a package, because it has no dependency to
authorize against. To point at an interpreter envy installs, use the
`{ DEPENDS, SHELL }` form in [the next section](#bootstrapping-a-custom-shell).

## How a custom shell is invoked

The two custom modes differ only in how the script reaches the interpreter:

| Mode | What envy runs | Use it when |
| --- | --- | --- |
| `file` | `<argv...> <temp-script-path>` | The interpreter takes a script file, like `tclsh script.tcl`. |
| `inline` | `<argv...> <script text>` | The interpreter has a "run this string" flag, like `python3 -c`. |

Built-in shells behave like `file` mode. envy writes the script out and runs
`bash <path>`.

Two consequences worth knowing. In `file` mode the script exists on disk while
it runs, so `$0` and traceback line numbers refer to a real file. In `inline`
mode the whole script is one argv element, so very large generated scripts can
run into the platform's argument-length limit.

## Bootstrapping a custom shell

The point of a custom shell is to stop assuming anything about the host. A
project that writes its build logic in Python should not care which Python the
machine has, or whether it has one at all.

Package the interpreter, then name it with the `{ DEPENDS, SHELL }` form:

```lua title="envy.lua"
-- @envy schema "1"
-- @envy version "0.2.0"
-- @envy bin "bin"
-- @envy deploy "true"

BUNDLES = {
  envy = {
    identity = "envy.package-specs@r3",
    source = "https://github.com/envy-package-manager/package-specs.git",
    ref = "ded36a39bbf13744f5a0e539f2f4741fecb61dd0",
  },
}

PACKAGES = {
  { spec = "envy.python@r1", bundle = "envy",
    options = { version = "3.13.14", release = "20260623", provide_python3 = true } },

  { spec = "acme.codegen@r0", source = envy.abspath("envy/acme.codegen.lua") },
}

DEFAULT_SHELL = {
  DEPENDS = { "envy.python@r1" },
  SHELL = function()
    return { file = { envy.product("python3") }, ext = ".py" }
  end,
}
```

Every string verb in the project now runs under the pinned interpreter, so a
spec's verbs are Python:

```lua title="envy/acme.codegen.lua"
-- @envy schema "1"
IDENTITY = "acme.codegen@r0"

FETCH = "https://vendor.example/codegen-2.1.tar.gz"
STAGE = { strip = 1 }

BUILD = [[
import pathlib, sys
for src in pathlib.Path("templates").glob("*.in"):
    out = src.with_suffix(".c")
    out.write_text(src.read_text().replace("@VERSION@", "2.1"))
    print(f"generated {out}", file=sys.stderr)
]]
```

### The rules

- **`DEPENDS` names packages the manifest already declares.** Entries are
  [queries](../reference/cli/index.md#package-queries) against `PACKAGES`, the
  same matching the CLI uses. An entry that matches nothing is an error that
  names it.
- **`DEPENDS` requires `SHELL` to be a function.** A value form is read before
  any package exists, so it could never name one, and envy says
  `DEFAULT_SHELL DEPENDS requires SHELL to be a function`.
- **`envy.product` and `envy.package` both work inside `SHELL`.** envy
  synthesizes a consumer for the manifest-wide shell, holding an edge to each
  `DEPENDS` entry. It shows up in traces as `envy.DEFAULT_SHELL@v1`. A bare
  function with no `DEPENDS` has no such edges, so `envy.product` there fails.
- **The interpreter is installed first.** envy waits for the whole `DEPENDS`
  closure to complete, then resolves the shell once, and only then can another
  package's string verb run.
- **Resolution happens once, lazily.** The function is called on the first
  request for a shell, not while the manifest loads.
- **Strong references only.** A weak or product reference inside the `DEPENDS`
  closure is refused with `DEFAULT_SHELL dependency closure must use strong
  dependencies`, because that closure can be needed before the resolution pass
  that would settle it.

:::caution The bootstrap exception
The `DEPENDS` closure supplies the shell, so it cannot consume it. The
interpreter package and everything it depends on run their own string verbs under
the platform built-in, transitively. Without that carve-out, installing Python
would require Python.

The same applies to `envy.run` called inside the `SHELL` function itself: it runs
under the built-in, which also keeps the lazy resolution from re-entering itself.
:::

### Overriding one verb instead of the project

`envy.run` takes the same shapes as `DEFAULT_SHELL`, so a single verb can use a
different interpreter without changing the project default:

```lua
DEPENDENCIES = { { product = "python3" } }

BUILD = function(install_dir, stage_dir, fetch_dir, tmp_dir, opts)
  envy.run("print('generating')", {
    shell = { file = { envy.product("python3") }, ext = ".py" },
  })
end
```

Use this for a project that is mostly shell with one Python step, and inside the
interpreter's own spec, where the carve-out applies.

## `envy.run`

For explicit process control from a function verb:

```lua
envy.run("make -j")                                  -- one script
envy.run({ "cd build", "cmake --build ." })          -- array of successive lines

local r = envy.run("git rev-parse HEAD", { capture = true })
envy.info("head is " .. r.stdout)
```

`envy.run` takes shell script text rather than an argv array. An array argument
is joined with newlines into one script. The return value is
`{ exit_code, stdout, stderr }`, and `stdout` and `stderr` are populated only
when requested.

| Option | Default | Effect |
| --- | --- | --- |
| `capture` | `false` | Return `stdout` and `stderr` as strings. |
| `check` | `true` | A non-zero exit raises. Set `false` to inspect `exit_code` yourself. |
| `quiet` | `false` | Do not log the command or its output. |
| `interactive` | `false` | Give the child the terminal and stream its output, for `sudo` prompts and license agreements. |
| `cwd` | the verb's directory | Run somewhere else. |
| `env` | inherited | Extra environment variables. |
| `shell` | `DEFAULT_SHELL` | Override the interpreter for this call. |

`check = false` with `capture = true` is the standard way to write a
[`SETUP`](./specs/setup.md) `CHECK`. There, a non-zero exit is an answer rather
than a failure:

```lua
CHECK = function(pkg_dir, opts)
  local r = envy.run("dpkg-query -W " .. table.concat(opts.packages, " "),
                     { capture = true, quiet = true, check = false })
  return r.exit_code == 0
end
```

## Generating scripts

`envy.template` substitutes `{{placeholder}}` and raises on a missing value
instead of substituting an empty string. A typo becomes a clear failure rather
than a broken command line:

```lua
BUILD = function(install_dir, stage_dir, fetch_dir, tmp_dir, opts)
  return envy.template([[
    ./configure --prefix={{prefix}}
    make -j{{jobs}}
  ]], { prefix = install_dir, jobs = opts.jobs or 4 })
end
```

## Failure semantics

- A non-zero exit fails the verb, which fails the package, unless it came from
  `envy.run` with `check = false`.
- A signal always fails, and the error names it.
- The failure message carries the script text and captured output. A build that
  dies on line 30 of a generated script shows you the script.
- On failure envy removes `pkg/` and `work/` and keeps `fetch/`. The next run
  starts the verb over. See
  [the lifecycle](./specs/lifecycle.md#when-something-fails).

## See also

- [BUILD](./specs/build.md) and [INSTALL](./specs/install.md) for the verbs most likely to be scripts.
- [SETUP](./specs/setup.md) for scripts that run against the host.
- [Projects & Manifests](./projects.md) for where `DEFAULT_SHELL` lives.
- [Lua API](../reference/lua-api.md) for the full `envy.*` surface.
