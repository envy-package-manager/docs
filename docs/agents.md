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
  `envy.import()`, `envy.extend()` all legal.
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
  time (`exec "$("$ENVY_SCRIPT_DIR/envy" product cmake)" "$@"`), so they never go
  stale. Every wrapper also prepends its own bin dir to PATH (so a tool can shell
  out to a sibling product) and exports `ENVY_PROJECT_ROOT`, stamped as a hop
  relative to the bin dir, and only for a root manifest (`root "false"` leaves it
  empty and the caller's value stands). The `.bat` twin needs `setlocal`, or PATH
  and the product path leak into the calling cmd.exe and a sibling product
  re-runs the first payload forever. Wrapper/bootstrap schema is `4` (POSIX
  wrappers run `set -Eeuo pipefail`; a bump restamps every wrapper once).
- **manifest discovery**: walk up from an anchor. Precedence `--manifest <path>`
  (no walk) > global `--project <dir>` > CWD. `--subproject` means "nearest to
  where I stand", so it anchors on CWD even under `--project`, and stops at the
  first `envy.lua` ignoring `@envy root`. `envy run` also infers an anchor from
  `-- <script>` or a first arg naming an existing file; `--project` outranks
  both. Bootstrap and wrapper scripts inject `--project <their own dir>` ahead of
  your argv (option takes last value, so a typed one still wins), so a bin dir
  decides its project and `../B/bin/uv run x.py` acts on B, not on your CWD.
  Trace event `manifest_resolved{path,anchor,mode,nearest}`, `mode` one of
  `explicit|project|cwd`; `run` emits none (execvp beats the trace drain).
- `deploy` verifies the walk back: a **root** manifest whose `@envy bin` walks up
  to a *different* `envy.lua` is a hard error (`..` in `@envy bin`, a `.git`
  between, or a `--manifest` outside the bin dir's tree). Finding nothing, or a
  manifest not named `envy.lua`, warns. `root "false"` opts out entirely, which
  is what lets a superproject restamp a submodule's bin dir byte-identically.
  `deploy` also warns when it stamps scripts from a version the manifest does not
  pin (reachable only via dev build or `ENVY_NO_REEXEC`).
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
  Layout `envy/<ver>/{envy,envy.lua}` + `envy/latest`, `packages/`, `specs/`,
  `shell/`, `locks/`; entry key `identity/<platform>-<arch>-blake3-<hash>`.
  First-run notice ("Caching packages in ...") fires for LOCAL trees only, on
  stderr, keyed on `packages/` not existing, never a prompt. The shared default
  is silent.
- **a local tree reads the user-wide one, never writes to it**. Launchers and
  reexec try `<project cache>/envy/<ver>/envy`, then `<user-wide>/envy/<ver>/envy`.
  The second is tried only for a LOCAL tree with **no** `@envy sha256sums` (the fast
  path never re-hashes, and every other project writes that tree, so a pin must
  stay the trust boundary). Never the reverse (a clone shipping its own
  `envy/<ver>/envy` would be arbitrary code execution). A candidate that is not a
  regular non-empty executable file is skipped, not exec'd. A borrowed binary
  still self-deploys into the project's own tree, so a local cache stays
  self-contained. `envy cache --local/--shared` deploys into the mode it is
  *establishing*, not the one still recorded. `envy cache --user-wide-root`
  prints that second root, as `--root` prints the first.
- **shell hooks are user-wide only**. Hook root is `--cache-root`/
  `$ENVY_CACHE_ROOT` else platform default; no project tier moves it, and a
  local-cache project writes **no** hooks at all. `envy shell` says so instead of
  suggesting a command that cannot produce them, and names a stale project-local
  `shell/` an older envy left. Warns about cache relocation only under an
  override.
- reproducibility: no lockfile. Pins live in the manifest: `@envy version` plus
  `sha256sums`, per-source `sha256`, git `ref` as a full sha via
  `envy git-resolve <url> <ref>`. Unhashed fetches re-download every run.

## windows

Supported target, not a port. Same manifest, same specs, same cache layout.

- bootstrap `bin\envy.bat` (batch, parses the `@envy` header itself, walks up for
  the root manifest, honors `ENVY_CACHE_ROOT`/`ENVY_MIRROR`). Wrappers are
  `bin\<tool>.bat`, using `setlocal`, `set "PATH=%~dp0.;%PATH%"`,
  `%~dp0envy.bat product <name>` then `call "%ENVY_PRODUCT_PATH%" %*`, forwarding
  `%ERRORLEVEL%`. Plain `setlocal`, not `EnableDelayedExpansion`: a product path
  containing `!` must survive.
- `--platform posix|windows|all` on `init`/`sync`/`deploy` selects which script
  flavors get written, defaulting to the host. Bootstrap AND wrappers are
  per-flavor, so a plain `sync` on macOS does NOT restamp `envy.bat`. Use
  `--platform all` in a cross-platform repo. A host-only deploy does not prune
  the other flavor.
- scripts get the newlines their TARGET needs, not the host's: **CRLF for every
  `.bat`** (`envy.bat` and the wrappers), LF otherwise, POSIX ones mode 755.
  cmd.exe resolves `goto`/`call :label` by seeking with offsets that assume CRLF,
  so an LF batch with labels drifts a byte per line until the search walks past
  the label and no `@envy` directive is parsed at all. envy renormalizes both
  directions. A committed bin dir is byte-identical in every checkout.
  `core.autocrlf` rewriting the POSIX scripts makes every deploy report
  "updated"; fix with `bin/** -text` in `.gitattributes`. `*.bat eol=crlf` is
  also compatible now.
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
  `envy.product`/`envy.package` work inside a `source.fetch` function: entries
  are wired with `needed_by = spec_fetch` before it runs. Every
  `source.dependencies` entry must be **strong** (`spec` + `source`), and so must
  everything in its transitive closure. The weak pass runs at a resolution
  barrier after every spec_fetch, including that of the consumer still waiting,
  so nothing weak can be ordered in time.
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

`envy <cmd>`. Global flags `--verbose -q --trace[=sinks] --cache-root --project`
go before the subcommand (`envy sync --verbose` is a parse error). stdout is
machine-readable only, and human output goes to stderr. `--project <dir>` is
honored by every manifest-loading command: `sync install deploy product package
run export import use cache shell`.

- `sync [queries]`: install plus deploy product scripts. The main command.
- `install [queries]`: install only.
- `deploy [queries] [--strict] [--platform ...]`: deploy product scripts only,
  no installs. Prunes marked wrappers outside the resolved graph.
- `init <project-dir> <bin-dir> [--envy-version X.Y.Z] [--mirror URL]
  [--pin-sums] [--deploy=bool] [--root=bool] [--platform ...]`: new project,
  manifest plus bootstrap scripts plus `.luarc.json`, and appends `.envy/` +
  `.envy-cache-*` to `.gitignore` (only if `<project-dir>/.git` exists; skips
  entries already present in any equivalent git spelling, `!` negation included).
  `--envy-version` re-execs into that release so the pin, the script stamp, and
  the extracted types all come from it; parent-side and stripped from the child's
  argv, so releases predating the flag still work. Downloads it from `--mirror`.
  A dev build (0.0.0) or `ENVY_NO_REEXEC` warns and stamps itself.
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
- `fetch <src> <dst>`, `extract <archive> [dst] [--only PATH|GLOB]...`,
  `hash <paths>`, `git-resolve`, `lua <script>`: standalone utilities, no
  manifest or project required. Transports and formats are compiled in: AWS SDK
  (so `s3://` works with ambient credentials and no AWS CLI), libgit2 (no `git`
  binary), libarchive (tar/gz/xz/bz2/zst/zip/7z/rar/iso). Package the AWS CLI
  only when a project wants the CLI itself. `mirror-envy` to an `s3://`
  destination resolves credentials BEFORE downloading, failing with
  `no usable AWS credentials` plus the SDK's per-provider reason (expired SSO
  token being the usual one). S3 error hints: 501 = unsigned write, 301 /
  `PermanentRedirect` = wrong region (SDK defaults `us-east-1`), 403 = no
  `s3:PutObject`, `NoSuchBucket` = envy never creates buckets.
- `cache [--root | --user-wide-root | --local | --shared]`: cache location and
  disk usage; flags mutually exclusive, one action per invocation. Also
  `version`, `mirror-envy`.
- fetch retries: transport failures are retried (`connect`, `transfer`,
  `timeout`, HTTP 5xx and 429; every other 4xx and any malformed-URL/local error
  is fatal). Safe because fetches are idempotent GETs and payloads are
  sha256-verified after transport. `ENVY_FETCH_ATTEMPTS` (default 3, clamp
  1..10), `ENVY_FETCH_RETRY_BASE_MS` (default 1000, clamp 0..60000), backoff 1x
  4x 16x jittered ±50%, capped 60s. `s3://` excluded (AWS SDK retries itself).
  Trace event `download_retry{url,attempt,delay_ms,reason,error}`.
- editor support: `init` writes `.luarc.json` with three platform cache paths and
  envy's LuaCATS type definitions on `workspace.library`; `sync`/`deploy` rewrite
  stale `envy/<semver>` entries and preserve everything else. Delete the file to
  opt out. `BUNDLES` is not in the default `diagnostics.globals` list.

Superprojects: nested `envy.lua` manifests compose. A sub-manifest sets `@envy
root "false"`, and the superproject imports it via
`envy.import("libs/common")` plus `envy.extend(PACKAGES, {...})`. Commands walk
up to the root manifest, and `--subproject` stops at the nearest.

`envy.import(path)` (**0.3.0+**, MANIFEST SCOPE ONLY, not in specs or `envy lua`)
runs another manifest in a sandbox and returns its globals. Path is relative to
the calling manifest; a directory appends `envy.lua`. An imported entry stays
tied to its own file: relative `source` anchors on the IMPORTED manifest's dir,
and `bundle = "alias"` resolves against ITS `BUNDLES` first, then the root's (no
re-export needed; two components may reuse an alias). Declarer stays the
superproject, so project root, SETUP cwd and custom-fetch cache keys name the
root. Only `PACKAGES`/`BUNDLES` are tagged; splice other globals by hand
(`PACKAGE_DEPOTS = sub.PACKAGE_DEPOTS`). Imported file sees `ENVY_IMPORTER` =
importer's absolute path, `nil` standalone: `if not ENVY_IMPORTER then` is the
standalone-only gate that replaced env-var gates. Nesting fine, cycles error.
**Imported header is INERT** (`bin`, `deploy`, `cache-*`, `state-dir`, `mirror`,
`sha256sums`, `root` all do nothing; one tree, one cache root, one binary per run,
all from the root header). Sole exception: imported `@envy version` NEWER than
the root pin errors, older warns. Discovery never sees the file, so no
`manifest_resolved` names it; `manifest_imported{path,importer}` is the record.
Pre-0.3.0 this was `envy.loadenv`, which needed `envy.abspath` on every component
source path and a manual `BUNDLES = sub.BUNDLES`; both traps were silent.

