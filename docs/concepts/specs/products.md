---
sidebar_position: 10
title: Products
---

# Products

A product is a named capability a package offers. Consumers ask for the name,
such as `cmake` or `doctest_cpp_h`, and envy answers with a concrete path or
value. Nothing hardcodes a cache path, so the cache can stay content-addressed
and disposable.

```lua
PRODUCTS = {
  cmake = "bin/cmake" .. envy.EXE_EXT,
  ctest = "bin/ctest" .. envy.EXE_EXT,
}
```

Values are relative to the package directory. envy resolves them against `pkg/`
when queried.

:::caution A product is not necessarily a script
Executable products get [wrapper scripts](../environment/product-scripts.md)
deployed. But a product can be any named value: a header path for a header-only
library, a shared library, a data directory, an apt package name. Mark those
`script = false`. They deploy nothing, and consumers reach them through
`envy product <name>` or `envy.product(name)`. Header-only packages need no
bin-directory tricks.
:::

## Declaring products

### Table with string values, for executables

```lua
PRODUCTS = { gn = "gn" .. envy.EXE_EXT }
```

The string shorthand means `{ value = <string>, script = true }`.

### Table with table values, for everything else

```lua
PRODUCTS = {
  doctest_cpp_dir = { value = ".", script = false },
  doctest_cpp_h = { value = "doctest.h", script = false },
  libjlink = { value = "libjlinkarm.so", script = false, platforms = { "linux" } },
}
```

| Field | Meaning |
| --- | --- |
| `value` | Required string. A path relative to the package directory, or a raw value for [user-managed](./user-managed.md) packages. |
| `script` | Deploy a wrapper script for it. Defaults to `true`. |
| `platforms` | Restrict the product, for example `{ "linux" }`. |

Directory products and file products are both common. A build system usually
wants the include directory, while a dependency edge wants the file.

### Function, computed from options

`PRODUCTS(opts)` returns the table. Use it when the layout depends on an option,
or to generate one product per list element:

```lua
-- One product per requested tool.
PRODUCTS = function(opts)
  local result = {}
  for _, tool in ipairs(opts.tools) do
    result[tool] = tool .. envy.EXE_EXT
  end
  return result
end
```

```lua
-- Claim the bare `python3` name only if this project asked for it, so several
-- interpreters can coexist. Each also provides its own `python3.13`.
PRODUCTS = function(opts)
  local python = ((envy.PLATFORM == "windows") and "install/" or "install/bin/")
      .. "python" .. envy.EXE_EXT

  return {
    python = opts.provide_python and python or nil,
    python3 = opts.provide_python3 and python or nil,
    ["python" .. opts.version:match("^(%d+%.%d+)")] = python,
  }
end
```

Setting a key to `nil` omits it, which is how an option turns a product on and
off.

```lua
-- Vendor layout differs enough per platform that the whole table is computed.
PRODUCTS = function(opts)
  local products = ({
    darwin  = { aws = "aws-cli/aws" },
    windows = { aws = "Amazon/AWSCLIV2/aws.exe" },
    linux   = { aws = "bin/aws" },
  })[envy.PLATFORM]
  assert(products, "unsupported platform: " .. envy.PLATFORM)
  return products
end
```

## The three consumption surfaces

| Surface | How | Who uses it |
| --- | --- | --- |
| Deployed wrapper | `cmake` | humans, Makefiles, anything expecting a normal executable |
| CLI | [`envy product cmake`](../../reference/cli/product.md), `envy product --json` | build-system glue, scripts, `envy run` users |
| Lua | `envy.product("ninja")` | other specs, during `BUILD` and `INSTALL` |

From Lua, the usual shape is a product feeding a generated script:

```lua
DEPENDENCIES = { { product = "cmake" }, { product = "ninja" } }

BUILD = function(install_dir, stage_dir, fetch_dir, tmp_dir, opts)
  return envy.template([[
{{cmake}} -G Ninja -DCMAKE_MAKE_PROGRAM={{ninja}} -S . -B build
{{ninja}} -C build
]], { cmake = envy.product("cmake"), ninja = envy.product("ninja") })
end
```

`envy.product` returns the provider's absolute path, so the script never names a
cache path. It resolves declared dependencies only, and only once the dependency
is ready for the phase you call from. An undeclared name is an error rather than
a lookup, and a product declared `needed_by = "build"`, the default, cannot be
resolved during `FETCH`. See
[BUILD](./build.md#function-using-dependency-products).

Asking for a product installs its provider on demand, which is why a deployed
wrapper works on a machine that has never synced. The four-line script calls
`envy product`, and the package materializes.

## Resolution rules

- Product names are global within a project. `cmake` means one thing.
- Two packages providing the same product name is an error. There are no
  priority rules and no tie-breaks. Options exist so that a spec can decline to
  claim a generic name, as in the `provide_python3` example above.
- A product whose `platforms` exclude the current machine is not present.
- User-managed products are raw values rather than paths, because there is no
  cache directory to resolve against.

## Depending on a product

An entry can name a product instead of an identity, which says "I need whatever
provides `ninja`" without naming a spec:

```lua
DEPENDENCIES = { { product = "ninja" }, { product = "cmake" } }
```

See [Declaring Dependencies](../dependencies/declaring.md).

## See also

- [Product Scripts](../environment/product-scripts.md) for how wrappers are written and pruned.
- [`envy product`](../../reference/cli/product.md) for the CLI surface.
- [Build Systems](../../guides/integrations/build-systems.md) for consuming products from CMake, Bazel, and others.
