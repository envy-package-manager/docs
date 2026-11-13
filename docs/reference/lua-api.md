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
| `subproject` | manifest top level only | no | not installed in specs or `envy lua`. Requires envy 0.7.0. |
| `loadenv_bundle` | manifest top level only | no | materializes the bundle first. Requires envy 0.4.6. |
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
envy.loadenv_bundle: manifest scope only; a spec reaches a bundle it declared with envy.loadenv_spec(identity, module)
```

## Constants

| Constant | Value |
| --- | --- |
| `envy.PLATFORM` | `"darwin"`, `"linux"`, or `"windows"` |
| `envy.ARCH` | `"arm64"` or `"x86_64"` |
| `envy.PLATFORM_ARCH` | the two joined, for example `"darwin-arm64"` |
| `envy.EXE_EXT` | `".exe"` on Windows, `""` elsewhere |
| `envy.PROJECT_ROOT` | the project's directory, symlinks resolved. In a subproject's manifest, the subproject's own directory. Everywhere else, the root manifest's. `nil` under `envy lua`, which has no project. Requires envy 0.6.0. |
| `envy.IS_SUBPROJECT` | `true` in a manifest loaded by [`envy.subproject`](#envysubprojectdir), `false` in the root manifest. `nil` in specs and under `envy lua`. Requires envy 0.7.0. |
| `ENVY_SHELL.BASH`, `.SH`, `.CMD`, `.POWERSHELL` | shell selectors for `envy.run` and `DEFAULT_SHELL` |

`ENVY_SHELL` is a top-level global, not a field of `envy`. All four constants
exist on every platform, and an incompatible choice is rejected when used.

`envy.PROJECT_ROOT` is the root manifest's directory in the root manifest, at a
spec's top level, in every phase, and during bundle loading. SETUP verbs and
`DEFAULT_SHELL` run in that directory. In a [subproject's](#envysubprojectdir)
manifest, and in code it defines or loads, it is the subproject's directory
instead.
Keep it out of `options` and cache-managed payloads, since cache entries are
shared across projects. It suits SETUP pairs, which do host work outside the cache:

```lua
SETUP = {
  hooks = {
    CHECK = function()
      return envy.exists(envy.path.join(envy.PROJECT_ROOT, ".git/hooks/pre-commit"))
    end,
    INSTALL = function(pkg_dir)
      envy.copy(envy.path.join(pkg_dir, "pre-commit"),
                envy.path.join(envy.PROJECT_ROOT, ".git/hooks/pre-commit"))
    end,
  },
}
```

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

To label the package's own progress rows rather than log a line, set
[`DISPLAY`](./spec-globals.md#display) instead.

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
| `env` | inherited | Table of strings merged over the inherited environment. It cannot unset a variable. |
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

From envy 0.6.0 the inherited environment is the one from before any shell
[activation](/concepts/environment/package-env#activation-never-reaches-a-build),
plus the [`ENV`](/concepts/environment/package-env#in-builds) of the packages
this phase depends on. `opts.env` goes on top. String verbs get the same
environment. So does Lua's `os.getenv`, without the dependencies' `ENV`.

`os.execute` and `io.popen` are not available, because they would start a
process with the live environment. Call `envy.run`, and use `capture = true` in
place of `io.popen`:

```text
os.execute is unavailable; use envy.run
io.popen is unavailable; use envy.run (capture = true)
```

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
| `only` | Extract just these archive-relative paths or globs, matched after `strip`. A directory brings its subtree. A leading `!` excludes. |
| `archives` | `envy.extract_all` only. Filenames or globs in `src_dir` to unpack whatever their extension, such as `"*.whl"`. A leading `!` keeps a file whole. Since envy 0.4.9. |

`only` globs support `*` and `?` within one component, `**` across components,
and `[a-z]` or `[!a-z]` classes.

```lua
STAGE = function(fetch_dir, stage_dir, tmp_dir, opts)
  envy.extract(envy.path.join(fetch_dir, "tool.tar.gz"), stage_dir,
               { strip = 1, only = { "bin/**", "LICENSE" } })
