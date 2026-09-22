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

**Current release: 0.4.7.** This page describes it. Behaviour that changed
during 0.4.x is marked (`0.4.2+`, `0.4.6+`) because a project may pin something
older; anything unmarked has been there since 0.3.0 and is not worth checking.
The newest features are `ENVY_BUNDLE` (0.4.7) and, in 0.4.6,
`envy.loadenv_bundle`, a loaded module's return value being the result, `vendor`
on a bundle entry, and a wall-clock fetch-retry budget. 0.4.3 to 0.4.5 are TUI
fixes.

Releases ship archives, not bare binaries:
`envy-{linux,darwin}-{x86_64,arm64}.tar.gz` and
`envy-windows-{x86_64,arm64}.zip`, plus `SHA256SUMS`, all under
`https://github.com/envy-package-manager/envy/releases/download/v<version>/`.
The archived binary keeps mode 0755, so no `chmod` after extracting.

## a complete manifest and a complete spec

Everything below is detail on these two files. A manifest:

```lua
-- @envy version "0.4.7"
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

A bundle's spec names, revisions and option names are NOT discoverable from
envy — there is no `envy bundle list`. Read the bundle repo (for the first-party
one, `specs/` plus the README table in `package-specs`), and pin `ref` to a full
sha. A wrong `@rev` is a hard error, not a fallback.

Header directives come before the first code line, one per line, exactly
`-- @envy <key> "<value>"`. `bin` is required. The `sha256` on a `PACKAGES` entry
pins the SPEC source, not anything the spec then fetches. A bundle entry takes no
`sha256`/`ref` — the `BUNDLES` declaration carries the pin — but does take
`vendor` (0.4.6+).

And a spec:

```lua
IDENTITY = "acme.mytool@r0"
PLATFORMS = { "darwin", "linux", "windows" }
EXPORTABLE = true

-- A spec is an ordinary Lua script, so file-scope locals work. Key the table
-- by EVERY option the payload varies with -- here repo as well as version, or
-- three of the four instances below would verify against the wrong bytes.
local hashes = {
  ["libusb/hidapi"] = {
    ["1.4.0"] = { ["darwin-arm64"] = "24ad...37be", ["linux-x86_64"] = "8c91...02af" },
  },
}

OPTIONS = {
  version = { required = true, type = "string" },
  repo    = { required = true, type = "string" },
}

-- 0.4.2+. Names this instance on its progress rows: one spec, many packages.
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

-- Product NAMES are global across the manifest: two packages exporting the same
-- name is a hard error. A spec instantiated several times must therefore derive
-- its names from an option, not hardcode them. PRODUCTS runs BEFORE OPTIONS
-- validates, so guard every read. See both traps below.
PRODUCTS = function(opts)
  local repo = opts.repo or ""
  return { [repo:match("[^/]+$") or "mytool"] = "bin/mytool" .. envy.EXE_EXT }
