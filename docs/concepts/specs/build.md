---
sidebar_position: 5
title: BUILD
---

# BUILD

Transform the staged tree: compile, configure, generate. Prebuilt-binary specs
skip it, which is most specs.

Scripts run with the working directory set to the staging tree, `work/stage/`,
where the unpacked sources are.

## The three shapes

| Shape | Meaning |
| --- | --- |
| omitted | No build step. |
| string | A shell script. |
| function `BUILD(install_dir, stage_dir, fetch_dir, tmp_dir, opts)` | Programmatic build. If it returns a string, that string runs as a shell script. |

There is no table form. A build is either a script or code that produces one.

### string

```lua
BUILD = "./configure && make -j"
```

Enough when nothing in the command depends on options, platform, or paths.

### function returning a script

The common middle ground: compute the script and return it. `envy.template`
keeps it readable and raises on a missing placeholder value instead of
substituting an empty string.

```lua
BUILD = function(install_dir, stage_dir, fetch_dir, tmp_dir, opts)
  return envy.template([[
    ./configure --prefix={{prefix}}
    make -j
  ]], { prefix = install_dir })
end
```

`install_dir` matters here. An autotools package has to be configured with its
final location, because that path is baked into the binaries. A package
configured for the staging directory and then moved is broken.

### function using dependency products

This is the standard way to put another package's tool into a script. Declare the
dependency, then let `envy.product(name)` supply the absolute path as a template
value:

```lua
DEPENDENCIES = { { product = "ninja" }, { product = "cmake" } }

BUILD = function(install_dir, stage_dir, fetch_dir, tmp_dir, opts)
  return envy.template([[
mkdir build
cd build
{{cmake}} -G Ninja ../llvm -DCMAKE_MAKE_PROGRAM={{ninja}} -DCMAKE_BUILD_TYPE=Release
{{ninja}} {{targets}}
]], {
    cmake = envy.product("cmake"),
    ninja = envy.product("ninja"),
    targets = table.concat(opts.tools, " "),
  })
end
```

`envy.product` looks the name up in this package's resolved product dependencies
and returns the provider's absolute path. Nothing in the script mentions a cache
path. Two rules govern the call:

- The name has to be **declared**. An undeclared name is an error rather than a
  lookup, because the dependency edge is what guarantees cmake exists before
  this build runs.
- The dependency's `needed_by` has to be at or before the phase you call from.
  The default is `build`, which is why the call above works in `BUILD`. To
  resolve a product inside `FETCH`, declare it
  `{ product = "jf", needed_by = "fetch" }`. Without that, envy reports
  `product 'jf' needed_by 'build' but accessed during 'fetch'`.

`envy.package(identity)` follows the same rules and returns the package
directory, for a dependency whose author never named a product.

### function doing the work directly

Return nothing and drive the build with `envy.run`. Prefer this when you need
output, exit codes, or conditional logic partway through:

```lua
BUILD = function(install_dir, stage_dir, fetch_dir, tmp_dir, opts)
  local jobs = envy.run("getconf _NPROCESSORS_ONLN", { capture = true }).stdout
  envy.run("make -j" .. jobs:gsub("%s+", ""))
end
```

See [Shells & Scripts](./shells.md) for `envy.run`'s options and for choosing
the interpreter that runs your strings.

### defined conditionally

Whether a spec builds at all can be a platform decision: build from source
where no binaries are published, and use prebuilt archives elsewhere.

```lua
if envy.PLATFORM == "darwin" then
  BUILD = function(install_dir, stage_dir, fetch_dir, tmp_dir, opts)
    return envy.template([[
      ./configure --prefix={{prefix}}
      make -j
    ]], { prefix = install_dir })
  end
end
```

A function `BUILD` also changes where staging writes. Extraction goes to
`work/stage/` rather than straight into `pkg/`, because a build needs a scratch
tree. See [The Package Lifecycle](./lifecycle.md#where-extraction-lands).

## Failure

A non-zero exit fails the verb, which fails the package. envy leaves the entry
unmarked and removes its `pkg/` and `work/` trees, so the next run starts the
build over. `fetch/` survives, so nothing downloads twice.

## See also

- [STAGE](./stage.md) for the tree `BUILD` starts from.
- [INSTALL](./install.md) for turning the build result into the package.
- [Declaring Dependencies](../dependencies/declaring.md) for making `envy.product` legal.
