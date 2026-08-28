---
sidebar_position: 2
title: envy for Agents
slug: /agents
---

# envy for agents

> This page is intentionally not prose. It is a low-token, maximal-density
> summary for AI coding agents. Humans should read the rest of the manual.

envy: per-project package manager. Lua manifest `envy.lua` at project root pins
everything including envy itself. No install step, no server, no registry, no
lockfile. Committed bootstrap script `<bin>/envy` (plus `envy.bat`) downloads the
pinned envy binary on first run.

Using an already-set-up project needs NO setup step: run `./bin/<tool>` (a
committed wrapper) or `./bin/envy run <cmd>`, and the wrapper bootstraps envy and
installs that tool's subgraph on demand. `./bin/envy sync` is for after a
manifest edit, or to install everything up front. Windows: `bin\envy.bat`,
`bin\<tool>.bat`. With the shell hook installed the bin dir is on PATH, so bare
`envy sync` and `cmake` work, which is the form the rest of the docs use. In CI
and scripts use the explicit path.

## model

- manifest `envy.lua`: header comment directives `-- @envy key "value"` before
  the first code line, plus globals `PACKAGES` (required), `BUNDLES`,
  `PACKAGE_DEPOTS`, `DEFAULT_SHELL`. Manifest is real Lua: conditionals,
  `envy.loadenv()`, `envy.extend()` all legal.
- shells: string verbs, and strings returned from function verbs, run under
  `DEFAULT_SHELL`. Default bash on POSIX, PowerShell on Windows. Built-ins
  `ENVY_SHELL.BASH|SH|CMD|POWERSHELL`, platform-validated, wrong platform is an
  error not a fallback. Custom: `{ file = <path|argv>, ext = ".py" }` runs
  `argv <tempfile>`; `{ inline = argv }` runs `argv <script text>`. The function
  form can resolve an envy-installed interpreter, but only through the
  `{ DEPENDS, SHELL }` wrapper:
  `DEFAULT_SHELL = { DEPENDS = { "envy.python@r1" }, SHELL = function() return { file = { envy.product("python3") }, ext = ".py" } end }`.
  DEPENDS entries are queries against PACKAGES; DEPENDS requires SHELL to be a
  function; envy.product/envy.package authorize against a synthesized
  `envy.DEFAULT_SHELL@v1` consumer; the closure installs before the shell
  resolves and before any other string verb; closure members (transitively) run
  under the platform built-in, which is the bootstrap carve-out. A bare
  `DEFAULT_SHELL = function()` has no edges, so envy.product fails there.
  Per-call override: `envy.run(script, { shell = ... })`.
- directives: `version` pins envy. `sha256sums` pins release checksums and
  requires `version`. `bin` is REQUIRED and names the project bin dir. `mirror`
  sets the release mirror. `deploy "true"` enables product scripts. `root
  "true|false"` marks a superproject boundary, default true.
  `cache-local` puts the cache in a tree inside the project (`cache-mode` and
  `state-dir` tune that; all three need envy 0.2.0, and `cache-posix`/`cache-win`
  now error). `schema` sets the schema version.
- spec = Lua file describing one package: `IDENTITY = "ns.name@rev"` required,
  where `@rev` versions the spec rather than the payload, and `local.*` means
  project-local. Package = installed instance keyed `(identity, options,
  platform)`.
- verbs: `FETCH → STAGE → BUILD → INSTALL`, plus `SETUP` (named CHECK/INSTALL
  pairs). Each verb: string, table, function, or omitted, all with defaults. See
  table below.
- products: spec exports named entry points, `PRODUCTS = { cmake = "bin/cmake" }`.
  Consumers use the product name rather than the identity: CLI
  `envy product cmake`, Lua `envy.product("cmake")`, or deployed wrapper script
  `./bin/cmake`.
- **commit the whole bin dir**: `<bin>/envy` and `envy.bat` plus every deployed
  product script (and `.bat` twin under `--platform all`). A fresh clone then
  runs `./bin/cmake` with nothing installed: the wrapper calls `bin/envy`, which
  downloads pinned envy, which installs the package. Wrappers resolve at call
  time (`exec "$(envy product cmake)" "$@"`), so they never go stale.
- **ownership**: envy creates, updates, and prunes only bin-dir files containing
  the `envy-managed` marker (substring match). An unmarked file is skipped, or an
  error under `--strict`. Writing your own `bin/gn` therefore takes that name
  permanently, which is the supported way to wrap several products or run a
  pre-step. `envy`/`envy.bat` are always restamped, never pruned. A filtered
  `sync` prunes marked wrappers outside the filtered subgraph.
- cache: content-addressed, safe to delete; user-wide and shared across projects
  by default, or a tree inside the project. Root precedence: `--cache-root` or
  `$ENVY_CACHE_ROOT` (absolute), then a `.envy-cache-local`/`.envy-cache-shared`
  marker from `envy cache --local/--shared`, then `@envy cache-mode`, then
  `@envy cache-local` being present, then platform default
  (`~/Library/Caches/envy`, `$XDG_CACHE_HOME/envy`, `%LOCALAPPDATA%\envy`).
