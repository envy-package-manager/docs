---
sidebar_position: 4
title: Lua API
---

# Lua API

The `envy` table, available in every manifest and spec. Lua 5.4.

Your editor has all of this as hover documentation. See
[Editor Setup](../guides/integrations/editors.md).

## Where each function works

| Function | Manifest and spec top level | Phase functions | Notes |
| --- | --- | --- | --- |
| constants, `path.*`, `template`, `extend`, logging | yes | yes | pure |
| `abspath`, `loadenv` | yes | yes | resolves against the calling file |
| `import` | manifest top level only | no | not installed in specs or `envy lua` |
| `copy`, `move`, `remove`, `exists`, `is_file`, `is_dir` | yes | yes | relative paths anchor to `stage_dir` in phases |
| `run`, `extract`, `extract_all` | yes | yes | |
| `fetch` | no | `FETCH` only | |
| `commit_fetch` | no | `FETCH` only | needs the cache lock |
| `verify_hash` | yes | yes | |
| `package`, `product`, `loadenv_spec` | no | yes | subject to `needed_by` |
| `options` | in an `OPTIONS` function | no | |

Calling a phase-only function too early is an error, not undefined behavior:

```text
envy.product: not in phase context (missing pkg)
envy.commit_fetch: can only be called from FETCH phase with cache lock active
envy.loadenv_spec: can only be called within phase functions, not at global scope
```

## Constants

| Constant | Value |
| --- | --- |
| `envy.PLATFORM` | `"darwin"`, `"linux"`, or `"windows"` |
| `envy.ARCH` | `"arm64"` or `"x86_64"` |
| `envy.PLATFORM_ARCH` | the two joined, for example `"darwin-arm64"` |
| `envy.EXE_EXT` | `".exe"` on Windows, `""` elsewhere |
| `ENVY_SHELL.BASH`, `.SH`, `.CMD`, `.POWERSHELL` | shell selectors for `envy.run` and `DEFAULT_SHELL` |

`ENVY_SHELL` is a top-level global, not a field of `envy`. All four constants
exist on every platform, and an incompatible choice is rejected when used.

```lua
FETCH = function(tmp_dir, opts)
  local asset = "tool-" .. opts.version .. "-" .. envy.PLATFORM_ARCH .. ".tar.gz"
  return "https://example.com/releases/" .. asset
end

PRODUCTS = { mytool = "bin/mytool" .. envy.EXE_EXT }
```

## Logging

```lua
envy.debug(msg)   -- only with --verbose
envy.info(msg)    -- default level
envy.warn(msg)
envy.error(msg)
envy.stdout(msg)  -- bypasses the log, writes to stdout
print(...)        -- routed to the log at info level
```

