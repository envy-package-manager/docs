---
sidebar_position: 2
title: envy for Agents
slug: /agents
---

# envy for agents

> **Placeholder content.** This page is intentionally not prose. It is a low-token,
> maximal-density summary for AI coding agents. Humans should read the rest of
> the manual. Verify facts against the envy sources before publishing, and keep
> this page current with every behavior change.

envy: per-project package manager. Lua manifest `envy.lua` at project root pins
everything including envy itself. No install step, no server, no registry, no
lockfile. Committed bootstrap script `<bin>/envy` (plus `envy.bat`) downloads the
pinned envy binary on first run. Everyday command: `./bin/envy sync`.

## model

- manifest `envy.lua`: header comment directives `-- @envy key "value"` before
  the first code line, plus globals `PACKAGES` (required), `BUNDLES`,
  `PACKAGE_DEPOTS`, `DEFAULT_SHELL`. Manifest is real Lua: conditionals,
  `envy.loadenv()`, `envy.extend()` all legal.
- directives: `version` pins envy. `sha256sums` pins release checksums and
  requires `version`. `bin` is REQUIRED and names the project bin dir. `mirror`
  sets the release mirror. `deploy "true"` enables product scripts. `root
  "true|false"` marks a superproject boundary, default true.
  `cache-posix`/`cache-win` override the cache root. `schema` sets the schema
  version.
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
- cache: user-wide, content-addressed, shared across projects, safe to delete.
  Root precedence: `--cache-root`, then `$ENVY_CACHE_ROOT`, then `@envy cache-*`,
  then platform default (`~/Library/Caches/envy`, `$XDG_CACHE_HOME/envy`,
  `%LOCALAPPDATA%\envy`).
- reproducibility: no lockfile. Pins live in the manifest: `@envy version` plus
  `sha256sums`, per-source `sha256`, git `ref` as a full sha via
  `envy git-resolve <url> <ref>`. Unhashed fetches re-download every run.

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
- `product [name] [--json]`: resolve a product path. No name lists all.
- `package <identity>`: install and print the package dir path.
- `run <cmd...>`: exec cmd with project bin on PATH and `ENVY_PROJECT_ROOT` set.
- `shell <bash|zsh|fish|powershell>`: print the shell-hook source line.
- `use <version>`: retarget the pinned envy version in the manifest.
- `git-resolve <url> <ref>`: remote ref to full sha, for pinning.
- `hash <paths>`: sha256 lines for depot indexes.
- `export`, `import`, `merge-depot`: depot artifact publish and consume.
- `fetch <src> <dst>`, `extract <archive> [dst]`, `lua <script>`: spec-dev
  utilities.
- `cache`: show cache location and disk usage. Also `version`, `mirror-envy`.

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
`envy.options(schema)`, `envy.loadenv`, and constants `envy.PLATFORM`
(`darwin|linux|windows`), `envy.ARCH`, `envy.PLATFORM_ARCH`, `envy.EXE_EXT`.