- reproducibility: no lockfile. Pins live in the manifest: `@envy version` plus
  `sha256sums`, per-source `sha256`, git `ref` as a full sha via
  `envy git-resolve <url> <ref>`. Unhashed fetches re-download every run.

## windows

First-class, not a port. Same manifest, same specs, same cache layout.

- bootstrap `bin\envy.bat` (batch, parses the `@envy` header itself, walks up for
  the root manifest, honors `ENVY_CACHE_ROOT`/`ENVY_MIRROR`). Wrappers are
  `bin\<tool>.bat`, using `%~dp0envy.bat product <name>` then
  `call "%PRODUCT_PATH%" %*`, forwarding `%ERRORLEVEL%`.
- `--platform posix|windows|all` on `init`/`sync`/`deploy` selects which script
  flavors get written, defaulting to the host. Bootstrap AND wrappers are
  per-flavor, so a plain `sync` on macOS does NOT restamp `envy.bat`. Use
  `--platform all` in a cross-platform repo. A host-only deploy does not prune
  the other flavor.
- scripts are written LF on every platform, POSIX ones mode 755. `core.autocrlf`
  rewriting them makes every deploy report "updated"; fix with `bin/** -text` in
  `.gitattributes`.
- string verbs default to PowerShell, invoked
  `powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File <temp .ps1>`;
  cmd is `cmd.exe /D /V:ON /S /C <temp .cmd>`. POSIX gets `bash -e`, so fail-fast
  is free there; on Windows `check=true` (default) makes envy INJECT fail-fast
  (`$ErrorActionPreference='Stop'`, per-line `$LASTEXITCODE` test, final
  `$Error.Count` check; cmd gets `|| exit /b !errorlevel!` per line). `check=false`
  injects nothing, so a Windows script keeps going where a POSIX one stops.
- paths are native: `envy.path.join`/`envy.abspath`/`envy product` all yield
  backslashes. Never hardcode `/`. `envy.EXE_EXT` is `".exe"`.
- cache `%LOCALAPPDATA%\envy`; long-path prefix used internally for cache scans;
  deletions retry with backoff around antivirus handles.
- `envy run <name>` finds `bin\<name>.bat` (no `execvp`, so it spawns, waits, and
  forwards the exit code). PATH separator `;`, bin dir first.
- shell hook is PowerShell only, dot-sourced from `$PROFILE`
  (`. "${env:USERPROFILE}/AppData/Local/envy/shell/hook.ps1"`). `cmd.exe` has no
  hook; use the `.bat` wrappers or `envy run`.
- PowerShell `>` writes UTF-16. Redirecting `export`/`hash`/`product --json`
  output needs `| Out-File -Encoding ascii|utf8`.
- host mutation via `winget`/`choco` in a `USER_MANAGED` spec's SETUP pair;
  elevation needs `interactive = true`.

## verb forms

| Verb | string | table | function | omitted |
|---|---|---|---|---|
| `FETCH(tmp_dir, opts)` | single URL, unverified | `{source, sha256?, ref?, dest?, post_data?}` or array of either | imperative, or return any declarative form | error for cache-managed specs, since FETCH is required unless `USER_MANAGED` |
| `STAGE(fetch_dir, stage_dir, tmp_dir, opts)` | shell script | `{strip=N, only={globs}}` extraction filter | programmatic | extract all fetched archives |
| `BUILD(install_dir, stage_dir, fetch_dir, tmp_dir, opts)` | shell script, cwd = stage | not accepted | may return string, which runs as a shell script | no-op |
| `INSTALL(install_dir, stage_dir, fetch_dir, tmp_dir, opts)` | shell script | not accepted | may return string, which runs as a shell script | promote staged tree to install dir |
| `SETUP.<name>.CHECK(pkg_dir, opts)` | shell, exit 0 = satisfied | not accepted | return bool, or string which runs as shell | pair requires both CHECK and INSTALL |
| `SETUP.<name>.INSTALL(pkg_dir, opts)` | shell | not accepted | may return string, which runs as shell | not applicable |

Other spec globals: `OPTIONS` (schema table with
`required`/`type`/`choices`/`range`/`validate`, types including `list` and
`semver`, or a validator function), `PRODUCTS` (table or `function(opts)`, with
`{value=..., script=false}` for non-executables), `DEPENDENCIES`, `PLATFORMS`
(`darwin|linux|windows[-arch]`), `USER_MANAGED` (host-mutating specs: must
define SETUP pairs, must not define FETCH/STAGE/BUILD/INSTALL), `EXPORTABLE`
(false means a depot exports fetched bytes rather than install output).

## dependencies

