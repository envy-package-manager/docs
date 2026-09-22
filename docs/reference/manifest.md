---
sidebar_position: 2
title: Manifest Reference
---

# Manifest Reference

Terse companion to [Projects & Manifests](/concepts/projects).

## `@envy` header directives

| Directive | Default | Meaning |
| --- | --- | --- |
| `bin "<relpath>"` | **required** | Project bin directory, relative to the manifest. `bin-dir` is accepted as a synonym. |
| `version "x.y.z"` | resolved dynamically | Pinned envy version. Without it, the bootstrap script takes the latest it can resolve. |
| `sha256sums "<64 hex>"` | none | sha256 of the release's `SHA256SUMS` file. Requires `version`. |
| `mirror "<url>"` | GitHub releases | Where to download envy itself. `https://`, `s3://`, and `file://` all work. |
| `deploy "true\|false"` | `false` | Write product scripts into the bin directory. |
| `root "true\|false"` | `true` | Whether [discovery](/concepts/projects#manifest-discovery) stops here. |
| `cache-local "<path>"` | none | Project-local cache tree, relative to the manifest. Declaring it makes local the project's default. Requires envy 0.2.0. |
| `cache-mode "local\|shared"` | implied by `cache-local` | Overrides that implication. Requires envy 0.2.0. |
| `state-dir "<path>"` | manifest's directory | Where `envy cache --local/--shared` writes its marker. Requires envy 0.2.0. |
| `schema "N"` | none | Manifest schema version. |

Rules:

- A directive is a comment line before the manifest's first line of Lua. The
  first line of code ends the header, and a `-- @envy` comment below it is just a
  comment.
- The last occurrence of a key wins.
- Unknown keys are ignored, so an older envy can still read a newer manifest.
- `cache-local` and `state-dir` are relative literals anchored to the manifest's
  directory, never to your working directory. No expansion of any kind: `..`, a
  leading separator, a drive letter, `~`, `$VAR` and `%VAR%` are all rejected. An
  absolute cache root is `ENVY_CACHE_ROOT`'s job. See
  [The Cache](/concepts/cache#where-the-root-lives).
- `bin` is anchored the same way, and since envy 0.3.2 it is validated the same
  way: no drive letter, no leading separator, no `~`, `$` or `%`. `.` and `..`
  stay legal, because `bin "."` is a supported flat layout and an escaping bin
  directory is the design under `root "false"`.
  [`deploy`](./cli/deploy.md#bin-directory-placement) judges whether a given
  escape is safe.
- `cache-posix` and `cache-win` were removed in envy 0.2.0 and now raise an error
  naming `cache-local`. Because an older envy ignores keys it does not know, the
  bootstrap launchers refuse to run one older than 0.2.0 against a manifest using
  the new directives, rather than let it silently pick the shared cache.
- `sha256sums` without `version` is an error. A sums pin names one release, so it
  is meaningless when the version is resolved dynamically.
- `@envy package-depot` was removed. It now raises an error telling you to
  declare `PACKAGE_DEPOTS` instead.

## Globals

| Global | Type | Meaning |
| --- | --- | --- |
| `PACKAGES` | array | Package entries. Required. |
| `BUNDLES` | table | Alias to `{ identity, source, ref, sha256 }`. |
| `PACKAGE_DEPOTS` | array | Depot index URIs, or `{ DEPENDS, FETCH }` tables. Root manifest only. |
| `DEFAULT_SHELL` | constant, table, or function | Shell for string verbs. See [Shells & Scripts](/concepts/shells). Root manifest only. |
| `VENDOR_ROOT` | string | Project-relative directory that `vendor = true` entries land under. See [Vendoring](/concepts/vendoring). Root manifest only. Requires envy 0.4.0. |

Manifests are Lua, so `envy.import`, `envy.extend`, and `envy.abspath` are all
available. See [Lua API](./lua-api.md).

## Package entry fields

| Field | Type | Notes |
| --- | --- | --- |
| `spec` | string | Required. `namespace.name@revision`. |
| `source` | string | URL, path, or git URL. Mutually exclusive with `bundle`. A `{ fetch, dependencies }` table is rejected here, because nothing could call the function. See [Fetch Dependencies](/concepts/dependencies/fetch-dependencies#where-it-can-be-declared). |
| `bundle` | string or table | A `BUNDLES` alias, or an inline bundle table. Requires `spec`. |
| `sha256` | string | Pins a downloaded spec file. |
| `ref` | string | Commit for a git source. |
| `options` | table | Part of the package identity. Functions are rejected. |
| `platforms` | array of strings | Skip this entry on other platforms. |
| `setup` | array of strings | Select [`SETUP`](/concepts/specs/setup) pairs by name. |
| `needed_by` | string | One of `check`, `import`, `fetch`, `stage`, `build`, `install`. Defaults to `build`. |
| `product` | string | Makes this a [product dependency](/concepts/dependencies/declaring#product). |
| `vendor` | boolean, string, or table | Copy this package into the project tree. See [the forms below](#vendor-forms). Manifest entries only. Requires envy 0.4.0. |
| `weak` | table | Not accepted on a manifest entry. Declare weak references in a spec's [`DEPENDENCIES`](/concepts/dependencies/declaring#weak). |

An entry is always a table. There is no bare-string shorthand, and every entry
needs a `source` or a `bundle`.

Since envy 0.3.1 an unknown key is an error rather than an inert field, and the
message lists what the entry shape accepts:

```text
error: /src/app/envy.lua: PACKAGES[2]: Package: unknown key 'platfroms'; allowed keys are ENVY_BASE, ENVY_BUNDLES, needed_by, options, platforms, product, ref, setup, sha256, source, spec, vendor
```

The wrapper names the file and the index, so a typo in a fifty-entry manifest
points at one line.

## `vendor` forms

Copies the package's installed files into the project tree. See
[Vendoring](/concepts/vendoring) for the whole feature.

| Form | Meaning |
| --- | --- |
| `vendor = true` | Copy to a derived name under `VENDOR_ROOT`. |
| `vendor = false` | Do not copy. Same as omitting the key, so the setting toggles without being deleted. |
| `vendor = "deps/cobs"` | Copy to exactly that directory, relative to the root manifest. Needs no `VENDOR_ROOT`. |
| `vendor = { path = "deps/cobs", auto_sync = false }` | The same two settings written out. Both keys are optional, and any other key is an error. |
| `vendor = {}` | Same as `vendor = true`. |

`auto_sync` defaults to `true`, which means a destination that no longer matches
the package is wiped and copied again. `false` reports the mismatch as a warning
and leaves the directory alone, until
[`envy vendor --force`](./cli/vendor.md) is run against it.

A derived name is `name`, escalating to `namespace.name`, then
`namespace.name@revision`, then that plus a hash of the options, and only as far
as it must to stay unique across the manifest. An explicit path never escalates.

Paths must be relative, with no leading separator, no drive letter, no `.` or
`..` component, and no `~`, `$` or `%`.

```lua
VENDOR_ROOT = "third_party"

PACKAGES = {
  { spec = "local.nanocobs@r3", source = envy.abspath("envy/nanocobs.lua"),
    vendor = true },                                  -- third_party/nanocobs
  { spec = "acme.armgcc@r1", source = "https://specs.acme.example/armgcc.lua",
    sha256 = "e3b0c442...52b855", vendor = "toolchains/armgcc" },   -- exactly there
  { spec = "local.patched@r1", source = envy.abspath("envy/patched.lua"),
    vendor = { auto_sync = false } },                 -- report drift, do not repair
}
```

An entry that takes its spec from a `bundle` is its own narrower shape, without
`source`, `sha256`, or `ref`, since the bundle declaration carries those. It can
carry `vendor` from envy 0.4.6 on. Before that the key was rejected there as
unknown, which took vendoring away from any spec that moved into a bundle.

## Bundle entry fields

| Field | Notes |
| --- | --- |
| `identity` | Required. The bundle's `BUNDLE` value, `namespace.name@revision`. |
| `source` | Required. Git URL, archive URL, local path, or a `{ fetch, dependencies }` table for a [custom fetch](/concepts/dependencies/fetch-dependencies). |
| `ref` | Commit for a git source. Required in practice, since a moving ref is not reproducible. |
| `sha256` | For an archive source. |

Declaring the same bundle identity twice with different sources or refs is an
error.

## `PACKAGE_DEPOTS` forms

```lua
PACKAGE_DEPOTS = {
  "s3://acme-envy-packages/packages.txt",     -- plain URI

  { DEPENDS = { "tools.registry-cli@r1" },    -- fetched through a tool
    FETCH = function(ctx)
      local cli = envy.path.join(ctx.deps["tools.registry-cli@r1"].pkg_path, "bin", "reg")
      local index = envy.path.join(ctx.tmp_dir, "packages.txt")
      envy.run(cli .. " download envy-packages/packages.txt " .. index)
      return index
    end },
}
```

`FETCH(ctx)` gets `ctx.tmp_dir` and `ctx.deps[identity].pkg_path`, and returns
index text, a path to an index file, or an array of `{ url, sha256 }`. See
[Package Depots](/concepts/depots).

## A complete manifest

```lua title="envy.lua"
-- @envy schema "1"
-- @envy version "0.1.10"
-- @envy bin "bin"
-- @envy deploy "true"
-- @envy root "true"

BUNDLES = {
  ["first-party"] = {
    identity = "envy.package-specs@r3",
    source = "https://github.com/envy-package-manager/package-specs.git",
    ref = "ded36a39bbf13744f5a0e539f2f4741fecb61dd0",
  },
}

PACKAGE_DEPOTS = { "s3://acme-envy-packages/packages.txt" }

PACKAGES = {
  -- From the bundle, pinned by option.
  { spec = "envy.cmake@r0", bundle = "first-party", options = { version = "4.4.0" } },
  { spec = "envy.ninja@r0", bundle = "first-party", options = { version = "1.13.2" } },

  -- A local spec file next to this manifest.
  { spec = "local.mytool@r1", source = envy.abspath("envy/mytool.lua") },

  -- A spec fetched from a URL, pinned by hash.
  { spec = "acme.protoc@r2",
    source = "https://specs.acme.example/protoc.lua",
    sha256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    options = { version = "35.1" } },

  -- Linux-only, and it mutates the host, so a SETUP pair is selected.
  { spec = "acme.apt-packages@r1", bundle = "first-party",
    platforms = { "linux" }, setup = { "build_essential" } },
}
```

## Errors you will meet

| Message | Cause |
| --- | --- |
| `Manifest missing required '@envy bin' directive.` | No `bin` or `bin-dir`. |
| `'@envy bin' must be relative, with no leading separator: '/opt/bin'` | The bin path has a leading separator, a drive letter, or a `~`, `$` or `%`. |
| `Package cannot specify both 'source' and 'bundle' fields` | Pick one. |
| `Package: unknown key 'x'; allowed keys are ...` | A typo, or a field that belongs on a different entry shape. |
| `Package 'source' cannot be a { fetch = ... } table` | Move the declaration into a spec's `DEPENDENCIES` or a `BUNDLES` table. |
| `manifest PACKAGES entries cannot be weak` | Weak references belong in a spec's `DEPENDENCIES`. |
| `Package with 'bundle' field requires 'spec' field` | A bundle entry needs the spec identity. |
| `Bundle alias 'x' not found in BUNDLES table for spec '...'` | Typo, or the alias is declared in a different manifest. |
| `'@envy sha256sums' requires '@envy version'` | Add the version, or drop the pin. |
| `warning: deployment is disabled in <manifest>` | `deploy` is absent or false, so no product scripts were written. |
| `package 'x' asks to be vendored, but the manifest sets no VENDOR_ROOT` | `vendor = true` with no `VENDOR_ROOT`. Add the global, or give the entry a path. |
| `vendor destination collision: 'a' and 'b' both vendor to <dir>` | Two explicit paths naming one directory. Derived names escalate instead. |
| `nested vendor destinations: ... one would be erased by the other` | One destination sits inside another, and vendoring wipes before it copies. |
| `Package 'vendor' must be a boolean, a project-relative path, or a table of { path, auto_sync }` | A number, or some other type. |
| `Package 'vendor' path cannot be empty; use vendor = true to derive one` | `vendor = ""`. |
| `package 'x' is declared USER_MANAGED, which has no cached payload to vendor` | A host-mutating package has nothing to copy. |

## See also

- [Projects & Manifests](/concepts/projects) for the concepts
- [Spec Reference](./spec-globals.md)
- [`envy init`](./cli/init.md), which writes a minimal manifest for you