All of it goes to stderr except `envy.stdout`. Do not write progress chatter to
stdout, because [callers parse it](./observability.md#stdout-is-a-contract).

## Strings and tables

### `envy.template(str, values)`

Replaces `{{key}}` placeholders. Surrounding whitespace in a placeholder is
ignored, so `{{ jf }}` and `{{jf}}` are the same key.

```lua
BUILD = function(install_dir, stage_dir, fetch_dir, tmp_dir, opts)
  envy.run(envy.template("{{ cmake }} --build . --parallel -j {{ jobs }}", {
    cmake = envy.product("cmake"),
    jobs = opts.jobs or 4,
  }))
end
```

`envy.product` only works inside a phase function, so build the string there
rather than at the spec's top level.

Three things are errors rather than silent surprises: a placeholder with no value,
an unmatched `{{` or `}}`, and a placeholder name that is not an identifier.

```text
envy.template: missing value for placeholder 'a'
envy.template: unmatched '{{' (missing closing '}}')
```

### `envy.extend(target, ...)`

Appends every source array to `target` in place and returns it.

```lua
local args = { "--prefix", install_dir }
envy.extend(args, extra_flags, { "--verbose" })
```

## Paths

```lua
envy.path.join(...)          -- platform separator
envy.path.basename(path)     -- "z.tar.gz"
envy.path.dirname(path)      -- "/x/y"
envy.path.stem(path)         -- "z.tar", one extension is removed
envy.path.extension(path)    -- ".gz"
envy.abspath(relative_path)  -- absolute, anchored at the calling file
```

`join` uses the platform separator and `abspath` returns a native path, so both
produce backslashes on Windows. Build every path with these rather than
concatenating `"/"`, and a spec works on all three platforms unchanged.

Every path envy hands a spec is native throughout: phase arguments,
`envy.package`, `envy.product`, `envy.path.*`, `envy.abspath`, and a depot fetch
function's `ctx.tmp_dir` and `ctx.deps`. envy assembles those from a cache root,
manifest text, and Lua fragments, any of which may be spelled either way, so
joining alone would yield `C:/cache/pkg\file`. Two APIs naming the same location
always agree on spelling, so a product path and the same file reached through
`envy.package` compare equal rather than differing by a separator.

The exception is archive entry paths, which stay forward-slash on every
platform. That is `envy.extract`'s and `envy.extract_all`'s `only` patterns, and
[`envy extract --only`](./cli/extract.md), matching the archive formats
themselves.

`envy.abspath` is what lets a manifest name a sibling file without caring about
your working directory:

```lua
PACKAGES = {
  { spec = "local.mytool@r1", source = envy.abspath("envy/mytool.lua") },
}
```

It requires a relative path. Handing it an absolute one is an error, because the
result would not depend on the anchor.

## Files

```lua
envy.copy(src, dst)    -- files or directories, recursive
envy.move(src, dst)
envy.remove(path)      -- recursive
envy.exists(path)      --> boolean
envy.is_file(path)     --> boolean
envy.is_dir(path)      --> boolean
```

In a phase function, relative paths resolve against `stage_dir`. Prefer the
absolute directories the phase hands you.

```lua
INSTALL = function(install_dir, stage_dir, fetch_dir, tmp_dir, opts)
  envy.copy(envy.path.join(stage_dir, "bin"), envy.path.join(install_dir, "bin"))
  if envy.exists(envy.path.join(stage_dir, "share")) then
    envy.copy(envy.path.join(stage_dir, "share"), envy.path.join(install_dir, "share"))
  end
end
```

## Processes

### `envy.run(script, opts?)`

`script` is a string or an array of lines. Returns
`{ exit_code, stdout, stderr }`, where the two streams are present only with
`capture = true`.

| Option | Default | Meaning |
| --- | --- | --- |
| `cwd` | the phase's directory | Working directory. |
| `env` | inherited | Table merged over the inherited environment. |
| `shell` | the platform default or `DEFAULT_SHELL` | `ENVY_SHELL.*` or a shell config table. |
| `quiet` | `false` | Suppress the child's output. |
| `capture` | `false` | Put stdout and stderr in the result. |
| `check` | `true` | Throw on a non-zero exit. |
| `interactive` | `false` | Connect the terminal, for `sudo` and license prompts. |

```lua
local r = envy.run("git describe --tags", { capture = true, check = false })
if r.exit_code ~= 0 then
  envy.warn("no tags: " .. r.stderr)
end
```

`check = false` is how you inspect an exit code. With the default, a non-zero exit
aborts the phase.

Scripts are not portable by themselves. The interpreter is bash on macOS and
Linux and PowerShell on Windows, so branch on `envy.PLATFORM`, pass
`shell = ENVY_SHELL.CMD` or `.POWERSHELL` per call, or set `DEFAULT_SHELL` so one
dialect covers everything.

`check` also behaves differently underneath. bash gets `-e`, so a failing line
stops the script whatever `check` says. On Windows there is no `-e`, so
`check = true` makes envy inject fail-fast into the generated PowerShell or cmd
script, and `check = false` injects nothing. See
[Shells & Scripts](/concepts/shells#how-each-built-in-is-invoked).

## Archives

```text
envy.extract(archive_path, dest_dir, opts?)  --> file count
envy.extract_all(src_dir, dest_dir, opts?)
```

| Option | Meaning |
| --- | --- |
| `strip` | Drop this many leading path components. |
| `only` | Extract just these archive-relative paths or globs, matched after `strip`. A directory brings its subtree. |

`only` globs support `*` and `?` within one component, `**` across components,
and `[a-z]` or `[!a-z]` classes.

```lua
STAGE = function(fetch_dir, stage_dir, tmp_dir, opts)
  envy.extract(envy.path.join(fetch_dir, "tool.tar.gz"), stage_dir,
               { strip = 1, only = { "bin/**", "LICENSE" } })
end
```

An `only` entry that matches nothing is an error, so a renamed upstream directory
fails loudly:

```text
extract tool.tar.gz: 'only' entries matched no archive contents: "bin/**"
```

envy handles `tar` with gzip, bzip2, xz, zstd, or lzma, plus `zip`, `7z`,
`rar`, `iso`, and bare compressed streams such as a lone `.gz`. You rarely need
to care which, which matters most on Windows, where upstream ships a `.zip` and
the same two lines of Lua unpack it.

## Fetching

These belong to the `FETCH` phase. See
[The FETCH Verb](/concepts/specs/fetch).

### `envy.fetch(source, { dest = dir })`

Downloads one or many sources into `dest` and returns the basename it wrote, or
an array of them for an array argument. `source` is a URL string, a
`{ source, sha256, ref, post_data, dest }` table, or an array of either.

```lua
FETCH = function(tmp_dir, opts)
  local name = envy.fetch({
    source = "https://example.com/tool-" .. opts.version .. ".tar.gz",
    sha256 = hashes[opts.version],
  }, { dest = tmp_dir })
  envy.commit_fetch(name)
end
```

`dest` inside a source table renames the downloaded file, and it has to be a
plain filename with no separators.

### `envy.commit_fetch(files)`

Moves files from `tmp_dir` into the durable fetch directory, verifying hashes on
the way. Argument forms: a filename, a `{ filename, sha256 }` table, or an array
of either.

Anything left in `tmp_dir` is discarded. Committing is what carries a download
into the next phase and the next run.

### `envy.verify_hash(path, sha256)`

Returns a boolean instead of throwing. Use it when a mismatch is something you
want to handle.

## Dependencies

### `envy.product(name)`

Resolves a product declared as a product dependency, and returns its value,
usually an absolute path.

```lua
DEPENDENCIES = {
  { spec = "envy.cmake@r0", product = "cmake", needed_by = "build" },
}

BUILD = function(install_dir, stage_dir, fetch_dir, tmp_dir, opts)
  envy.run({ envy.product("cmake") .. " --build . --parallel" })
end
```

The name resolves either from an explicit `product =` on a dependency entry or,
failing that, from the project-wide product registry. Either way a dependency
edge is required, and its `needed_by` must already have been reached. The edge is
what drove the provider through install, and the registry only answers who
provides the name. A provider you reach only transitively is refused.

Undeclared access is an error naming both sides:

```text
envy.product: pkg 'local.user@r1' does not declare product dependency on 'nope_txt'
```

It also works inside a `source.fetch` function. `source.dependencies` entries are
wired with `needed_by = spec_fetch` before the fetch runs, so their products are
readable there:

```lua
source = {
  dependencies = { { spec = "tools.jfrog-cli@r1", source = "jfrog.lua" } },
  fetch = function(tmp_dir)
    envy.run(envy.product("jf") .. " rt dl specs/ " .. tmp_dir)
  end,
}
```

See [Fetch Dependencies](/concepts/dependencies/fetch-dependencies) for the
strong-reference rule that comes with it.

### `envy.package(identity)`

Returns a declared dependency's installed package directory. Use it when you need
a directory rather than a product, for example an include path.

### `envy.loadenv_spec(identity, module)`

Loads a Lua module out of a declared dependency and returns its globals. The
identity matches loosely, so `"helpers"` finds `"acme.helpers@v1"`. Inside a
bundle, the module path resolves against the bundle root.

```lua
DEPENDENCIES = {
  { spec = "acme.helpers@v1", needed_by = "fetch" },
}

FETCH = function(tmp_dir, opts)
  local gh = envy.loadenv_spec("acme.helpers", "lib.github")
  return gh.release_url("acme/tool", "v" .. opts.version)
end
```

It returns the module's sandbox globals, not its `return` value. See
[Shipping an API with your specs](/concepts/dependencies/bundles#shipping-an-api-with-your-specs).

All three respect `needed_by`. A dependency declared `needed_by = "build"` is not
resolvable from `FETCH`, and the error says so rather than handing you a path to
a half-built package.

## Composition

### `envy.import(path)`

Runs another manifest in a sandbox and returns its globals. Requires **envy
0.3.0 or newer**. This is how a superproject composes a component's package list:

```lua title="envy.lua"
local common = envy.import("libs/common")

PACKAGES = envy.extend(common.PACKAGES, {
  { spec = "local.mytool@r1", source = "envy/mytool.lua" },
})
```

`path` is relative to the calling manifest. A directory appends `envy.lua`, so
`envy.import("libs/common")` and `envy.import("libs/common/envy.lua")` are the
same call.

What comes back is a table of every global the imported manifest assigned, which
is `PACKAGES` and `BUNDLES` and anything else it set. Only `PACKAGES` and
`BUNDLES` carry import bookkeeping. Assign the rest yourself:

```lua
PACKAGE_DEPOTS = common.PACKAGE_DEPOTS
```

An imported entry stays tied to the file that wrote it:

- **Relative `source` paths resolve against the imported manifest's directory.**
  A component's `source = "envy/protoc.lua"` means `libs/common/envy/protoc.lua`
  no matter who imports it. `envy.abspath` is no longer needed for this.
- **`bundle = "alias"` resolves against the imported `BUNDLES` first**, then the
  root's. Re-exporting `BUNDLES` is unnecessary, and two components can use the
  same alias for different bundles.

Everything else names the superproject: the project root, the `SETUP` working
directory, and custom-fetch cache keys. The imported manifest supplies
declarations, not a second project.

The imported file sees `ENVY_IMPORTER`, the absolute path of the manifest that
imported it. It is `nil` when the file runs as a manifest on its own, which is
how a component gates an entry only it needs:

```lua title="libs/common/envy.lua"
if not ENVY_IMPORTER then
  envy.extend(PACKAGES, {
    { spec = "acme.armgcc@r1", source = "envy/acme.armgcc.lua" },
  })
end
```

Nesting works, and a cycle is an error naming the chain:

```text
error: Failed to execute manifest script: envy.import: 'nope' not found (resolved to /src/app/nope)
error: Failed to execute manifest script: envy.import: import cycle: /src/a/envy.lua -> /src/b/envy.lua -> /src/a/envy.lua
```

The imported header is otherwise inert. The one thing envy reads from it is
`@envy version`, and only when the root manifest pins one too. Newer than the
root pin is an error, because bootstrap already chose the binary:

```text
error: Failed to execute manifest script: envy.import: /src/sub/envy.lua requires envy 0.4.0, but the root manifest pins 0.3.0
warning: envy.import: /src/sub/envy.lua pins envy 0.2.5; the root manifest pins 0.3.0
```

See [The bootstrap boundary](/guides/monorepos#the-bootstrap-boundary).

### `envy.loadenv(module)`

Loads a Lua file next to the calling file and returns its globals. Dots are path
separators, so `"libs.common.helpers"` means `libs/common/helpers.lua`. Use it
for shared helper files:

```lua title="envy.lua"
local versions = envy.loadenv("envy.versions")

PACKAGES = {
  { spec = "envy.cmake@r0", bundle = "envy", options = { version = versions.cmake } },
}
```

**To compose one manifest from another, use
[`envy.import`](#envyimportpath) instead.** `loadenv` hands back a plain table,
so an imported entry's relative `source` paths would resolve against the wrong
directory and its bundle aliases would not resolve at all. Both are silent, and
both are what `envy.import` exists to fix.

## Options

### `envy.options(schema)`

Validates the current options inside an `OPTIONS` function. Throws on failure, and
also rejects options the schema does not declare.

```lua
OPTIONS = function(opts)
  envy.options({
    version = { required = true, type = "semver" },
    jobs = { type = "int", range = ">=1 <=64" },
    variant = { choices = { "release", "debug" } },
  })
end
```

Constraint keys are `required`, `type` (`string`, `int`, `float`, `boolean`,
`table`, `list`, `semver`), `range`, `choices`, and `validate`. The declarative
table form of `OPTIONS` takes the same constraints without the function wrapper.
See [Options](/concepts/specs/options).

## See also

- [Spec Reference](./spec-globals.md) for the globals these functions appear in
- [Anatomy of a Spec](/concepts/specs)
- [Shells & Scripts](/concepts/shells)