end
```

Since envy 0.4.0 an entry beginning with `!` excludes instead of including, and
an exclusion beats an inclusion. That makes "everything but" expressible:

```lua
envy.extract(envy.path.join(fetch_dir, "sdk.tar.gz"), stage_dir,
             { only = { "**", "!docs/**", "!**/*.pdb" } })
```

This is envy's one selector language. `only` here, a spec's
[`VENDOR`](/concepts/vendoring#what-gets-copied) list, and
[`envy hash --tree --only`](./cli/hash.md#subtree-hashing) are parsed and matched
by the same code.

An *inclusion* that matches nothing is an error, so a renamed upstream directory
fails loudly:

```text
extract tool.tar.gz: 'only' entries matched no archive contents: "bin/**"
```

An exclusion that matches nothing is not an error. A bare `"!"` is.

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
`{ source, sha256, ref, submodules, post_data, dest }` table, or an array of
either. The table keys mean what they do in a [`FETCH`](/concepts/specs/fetch)
table. From envy 0.5.0 any other key is an error.

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

`submodules` also takes a function here and in a `FETCH` table (envy 0.5.1+). It
is asked about each submodule found and returns a boolean. See
[Submodules](/concepts/specs/fetch#choosing-submodules-with-a-function).

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
failing that, from the project-wide product registry. Either way one of *your
own* dependency entries has to name the provider, and its `needed_by` must
already have been reached. The edge is what drove the provider through install,
and the registry only answers who provides the name. A provider you reach only
through someone else's edge is refused.

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
a directory rather than a product, for example an include path. The identity
matches loosely, so `"helpers"` finds `"acme.helpers@v1"`, and among several
matching entries the earliest `needed_by` wins.

### `envy.loadenv_spec(identity, module)`

Loads a Lua module out of a declared dependency. The identity matches the same
loose way. Inside a bundle, the module path resolves against the bundle root.

`module` is Lua dot syntax naming a file inside the dependency, so `"lib.common"`
loads `lib/common.lua`. Path separators, a leading or trailing `.`, and `..` are
all rejected, and the resolved path is checked against the load root as well.

```lua
DEPENDENCIES = {
  { spec = "acme.helpers@v1", needed_by = "fetch" },
}

FETCH = function(tmp_dir, opts)
  local gh = envy.loadenv_spec("acme.helpers", "lib.github")
  return gh.release_url("acme/tool", "v" .. opts.version)
end
```

What comes back follows
[the module rule](#what-a-module-hands-back). A module loaded out of a bundle
also sees [`ENVY_BUNDLE`](#envy_bundle), whose `alias` is `nil` here, since
`loadenv_spec` names the dependency by identity. See
[Shipping an API with your specs](/concepts/dependencies/bundles#shipping-an-api-with-your-specs).

All three respect `needed_by`. A dependency declared `needed_by = "build"` is not
resolvable from `FETCH`, and the error says so rather than handing you a path to
a half-built package.

All three also answer from your own `DEPENDENCIES` only. If `top` depends on
`mid` and `mid` depends on `base`, then `top` cannot reach `base`:

```text
error: envy.package: pkg 'local.top@v1' has no strong dependency on 'local.base@v1'
```

Declare `base` in `top` as well. The two entries name one package, so nothing is
built twice. Before envy 0.3.1 the lookup walked the whole graph, and a
transitive hit could hand back the wrong package's directory.

### What a module hands back

`loadenv_spec`, [`loadenv_bundle`](#envyloadenv_bundlealias-module), and
[`loadenv`](#envyloadenvmodule) share one rule, the one `require` already
teaches. A module that returns a table hands back that table. A module that
returns nothing hands back the globals it assigned. Anything else is an error
naming the module:

```text
envy.loadenv_spec: module 'lib.common' returned a number; a module returns a table or nothing
```

Before envy 0.4.6 all three handed back the sandbox globals whatever the module
returned, so the shape every Lua author writes came back empty:

```lua
local M = {}
function M.release_url(repo, tag, file) ... end
return M                                  -- before 0.4.6, the caller got {}
```

Nothing failed at the load. The call site got an empty table and reported
`attempt to call a nil value` somewhere later. A module that served both
`require` and `loadenv_spec` had to assign a global *and* return a table.
Returning the table is now enough.

### What a module can read

A module reads the globals of the file that loaded it. What the module assigns
stays in its own sandbox, so loading it never changes the caller's globals. A
helper can therefore follow its caller's settings without taking them as
arguments:

```lua title="lib/paths.lua"
local M = {}

