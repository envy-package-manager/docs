---
sidebar_position: 2
title: envy for Agents
slug: /agents
---

# envy for agents

> This page is intentionally not prose. It is a low-token, maximal-density
> summary for AI coding agents. Humans should read the rest of the manual.

envy = per-project package manager. Lua manifest `envy.lua` at project root pins
everything incl. envy itself. No install step, server, registry, lockfile.
Committed bootstrap `<bin>/envy` + `envy.bat` downloads pinned envy on first run.

**Current release 0.4.8.** `(0.4.N+)` = minimum version, check the project's
`@envy version`. Unmarked = 0.3.0+. Newest: module reads the loading file's
globals (0.4.8), `ENVY_BUNDLE` (0.4.7), `envy.loadenv_bundle` / module return value /
`vendor` on bundle entries / fetch-retry budget (0.4.6).

Release assets under
`https://github.com/envy-package-manager/envy/releases/download/v<ver>/`:
`envy-{linux,darwin}-{x86_64,arm64}.tar.gz`, `envy-windows-{x86_64,arm64}.zip`,
`SHA256SUMS`. Archived binary already 0755.

## manifest + spec

```lua
-- @envy version "0.4.8"
-- @envy sha256sums "9f2c...e10b"
-- @envy bin "bin"
-- @envy deploy "true"

BUNDLES = {
  ["first-party"] = {
    identity = "envy.package-specs@r5",
    source = "https://github.com/envy-package-manager/package-specs.git",
    ref = "<full sha from `envy git-resolve <url> main`>",
  },
}

VENDOR_ROOT = "third_party/vendored"   -- only if something below vendors

PACKAGES = {
  -- from a bundle
  { spec = "envy.cmake@r1", bundle = "first-party", options = { version = "4.4.3" } },
  { spec = "envy.ninja@r0", bundle = "first-party", options = { version = "1.13.2" } },
  -- from a URL, pinned
  { spec = "acme.mytool@r0", source = "https://example.com/specs/mytool.lua",
    sha256 = "24ad...37be" },
  -- local file, with options, copied into the tree for a GN/Bazel build
  { spec = "local.nanocobs@r3", source = envy.abspath("envy/nanocobs.lua"),
    options = { version = "0.4.1" }, vendor = true },
}
```

- header: before first code line, one per line, exactly `-- @envy <key> "<value>"`.
  `bin` required.
- bundle contents NOT discoverable from envy (no `envy bundle list`): read the
  bundle repo (`package-specs`: `specs/` + README table). `ref` = full sha. Wrong
  `@rev` = hard error, no fallback.
- entry `sha256` pins the SPEC file, not what the spec fetches. Bundle entry: no
  `sha256`/`ref` (`BUNDLES` carries the pin), `vendor` ok (0.4.6+).

```lua
IDENTITY = "acme.mytool@r0"
PLATFORMS = { "darwin", "linux", "windows" }
EXPORTABLE = true

-- plain Lua, file-scope locals ok. Key hashes by EVERY option the payload varies with.
local hashes = {
  ["libusb/hidapi"] = {
    ["1.4.0"] = { ["darwin-arm64"] = "24ad...37be", ["linux-x86_64"] = "8c91...02af" },
  },
}

OPTIONS = {
  version = { required = true, type = "string" },
  repo    = { required = true, type = "string" },
}

-- 0.4.2+. extra label on progress rows, for one spec instantiated many times
DISPLAY = function(opts) return opts.repo end

FETCH = function(tmp_dir, opts)
  local ext = (envy.PLATFORM == "windows") and ".zip" or ".tar.gz"
  return {
    source = "https://github.com/" .. opts.repo .. "/releases/download/v"
             .. opts.version .. "/mytool-" .. envy.PLATFORM_ARCH .. ext,
    sha256 = hashes[opts.repo][opts.version][envy.PLATFORM_ARCH],
  }
end

STAGE = { strip = 1 }

-- product NAMES are manifest-global, duplicate = error: derive from an option if
-- instantiated >1x. Runs BEFORE OPTIONS validates: guard every read.
PRODUCTS = function(opts)
  local repo = opts.repo or ""
  return { [repo:match("[^/]+$") or "mytool"] = "bin/mytool" .. envy.EXE_EXT }
end
```

- OPTIONS keys exactly `required`, `type`
  (`string|int|float|boolean|table|list|semver`), `range` (`">=1 <=64"`),
  `choices` (array), `validate` (fn: `nil`/`true` ok, `false` fail, string =
  message shown). Or `OPTIONS = function` validator. **No `default`**: omitted
  option = `nil` in every verb.
