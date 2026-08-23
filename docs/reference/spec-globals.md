---
sidebar_position: 3
title: Spec Reference
---

# Spec Reference

Terse companion to [Anatomy of a Spec](/concepts/specs).

## Globals

| Global | Allowed forms | When omitted |
| --- | --- | --- |
| `IDENTITY` | `"namespace.name@revision"` | error, always required |
| `FETCH` | string, table, array of tables, or function | error, unless `USER_MANAGED` |
| `STAGE` | table or function | every fetched archive is extracted |
| `BUILD` | string or function | nothing runs |
| `INSTALL` | string or function | the staged tree becomes the package |
| `SETUP` | table of named pairs | no host-side work |
| `OPTIONS` | schema table or function | options are accepted unvalidated |
| `PRODUCTS` | table or function | the package exports nothing |
| `DEPENDENCIES` | array of entry tables | none |
| `PLATFORMS` | array of strings, `darwin`, `linux`, `windows`, optionally `-arm64` or `-x86_64` | every platform |
| `USER_MANAGED` | boolean or function | `false`, meaning cache-managed |
| `EXPORTABLE` | boolean | `false`, so only fetched bytes are kept for export |

`DEFAULT_SHELL` is a manifest global, not a spec global. A spec picks a shell per
call with `envy.run(..., { shell = ... })`.

## Verb signatures

```text
FETCH(tmp_dir, options)
STAGE(fetch_dir, stage_dir, tmp_dir, options)
BUILD(install_dir, stage_dir, fetch_dir, tmp_dir, options)
INSTALL(install_dir, stage_dir, fetch_dir, tmp_dir, options)
SETUP.<name>.CHECK(pkg_dir, options)     -- pkg_dir is nil for user-managed
SETUP.<name>.INSTALL(pkg_dir, options)
PRODUCTS(options)
OPTIONS(options)
USER_MANAGED()
```

Every directory argument arrives with a trailing path separator. The one
exception is the `tmp_dir` handed to a `source.fetch` function, which does not.

Return values:

| Verb | Returns |
| --- | --- |
| `FETCH` | nothing, or a URL string, optionally followed by a sha256 |
| `STAGE`, `BUILD`, `INSTALL` | nothing |
| `SETUP.<name>.CHECK` | `true` for satisfied, `false` for not, or a script string to run |
| `SETUP.<name>.INSTALL` | nothing, or a script string to run |
| `PRODUCTS` | the products table |
| `OPTIONS` | nothing, `true`, `false`, or an error message string |
| `USER_MANAGED` | boolean |

## `FETCH` table fields

| Field | Meaning |
| --- | --- |
| `source` | URL, local path, or git URL. Required. |
| `sha256` | Verifies the download, and lets the cache reuse it. |
| `ref` | Commit for a git source. |
| `dest` | Rename the downloaded file. A plain filename, no separators. |
| `post_data` | HTTP POST body. HTTP and HTTPS only. |

An array of these tables fetches several files.

## `STAGE` table fields

| Field | Meaning |
| --- | --- |
| `strip` | Drop this many leading path components. |
| `only` | Extract just these archive-relative paths or globs, matched after `strip`. |

## Platform-aware specs

A spec runs on the machine doing the install, so the platform is read at spec
load time rather than declared:

```lua
PLATFORMS = { "darwin", "linux", "windows" }

PRODUCTS = { mytool = "bin/mytool" .. envy.EXE_EXT }

FETCH = function(tmp_dir, opts)
  local ext = (envy.PLATFORM == "windows") and ".zip" or ".tar.gz"
  return {
    source = base .. opts.version .. "-" .. envy.PLATFORM_ARCH .. ext,
    sha256 = hashes[opts.version][envy.PLATFORM_ARCH],
  }
end
```