function M.vendor_dir(name)
  return (VENDOR_ROOT or "vendor") .. "/" .. name
end

return M
```

The loading file can be a manifest, a [subproject's](#envysubprojectdir)
manifest, a spec, or another module. Each one's own globals show through, so a
helper that a subproject loads sees the subproject's `VENDOR_ROOT` and `envy`
rather than the root manifest's.

This needs envy 0.4.8. Before it, a module read the root manifest's globals (in
a spec, the spec's) no matter which file loaded it.

[`ENVY_BUNDLE`](#envy_bundle) does not show through. It always names the bundle
that the current load resolved, so a file that a bundled module loads with
`envy.loadenv` sees `nil` rather than the outer module's bundle.

## Composition

### `envy.subproject(dir)`

Runs a subproject's `envy.lua` in a sandbox and returns its globals. Requires
**envy 0.7.0 or newer**. This is how a superproject composes a subproject's
package list:

```lua title="envy.lua"
local common = envy.subproject("libs/common")

PACKAGES = envy.extend(common.PACKAGES, {
  { spec = "local.mytool@r1", source = "envy/mytool.lua" },
})
```

`dir` is the directory that holds the subproject's `envy.lua`, relative to the
calling manifest. A path to a file is an error.

What comes back is a table of every global the subproject assigned, which is
`PACKAGES` and `BUNDLES` and anything else it set. Entries in `PACKAGES` and
`BUNDLES` keep resolving against the subproject. Other globals take effect only
if the root assigns them:

```lua
VENDOR_ROOT = common.VENDOR_ROOT
```

The table also carries `PROJECT_ROOT`, the subproject's directory. It is not one
of the subproject's globals, so copying the table with `pairs` takes only what
the subproject assigned. Use it to name a spec the subproject keeps but does not
declare:

```lua
{ spec = "acme.armgcc@r1", source = common.PROJECT_ROOT .. "/envy/acme.armgcc.lua" }
```

envy reads `DEFAULT_SHELL` and `VENDOR_ROOT` from the root manifest only. A
subproject that sets one is an error unless the root assigns the same value:

```text
error: envy.subproject: /src/libs/common/envy.lua sets VENDOR_ROOT, which is read
       only from the root manifest; assign it there (e.g. VENDOR_ROOT =
       envy.subproject(...).VENDOR_ROOT)
```

Assigning it as above fixes the error. A different value in the root does not.

`PACKAGE_DEPOTS` is also root-only, but a subproject's is not an error. envy
ignores it. It does not fetch the index or build the depot's `DEPENDS`. To use
it, assign it in the root, or merge it with the root's own:

```lua
PACKAGE_DEPOTS = envy.extend({ "s3://acme-envy-packages/packages.txt" },
                             common.PACKAGE_DEPOTS)
```

`envy.extend` rejects `nil`, so only merge subprojects that declare a depot.

A subproject's entry stays tied to the file that wrote it:

- **Relative `source` paths resolve against the subproject's directory.** A
  subproject's `source = "envy/protoc.lua"` means `libs/common/envy/protoc.lua`
  no matter who loads it.
- **`bundle = "alias"` resolves against the subproject's `BUNDLES` first**, then
  the root's. Re-exporting `BUNDLES` is unnecessary, and two subprojects can use
  the same alias for different bundles.
- **Provenance is the subproject's file too.** A conflict between two
  subprojects names both manifests, not the root that loaded them. A custom
  fetch is also cached under the subproject's file, so every superproject that
  loads it shares one spec entry.

Inside the subproject's manifest, `envy.PROJECT_ROOT` is the subproject's
directory and `envy.IS_SUBPROJECT` is `true`. Both values stay with the
subproject's code when it runs later. That covers functions the root calls,
modules the subproject loads, and its `source.fetch` and depot `FETCH`
functions. The subproject has its own `envy` table, so its writes to `envy` stay
in the subproject.

When a function returns an entry, the entry's relative paths and bundle aliases
resolve against the manifest whose `PACKAGES` it ends up in. A subproject's
helper should build its paths from `envy.PROJECT_ROOT`:

```lua title="libs/common/envy.lua"
function armgcc(options)
  return { spec = "acme.armgcc@r1",
           source = envy.PROJECT_ROOT .. "/envy/acme.armgcc.lua",
           options = options }