- `envy.PLATFORM` `darwin|linux|windows`, `envy.ARCH` `arm64|x86_64`,
  `envy.PLATFORM_ARCH` `darwin-arm64` etc, `envy.EXE_EXT` `.exe`|`""`.

First binary (only step `init` cannot bootstrap):

```bash
curl -fsSL -O https://github.com/envy-package-manager/envy/releases/latest/download/envy-darwin-arm64.tar.gz
tar -xzf envy-darwin-arm64.tar.gz -C /tmp
/tmp/envy init . ./bin --pin-sums --deploy=true    # writes envy.lua + bin/, then delete /tmp/envy
```

Commit `envy.lua`, WHOLE bin dir, `.luarc.json` (machine-independent,
`~`/`${env:...}` placeholders). `init` gitignores `.envy/`, `.envy-cache-*`.

Existing project: NO setup step. `./bin/<tool>` or `./bin/envy run <cmd>`
bootstraps envy + installs that tool's subgraph on demand. Windows
`bin\envy.bat`, `bin\<tool>.bat`. Shell hook puts bin dir on PATH, so bare
`envy sync` / `cmake` (the form the rest of the docs use). CI/scripts: explicit
path.

## model

- manifest globals: `PACKAGES` (required), `BUNDLES`, `PACKAGE_DEPOTS`,
  `DEFAULT_SHELL`, `VENDOR_ROOT`. Real Lua: conditionals, `envy.import`,
  `envy.extend` legal.
- directives: `version` pins envy. `sha256sums` pins release checksums, needs
  `version`. `bin` REQUIRED, relative to manifest, no drive / leading sep / `~`
  / `$` / `%` (`.`/`..` legal, `deploy` judges escape). `mirror` = release
  mirror. `deploy "true|false"` **default FALSE**: without it `sync` deploys
  nothing + warns. `root "true|false"` superproject boundary, default true.
  `cache-local` = cache tree in project, tuned by `cache-mode`, `state-dir`
  (0.2.0+). `cache-posix`/`cache-win` = errors. `schema`.
- spec = one package recipe. `IDENTITY = "ns.name@rev"` required, `@rev`
  versions the SPEC not the payload, `local.*` = project-local. Package =
  `(identity, options, platform)`. Canonical key `ns.name@rev{["k"]=v,...}`,
  keys quoted + sorted. Option tables: all string keys or contiguous `1..n`, no
  functions, any depth.
