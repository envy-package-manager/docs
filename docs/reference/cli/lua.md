---
sidebar_position: 15
title: envy lua
---

# `envy lua`

Run a Lua script inside envy's runtime, with the full `envy.*` API loaded. Use it
as a scratchpad while authoring specs. Exercise a helper, check what a platform
string resolves to, or prototype a `BUILD` body without waiting on a fetch, a
stage, and a cache lock.

## Usage

```
envy lua <script>
```

## Arguments

| Argument | Meaning |
| --- | --- |
| `script` | Path to a Lua file. Required, and it must exist. There is no REPL. |

## What is in scope

The same environment a spec's phase functions see:

| Name | Purpose |
| --- | --- |
| `envy.info`, `envy.warn`, `envy.error`, `envy.debug` | Logging at each level, on stderr. `print` is rerouted to `envy.info`. |
| `envy.stdout` | Raw stdout, for scripts whose output is data. |
| `envy.PLATFORM`, `envy.ARCH`, `envy.PLATFORM_ARCH`, `envy.EXE_EXT` | Host identification, as specs see it. |
| `envy.template` | `{{placeholder}}` substitution, with a hard error on a missing value. |
| `envy.extend`, `envy.loadenv` | Table extension and environment-file loading. |
| `envy.path.join`, `.basename`, `.dirname`, `.stem`, `.extension` | Path manipulation, plus `envy.copy`, `envy.move`, `envy.remove`, `envy.exists`, `envy.is_file`, and `envy.is_dir`. |
| `envy.run` | Run a shell script, one string or an array of lines, the way a phase verb does. Returns `{exit_code, stdout, stderr}`. Options include `capture`, `check`, `cwd`, `env`, `shell`, `quiet`. |
| `envy.fetch`, `envy.extract` | The download and archive verbs. |
| `envy.package`, `envy.product`, `envy.options` | Resolution helpers. |
| `ENVY_SHELL.BASH`, `.SH`, `.CMD`, `.POWERSHELL` | Shell constants for string verbs. |

`envy.import` is not in scope. It composes manifests, and `envy lua` runs a
script rather than loading a manifest.

A Lua error exits non-zero with the message and traceback, formatted the way a
failing spec's error is.

## Examples

### To check what a spec will see on this machine

```bash
cat > /tmp/probe.lua <<'LUA'
envy.info(envy.PLATFORM_ARCH)                  -- darwin-arm64
envy.info("exe suffix: [" .. envy.EXE_EXT .. "]")
LUA
envy lua /tmp/probe.lua
```

The fastest way to settle a cross-platform naming question, with no manifest and
no package involved.

### To debug a URL template before putting it in a spec

```lua title="/tmp/url.lua"
local tmpl = "https://cdn.example/tool/{{version}}/tool-{{platform}}.tar.gz"
for _, v in ipairs({ "1.2.0", "1.3.0" }) do
  envy.info(envy.template(tmpl, { version = v, platform = envy.PLATFORM_ARCH }))
end
```

```bash
envy lua /tmp/url.lua
```

A missing placeholder value raises here, which is the same failure you would get
during `FETCH`.

### To prototype a build command

```lua title="/tmp/try-build.lua"
local r = envy.run("cmake --version", { capture = true })
envy.info("exit " .. r.exit_code .. ": " .. r.stdout)

envy.run({ "cd build", "cmake --build . --target all" })   -- array of script lines
```

```bash
envy lua /tmp/try-build.lua
```

`envy.run` takes shell script text rather than an argv array, and an array is
joined into successive lines. Output is captured rather than echoed, so pass
`capture = true` to see `stdout` and `stderr`. A non-zero exit raises by default,
which is why a phase stops on a failed command. All of that behaves here as it
does inside a spec.

### To write a small repo utility on envy's runtime

```bash
envy lua tools/gen-hashes.lua > specs/hashes.lua
```

`envy.stdout` writes to stdout while logging stays on stderr, so a generator
script is safe to redirect.

## See also

- [Lua API](../lua-api.md) for the full surface.
- [Spec Reference](../spec-globals.md)
- [Writing a Spec](/guides/writing-a-spec)