end
```

Specs, their phases, and `SETUP` still see the root manifest's directory.
`SETUP` verbs run there too. The subproject supplies declarations, not a second
project. A [`vendor`](/concepts/vendoring) path follows the project rather than
the file, so it resolves against the root manifest's directory wherever it was
written.

`envy.IS_SUBPROJECT` is `false` when the file runs as the root. Use it to gate
an entry that only the standalone subproject needs. `--subproject` makes the
file the root, so it takes this branch too:

```lua title="libs/common/envy.lua"
if not envy.IS_SUBPROJECT then
  envy.extend(PACKAGES, {
    { spec = "acme.armgcc@r1", source = "envy/acme.armgcc.lua" },
  })
end
```

Nesting works, and two subprojects can load the same third one. A missing
directory, a path to a file, a cycle, and a `PROJECT_ROOT` global are errors:

```text
error: Failed to execute manifest script: envy.subproject: 'nope' not found (resolved to /src/app/nope/envy.lua)
error: Failed to execute manifest script: envy.subproject: 'libs/common/envy.lua' is not a directory holding an envy.lua
error: Failed to execute manifest script: envy.subproject: /src/a/envy.lua: envy.subproject: /src/b/envy.lua: envy.subproject: subproject cycle: /src/a/envy.lua -> /src/b/envy.lua -> /src/a/envy.lua
error: Failed to execute manifest script: envy.subproject: /src/sub/envy.lua assigns PROJECT_ROOT, which envy sets on its table
```

The subproject's header is otherwise inert. The one thing envy reads from it is
`@envy version`, and only when the root manifest pins one too. Newer than the
root pin is an error, because bootstrap already chose the binary:

```text
error: Failed to execute manifest script: envy.subproject: /src/sub/envy.lua requires envy 0.8.0, but the root manifest pins 0.7.0
warning: envy.subproject: /src/sub/envy.lua pins envy 0.6.1; the root manifest pins 0.7.0
```

See [The bootstrap boundary](/guides/monorepos#the-bootstrap-boundary).

### `envy.loadenv_bundle(alias, module)`

Loads a Lua module out of a bundle from the manifest's own top level, fetching
the bundle first. Requires **envy 0.4.6 or newer**. This is how a bundle ships a
helper its consumers call while they are still building `PACKAGES`:

```lua title="envy.lua"
BUNDLES = {
  tools = {
    identity = "acme.specs@r1",
    source = "https://github.com/acme/envy-specs.git",
    ref = "ded36a39bbf13744f5a0e539f2f4741fecb61dd0",
  },
}

local gh = envy.loadenv_bundle("tools", "lib.github")