- verbs `FETCH → STAGE → BUILD → INSTALL`, plus `SETUP` (named CHECK/INSTALL
  pairs). See [verb forms](#verb-forms).
- products: `PRODUCTS = { cmake = "bin/cmake" }`. Consumers name the product,
  not the identity: `envy product cmake`, `envy.product("cmake")`, `./bin/cmake`.
  Non-executable (header, data file):
  `PRODUCTS = { doctest_h = { value = "doctest.h", script = false } }` = no
  wrapper, path via `envy product doctest_h`.
- reproducibility: no lockfile. Pins = `@envy version` + `sha256sums`, per-source
  `sha256`, git `ref` full sha (`envy git-resolve <url> <ref>`). Unhashed fetch
  re-downloads every run.
- **re-exec**: every manifest-aware command compares own version to
  `@envy version` FIRST, mismatch → replaces itself with that release. Invoked
  binary ≠ acting binary, `envy --version` ≠ project version: read the header.
  Lookup: project cache tree → user-wide tree (see cache) → download from mirror
  to temp, checked against `sha256sums` if pinned, child installs itself into
  cache. ONE hop (`ENVY_REEXEC=1`), argv minus envy-choosing options
  (`init --envy-version`). Skipped: no pin, match, self `0.0.0` (dev build),
  `ENVY_NO_REEXEC`. Hard error: resolved cache mode (`cache-local`/`cache-mode`/
  `state-dir`/`envy cache --local` marker) + pin `< 0.2.0`. Never re-exec: `use`,
  `cache`, `version` (read header as text). `--trace=file:` spans the handoff
  (0.4.4+).
- **bin dir**: `envy`, `envy.bat`, one wrapper per product (+ `.bat` twin under
  `--platform all`). Fresh clone: `./bin/cmake` → `bin/envy` → pinned envy →
  install. Wrappers resolve at call time
  (`exec "$("$ENVY_SCRIPT_DIR/envy" product cmake)" "$@"`), never stale. Each
  prepends own bin dir to PATH (siblings callable), exports `ENVY_PROJECT_ROOT`
  (root manifest only, `root "false"` keeps caller's). Schema `4`
  (`envy-managed schema "4"`, POSIX `set -Eeuo pipefail`). Bootstrap restamped
  on content change.
- **ownership**: envy touches only bin files containing `envy-managed`
  (substring). Unmarked = skipped (`--strict`: error), so your own `bin/gn` owns
  that name for good (supported way to wrap/pre-step). `envy`/`envy.bat` always
  restamped, never pruned. Filtered `sync` prunes marked wrappers outside the
  filtered subgraph.
- deploy walk-back: ROOT manifest whose `@envy bin` walks up to a DIFFERENT
  `envy.lua` = error (`..` in bin, `.git` between, `--manifest` outside bin
  tree). Nothing found / not named `envy.lua` = warn. `root "false"` skips it
  (superproject restamps submodule bin byte-identically). Stamping from an
  unpinned version (dev build, `ENVY_NO_REEXEC`) warns.
- **manifest discovery**: walk up from anchor. `--manifest <path>` (no walk) >
  `--project <dir>` > CWD. `--subproject` = nearest to CWD even under
  `--project`, first `envy.lua`, ignores `@envy root`. `envy run` also anchors
  on `-- <script>` or a first arg naming an existing file, `--project` wins.
  Bootstrap + wrappers inject `--project <own dir>` before argv (typed one still
  wins), so `../B/bin/uv run x.py` acts on B.

## cache

- content-addressed, safe to delete. Default user-wide shared, or a project-local
  tree. Root: `--cache-root`/`$ENVY_CACHE_ROOT` (absolute) >
  `.envy-cache-local`/`.envy-cache-shared` marker (`envy cache --local/--shared`) >
  `@envy cache-mode` > `@envy cache-local` present > default
  (`~/Library/Caches/envy`, `$XDG_CACHE_HOME/envy`, `%LOCALAPPDATA%\envy`).
- layout `envy/<ver>/{envy,envy.lua}`, `envy/latest`, `packages/`, `specs/`,
  `shell/`, `locks/`. Entry `identity/<platform>-<arch>-blake3-<hash>`.
  First-run stderr notice for LOCAL tree only. Never prompts.
- local tree reads user-wide, never writes it: launchers/re-exec try
  `<project cache>/envy/<ver>/envy` then `<user-wide>/envy/<ver>/envy`, the
  second ONLY without `@envy sha256sums`. Never the reverse. Non-regular / empty
  / non-exec candidate skipped. Borrowed binary self-deploys into project tree.
  `envy cache --local/--shared` deploys into the mode being established.
  `envy cache --root` / `--user-wide-root` print the two roots.
- shell hooks: user-wide only (`--cache-root`/`$ENVY_CACHE_ROOT` else default).
  Local-cache project writes NO hooks, `envy shell` says so. Refresh by content
  (`_ENVY_HOOK_STAMP=<ver>:<digest>`), never overwrites a hook a NEWER envy
  wrote. Refresh prints once:
  `Shell hooks updated (bash, zsh, fish) — restart your shell`.

## shells

- string verbs + strings returned from function verbs run under `DEFAULT_SHELL`
  (root manifest only). Default bash (POSIX), PowerShell (Windows). Built-ins
  `ENVY_SHELL.BASH|SH|CMD|POWERSHELL`, wrong platform = error.
  `{ file = <path|argv>, ext = ".py" }` → `argv <tempfile>`.
  `{ inline = argv }` → `argv <script text>`. Per call:
  `envy.run(script, { shell = ... })`.
- envy-installed interpreter REQUIRES the `{ DEPENDS, SHELL }` form (bare
  function has no edges, `envy.product` fails):
  `DEFAULT_SHELL = { DEPENDS = { "envy.python@r1" }, SHELL = function() return { file = { envy.product("python3") }, ext = ".py" } end }`.
  DEPENDS = queries vs PACKAGES (strict matcher, see
  [dependencies](#dependencies)). SHELL must be a function, either half alone =
  error. Lazy: a run with no string verb never installs it. Bootstrap closures
  (DEPENDS, `source.dependencies`, PACKAGE_DEPOTS DEPENDS, manifest Lua) use the
  platform built-in.

## windows

Same manifest, specs, cache layout. Not a port.

- `bin\envy.bat` parses the header itself, walks up, honors
  `ENVY_CACHE_ROOT`/`ENVY_MIRROR`. Wrappers `bin\<tool>.bat` (`setlocal`,
  forward `%ERRORLEVEL%`).
- `--platform posix|windows|all` on `init`/`sync`/`deploy`, default host.
  Bootstrap AND wrappers per flavor: plain `sync` on macOS does NOT restamp
  `envy.bat`. Cross-platform repo: `--platform all`. Host-only deploy never
  prunes the other flavor.
- newlines per TARGET: CRLF every `.bat`, LF else, POSIX 0755. LF `.bat`
  silently stops parsing `@envy` directives. `core.autocrlf` → every deploy says
  "updated": `.gitattributes` `bin/** -text` (`*.bat eol=crlf` also ok).
- string verbs: PowerShell (no profile, policy bypassed) from a temp script.
  POSIX gets `bash -e`. Windows fail-fast injected only when `check=true`
  (default), so `check=false` keeps going on Windows where POSIX stops.
- paths native (`envy.path.join`, `envy.abspath`, `envy product` → backslashes).
  Build filesystem paths with `envy.path.join`. Declarative package-relative
  strings always `/`: `PRODUCTS` values, `STAGE.only`, `VENDOR`, `vendor`.
- `envy run <name>` finds `bin\<name>.bat` (spawn + wait, forwards exit). PATH
  sep `;`. Long paths, AV file locks handled.
- hook PowerShell only:
  `. "${env:USERPROFILE}/AppData/Local/envy/shell/hook.ps1"` in `$PROFILE`.
  cmd.exe: no hook, use `.bat` / `envy run`.
- PowerShell `>` = UTF-16: redirect `export`/`hash`/`product --json` via
  `| Out-File -Encoding ascii|utf8`.
- host mutation: `winget`/`choco` in a USER_MANAGED SETUP pair. Elevation needs
  `interactive = true`.

## verb forms

| Verb | string | table | function | omitted |
|---|---|---|---|---|
| `FETCH(tmp_dir, opts)` | one URL, unverified | `{source, sha256?, ref?, dest?, post_data?}` or array | imperative, or return any declarative form | error unless `USER_MANAGED` |
| `STAGE(fetch_dir, stage_dir, tmp_dir, opts)` | shell | `{strip=N, only={globs}}` | programmatic | extract all fetched archives |
| `BUILD(install_dir, stage_dir, fetch_dir, tmp_dir, opts)` | shell, cwd = stage | no | may return string → shell | no-op |
| `INSTALL(install_dir, stage_dir, fetch_dir, tmp_dir, opts)` | shell | no | may return string → shell | promote stage to install dir |
| `SETUP.<name>.CHECK(pkg_dir, opts)` | shell, exit 0 = satisfied | no | bool, or string → shell | pair needs CHECK + INSTALL |
| `SETUP.<name>.INSTALL(pkg_dir, opts)` | shell | no | may return string → shell | n/a |

- other spec globals: `DEPENDENCIES`, `PLATFORMS` (`darwin|linux|windows[-arch]`),
  `USER_MANAGED` (host-mutating: SETUP pairs only, no FETCH/STAGE/BUILD/INSTALL),
  `EXPORTABLE` (false → depot exports fetched bytes, not install output),
  `VENDOR` (selectors: what of `pkg/` a vendoring manifest copies), `DISPLAY`
  (0.4.2+).
- SETUP = host work that is NOT part of the package hash. Runs only if selected
  (`setup = {"pair"}` on the entry).
- **PRODUCTS runs BEFORE OPTIONS**, gets the entry's options raw: unvalidated,
  no defaults, `{}` if none. Every key may be nil. `opts.target:lower()` →
  `attempt to index a nil value (field 'target')`, and `required` does NOT save
  you (OPTIONS has not run). Guard every read. `DISPLAY` runs AFTER OPTIONS,
  gets the checked table.

## output

- **exit 0 = success, every command.** `envy run` forwards its child's code.
  Only reliable signal.
- human output → stderr. stdout = machine-readable only, empty unless the
  command answers: `product` (path, `--json`), `package` (dir), `hash`
  (`<sha256>  <name>`), `export`/`merge-depot` (index lines), `git-resolve`
  (sha), `import` (dir), `cache` (usage).
- row = `[identity]` + spec `DISPLAY` + status, columns padded.
- `DISPLAY` (0.4.2+): string or `function(options)` → string|nil, after OPTIONS.
  Adds to identity, reaches the outcome line. One printable line: any byte
  `< 0x20` or `0x7f` = error. No spec sets one = no column.
- **no work = no row (0.4.2+).** Rows only for timed outcomes (`installed`,
  `fetched`, `imported from depot`), a SETUP pair that ran, a vendor copy that
  wrote. `cache hit`, `setup complete`, `local bundle` silent. Warm `install`
  writes NOTHING to the terminal (0.4.3+). `deploy:` summary only when a wrapper
  changed. **Silence ≠ failure: check exit code.**
- off a TTY every package reports, cache hits too: piped run lists MORE than
  terminal. `--verbose` narrates all.
- short/empty CI log: stderr not captured (`2>&1`), global `-q`, Windows `>`
  UTF-16, `platforms` filter. Not the silence rule.
- vendored package's row = `vendored N files to <dir>`, replaces `cache hit` and
  `installed (2.5s)` alike (0.4.5+). `pkg_outcome` trace keeps the payload
  verdict. Under `envy vendor` the command reports, not the row.
- vendor destinations shown project-relative with `/`. Absolute only in
  filesystem-failure errors and "resolves outside the project".

## vendoring

0.4.0+. Copy cached `pkg/` into the project tree for build systems that need
in-tree inputs (GN, Bazel `//` labels). Make/CMake: use `envy product`'s
absolute path, skip this. Copy, not move/link. Cache stays authoritative.

- manifest asks (`vendor` on a PACKAGES entry, bundle shape 0.4.6+), spec
  narrows (`VENDOR = { selectors }`, absent/empty = all, bad glob fails at
  spec_fetch). A spec never requests it. DEPENDENCIES / `source.dependencies`
  entry with `vendor` = unknown-key error.
- forms: `true` (derived leaf under `VENDOR_ROOT`) | `false`/absent |
  `"dir"` (project-relative, no VENDOR_ROOT needed) | `{ path, auto_sync }` |
  `{}` = true. `VENDOR_ROOT` needed ONLY for `true`.
- derived names escalate per colliding group: `name` → `ns.name` → `ns.name@rev`
  → `ns.name@rev-<options hash>`. Explicit path never escalates.
- path: relative, no leading sep / drive / `.` / `..` / `~` / `$` / `%`.
  Anchored on ROOT manifest dir, NOT the file that wrote it (unlike `source`
  under import): a component's `vendor` path differs standalone vs imported.
  Gate on `ENVY_IMPORTER` or vendor from root.
- whole plan checked before any write: duplicate or nested destinations = error
  naming both. Platform-excluded entries dropped first. Destination resolved
  through symlinks, outside project = refused.
- per-package phase of `install`/`sync`, so `install` writes the work tree when
  the manifest vendors.
- drift: no project-side state. BLAKE3 tree digest of destination vs pristine
  digest in cache entry. ANY mismatch (edit, stray/deleted file, empty dir,
  symlink target, exec bit, package moved) → wipe + recopy. mtime ignored.
  Committed vendored tree adopted as-is on a fresh machine.
- `auto_sync = false`: mismatch → warning naming `envy vendor --force`, dir left.
  Absent destination still copied.
- destination that IS a symlink: wipe removes link, copy makes real dir.
- never prunes: moved destination leaves old dir, removed `vendor` leaves dir.
- refusals: `USER_MANAGED` (no payload), `vendor = ""`, bad type, unknown key
  in table, non-boolean `auto_sync`.
- `VENDOR_ROOT` root-only (see [superprojects](#superprojects)).
- selector language shared by `STAGE.only`, `envy.extract` `only`,
  `envy extract --only`, `VENDOR`, `envy hash --tree --only`: `/`-separated,
  case-sensitive, `*`/`?` within a component, `**` spans, `[a-z]`/`[!a-z]`.
  Leading `!` excludes, beats inclusion. Empty include list = all. Inclusion
  matching nothing = error, exclusion matching nothing = fine.
- `envy hash --tree <dir>` = the digest vendoring compares (path, kind, exec
  bit, contents, empty dirs. Not mtimes. Symlinks by stored target. Exec bit 0
  on Windows).

## dependencies

- kinds: strong `{spec, source}` | weak (query + `weak = {fallback}`, used only
  if nothing else provides) | reference-only (query, satisfied elsewhere) |
  product `{product = "ninja"}`.
- `needed_by` = phase of the DEPENDENT that blocks:
  `check|import|fetch|stage|build|install`, default `build`.
- entry shapes closed. Unknown key = error listing allowed, prefixed
  `<manifest>: PACKAGES[2]:` / `spec 'x@r1': DEPENDENCIES[2]:`.
  - manifest PACKAGES:
    `spec|source|bundle|sha256|ref|options|platforms|setup|needed_by|product|vendor`.
    Always a table. No `weak`, no `source = { fetch = ... }`.
  - bundle entry: `spec|bundle|options|platforms|setup|needed_by|product|vendor`.
  - spec DEPENDENCIES: PACKAGES set minus `platforms`/`vendor`, plus `weak`.
    Gate platforms with `if envy.PLATFORM`.
  - `source.dependencies`: also minus `needed_by` (always spec_fetch). Strong
    only, whole closure.
  - `weak = {...}` fallback: complete strong decl, no `bundle|setup|weak|needed_by`.
- `envy.product` / `envy.package` / `envy.loadenv_spec`: DIRECT deps only,
  transitive = error naming it. Declare it too (same package, built once).
  Fuzzy match, earliest `needed_by` wins, ties by identity.
- one identity, one option set, per dependency list: same identity + different
  `options` = error. NOT top-level PACKAGES: N option sets there = N packages
  (DISPLAY's use case).
- cycle = error naming path (`Dependency cycle detected: a -> b -> c -> a`).
- **fetch dependencies**: installed before the dependent's spec is fetched
  (Artifactory / auth CLI).
  `source = { dependencies = {{spec, source}}, fetch = function(tmp_dir, opts) ... end }`.
  fetch fn commits `spec.lua` (+ helper files) via `envy.commit_fetch`.
  `envy.product`/`envy.package` work inside. Spec-declared fetch runs as the
  CHILD: entry's own options + own `source.dependencies`, one spec cache entry
  per option set. `source` table without `fetch`/`dependencies` = error.
- bundles: one container, many specs.
  `BUNDLES = { alias = { identity, source, ref } }`, entry `bundle = "alias"`
  instead of `source`. Alias resolves against the DECLARING file's `BUNDLES`
  (a spec's own, an imported manifest's own then root's). Lua under `lib/`: see
  [lua modules](#lua-modules).
- same identity declared with different sources = error naming both files.
- depot (OPTIONAL): `PACKAGE_DEPOTS = { "s3://bucket/packages.txt" }`, index of
  prebuilt `.tar.zst`. Hit skips fetch + build. Bypass `--ignore-depot` /
  `ENVY_IGNORE_DEPOT=1`. Publish: `envy export` → `envy merge-depot` → upload.
  Depot's own DEPENDS closure exempt from the index.
- queries: fuzzy `name` | `ns.name` | `name@rev` | canonical key, dotted rev ok
  (`gcc@13.2.0`). CLI takes FIRST match in manifest order. `DEFAULT_SHELL` /
  `PACKAGE_DEPOTS` DEPENDS strict: 0 or 2 distinct matches = error.
- failure: each package's own error, dedup + sorted. Hang →
  `Deadlock: no task is running while N wait(s) are blocked:` + each wait.

## lua modules

| call | scope | resolves against |
| --- | --- | --- |
| `require(mod)` | spec INSIDE a bundle | bundle root, on `package.path` |
| `envy.loadenv(mod)` | anywhere, incl. `envy lua` | CALLING FILE's dir |
| `envy.loadenv_spec(id, mod)` | spec PHASE functions only | declared dependency's root (bundle root if from one) |
| `envy.loadenv_bundle(alias, mod)` | manifest GLOBAL SCOPE only (0.4.6+) | calling file's `BUNDLES` alias |

- `envy.*` loaders: fresh sandbox, ALWAYS re-execute. `require` caches.
- **returns (0.4.6+)**: module's returned table, else globals it assigned (if it
  returned nothing), else error naming module. `local M = {} ... return M`
  works. Pre-0.4.6: always globals, `return M` came back `{}`.
- **reads (0.4.8+)**: sandbox falls through to the LOADING file's globals: root
  manifest, imported fragment (its `VENDOR_ROOT`, `ENVY_IMPORTER`), spec, outer
  module. Writes stay in the sandbox. Pre-0.4.8: root manifest's (or spec's)
  globals regardless of loader, so a module loaded by an `envy.import`ed file or
  another module silently read the root's values / `nil`.
- `mod` for `loadenv_spec`/`loadenv_bundle`: dot syntax, no separators, no
  `..`, no leading/trailing `.`, re-checked under load root. `loadenv` allows a
  separator, cannot escape caller's dir (0.4.6+).
- `loadenv_bundle`: fetches the bundle DURING manifest global scope, so entries
  go straight into PACKAGES. `BUNDLES` must be assigned ABOVE the call. Fragment:
  own `BUNDLES` then root's. `local.` dir bundle read in place, else cached once.
  Prints `bundle <id>: fetching, the manifest reads it`. Refused: outside
  manifest scope, unknown alias (names alias + file), custom-fetch bundle.
  Trace `lua_ctx_loadenv_bundle`.
- returned entries parse like literal ones: `bundle` = CONSUMER's alias (any,
  even another bundle), `vendor` ok.
- **`ENVY_BUNDLE`** (0.4.7+): `{ identity, alias, root }` in a module that
  `loadenv_bundle`/`loadenv_spec` loaded out of a bundle. `alias` = caller's name
  for it, `nil` under `loadenv_spec`. Whole global `nil` elsewhere: manifest,
  spec, `envy.loadenv` target (incl. a sibling a bundled module loads, never
  inherited), `require`d module. Not a module global: not handed back, not
  leaked into `options`.
- bare globals envy installs: `ENVY_SHELL`, `ENVY_IMPORTER`, `ENVY_BUNDLE`.

Builder pattern, a bundle shipping the helper that writes its consumers' entries:

```lua
-- lib/github.lua, in the bundle
local M = {}
function M.repo(name, repo, ref)
  return { spec = "acme.github@r0", bundle = ENVY_BUNDLE.alias,
           vendor = (VENDOR_ROOT or "vendor") .. "/" .. name,  -- consumer's VENDOR_ROOT
           options = { repo = repo, ref = ref } }
end
return M

-- consumer envy.lua (BUNDLES above)
VENDOR_ROOT = "third_party"
local gh = envy.loadenv_bundle("tools", "lib.github")
PACKAGES = { gh.repo("libb64", "libb64/libb64", "<sha>") }   -- → third_party/libb64
```

Spell the leaf: N entries of one identity with `vendor = true` escalate to
options-hash names.

## superprojects

- component manifest: `@envy root "false"`. Superproject:
  `local sub = envy.import("libs/common")` +
  `PACKAGES = envy.extend(sub.PACKAGES, {...})`. Commands walk up to root,
  `--subproject` stops at nearest.
- `envy.import(path)`: MANIFEST SCOPE ONLY (not specs, not `envy lua`). Relative
  to caller, directory → `envy.lua`. Sandbox, returns its globals. Nesting ok,
  cycle = error naming chain.
- imported entry stays tied to its file: relative `source` → imported dir,
  `bundle` → its `BUNDLES` then root's (no re-export). Provenance (conflict
  messages) and custom-fetch cache key = imported file. Project root, SETUP cwd
  = root.
- only `PACKAGES`/`BUNDLES` tagged, splice others by hand. Root-only
  `PACKAGE_DEPOTS`/`DEFAULT_SHELL`/`VENDOR_ROOT`: set in an import without the
  root holding that value = error. `VENDOR_ROOT = sub.VENDOR_ROOT`.
- `ENVY_IMPORTER` = importer's absolute path in the imported file (and in modules
  it loads, 0.4.8+), `nil` standalone. `if not ENVY_IMPORTER then` = standalone
  gate.
- imported header INERT (`bin`, `deploy`, `cache-*`, `state-dir`, `mirror`,
  `sha256sums`, `root`). Only `@envy version` checked, and only if root pins:
  newer than root = error, older = warn.

## CLI

Global flags BEFORE subcommand: `--verbose -q --trace[=sinks] --cache-root
--project` (`envy sync --verbose` = parse error). `--project` honored by `sync
install deploy vendor product package run export import use cache shell`.
`[q]` = package queries, omitted = whole manifest.

- `install [q]`: packages only, NO bin-dir writes (vendored trees yes). DEFAULT
  for "just want bytes": warm CI/Docker cache, prefetch, prove a spec builds,
  bump a version option, after cache wipe or `envy cache --local/--shared`.
- `sync [q]`: install + deploy. Needed only when the bin dir changes: product
  added/removed/renamed, after `use`, `--platform all`, restoring bin dir.
  Options edit → `install`. Unsure → `sync` is safe.
- `deploy [q] [--strict] [--platform ...]`: scripts only, no installs, prunes
  marked wrappers outside graph.
- `vendor <q>... | --all [--force] [--dry-run] [--threads N] [--manifest=...]`
  (0.4.0+): vendor step alone. Re-execs. No `--subproject`/`--ignore-depot`.
  Selection REQUIRED + exclusive (bare = error, q + `--all` = error). Plan
  checked over whole manifest, then filtered, vendored deps of a target NOT
  included. Runs targets to completion (fetch/build), `--dry-run` too. Named
  package without `vendor` = error (`'x' is not vendored`), `--all` skips them,
  manifest vendoring nothing = error. `--force` = treat all as
  `auto_sync = true` (up-to-date still no-op). `--dry-run` = no destination
  writes (cache still written), `would (re-)vendor`. `--threads 0` = default,
  negative = error. Report per target, stderr: `vendored N files to <dir>` |
  `re-vendored N files to <dir>: contents were dirty` | `up to date: <dir>` |
  `kept <dir>: contents differ from the package`.
- `init <project-dir> <bin-dir> [--envy-version X.Y.Z] [--mirror URL]
  [--pin-sums] [--deploy=bool] [--root=bool] [--platform ...]`: manifest +
  bootstrap + `.luarc.json`, appends `.envy/`, `.envy-cache-*` to `.gitignore`
  if `.git` exists (skips equivalents). `--envy-version` re-execs into that
  release (pin, stamp, types all from it), downloads from `--mirror`. Dev build /
  `ENVY_NO_REEXEC` warns, stamps itself. Relative `<bin-dir>` resolves against
  `<project-dir>`, NOT cwd. Escaping bin dir under root manifest warns. No
  relative path possible (two Windows drives) = error.
- `product [name] [--json]`: path. Name installs its provider. No name lists.
  `--json` = all products, NO install.
- `package <identity>`: install, print pkg dir.
- `run <cmd...>`: exec with bin dir on PATH + `ENVY_PROJECT_ROOT`.
- `shell <bash|zsh|fish|powershell>`: hook source line.
- `use <version>`: retarget the pin.
- `git-resolve <url> <ref>`: full sha.
- `hash <paths>`: sha256 lines (depot). `hash --tree <dirs>`: BLAKE3 tree digest
  per dir, `--only`, `--threads` (0 = perf cores), `--json` (`duration_ms` =
  hash time), `--stats` (stderr, in object under `--json`, `-q` suppresses).
  `--tree` excludes `--prefix`. Tree flags without `--tree` = error. Args must be
  dirs.
- `export`, `import`, `merge-depot`: depot publish/consume.
- no manifest needed: `fetch <src> <dst>`,
  `extract <archive> [dst] [--only PATH|GLOB|!GLOB]...`, `hash`, `git-resolve`,
  `lua <script>`. Built in: AWS SDK (`s3://`, ambient creds, no AWS CLI),
  libgit2 (no `git`), libarchive (tar/gz/xz/bz2/zst/zip/7z/rar/iso).
- `cache [--root | --user-wide-root | --local | --shared]`: location + usage,
  one flag max. `version`. `mirror-envy` (`s3://` creds checked before download).
- fetch retry: `connect`, `transfer`, `timeout`, 5xx, 429 retry. Other 4xx, bad
  URL, local error = fatal. Budget (0.4.6+): `ENVY_FETCH_BUDGET_MS` default
  90000 from FIRST failure, never-handshake capped 5s. `ENVY_FETCH_ATTEMPTS` =
  ceiling, default 10. Backoff 1x/2x/4x `ENVY_FETCH_RETRY_BASE_MS` (1000) ±50%,
  max 30s. `Retry-After` = jittered floor, longer than remaining budget → give
  up. `s3://` excluded (SDK retries). Row `retry 2 in 6s (http_status) tool.tar.gz`.
  Non-status error names what arrived
  (`... after 0 of 54881 bytes (HTTP 200, text/html)`) = HTML interstitial, not
  network.
- editor: `init` writes `.luarc.json` (3 platform cache paths, LuaCATS types on
  `workspace.library`). `sync`/`deploy` rewrite stale `envy/<semver>` entries,
  keep the rest. Delete to opt out. `BUNDLES` not in `diagnostics.globals`,
  `ENVY_BUNDLE` is (0.4.7+).
- `--trace[=sinks]`: one structured event per decision. Schemas in the Logging &
  Tracing reference, not here. `pkg_outcome` = PAYLOAD verdict (`cache_hit`,
  `installed`, `imported`, ...) whatever the row said.
- env read: `ENVY_CACHE_ROOT`, `ENVY_MIRROR`, `ENVY_IGNORE_DEPOT`,
  `ENVY_NO_REEXEC`, `ENVY_FETCH_BUDGET_MS`, `ENVY_FETCH_ATTEMPTS`,
  `ENVY_FETCH_RETRY_BASE_MS`. Hook-only `ENVY_SHELL_HOOK_DISABLE`,
  `ENVY_SHELL_NO_ENTER_EXIT_ANNOUNCE`, `ENVY_SHELL_NO_ICON`. Written:
  `ENVY_PROJECT_ROOT`, `PATH` (by `envy run`, hook, every wrapper).

## lua API

`envy.run(script|{lines}, {quiet, check, capture, interactive, env, cwd, shell})`,
`envy.fetch(src, {dest})`, `envy.commit_fetch`, `envy.verify_hash`,
`envy.extract`, `envy.extract_all(src, dst, {strip, only})`,
`envy.copy/move/remove/exists/is_file/is_dir`, `envy.path.*`, `envy.abspath`,
`envy.template(str, vars)`, `envy.product(name)`, `envy.package(identity)`,
`envy.options(schema)`, `envy.import`, `envy.extend`, loaders (see
[lua modules](#lua-modules)), constants (see top). Log:
`envy.debug/info/warn/error` + `print` → stderr, `envy.stdout` → stdout (a
contract, keep it clean).
