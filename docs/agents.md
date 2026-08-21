---
sidebar_position: 2
title: envy for Agents
slug: /agents
---

# envy for agents

> **Placeholder content.** This page is *deliberately* not prose: it is a
> low-token, maximal-density summary for AI coding agents. Humans should read
> the rest of the manual. Verify facts against the envy sources before
> publishing; keep this page current with every behavior change.

envy: per-project package manager. Lua manifest `envy.lua` at project root pins
everything incl. envy itself. No install step, no server, no registry, no
lockfile. Committed bootstrap script `<bin>/envy` (+ `envy.bat`) downloads
pinned envy binary on first run. Everyday command: `./bin/envy sync`.

## model

- manifest `envy.lua`: header comment directives `-- @envy key "value"` (before
  first code line) + globals `PACKAGES` (required), `BUNDLES`, `PACKAGE_DEPOTS`,
  `DEFAULT_SHELL`. Manifest is real Lua: conditionals, `envy.loadenv()`,
  `envy.extend()` legal.
- directives: `version` (pin envy), `sha256sums` (pin release checksums;
  requires `version`), `bin` (REQUIRED; project bin dir), `mirror`, `deploy
  "true"` (enable product scripts), `root "true|false"` (superproject boundary;
  default true), `cache-posix`/`cache-win`, `schema`.
- spec = Lua file describing one package: `IDENTITY = "ns.name@ver"` (required;
  `@ver` = spec version, not asset version; `local.*` = project-local) + verbs.
  Package = installed instance keyed `(identity, options, platform)`.
- verbs: `FETCH → STAGE → BUILD → INSTALL`, plus `SETUP` (named
  CHECK/INSTALL pairs). Each verb: string | table | function | omitted, all
  with defaults. See table.
- products: spec exports named entry points (`PRODUCTS = { cmake = "bin/cmake" }`).
  Consumers use product name, not identity: CLI `envy product cmake`, Lua
  `envy.product("cmake")`, or deployed wrapper script `./bin/cmake`.
- cache: user-wide, content-addressed, shared across projects, safe to delete.
  Roots: `$ENVY_CACHE_ROOT` > `--cache-root` > `@envy cache-*` > platform
  default (`~/Library/Caches/envy`, `$XDG_CACHE_HOME/envy`, `%LOCALAPPDATA%\envy`).
- reproducibility: no lockfile. Pins live in-manifest: `@envy version` +
  `sha256sums`, per-source `sha256`, git `ref` (full sha; get via
  `envy git-resolve <url> <ref>`). Unhashed fetches re-download every run.

## verb forms

| Verb | string | table | function | omitted |
|---|---|---|---|---|
| `FETCH(tmp_dir, opts)` | single URL, unverified | `{source, sha256?, ref?, dest?, post_data?}` or array of either | imperative and/or return any declarative form | error for cache-managed specs (FETCH required unless `USER_MANAGED`) |
| `STAGE(fetch_dir, stage_dir, tmp_dir, opts)` | shell script | `{strip=N, only={globs}}` extraction filter | programmatic | extract all fetched archives |
| `BUILD(install_dir, stage_dir, fetch_dir, tmp_dir, opts)` | shell script (cwd stage) | — | may return string ⇒ runs as shell script | no-op |
| `INSTALL(install_dir, stage_dir, fetch_dir, tmp_dir, opts)` | shell script | — | may return string ⇒ runs as shell script | promote staged tree to install dir |
| `SETUP.<name>.CHECK(pkg_dir, opts)` | shell; exit 0 = satisfied | — | return bool, or string ⇒ run as shell | pair requires both CHECK+INSTALL |
| `SETUP.<name>.INSTALL(pkg_dir, opts)` | shell | — | may return string ⇒ shell | — |