- kinds: **strong** (`{spec=..., source=...}`, instantiated immediately),
  **weak** (query plus `weak={fallback spec}`, used only if nothing else
  provides), **reference-only** (query that must be satisfied elsewhere),
  **product** (`{product="ninja"}`, whoever provides it).
- ordering: `needed_by` on a dependency names the phase of the *dependent* that
  blocks on it, one of `check|import|fetch|stage|build|install`. Default `build`.
- **fetch dependencies**: a package needed before another package's spec or
  payload can be fetched, for example an Artifactory or corporate auth CLI.
  Declared inside the source table:
  `source = { dependencies = {{spec=..., source=...}}, fetch = function(tmp_dir, opts) ... end }`.
  Fetch deps are fully installed before the dependent's spec is loaded. The
  fetch function commits a file named `spec.lua` via `envy.commit_fetch`.
- setup selection: manifest entry `setup = {"pair", ...}` opts into SETUP pairs.
  Nothing runs unselected, and the selection is not part of the cache key.
- bundles: one fetched container of many specs.
  `BUNDLES = { alias = {identity, source, ref} }`, and an entry uses
  `bundle = "alias"` instead of `source`.
- depot (OPTIONAL): `PACKAGE_DEPOTS = { "s3://bucket/packages.txt" }`, an index
  of prebuilt `.tar.zst` artifacts. A hit skips fetch and build. Bypass with
  `--ignore-depot` or `ENVY_IGNORE_DEPOT=1`. Publish loop: `envy export`, then
  `envy merge-depot`, then upload.

## CLI

`envy <cmd>`. Global flags `--verbose -q --trace[=sinks] --cache-root` go before
the subcommand. stdout is machine-readable only, and human output goes to
stderr.

- `sync [queries]`: install plus deploy product scripts. The main command.
- `install [queries]`: install only.
- `init <project-dir> <bin-dir>`: new project, manifest plus bootstrap scripts.
- `product [name] [--json]`: resolve a product path. Naming one installs its
  provider; no name lists all; `--json` dumps every product as one object and
  computes paths WITHOUT installing, so `sync` first if the files must exist.
- `package <identity>`: install and print the package dir path.
- `run <cmd...>`: exec cmd with project bin on PATH and `ENVY_PROJECT_ROOT` set.
- `shell <bash|zsh|fish|powershell>`: print the shell-hook source line.
- `use <version>`: retarget the pinned envy version in the manifest.
- `git-resolve <url> <ref>`: remote ref to full sha, for pinning.
- `hash <paths>`: sha256 lines for depot indexes.
- `export`, `import`, `merge-depot`: depot artifact publish and consume.
- `fetch <src> <dst>`, `extract <archive> [dst]`, `hash <paths>`,
  `git-resolve`, `lua <script>`: standalone utilities, no manifest or project
  required. Transports and formats are compiled in: AWS SDK (so `s3://` works
  with ambient credentials and no AWS CLI), libgit2 (no `git` binary),
  libarchive (tar/gz/xz/bz2/zst/zip/7z/rar/iso). Package the AWS CLI only when a
  project wants the CLI itself.
- `cache`: show cache location and disk usage. Also `version`, `mirror-envy`.
- editor support: `init` writes `.luarc.json` with three platform cache paths and
  envy's LuaCATS type definitions on `workspace.library`; `sync`/`deploy` rewrite
  stale `envy/<semver>` entries and preserve everything else. Delete the file to
  opt out. `BUNDLES` is not in the default `diagnostics.globals` list.

Superprojects: nested `envy.lua` manifests compose. A sub-manifest sets `@envy
root "false"`, and the superproject imports it via
`envy.loadenv("path.to.envy")` plus `envy.extend(PACKAGES, {...})`. Commands walk
up to the root manifest, and `--subproject` stops at the nearest.

Env vars: `ENVY_CACHE_ROOT`, `ENVY_MIRROR`, `ENVY_IGNORE_DEPOT`,
`ENVY_PROJECT_ROOT` (set by envy), `ENVY_SHELL_HOOK_DISABLE`, `ENVY_NO_REEXEC`.

Lua API in specs: `envy.run(script|{lines}, {quiet, check, capture, interactive,
env, cwd, shell})`, `envy.fetch(src, {dest})`, `envy.commit_fetch`,
`envy.verify_hash`, `envy.extract`, `envy.extract_all(src, dst, {strip, only})`,
`envy.copy/move/remove/exists`, `envy.path.*`, `envy.abspath`,
`envy.template(str, vars)`, `envy.product(name)`, `envy.package(identity)`,
`envy.options(schema)`, `envy.loadenv`, `envy.loadenv_spec(identity, module)`
(returns a module's globals out of a declared dependency), and constants `envy.PLATFORM`
(`darwin|linux|windows`), `envy.ARCH`, `envy.PLATFORM_ARCH`, `envy.EXE_EXT`.
