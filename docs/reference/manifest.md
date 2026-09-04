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
| `PACKAGE_DEPOTS` | array | Depot index URIs, or `{ DEPENDS, FETCH }` tables. |
| `DEFAULT_SHELL` | constant, table, or function | Shell for string verbs. See [Shells & Scripts](/concepts/shells). |

Manifests are Lua, so `envy.import`, `envy.extend`, and `envy.abspath` are all
available. See [Lua API](./lua-api.md).

## Package entry fields

| Field | Type | Notes |
| --- | --- | --- |
| `spec` | string | Required. `namespace.name@revision`. |
| `source` | string or table | URL, path, git URL, or `{ fetch, dependencies }` for [fetch dependencies](/concepts/dependencies/fetch-dependencies). Mutually exclusive with `bundle`. |
| `bundle` | string or table | A `BUNDLES` alias, or an inline bundle table. Requires `spec`. |
| `sha256` | string | Pins a downloaded spec file. |
| `ref` | string | Commit for a git source. |
| `options` | table | Part of the package identity. Functions are rejected. |
| `platforms` | array of strings | Skip this entry on other platforms. |
| `setup` | array of strings | Select [`SETUP`](/concepts/specs/setup) pairs by name. |
| `needed_by` | string | One of `check`, `import`, `fetch`, `stage`, `build`, `install`. Defaults to `build`. |
| `product` | string | Makes this a [product dependency](/concepts/dependencies/declaring#product). |
| `weak` | table | Fallback entry for a [weak dependency](/concepts/dependencies/declaring#weak). Mutually exclusive with `source`. |

A bare string entry is shorthand for `{ spec = "..." }`, which only works when
the spec is resolvable without a source, so in practice from a bundle or a weak
query.

## Bundle entry fields

| Field | Notes |
| --- | --- |
| `identity` | Required. The bundle's `BUNDLE` value, `namespace.name@revision`. |
| `source` | Required. Git URL, archive URL, or local path. |
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
| `Package cannot specify both 'source' and 'bundle' fields` | Pick one. |
| `Package with 'bundle' field requires 'spec' field` | A bundle entry needs the spec identity. |
| `Bundle alias 'x' not found in BUNDLES table for spec '...'` | Typo, or the alias is declared in a different manifest. |
| `'@envy sha256sums' requires '@envy version'` | Add the version, or drop the pin. |
| `warning: deployment is disabled in <manifest>` | `deploy` is absent or false, so no product scripts were written. |

## See also

- [Projects & Manifests](/concepts/projects) for the concepts
- [Spec Reference](./spec-globals.md)
- [`envy init`](./cli/init.md), which writes a minimal manifest for you