end
```

Constraint keys are exactly `required`, `type` (`string|int|float|boolean|table|list|semver`),
`range` (a comparison chain, `">=1 <=64"`), `choices` (an array), and `validate`
— a function returning `nil` or `true` for valid, or `false`, or an error-message
string, which becomes the message the user sees. **There is no `default`**: an
option the manifest omits is `nil` in every verb, so branch on it or require it. `envy.ARCH` is `arm64|x86_64`,
`envy.PLATFORM` is `darwin|linux|windows`, `envy.PLATFORM_ARCH` joins them.

Getting the FIRST binary (the only step `envy init` cannot bootstrap):

```bash
curl -fsSL -O https://github.com/envy-package-manager/envy/releases/latest/download/envy-darwin-arm64.tar.gz
tar -xzf envy-darwin-arm64.tar.gz -C /tmp
/tmp/envy init . ./bin --pin-sums --deploy=true    # writes envy.lua + bin/, then delete /tmp/envy
```

Commit: `envy.lua`, the whole bin dir, and `.luarc.json` (it lists every
platform's cache path with `~`/`${env:...}` placeholders, never an absolute one,
so it is machine-independent by design). `init` adds `.envy/` and
`.envy-cache-*` to `.gitignore` — those are project-local cache/state trees.

Using an already-set-up project needs NO setup step: run `./bin/<tool>` (a
committed wrapper) or `./bin/envy run <cmd>`, and the wrapper bootstraps envy and
installs that tool's subgraph on demand. `./bin/envy install` installs
everything up front; `./bin/envy sync` is that plus the bin dir, which only a
product change needs (see the CLI section). Windows: `bin\envy.bat`,
`bin\<tool>.bat`. With the shell hook installed the bin dir is on PATH, so bare
`envy sync` and `cmake` work, which is the form the rest of the docs use. In CI
and scripts use the explicit path.

## model

- manifest `envy.lua`: header comment directives `-- @envy key "value"` before
  the first code line, plus globals `PACKAGES` (required), `BUNDLES`,
  `PACKAGE_DEPOTS`, `DEFAULT_SHELL`, `VENDOR_ROOT`. Manifest is real Lua:
  conditionals, `envy.import()`, `envy.extend()` all legal.
- shells: string verbs, and strings returned from function verbs, run under
  `DEFAULT_SHELL` (root manifest only; an import declaring it errors unless the
  root holds that exact value). Default bash on POSIX, PowerShell on Windows.
  Built-ins `ENVY_SHELL.BASH|SH|CMD|POWERSHELL`, platform-validated — wrong
  platform is an error, not a fallback. Custom:
  `{ file = <path|argv>, ext = ".py" }` runs `argv <tempfile>`,
  `{ inline = argv }` runs `argv <script text>`. To use an ENVY-INSTALLED
  interpreter you must go through the `{ DEPENDS, SHELL }` wrapper — a bare
  `DEFAULT_SHELL = function()` has no dependency edges, so `envy.product` fails
  inside it:
  `DEFAULT_SHELL = { DEPENDS = { "envy.python@r1" }, SHELL = function() return { file = { envy.product("python3") }, ext = ".py" } end }`.
  DEPENDS entries are queries against PACKAGES, and require SHELL to be a
  function (either half alone is an error). Resolution and the DEPENDS install
  are lazy, so a run with no string verb (e.g. `deploy`) never installs the
  interpreter. Anything in a bootstrap closure (DEPENDS, `source.dependencies`,
  PACKAGE_DEPOTS DEPENDS, Lua in the manifest state) uses the platform built-in
  instead, so resolving the shell cannot require the shell. Per-call override:
  `envy.run(script, { shell = ... })`.
- directives: `version` pins envy. `sha256sums` pins release checksums and
  requires `version`. `bin` is REQUIRED and names the project bin dir, relative
  to the manifest, validated like `cache-local` (no drive letter,
  leading separator, `~`, `$`, `%`) except that `.` and `..` stay legal and
  `deploy` judges an escape. `mirror`
  sets the release mirror. `deploy "true|false"` writes product scripts into the
  bin dir and **defaults to FALSE** — without it a `sync` deploys nothing and
  warns. `root "true|false"` marks a superproject boundary, default true.
  `cache-local` puts the cache in a tree inside the project (`cache-mode` and
  `state-dir` tune that; all three need envy 0.2.0; `cache-posix`/`cache-win` are
  errors). `schema` sets the schema version.
- **re-exec**: every manifest-aware command compares its own version to `@envy
  version` BEFORE doing any work and, on a mismatch, replaces itself with that
  release. So the binary you invoked is almost never the one that acts, and
  `envy --version` is not the project's version — read the header, or ask a
  command that does not re-exec. Which release: project cache tree, then
  user-wide tree (borrow rules below), then a download to a temp dir from the
  mirror, attested against `@envy sha256sums` before unpacking when one is
  pinned; the child installs itself into the cache. Exactly ONE hop — the child is handed
  `ENVY_REEXEC=1` and proceeds — and it gets your argv minus any option that
  chose which envy runs (`init --envy-version`), which an older release would
  reject. Skipped when: no `@envy version`, it already matches, self is `0.0.0`
  (dev build), or `ENVY_NO_REEXEC`. REFUSED (hard error, not a downgrade) when
  the manifest resolves a cache mode (`cache-local`/`cache-mode`/`state-dir`, or
  an `envy cache --local` marker) and pins an envy `< 0.2.0`, which would
  silently use the shared cache and exit 0. Opted out by `use`, `cache`,
  `version`: they read the header as text so they still work when the pinned
  envy is what cannot run. `ENVY_NO_REEXEC` and a dev build are also the only
  ways a `deploy` stamps scripts from an unpinned version (it warns). A
  `--trace=file:` sink is closed and handed to the child before the exec, so one
  trace file spans the handoff (0.4.4+; before that, Windows — whose exec waits
  rather than replacing — kept the parent's handle open and interleaved its
  records into the child's file).
- spec = Lua file describing one package: `IDENTITY = "ns.name@rev"` required,
  where `@rev` versions the spec rather than the payload, and `local.*` means
  project-local. Package = installed instance keyed `(identity, options,
  platform)`. Canonical key `ns.name@rev{["k"]=v,...}`, option names quoted and
  sorted. Option tables
  must be all-string-keyed or a contiguous `1..n` array, and hold no function, at
  any depth.
- verbs: `FETCH → STAGE → BUILD → INSTALL`, plus `SETUP` (named CHECK/INSTALL
  pairs). Each verb: string, table, function, or omitted, all with defaults. See
  table below.
- **vendoring (0.4.0+)**: copy a package's `pkg/` into the project tree, for
  build systems that cannot name a file outside the project (GN, Bazel: every
  input is a `//`-relative label). Make/CMake take an absolute `envy product`
  path and need none of this. `install`/`sync` keep the copies current;
  `envy vendor` runs that step alone. See the vendoring section below.
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
  re-runs the first payload forever. Wrapper schema is `4`, stamped as
  `envy-managed schema "4"` (POSIX wrappers run `set -Eeuo pipefail`; a bump
  restamps every wrapper once). The bootstrap scripts carry no schema number and
  are rewritten whenever their content changes.
- **manifest discovery**: walk up from an anchor. Precedence `--manifest <path>`
  (no walk) > global `--project <dir>` > CWD. `--subproject` means "nearest to
  where I stand", so it anchors on CWD even under `--project`, and stops at the
  first `envy.lua` ignoring `@envy root`. `envy run` also infers an anchor from
  `-- <script>` or a first arg naming an existing file; `--project` outranks
  both. Bootstrap and wrapper scripts inject `--project <their own dir>` ahead of
  your argv (option takes last value, so a typed one still wins), so a bin dir
  decides its project and `../B/bin/uv run x.py` acts on B, not on your CWD.
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
  `shell/`, `locks/`; entry key `identity/<platform>-<arch>-blake3-<hash>`. A
  first-run notice on stderr announces a LOCAL tree only; the shared default is
  silent. Neither one prompts.
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
  `shell/` for what it is. Warns about cache relocation only under an
  override. Refresh is by CONTENT: each hook carries
  `_ENVY_HOOK_STAMP=<writer version>:<digest of the resource text>`, and every
  command rewrites a hook whose bytes differ from its own copy, leaves a
  byte-identical one from another version labeled as-is, and never overwrites a
  hook a NEWER envy wrote (all versions share one `shell/`). One resource edit
  refreshes only the hooks it touched.