`envy.EXE_EXT` is `".exe"` on Windows and `""` elsewhere, so one `PRODUCTS` line
covers all three. A product that only exists on some platforms takes its own
`platforms` field instead. String verbs run under PowerShell on Windows, so a
spec with a `BUILD` string needs
[a portability plan](/concepts/specs/build#on-windows).

## `PRODUCTS` entry fields

A string value is shorthand for `{ value = "...", script = true }`.

| Field | Default | Meaning |
| --- | --- | --- |
| `value` | required | Path relative to the package directory, or an arbitrary string. |
| `script` | `true` | Whether to deploy a wrapper script into the project's bin directory. |
| `platforms` | all | Restrict this product to some platforms. |

## `DEPENDENCIES` entry fields

| Field | Notes |
| --- | --- |
| `spec` | Identity. Required, except for a product-only weak reference. |
| `source` | URL, path, git URL, or `{ fetch, dependencies }`. Mutually exclusive with `weak`. |
| `bundle` | Alias or inline bundle table, when the spec comes from a bundle. |
| `ref`, `sha256` | Pins for the spec source. |
| `options` | Part of the dependency's identity. |
| `needed_by` | `check`, `import`, `fetch`, `stage`, `build`, or `install`. Defaults to `build`. |
| `product` | Ask for one product rather than the whole package. |
| `weak` | Fallback entry when the query matches nothing. |
| `platforms` | Skip the dependency on other platforms. |
| `setup` | Select `SETUP` pairs by name. |

## `SETUP` pair fields

| Field | Required | Forms |
| --- | --- | --- |
| `CHECK` | yes | A script string, where exit 0 means satisfied, or a function returning a boolean or a script string. |
| `INSTALL` | yes | A script string, or a function returning nothing or a script string. |
| `PLATFORMS` | no | Per-pair platform filter. |
| `DEPENDS` | no | Names of sibling pairs that run first. Selecting a pair selects its prerequisites transitively. |

Setup pairs are re-evaluated every run, never cached, and never part of the
package key. See [The SETUP Verb](/concepts/specs/setup).

## `OPTIONS` constraint fields

| Field | Meaning |
| --- | --- |
| `required` | The option has to be present. |
| `type` | `string`, `int`, `float`, `boolean`, `table`, `list`, or `semver`. |
| `range` | Comparison chain for numbers and semver, for example `">=1 <=64"`. |
| `choices` | Array of allowed values. |
| `validate` | Function returning `nil` or `true` for valid, `false`, or an error message string. |

The table form validates declaratively. The function form receives the options
and may call `envy.options(schema)` to apply the same checks. Both reject options
the schema does not declare.

## Identity syntax

```text
namespace.name@revision
```

`namespace` and `name` are dot-separated identifiers, and `revision` is a spec
revision such as `r1` or `v1`, not the packaged tool's version. The tool version
belongs in `options`. A spec's `IDENTITY` has to match how the manifest names it,
and in a bundle it has to match its `SPECS` key.

## A minimal spec of each kind

```lua title="cache-managed"
IDENTITY = "acme.ripgrep@r0"
EXPORTABLE = true

FETCH = {
  source = "https://github.com/BurntSushi/ripgrep/releases/download/14.1.1/ripgrep-14.1.1-aarch64-apple-darwin.tar.gz",
  sha256 = "24ad76777745fbff131c8fbc466742b011f925bfa4fffa2ded6def23b5b937be",
}

STAGE = { strip = 1 }

PRODUCTS = { rg = "rg" }
```

```lua title="user-managed"
IDENTITY = "acme.build-essential@r1"
USER_MANAGED = true
PLATFORMS = { "linux" }

SETUP = {
  build_essential = {
    CHECK = "dpkg -s build-essential >/dev/null 2>&1",
    INSTALL = "sudo apt-get update && sudo apt-get install -y build-essential",
  },
}
```

## See also

- [Anatomy of a Spec](/concepts/specs) for the concepts and every verb form
- [Writing a Spec](../guides/writing-a-spec.md) for the tutorial
- [Lua API](./lua-api.md)
- [Manifest Reference](./manifest.md)
