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

:::warning[A product is not necessarily a script]
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
}
```

| Field | Meaning |
| --- | --- |
| `value` | A path relative to the package directory, or a raw value for [user-managed](./user-managed.md) packages. Required unless the product is a [command](#commands). |
| `command` | An argv instead of a path. See [Commands](#commands). Requires envy 0.8.0. |
| `script` | Deploy a wrapper script for it. Defaults to `true`. |
| `platforms` | Which wrapper flavors to deploy, for example `{ "windows" }` for a `.bat` only. See [Platforms](./platforms.md#how-1-2-and-4-combine). |

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

### Commands

From envy 0.8.0, a product can be a command line instead of a path. Use it for
a script that runs under another product's interpreter, or for a tool that
always needs fixed flags. Each `{{name}}` in the list is another product:

```lua
DEPENDENCIES = { { product = "node" }, { product = "java" } }

PRODUCTS = {
  ["yarn.cjs"]   = { value = "lib/yarn.cjs", script = false },
  yarn           = { command = { "{{node}}", "{{yarn.cjs}}" } },
  ["gradle.jar"] = { value = "lib/gradle.jar", script = false },
  gradle         = { command = { "{{java}}", "-Xmx2g", "-jar", "{{gradle.jar}}" } },
}
```

`./bin/yarn install` runs `node .../lib/yarn.cjs install`. envy fills in the
names each time the command runs, so nothing is written into the package.

- A command takes `command` in place of `value`. `script` and `platforms` work
  the same as for a path.
- Every `{{name}}` must be a product of this package or of a package it depends
  on, directly or not. envy checks this when it resolves the graph, so a typo
  fails early:

  ```text
  error: Product 'yarn' in spec 'acme.yarn@r0' runs '{{nod}}', but nothing in its dependency closure provides 'nod'
  ```

- A path product can sit inside an element, as in `--node={{node}}`. A command
  product must fill a whole element, and its arguments are spliced in. A command
  that reaches itself is an error.
- A command's own files are path products of its package, like `yarn.cjs`
  above. Mark them `script = false` unless they run on their own.
- The first element is the program. An absolute path runs as is. A bare name is
  searched on `PATH`.

`envy product yarn` prints the command line, quoted for the platform's shell.
`envy product --json` lists it as an array. A spec runs it with
[`envy.product_command`](/reference/lua-api#envyproduct_commandname-shell),
because `envy.product` only returns paths.

## The three consumption surfaces

| Surface | How | Who uses it |
| --- | --- | --- |
| Deployed wrapper | `cmake` | humans, Makefiles, anything expecting a normal executable |
| CLI | [`envy product cmake`](../../reference/cli/product.md), `envy product --json` | build-system glue, scripts, `envy run` users |
| Lua | `envy.product("ninja")`, `envy.product_command("yarn")` | other specs, during `BUILD` and `INSTALL` |

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
wrapper works on a machine that has never synced. The wrapper calls
`envy product --run`, and the package installs before the tool runs.

## Resolution rules

- Product names are global within a project. `cmake` means one thing.
- Two packages providing the same product name is an error. There are no
  priority rules and no tie-breaks. Options exist so that a spec can decline to
  claim a generic name, as in the `provide_python3` example above.
- A product's `platforms` only chooses its wrapper flavors. `envy product`
  resolves it on any machine that installs the package. To offer a product on
  some machines only, compute `PRODUCTS` from `envy.PLATFORM`.
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