PACKAGES = {
  gh.repo("libb64", "libb64/libb64", "ce864b1d3f4b9e0e2b0a4e5f0c9d8a7b6c5d4e3f"),
  gh.repo("hidapi", "libusb/hidapi", "4ebce6b0dcdd9eb9b8d8d0a0d0b9f8e7d6c5b4a3"),
}
```

The builder is the bundle's code. See
[Reaching a bundle's API from a manifest](/concepts/dependencies/bundles#reaching-a-bundles-api-from-a-manifest)
for what `lib/github.lua` holds.

`alias` is a key of the calling file's `BUNDLES`. Assign that table above the
call, because a manifest is read top to bottom. A
[subproject](#envysubprojectdir) resolves its own aliases against its own
file, the same way one of its literal entries would, and falls back to the root
manifest's `BUNDLES`.

`module` is Lua dot syntax, with the same rules as
[`envy.loadenv_spec`](#envyloadenv_specidentity-module). What comes back follows
[the module rule](#what-a-module-hands-back). The module sees
[`ENVY_BUNDLE`](#envy_bundle) and
[the calling file's globals](#what-a-module-can-read).

An entry the helper returns is parsed exactly like one written out in the
manifest, so its `bundle` names an alias of the *consuming* manifest, including
one pointing at a different bundle, and it can carry
[`vendor`](/concepts/vendoring).

The bundle is materialized during the manifest's own global scope, which is
earlier than envy fetches bundles for anything else. A bundle whose identity
starts with `local.` and whose source is a directory is read where it stands, so
edits to it land without a copy. Every other shape goes into the cache, where the
bundle's own package finds it complete a moment later, so nothing is fetched
twice. The fetch shows a progress bar, then an outcome row like any package:

```text
[acme.specs@r1] installed (1.2s)
```

A cache hit prints nothing. Before envy 0.4.11 the fetch printed
`bundle acme.specs@r1: fetching, the manifest reads it` and no progress bar.

Calling it anywhere but a manifest's top level, or naming an alias the calling
file does not have, is an error that says which:

```text
envy.loadenv_bundle: manifest scope only; a spec reaches a bundle it declared with envy.loadenv_spec(identity, module)
envy.loadenv_bundle: no bundle alias 'tolos' in the BUNDLES table of /src/app/envy.lua; declare it above the call, since a manifest is read top to bottom
```

A bundle with a [custom fetch](/concepts/dependencies/fetch-dependencies) is
refused by name, because its fetch function needs a phase to run in and its
`source.dependencies` cannot be ordered this early:

```text
envy.loadenv_bundle: bundle 'acme.cf@r1' uses a custom fetch, which needs a phase to run in; only a spec reaches one of those, with envy.loadenv_spec
```

A bad module path, a missing file, and a parse or execution error report as they
do for `envy.loadenv_spec`.

### `ENVY_BUNDLE`

A module that `envy.loadenv_bundle` or `envy.loadenv_spec` loaded out of a bundle
sees `ENVY_BUNDLE`, naming the bundle it came from. Requires **envy 0.4.7 or
newer**. It is `nil` everywhere else: in a manifest, in a spec, in anything
`envy.loadenv` reached (including a file a bundled module loads from beside
itself), and in a module a bundle's own spec reached with `require`, which is
plain Lua module loading.

| Field | Value |
| --- | --- |
| `identity` | The bundle's identity. |
| `alias` | What the calling file called it. `nil` under `envy.loadenv_spec`, which resolves by identity. |
| `root` | Absolute path of the bundle's materialized root. |

It saves a helper from being handed a name its caller already typed:

```lua title="lib/github.lua, inside bundle acme.specs@r1"
local M = {}

function M.repo(name, repo, ref)
  return {
    spec = "acme.github@r0",
    bundle = ENVY_BUNDLE.alias,      -- whatever the consuming manifest called us
    vendor = "vendor/" .. name,
    options = { repo = repo, ref = ref },
  }
end

return M
```

`ENVY_BUNDLE` is readable but is not one of the module's own globals, so a module
that returns nothing does not hand it back to its caller.

### `envy.loadenv(module)`

Loads a Lua file next to the calling file. Dots are path separators, so
`"libs.common.helpers"` means `libs/common/helpers.lua`. What comes back follows
[the module rule](#what-a-module-hands-back), and the file reads
[the caller's globals](#what-a-module-can-read). Use it for shared helper files:

```lua title="envy.lua"
local versions = envy.loadenv("envy.versions")

PACKAGES = {
  { spec = "envy.cmake@r0", bundle = "envy", options = { version = versions.cmake } },
}
```

The resolved path has to stay inside the calling file's directory. Since envy
0.4.6 one that does not is an error rather than a load from wherever it landed:

```text
envy.loadenv: module '/tmp/outside/helper' resolves outside the calling file's directory: /tmp/outside/helper.lua
```

**To compose one manifest from another, use
[`envy.subproject`](#envysubprojectdir) instead.** `loadenv` hands back a plain
table. A subproject's relative `source` paths would resolve against the wrong
directory, and its bundle aliases would not resolve at all. Neither mistake
reports an error.

**To reach a helper inside a bundle, use
[`envy.loadenv_bundle`](#envyloadenv_bundlealias-module) instead.** `loadenv`
only ever sees files beside the caller, and a manifest's neighbors are the
project's own files.

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