- reproducibility: no lockfile. Pins live in the manifest: `@envy version` plus
  `sha256sums`, per-source `sha256`, git `ref` as a full sha via
  `envy git-resolve <url> <ref>`. Unhashed fetches re-download every run.

## windows

Supported target, not a port. Same manifest, same specs, same cache layout.

- bootstrap `bin\envy.bat` (batch, parses the `@envy` header itself, walks up for
  the root manifest, honors `ENVY_CACHE_ROOT`/`ENVY_MIRROR`). Wrappers are
  `bin\<tool>.bat`: `setlocal`, bin dir prepended to PATH, resolve the product,
  `call` it, forward `%ERRORLEVEL%`.
- `--platform posix|windows|all` on `init`/`sync`/`deploy` selects which script
  flavors get written, defaulting to the host. Bootstrap AND wrappers are
  per-flavor, so a plain `sync` on macOS does NOT restamp `envy.bat`. Use
  `--platform all` in a cross-platform repo. A host-only deploy does not prune
  the other flavor.
- scripts get the newlines their TARGET needs, not the host's: **CRLF for every
  `.bat`** (`envy.bat` and the wrappers), LF otherwise, POSIX ones mode 755.
  An LF `.bat` does not merely look wrong: cmd.exe seeks labels by CRLF-assuming
  offsets, so it silently stops parsing `@envy` directives. envy renormalizes
  both directions, so a committed bin dir is byte-identical in every checkout.
  `core.autocrlf` rewriting the POSIX scripts makes every deploy report
  "updated"; fix with `bin/** -text` in `.gitattributes`. `*.bat eol=crlf` is also
  compatible.
- string verbs default to PowerShell (non-interactive, no profile, execution
  policy bypassed), run from a temp script. POSIX gets `bash -e`, so fail-fast is
  free; on Windows envy INJECTS fail-fast when `check=true` (the default). With
  `check=false` it injects nothing, so a Windows script keeps going where the
  POSIX one stops.
- paths are native: `envy.path.join`/`envy.abspath`/`envy product` all yield
  backslashes. Never hardcode a separator in a path you BUILD and hand to the
  filesystem — use `envy.path.join`. Declarative package-relative strings are the
  exception and are written with `/`: a `PRODUCTS` value, `STAGE.only`, `VENDOR`
  selectors and `vendor` paths are all `/`-separated on every platform, and envy
  joins them natively. `envy.EXE_EXT` is `".exe"`.
- cache `%LOCALAPPDATA%\envy`. Long paths and antivirus file locks are handled
  internally.
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
(false means a depot exports fetched bytes rather than install output), `VENDOR`
(selector list naming what of `pkg/` a vendoring manifest copies), `DISPLAY`
(0.4.2+, see output below).

**Spec-global evaluation order.** `PRODUCTS` is resolved
BEFORE `OPTIONS` runs, and is handed the manifest entry's options verbatim:
never validated, never defaulted, and an EMPTY TABLE (not nil) when the entry
declared none. So every key may be nil, and
`PRODUCTS = function(opts) return { t = paths[opts.target] } end` dies with a
bare "attempt to index a nil value" — `paths[nil]` is nil, and indexing that
throws. Marking `target` `required` in `OPTIONS` does NOT prevent it: `OPTIONS`
has not run yet, so the clean error it would have produced never happens. Guard
every option read in a `PRODUCTS` function. `DISPLAY` is the opposite — resolved
right AFTER `OPTIONS` validates, so its argument is always the checked table.

## output

**Exit code 0 = success, non-zero = failure, for every command.** The one
exception is `envy run`, which forwards its child's code. That is the ONLY
reliable signal: see the silence rule below before reading an empty screen as a
failure to start.

Human output (logs, progress, errors) is stderr. stdout is machine-readable only
and empty for every command that has no answer to print, so
`envy product cmake > p.txt` yields a path and nothing else. The commands with
stdout: `product` (a path, or `--json`), `package` (a dir), `hash`
(`<sha256>  <name>` lines), `export`/`merge-depot` (index lines), `git-resolve`
(one sha), `import` (a dir), `cache` (the usage report). Everything else: empty.

- a package's row is columns: `[identity]`, then the spec's `DISPLAY`, then what
  the row is saying. Rows are padded to the widest of each, so bars line up.
- **`DISPLAY` (spec global, 0.4.2+)**: string, or `function(options)` returning a
  string or nil, resolved once after OPTIONS validates. Adds to the identity, never
  replaces it. The case it is for is ONE spec instantiated many times, whose rows
  are otherwise indistinguishable — in a CI log as much as on screen, since it
  reaches the outcome line too. Must be one line of printable text: any byte
  `< 0x20` or `0x7f` (newline, tab, NUL, ESC) is an error, because the live region
  counts a row's width to erase it. No spec setting one = no column, no dead space.
