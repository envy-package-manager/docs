---
sidebar_position: 10
title: Products
---

# Products

> **Placeholder content.** Outline for review; verify against sources.

A product is a *named capability* a package offers. Consumers ask for the
name — `cmake`, `doctest_cpp_h` — and envy answers with a concrete path or
value. Nobody hardcodes cache paths.

Will cover:

- Declaring products:

```lua
-- executables: string shorthand
PRODUCTS = { gn = "gn" .. envy.EXE_EXT }

-- values and files that are NOT executables: script = false
PRODUCTS = {
  doctest_cpp_dir = { value = ".", script = false },
  doctest_cpp_h = { value = "doctest.h", script = false },
}

-- computed from options
PRODUCTS = function(opts) ... end
```

- :::caution A product is not necessarily a script
  A common misreading: "products are the things `envy sync` puts in the bin
  dir." Executable products *do* get wrapper scripts deployed — but a product
  can be any named value: a header path for a header-only C++ library, a
  library file, a data directory. `script = false` products deploy nothing
  and are consumed via `envy product <name>` (CLI / build systems) or
  `envy.product(name)` (other specs). Header-only packages need no bin-dir
  tricks.
  :::
- The three consumption surfaces: deployed wrappers (`./bin/cmake`), the CLI
  (`envy product doctest_cpp_h`, `--json` for all), and Lua
  (`envy.product("ninja")` from dependent specs).
- Resolution rules: product names are global within a project; two providers
  of the same name is an error (no priority tie-breaks).
- Per-product `platforms`; products from user-managed packages (raw values,
  e.g. an apt package name).
- Depending on a product instead of an identity —
  [product dependencies](/concepts/dependencies/declaring).
