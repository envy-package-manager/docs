---
sidebar_position: 8
title: Shells & Scripts
---

# Shells & Scripts

When a verb is a string, or a function returns one, envy runs it as a shell
script. This page covers which interpreter, in which directory, and what happens
on failure.

## The default interpreter

| Platform | Default |
| --- | --- |
| macOS, Linux | `bash` |
| Windows | PowerShell |

The built-in choices are `ENVY_SHELL.BASH`, `ENVY_SHELL.SH`, `ENVY_SHELL.CMD`,
and `ENVY_SHELL.POWERSHELL`. `BASH` and `SH` are Unix-only, `CMD` and
`POWERSHELL` are Windows-only. Asking for one on the wrong platform is an error
rather than a silent fallback.

## Working directories

| Verb | Working directory |
| --- | --- |
| [`STAGE`](./stage.md) | the staging destination: `work/stage/`, or `pkg/` for a fully declarative spec |
| [`BUILD`](./build.md) | `work/stage/` |
| [`INSTALL`](./install.md) | `work/stage/` |
| [`SETUP`](./setup.md) `CHECK` and `INSTALL` | the project root, because they act on host state |

## `DEFAULT_SHELL`

Set `DEFAULT_SHELL` in the manifest to change the interpreter for the whole
project. It takes four shapes.

A built-in constant:

```lua
DEFAULT_SHELL = ENVY_SHELL.SH
```

A file-based interpreter, where envy writes a script file and runs it:

```lua
DEFAULT_SHELL = { file = "/usr/bin/tclsh", ext = ".tcl" }
```

`file` is the interpreter, either a path string or an argv array such as
`{ "/usr/bin/python3", "-u" }`. `ext` is required, and is the extension of the
temporary script file, which keeps interpreters that care about file type happy.

An inline interpreter, where the script is passed as an argument:

```lua
DEFAULT_SHELL = { inline = { "/usr/bin/python3", "-c" } }
```

A function, to decide at load time:

```lua
DEFAULT_SHELL = function()
  if envy.PLATFORM == "windows" then return ENVY_SHELL.POWERSHELL end
  return os.getenv("CI") and ENVY_SHELL.SH or ENVY_SHELL.BASH
end
```

envy calls the function once, while loading the manifest, before any package
runs.

:::caution `DEFAULT_SHELL` cannot name an envy-managed interpreter
The function runs with no phase context, so `envy.product` and `envy.package`
are unavailable inside it and report `not in phase context (missing pkg)`. A
`file` or `inline` interpreter therefore has to be a path that already exists on
the machine, or one the environment supplies.

To run a verb under an interpreter envy installs, override the shell for that
call instead. `envy.run` takes the same shapes, and inside a phase verb the
product is resolvable:

```lua
DEPENDENCIES = { { product = "python3" } }

BUILD = function(install_dir, stage_dir, fetch_dir, tmp_dir, opts)
  envy.run("print('generating')", {
    shell = { file = { envy.product("python3") }, ext = ".py" },
  })
end
```
:::

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
[`SETUP`](./setup.md) `CHECK`. There, a non-zero exit is an answer rather than a
failure:

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
  [the lifecycle](./lifecycle.md#when-something-fails).

## See also

- [BUILD](./build.md) and [INSTALL](./install.md) for the verbs most likely to be scripts.
- [SETUP](./setup.md) for scripts that run against the host.
- [Lua API](../../reference/lua-api.md) for the full `envy.*` surface.
