---
sidebar_position: 9
title: Options
---

# Options

Options let one spec serve many needs. The manifest passes `options = { ... }`,
the spec validates them, every verb receives them, and they become part of the
package's identity.

```lua title="envy.lua"
PACKAGES = {
  { spec = "envy.python@r1", bundle = "envy",
    options = { version = "3.13.14", release = "20260623", provide_python3 = true } },
}
```

```lua title="python.lua"
OPTIONS = {
  version = { required = true },
  release = { required = true },
  provide_python = { type = "boolean" },
  provide_python3 = { type = "boolean" },
}

FETCH = function(tmp_dir, opts)
  return { source = url_for(opts.version, opts.release), sha256 = hash_for(opts) }
end
```

Validation happens during the spec fetch phase, before any download. A misspelled
option fails in a second rather than after 400 MB.

## Options are identity

envy names the cache entry with a hash of the identity plus the serialized
options, so two entries differing in one option are two packages:

```lua
PACKAGES = {
  { spec = "envy.python@r1", bundle = "envy",
    options = { version = "3.13.14", release = "20260623", provide_python3 = true } },
  { spec = "envy.python@r1", bundle = "envy",
    options = { version = "3.14.2", release = "20260623" } },
}
```

Both install, both coexist, and neither invalidates the other. The canonical key
being hashed is the identity with its options appended, sorted by name:

```
envy.python@r1{provide_python3=true,release="20260623",version="3.13.14"}
```

That string is what `envy product` prints in its provider column, and it works
as a fully specific
[query](../../reference/cli/index.md#package-queries).

Two consequences. Changing an option never mutates a package, it names a new
one. And options have to hash, so a function in an options table is rejected.

The platform is not an option. It is a separate component of the cache entry
path, so one option set on macOS and the same option set on Windows are two
entries that never collide. A spec should therefore branch on `envy.PLATFORM`
rather than take a `platform` option, and an option that only makes sense
somewhere can be validated per platform inside
[the function form](#shape-2-a-function).

## Shape 1: a schema table

```lua
OPTIONS = {
  version = { required = true, type = "semver", range = ">=3.9.0 <4.0.0" },
  tools = { required = true, type = "list" },
  optimize = { type = "string", choices = { "size", "speed", "debug" } },
  jobs = { type = "int", range = ">=1 <=64" },
  strict = { type = "boolean" },
}
```

| Constraint | Meaning |
| --- | --- |
| `required` | Absent is an error. Anything not `required` is optional. There are no defaults, so handle `nil` in your verbs. |
| `type` | One of `string`, `boolean`, `int`, `float`, `table`, `list`, `semver`. `list` means a sequential array, so gaps are rejected. `semver` parses the value as a semantic version. |
| `range` | For `semver`, a semver range such as `">=1.2 <2"`. Otherwise a numeric range: space-separated `>=`, `>`, `<=`, `<`, `==` terms, for example `">=1 <=64"`. Strings that parse as numbers are accepted. |
| `choices` | Allowed values. With `type = "list"`, every element must be one of them. |
| `validate` | A function receiving the value. Return `nil` or `true` to accept, `false` to reject, or a string to reject with that message. |

Undeclared options are rejected, and the error lists what the spec accepts, so a
misspelled `verison` is caught immediately.

Use `validate` when the rule is about the value's shape:

```lua
OPTIONS = {
  version = {
    required = true,
    validate = function(v)
      if not v:find("%.") then
        return "version must contain a dot, for example '9.12' rather than '912'"
      end
    end,
  },
  packages = {
    required = true,
    type = "list",
    validate = function(v)
      if #v == 0 then return "'packages' must be a non-empty array" end
      for i, name in ipairs(v) do
        if type(name) ~= "string" or name == "" then
          return string.format("package at index %d must be a non-empty string", i)
        end
      end
    end,
  },
}
```

## Shape 2: a function

Use a function when the valid set is computed, most often from the spec's own
fingerprint table. The versions it accepts are then the versions it has hashes
for. Call `envy.options(schema)` for the normal per-field validation, then add
whatever cross-field checks the spec needs:

```lua
local hashes  -- "<version>+<release>" -> triple -> sha256, filled in below

local function pin(opts) return opts.version .. "+" .. opts.release end

OPTIONS = function(opts)
  envy.options({
    version = { required = true },
    release = { required = true },
    provide_python = { type = "boolean" },
    provide_python3 = { type = "boolean" },
  })

  if not hashes[pin(opts)] then
    return "unrecorded version+release '" .. pin(opts) ..
        "'; recorded: " .. table.concat(recorded_pins(), ", ")
  end
end
```

Return values:

| Return | Result |
| --- | --- |
| `nil` or `true` | Accepted. |
| `false` | Rejected, with a generic message. |
| a string | Rejected, with that string as the message. Prefer this. It is the difference between "OPTIONS failed" and a list of the versions that exist. |
| anything else | An error about `OPTIONS` itself. |

## Shape 3: omitted

With no `OPTIONS` global there is no validation. Whatever the manifest passes
reaches the verbs untouched, and unknown keys are not caught. That is fine for a
spec with no options, or a private one-off. A published spec should declare a
schema, because it is the only description of what the spec accepts that cannot
drift.

## Options in verbs

Every verb receives the validated table as its last argument:

```text
FETCH    = function(tmp_dir, opts)
STAGE    = function(fetch_dir, stage_dir, tmp_dir, opts)
BUILD    = function(install_dir, stage_dir, fetch_dir, tmp_dir, opts)
INSTALL  = function(install_dir, stage_dir, fetch_dir, tmp_dir, opts)
PRODUCTS = function(opts)
SETUP.<pair>.CHECK = function(pkg_dir, opts)
```

One file, one set of verbs, and every project's variation expressed as data in
the manifest.

## See also

- [Anatomy of a Spec](./index.md) for where `OPTIONS` sits among the globals.
- [Products](./products.md) for products computed from options.
- [Package Entries](../projects#package-entries) for the manifest side.