Other spec globals: `OPTIONS` (schema table w/ `required/type/choices/range/
validate`, types incl `list`,`semver`; or validator function), `PRODUCTS`
(table | function(opts); `{value=..., script=false}` for non-executables),
`DEPENDENCIES`, `PLATFORMS` (`darwin|linux|windows[-arch]`), `USER_MANAGED`
(host-mutating specs: must define SETUP pairs, must NOT define
FETCH/STAGE/BUILD/INSTALL), `EXPORTABLE` (false ⇒ depot exports fetched bytes,
not install output).

## dependencies

- kinds: **strong** (`{spec=..., source=...}` — instantiated immediately),
  **weak** (query + `weak={fallback spec}` — used only if nothing else
  provides), **reference-only** (query; must be satisfied elsewhere),
  **product** (`{product="ninja"}` — whoever provides it).
- ordering: `needed_by` on a dependency = phase of the *dependent* that blocks
  on it: one of `check|import|fetch|stage|build|install`. DEFAULT: `build`.
- **fetch dependencies**: package needed before another package's spec/payload
  can even be *fetched* (e.g. artifactory/jfrog CLI, corporate auth tool).
  Declared inside the source table:
  `source = { dependencies = {{spec=..., source=...}}, fetch = function(...) ... end }`.
  Fetch-deps are fully installed before the dependent's spec is even loaded.
- setup selection: manifest entry `setup = {"pair", ...}` opts into SETUP
  pairs; nothing runs unselected; selection not part of cache key.
- bundles: one fetched container of many specs. `BUNDLES = { alias = {identity,
  source, ref} }`; entry uses `bundle = "alias"` instead of `source`.
- depot (OPTIONAL): `PACKAGE_DEPOTS = { "s3://bucket/packages.txt" }` — index
  of prebuilt `.tar.zst` artifacts; hit skips fetch/build. Bypass:
  `--ignore-depot` / `ENVY_IGNORE_DEPOT=1`. Publish loop: `envy export` →
  `envy merge-depot` → upload.

## CLI

`envy <cmd>`; global flags `--verbose -q --trace[=sinks] --cache-root`.
stdout = machine-readable only; human output on stderr.

- `sync [queries]` — install + deploy product scripts. THE command.
- `install [queries]` — install only.
- `init <project-dir> <bin-dir>` — new project: manifest + bootstrap scripts.
- `product [name] [--json]` — resolve product path; no name = list all.
- `package <identity>` — install + print package dir path.
- `run <cmd...>` — exec cmd with project bin on PATH.
- `shell <bash|zsh|fish|powershell>` — print shell-hook source line.
- `use <version>` — retarget pinned envy version in manifest.
- `git-resolve <url> <ref>` — remote ref → full sha (for pinning).
- `hash <paths>` — sha256 lines for depot manifests.
- `export` / `import` / `merge-depot` — depot artifact publish/consume.
- `fetch <src> <dst>`, `extract <archive> [dst]`, `lua <script>` — spec-dev
  utilities.
- `cache` — show cache location + disk usage. `version`, `mirror-envy`.

Superprojects: nested `envy.lua` manifests compose; sub-manifest sets `@envy
root "false"`, superproject imports it via `envy.loadenv("path.to.envy")` +
`envy.extend(PACKAGES, {...})`. Commands walk up to the root manifest;
`--subproject` stops at nearest.

Env vars: `ENVY_CACHE_ROOT`, `ENVY_MIRROR`, `ENVY_IGNORE_DEPOT`,
`ENVY_PROJECT_ROOT` (set by envy), `ENVY_SHELL_HOOK_DISABLE`.

Lua API in specs: `envy.run(cmd|{cmds}, {quiet, check, capture, interactive,
env})`, `envy.fetch`, `envy.extract`, `envy.extract_all(src, dst, {strip,
only})`, `envy.copy/move/remove/exists`, `envy.path.*`, `envy.template(str,
vars)`, `envy.product(name)`, `envy.package(identity)`, `envy.options(schema)`,
`envy.loadenv`, constants `envy.PLATFORM` (`darwin|linux|windows`), `envy.ARCH`,
`envy.PLATFORM_ARCH`, `envy.EXE_EXT`.