- **a package that did no work draws no row (0.4.2+)**. A package prints a row
  only for a timed outcome (`installed`, `fetched`, `imported from depot` — the
  three that print a wall clock), a SETUP pair that ran, or a vendor copy that
  wrote. The untimed outcomes do not qualify on their own: `cache hit`,
  `setup complete` (user-managed, every CHECK already satisfied), `local bundle`.
  So a second `envy install` over a warm cache writes NOTHING to the terminal,
  not even cursor and auto-wrap control bytes (0.4.3+; through 0.4.2 a no-work
  run still emitted the live region's escape sequences). The `deploy:` summary
  works the same way and has for longer: it prints only when a wrapper was
  created, updated or removed. Do NOT read silence as failure; check the exit
  code.
- **off a TTY every package still reports**, cache hits included: a log that omits
  the no-ops is not a record of the run. So a piped run and a terminal run legitimately
  list different packages — the PIPED one lists MORE. `--verbose` narrates every
  package either way.
- **"my CI log is short/empty" is almost never the silence rule**, which only ever
  adds rows to a redirected stream. Check, in order: the log captured stdout and
  not stderr (`2>&1` — all human output is stderr); a global `-q`; on Windows,
  PowerShell `>` writing UTF-16; a `platforms` filter excluding the packages on
  the runner.
- **a package that vendored reports the copy** (`vendored N files to <dir>`) as its
  whole row, replacing the payload verdict — `cache hit` AND `installed (2.5s)`
  alike (0.4.5+; 0.4.2-0.4.4 only replaced an untimed one, so a freshly built
  vendored package said `installed`). Vendoring is the last phase to write. The
  `pkg_outcome` trace is unaffected and still carries the payload's verdict, which
  is what machine readers want. Under `envy vendor` the command prints the report
  instead, so nothing doubles.
- every displayed vendor destination (outcome, `auto_sync` warning, collision and
  nesting errors) is project-root-relative with forward slashes. The two errors
  naming a filesystem failure, and "resolves outside the project", keep the
  absolute path.
- a shell-hook refresh announces itself once, naming the shells
  (`Shell hooks updated (bash, zsh, fish) — restart your shell`). First write is
  not an update and says nothing.

## vendoring

0.4.0+. Copy-in mechanism: a package's cached payload duplicated into the project
tree, for build systems that require in-source inputs. Not a move, not a link;
the cache entry stays authoritative.

- **manifest asks, spec narrows.** `vendor` on a `PACKAGES` entry is the ask.
  `VENDOR_ROOT = "<dir>"` in the root manifest is needed ONLY for `vendor = true`,
  which derives a leaf under it; `vendor = "exact/dir"` names its own destination
  and needs no VENDOR_ROOT at all. Spec's `VENDOR = { globs }` picks what of the
  install dir is worth copying (absent/empty = everything), validated at
  spec_fetch so a bad glob fails before any fetch. A spec never requests
  vendoring.
- `vendor` forms: `true` (derive a leaf under VENDOR_ROOT) | `false`/absent (no)
  | `"exact/dir"` (project-relative, needs NO VENDOR_ROOT) |
  `{ path = ..., auto_sync = ... }` | `{}` (= true). Manifest PACKAGES ONLY, and
  only the `source` shape: a DEPENDENCIES, `source.dependencies` or `bundle =`
  entry carrying it is an unknown-key error.
- **derived names escalate only as far as they must**, per colliding group and to
  a fixpoint: `name` → `ns.name` → `ns.name@rev` → `ns.name@rev-<options hash>`.
  So two option variants of one spec both vendor. An explicit path is a fixed
  point and never escalates; a derived name that wanted it steps aside.
- paths validated like `@envy cache-local`: relative, no leading separator, no
  drive letter, no `.`/`..` component, no `~`/`$`/`%`. **Anchored on the ROOT
  manifest's directory, NOT on the file that wrote the entry**: the opposite of
  an entry's `source` under `envy.import`, so one component's `vendor` path means
  different things standalone and imported. Gate on `ENVY_IMPORTER`, or declare
  vendoring in the root.
- **whole plan resolved and checked before any file is written**: duplicate
  destinations and nested ones (outer's wipe would erase inner) both error naming
  both packages. Platform-excluded entries are dropped first, so a linux-only and
  a darwin-only package may name the same dir. At copy time the destination is
  also resolved through symlinks and refused if it lands outside the project.
- **runs as a per-package phase (`pkg_vendor`, after export) of `install` and
  `sync`.** A package nobody vendors pays one no-op step. `install` therefore
  does write into the work tree when a manifest vendors.
- **`envy vendor` (0.4.0+) is the same ladder run for the sake of that one
  step**, and the only way to override `auto_sync` or to ask without doing.
  `vendor <queries>... | --all [--force] [--dry-run] [--threads N]
  [--manifest=...]`, plus the global `--project`. Re-execs into the pinned envy
  like `sync`/`install`. No `--subproject`, no `--ignore-depot`.
  - **selection is required and exclusive.** Bare `envy vendor` errors, queries +
    `--all` errors. No "all by default": the repair deletes directories.
  - **plan is resolved over the WHOLE manifest** (so a collision or nesting
    anywhere still errors before a byte is written), then filtered to the named
    targets. A vendored *dependency* of a target is NOT swept along.
  - runs targets to completion like `install`, so an uncached package is fetched
    and built first. True under `--dry-run` too.
  - a named package with no `vendor` field errors (`'x' is not vendored`);
    `--all` silently skips them. A manifest vendoring nothing errors either way.
  - `--force` = "read every destination as `auto_sync = true`". It lifts the
    exemption only; an up-to-date destination is still a no-op.
  - `--dry-run` = same decision, nothing written **to the destination**. Not "no
    writes at all" (the ladder still runs, the cache still records the pristine
    digest). `files`/`bytes` become what a copy would have written.
  - `--threads 0` = default; negative errors at execute, as `hash --threads`
    does. Does not change what lands.
  - report is one `tui::info` line per target on **stderr**, in target order
    (stdout stays empty): `vendored N files to <dir>` / `re-vendored N files to
    <dir>: contents were dirty` / `up to date: <dir>` / `kept <dir>: contents
    differ from the package`, with `would (re-)vendor` under `--dry-run`, `<dir>`
    project-relative. The command owns the report here, so the package row
    stays out of it (and these are the verdicts a row is silent about anyway).
- **drift check keeps NO project-side state.** Each run hashes the destination
  whole (`tree_hash`, BLAKE3) and compares against the pristine digest in the
  cache entry (`envy-vendor-<16 hex of the canonical selector list>`, beside
  `pkg/`, written at install and backfilled on a cache hit or depot import).
  Keyed on the selector set because a package cache key does not cover its spec's
  contents. Mismatch of ANY kind (edited file, stray file, deleted file, added or
  removed empty dir, repointed symlink, exec-bit change, package moved on) wipes
  and recopies. mtime alone is not drift. Consequence: a vendored tree committed
  to git is adopted as-is on a machine that never ran envy.
- `auto_sync = false` exempts one entry: a mismatch is a `tui::warn` (which names
  `envy vendor --force`) and the directory is left exactly as it is. Absent
  destination still copied, matching one still quiet. It is a manifest default,
  not a lock: `--force` overrides it.
- **a destination that IS a symlink does not survive the repair.** The wipe
  removes the link and leaves its target whole, and the copy then creates a real
  directory. (A symlinked path component resolving OUTSIDE the project is still
  a hard refusal.) So a vendor destination cannot be aliased onto a directory
  you maintain.
- **envy never prunes.** Moving a destination copies afresh and leaves the old
  one. Removing `vendor` leaves the directory.
- refusals: `USER_MANAGED` (no cached payload, caught at spec_fetch, names the
  package), `vendor = ""`, a bad `vendor` type, unknown key in the `vendor`
  table, non-boolean `auto_sync`. A BUNDLE entry vendors from **0.4.6**; before
  that the key was an unknown-key error there, which took vendoring away from
  any spec that moved into a bundle.
- **`VENDOR_ROOT` is root-only**, same rule as `DEFAULT_SHELL`/`PACKAGE_DEPOTS`:
  an `envy.import`ed manifest setting it errors unless the root holds that exact
  value.
- TUI: determinate bar on the package row counting files, and the copy is what
  the row's outcome then reports (see [output](#output)). Up-to-date draws nothing.
- **one selector language, four users**: `STAGE.only` / `envy.extract`'s `only` /
  `envy extract --only`, a spec's `VENDOR`, and `envy hash --tree --only`. Same
  parser: `/`-separated, case-sensitive, `*`/`?` within a component, `**`
  spanning, `[a-z]`/`[!a-z]` classes. Leading `!` excludes and beats an
  inclusion; an empty include list means everything. An INCLUSION matching
  nothing is an error (it is a typo); an exclusion matching nothing is fine.
- `envy hash --tree <dir>...` prints the digest vendoring compares, so a drift
  report is reproducible by hand. It folds path, kind, exec bit and contents;
  empty dirs count, mtimes do not, symlinks hash their stored target unfollowed,
  and the exec bit is always 0 on Windows.

## dependencies

- kinds: **strong** (`{spec=..., source=...}`, instantiated immediately),
  **weak** (query plus `weak={fallback spec}`, used only if nothing else
  provides), **reference-only** (query that must be satisfied elsewhere),
  **product** (`{product="ninja"}`, whoever provides it).
- ordering: `needed_by` on a dependency names the phase of the *dependent* that
  blocks on it, one of `check|import|fetch|stage|build|install`. Default `build`.
- **entry shapes are closed sets**: an unknown key is an error listing
  the allowed ones, wrapped with the file and index (`<manifest>: PACKAGES[2]:`,
  `spec 'x@r1': DEPENDENCIES[2]:`). Manifest PACKAGES takes
  `spec|source|bundle|sha256|ref|options|platforms|setup|needed_by|product|vendor`
  (`vendor` 0.4.0+, manifest-only), is
  always a TABLE (no bare-string shorthand), refuses `weak`, and refuses
  `source = { fetch = ... }` (nothing could call it). A `bundle` entry is its own
  narrower shape:
  `spec|bundle|options|platforms|setup|needed_by|product|vendor` only
  (`vendor` 0.4.6+), so `sha256|ref` there are unknown-key errors.
  Spec DEPENDENCIES takes the same minus `platforms` (its own message: platform
  filtering is a manifest field, gate with `if envy.PLATFORM`) plus `weak`. `source.dependencies` drops
  `needed_by` too (always spec_fetch). A `weak = {...}` fallback is a complete
  strong declaration and refuses `bundle|setup|weak|needed_by`.
- **envy.product / envy.package / envy.loadenv_spec answer from DIRECT edges
  only**. Transitive reachability is refused by name. Fuzzy match applies
  (`name`, `ns.name`, `name@rev`, full canonical), earliest `needed_by` wins,
  ties by identity. A dotted revision matches (`gcc@13.2.0`), in CLI queries too.
  `loadenv_spec` module paths are Lua dot syntax only: no separators, no `..`,
  no leading or trailing `.`, and the joined path is re-checked against the load
  root.
- **one identity, one option set, per DEPENDENCY LIST**. Dependency edges are
  identity-keyed, so two entries naming one identity with different `options`
  error: at parse time in a spec's DEPENDENCIES and in `source.dependencies`, and
  at wire time for any other edge. Agreeing options are fine (that is how several
  product entries share one provider). **This does NOT apply to top-level
  `PACKAGES`**, which is not a dependency list: N entries naming one identity with
  N different option sets are N packages, which is the whole point of options
  being part of the key — and the case `DISPLAY` exists to label.
- cycles are caught as each edge is added, by reachability rather than spawn
  path, and the message names the whole path
  (`Dependency cycle detected: a -> b -> c -> a`; `Fetch dependency cycle
  detected: ...`).
- **fetch dependencies**: a package needed before another package's spec or
  payload can be fetched, for example an Artifactory or corporate auth CLI.
  Declared inside the source table:
  `source = { dependencies = {{spec=..., source=...}}, fetch = function(tmp_dir, opts) ... end }`.
  Fetch deps are fully installed before the dependent's spec is loaded. The
  fetch function commits `spec.lua` via `envy.commit_fetch`, plus any helper
  files beside it, all of which land in the spec dir.
  `envy.product`/`envy.package` work inside a `source.fetch` function: entries
  are wired with `needed_by = spec_fetch` before it runs. A spec-declared fetch
  runs as the CHILD: `options` are the entry's own (not the
  declaring spec's), the reachable deps are the entry's own
  `source.dependencies`, and each option set gets its own spec cache entry.
  A `source` table with neither `fetch` nor `dependencies` errors (a URL or path
  is a plain string). Every
  `source.dependencies` entry must be **strong** (`spec` + `source`), and so must
  everything in its transitive closure. The weak pass runs at a resolution
  barrier after every spec_fetch, including that of the consumer still waiting,
  so nothing weak can be ordered in time.
- setup selection: manifest entry `setup = {"pair", ...}` opts into SETUP pairs.
  Nothing runs unselected, and the selection is not part of the cache key.
- bundles: one fetched container of many specs.
  `BUNDLES = { alias = {identity, source, ref} }`, and an entry uses
  `bundle = "alias"` instead of `source`. A bundle also carries Lua under
  `lib/`: its own specs reach it with `require`, an outside spec with
  `envy.loadenv_spec(identity, module)` from a phase, and a MANIFEST with
  `envy.loadenv_bundle(alias, module)` (**0.4.6+**) at global scope. See
  [lua modules](#lua-modules).
- **redeclaration must agree about the payload**: two declarations of one
  identity naming different sources error
  (`spec 'x@r1' is declared with conflicting sources in <a> and <b>`), for EVERY
  source kind. The files named are the ones that wrote the entries, so two
  imported components name themselves, not the root.
- depot (OPTIONAL): `PACKAGE_DEPOTS = { "s3://bucket/packages.txt" }`, an index
  of prebuilt `.tar.zst` artifacts. A hit skips fetch and build. Bypass with
  `--ignore-depot` or `ENVY_IGNORE_DEPOT=1`. Publish loop: `envy export`, then
  `envy merge-depot`, then upload. A package inside the depot's own DEPENDS
  closure is exempt from the index, which is how the depot bootstraps itself.
- DEFAULT_SHELL / PACKAGE_DEPOTS `DEPENDS` entries resolve through a stricter
  matcher than CLI queries: a query matching zero packages errors, and so does
  one matching two DISTINCT packages (dedup is on the canonical key first, so two
  entries collapsing onto one package count once). CLI queries still take
  the first match in manifest order.
- a failing run reports each package's own error, deduplicated and sorted. A hang
  reports
  `Deadlock: no task is running while N wait(s) are blocked:` plus every blocked
  wait and what it waits for.

## lua modules

Four loaders, and the scope each is legal in. The three `envy.*` ones run the
file in a sandbox and ALWAYS re-execute; only `require` caches.

| call | scope | resolves against |
| --- | --- | --- |
| `require(mod)` | a spec INSIDE a bundle | the bundle root, on `package.path` |
| `envy.loadenv(mod)` | anywhere, incl. `envy lua` | the CALLING FILE's directory |
| `envy.loadenv_spec(id, mod)` | spec PHASE functions only | a declared dependency's root (the bundle root when it came from one) |
| `envy.loadenv_bundle(alias, mod)` | manifest GLOBAL SCOPE only (**0.4.6+**) | a `BUNDLES` alias of the calling file |

- **what comes back (0.4.6+)**: the module's RETURN VALUE when it returned a
  table, the globals it assigned when it returned nothing, an error naming the
  module for anything else — the rule `require` teaches. Before 0.4.6
  `loadenv`/`loadenv_spec` handed back the globals REGARDLESS, so the ordinary
  `local M = {} ... return M` came back `{}` and failed later as `attempt to
  call a nil value`; a module serving both callers had to assign a global AND
  return a table. That double assignment is now dead weight, not an error.
- `mod` is Lua dot syntax for `loadenv_spec`/`loadenv_bundle`: no separators, no
  `..`, no leading or trailing `.`, and the joined path is re-checked against
  the load root. `loadenv` is looser (a separator works) but from 0.4.6 also
  cannot escape the calling file's directory.
- **`envy.loadenv_bundle`** materializes the bundle DURING the manifest's global
  scope, earlier than any other bundle fetch, so a helper's entries go straight
  into `PACKAGES`. Declare `BUNDLES` ABOVE the call (a manifest is read top to
  bottom). An imported fragment resolves its own `BUNDLES` against its own file,
  then the root's against the root. A `local.` bundle is read in place; every
  other shape lands in the cache the bundle's own package later finds complete.
  Refusals: called outside manifest scope (points at `loadenv_spec`), alias
  absent (names alias + file), CUSTOM-FETCH bundle (its fetch needs a phase).
  Trace: `lua_ctx_loadenv_bundle`.
- an entry a helper RETURNS parses exactly like a literal one: its `bundle`
  names an alias of the CONSUMING manifest (possibly a different bundle), and it
  may carry `vendor` (0.4.6+).
- **`ENVY_BUNDLE`** (**0.4.7+**): set in a module `loadenv_bundle` or
  `loadenv_spec` loaded out of a bundle, `{ identity, alias, root }`. `alias` is
  what the CALLING file called the bundle, `nil` under `loadenv_spec` (which
  resolves by identity). The whole global is `nil` where no bundle is involved —
  a manifest, a spec, anything `envy.loadenv` reached, and anything a bundle's
  own spec reached with plain `require`. It lets a bundled entry builder write
  `bundle = ENVY_BUNDLE.alias` instead of taking a name its caller already
  typed. Readable but NOT one of the module's own globals, so a module that
  returns nothing does not leak it into the caller's table (or into an entry's
  `options`, which would put a cache path in the cache key).
- `ENVY_SHELL`, `ENVY_IMPORTER` and `ENVY_BUNDLE` are the only bare globals envy
  installs.

## CLI

`envy <cmd>`. Global flags `--verbose -q --trace[=sinks] --cache-root --project`
go before the subcommand (`envy sync --verbose` is a parse error). `--project <dir>`
is honored by every manifest-loading command: `sync install deploy vendor product
package run export import use cache shell`. Streams and exit codes: see
[output](#output).

**`[queries]` throughout means package queries**, matched fuzzily in this order:
`name`, `ns.name`, `name@rev`, full canonical key
(`ns.name@rev{["k"]=v,...}`). A dotted revision works (`gcc@13.2.0`). A CLI
query takes the FIRST match in manifest order; the stricter matcher used by
`DEPENDS` (below) errors on zero and on two distinct matches instead. Omitted
where optional = the whole manifest.

- `install [queries]`: install packages. Writes NO bin-dir files — but it is not
  "no work-tree writes": a manifest that vendors gets its vendored trees written
  here. **The default choice for anything that just wants bytes**: warming a
  CI/Docker cache, prefetching, benchmarking a cold cache, proving a spec still
  builds, bumping a version option, repopulating after a cache wipe or an
  `envy cache --local/--shared`. Wrappers resolve their package at call time, so
  none of those need a deploy.
- `sync [queries]`: `install` plus deploy product scripts. Use it when the bin
  dir must change, which is narrower than "after a manifest edit": a **product**
  added/removed/renamed, after `use` (restamps bootstrap + `.luarc.json`),
  `--platform all`, or restoring a cleaned bin dir. Editing a package's `options`
  changes no wrapper, so `install` covers it. When in doubt `sync` is safe, just
  broader.
- `deploy [queries] [--strict] [--platform ...]`: deploy product scripts only,
  no installs. Prunes marked wrappers outside the resolved graph.
- `vendor <queries>... | --all [--force] [--dry-run] [--threads N]
  [--manifest=...]` (0.4.0+): run the vendor step alone. See the vendoring
  section. Selection is REQUIRED and exclusive: bare `envy vendor` errors, and so
  does queries + `--all`.
- `init <project-dir> <bin-dir> [--envy-version X.Y.Z] [--mirror URL]
  [--pin-sums] [--deploy=bool] [--root=bool] [--platform ...]`: new project,
  manifest plus bootstrap scripts plus `.luarc.json`, and appends `.envy/` +
  `.envy-cache-*` to `.gitignore` (only if `<project-dir>/.git` exists; skips
  entries already present in any equivalent git spelling, `!` negation included).
  `--envy-version` re-execs into that release so the pin, the script stamp, and
  the extracted types all come from it; parent-side and stripped from the child's
  argv. Downloads it from `--mirror`.
  A dev build (0.0.0) or `ENVY_NO_REEXEC` warns and stamps itself. A relative
  `<bin-dir>` resolves against `<project-dir>`, NOT the cwd, so `envy init proj bin`
  writes `proj/bin` from anywhere. An escaping
  bin dir under a root manifest warns (deploy owns the verdict); no relative path
  at all, two Windows drives, errors before anything is created.
- `product [name] [--json]`: resolve a product path. Naming one installs its
  provider; no name lists all; `--json` dumps every product as one object and
  computes paths WITHOUT installing, so `install` first if the files must exist.
- `package <identity>`: install and print the package dir path.
- `run <cmd...>`: exec cmd with project bin on PATH and `ENVY_PROJECT_ROOT` set.
- `shell <bash|zsh|fish|powershell>`: print the shell-hook source line.
- `use <version>`: retarget the pinned envy version in the manifest.
- `git-resolve <url> <ref>`: remote ref to full sha, for pinning.
- `hash <paths>`: sha256 lines for depot indexes. `hash --tree <dirs>` instead
  prints one BLAKE3 subtree digest per directory, the one vendoring compares,
  with `--only` (selector language, `!` included), `--threads` (0 = performance
  cores), `--json` (array of objects, `duration_ms` times the hash not the
  process), `--stats` (stage + per-worker balance, on stderr so stdout stays the
  digest, inside the object under `--json`, suppressed by `-q`). `--tree`
  excludes `--prefix`; the four `--tree` flags without it are an error, not
  ignored; every `--tree` argument must be a directory.
- `export`, `import`, `merge-depot`: depot artifact publish and consume.
- `fetch <src> <dst>`, `extract <archive> [dst] [--only PATH|GLOB|!GLOB]...`,
  `hash <paths>`, `git-resolve`, `lua <script>`: standalone utilities, no
  manifest or project required. Transports and formats are compiled in: AWS SDK
  (so `s3://` works with ambient credentials and no AWS CLI), libgit2 (no `git`
  binary), libarchive (tar/gz/xz/bz2/zst/zip/7z/rar/iso). Package the AWS CLI
  only when a project wants the CLI itself. `mirror-envy` to `s3://` resolves
  credentials BEFORE downloading, so an expired SSO token says so rather than
  surfacing as a transfer error; its S3 failures carry their own hints.
- `cache [--root | --user-wide-root | --local | --shared]`: cache location and
  disk usage; flags mutually exclusive, one action per invocation. Also
  `version`, `mirror-envy`.
- fetch retries: transport failures retry (`connect`, `transfer`, `timeout`,
  HTTP 5xx, 429); every other 4xx and any malformed-URL or local error is fatal.
  From **0.4.6** a WALL-CLOCK budget ends the loop, not the attempt count:
  `ENVY_FETCH_BUDGET_MS` (default 90000) measured from the FIRST failure, so an
  attempt burning its own connect timeout spends it too. `ENVY_FETCH_ATTEMPTS`
  is now a ceiling (default 10, was 3). A `connect` failure is capped at 5s
  instead (a host that will not handshake is down, not busy). Backoff doubles
  (1x/2x/4x `ENVY_FETCH_RETRY_BASE_MS`, default 1000) ±50%, max 30s per wait;
  `Retry-After` is a jittered FLOOR, and one longer than the budget's remainder
  ends the fetch. `s3://` is excluded, the AWS SDK retrying itself. A waiting
  package draws a countdown row, `retry 2 in 6s (http_status) tool.tar.gz`, so a
  90s wait does not read as a hang. A non-status transport error carries the
  status and Content-Type that did arrive
  (`... after 0 of 54881 bytes (HTTP 200, text/html)`), which is how a 200 HTML
  interstitial tells itself apart from a network fault.
- editor support: `init` writes `.luarc.json` with three platform cache paths and
  envy's LuaCATS type definitions on `workspace.library`; `sync`/`deploy` rewrite
  stale `envy/<semver>` entries and preserve everything else. Delete the file to
  opt out. `BUNDLES` is not in the default `diagnostics.globals` list;
  `ENVY_BUNDLE` is, from 0.4.7.

Superprojects: nested `envy.lua` manifests compose. A sub-manifest sets `@envy
root "false"`, and the superproject imports it via
`envy.import("libs/common")` plus `envy.extend(PACKAGES, {...})`. Commands walk
up to the root manifest, and `--subproject` stops at the nearest.

`envy.import(path)` (MANIFEST SCOPE ONLY, not in specs or `envy lua`)
runs another manifest in a sandbox and returns its globals. Path is relative to
the calling manifest; a directory appends `envy.lua`. An imported entry stays
tied to its own file: relative `source` anchors on the IMPORTED manifest's dir,
and `bundle = "alias"` resolves against ITS `BUNDLES` first, then the root's (no
re-export needed; two components may reuse an alias). Declarer stays the
superproject, so project root, SETUP cwd and custom-fetch cache keys name the
root. Only `PACKAGES`/`BUNDLES` are tagged; splice other globals by hand
(`PACKAGE_DEPOTS = sub.PACKAGE_DEPOTS`), and for the ROOT-ONLY globals
`PACKAGE_DEPOTS`/`DEFAULT_SHELL`/`VENDOR_ROOT` that splice is MANDATORY: an import
that sets one the root does not end up holding is an error, not a silent drop.
Provenance is the imported file, so a conflict names both component manifests
rather than the root. Imported file sees `ENVY_IMPORTER` = importer's absolute
path, `nil` standalone: `if not ENVY_IMPORTER then` is the standalone-only gate.
Nesting fine, cycles error.
**Imported header is INERT** (`bin`, `deploy`, `cache-*`, `state-dir`, `mirror`,
`sha256sums`, `root` all do nothing; one tree, one cache root, one binary per run,
all from the root header). Sole exception: imported `@envy version` NEWER than
the root pin errors, older warns.

`--trace[=sinks]` emits a structured event per decision (manifest resolution,
dependency waits, depot hits, download retries, every vendor destination and
result, package outcomes). Schemas are in the Logging & Tracing reference; do
not hand-transcribe them here. The one to know is `pkg_outcome`: it reports the
PAYLOAD's verdict (`cache_hit`, `installed`, `imported`, ...) regardless of what
the row on screen said.

Env vars read: `ENVY_CACHE_ROOT`, `ENVY_MIRROR`, `ENVY_IGNORE_DEPOT`,
`ENVY_NO_REEXEC`, `ENVY_FETCH_BUDGET_MS` (0.4.6+), `ENVY_FETCH_ATTEMPTS`,
`ENVY_FETCH_RETRY_BASE_MS`; hook-only
`ENVY_SHELL_HOOK_DISABLE`, `ENVY_SHELL_NO_ENTER_EXIT_ANNOUNCE`,
`ENVY_SHELL_NO_ICON`. Written: `ENVY_PROJECT_ROOT` and `PATH`, by `envy run`, the
shell hook, and every deployed product script.

Lua API in specs: `envy.run(script|{lines}, {quiet, check, capture, interactive,
env, cwd, shell})`, `envy.fetch(src, {dest})`, `envy.commit_fetch`,
`envy.verify_hash`, `envy.extract`, `envy.extract_all(src, dst, {strip, only})`,
`envy.copy/move/remove/exists`, `envy.path.*`, `envy.abspath`,
`envy.template(str, vars)`, `envy.product(name)`, `envy.package(identity)`,
`envy.options(schema)`, the module loaders `envy.loadenv` /
`envy.loadenv_spec` / `envy.loadenv_bundle` (see [lua modules](#lua-modules)),
and constants `envy.PLATFORM` (`darwin|linux|windows`), `envy.ARCH`,
`envy.PLATFORM_ARCH`, `envy.EXE_EXT`.