Env vars read: `ENVY_CACHE_ROOT`, `ENVY_MIRROR`, `ENVY_IGNORE_DEPOT`,
`ENVY_NO_REEXEC`, `ENVY_FETCH_ATTEMPTS`, `ENVY_FETCH_RETRY_BASE_MS`; hook-only
`ENVY_SHELL_HOOK_DISABLE`, `ENVY_SHELL_NO_ENTER_EXIT_ANNOUNCE`,
`ENVY_SHELL_NO_ICON`. Written: `ENVY_PROJECT_ROOT` and `PATH`, by `envy run`, the
shell hook, and every deployed product script.

Lua API in specs: `envy.run(script|{lines}, {quiet, check, capture, interactive,
env, cwd, shell})`, `envy.fetch(src, {dest})`, `envy.commit_fetch`,
`envy.verify_hash`, `envy.extract`, `envy.extract_all(src, dst, {strip, only})`,
`envy.copy/move/remove/exists`, `envy.path.*`, `envy.abspath`,
`envy.template(str, vars)`, `envy.product(name)`, `envy.package(identity)`,
`envy.options(schema)`, `envy.loadenv` (helper files; NOT manifest composition,
see `envy.import`), `envy.loadenv_spec(identity, module)`
(returns a module's globals out of a declared dependency), and constants `envy.PLATFORM`
(`darwin|linux|windows`), `envy.ARCH`, `envy.PLATFORM_ARCH`, `envy.EXE_EXT`.
