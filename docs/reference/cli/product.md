---
sidebar_position: 5
title: envy product
---

# `envy product`

Resolve a named product to its concrete path or value. This is envy's
integration primitive. The deployed wrappers are built on it, build systems
consume it, and CI scripts use it instead of hardcoding cache paths.

Naming one product installs its provider on demand and prints the resolved value
to stdout. Naming none lists every product in the manifest with its provider.
`--run` runs the product instead of printing it.

## Usage

```
envy product [<product>] [--manifest=<path>] [--json]
envy product --run <product> [-- <args>...]
```

## Arguments and flags

| Argument or flag | Meaning |
| --- | --- |
| `product` | Product name, spelled as the spec's `PRODUCTS` table spells it. Omit to list all. |
| `--manifest <path>` | Use this manifest instead of [discovery](/concepts/projects#manifest-discovery). |
| `--json` | Print every product as a JSON object, name to resolved value, on stdout. |
| `--run` | Run the product in the project's activation, passing everything after `--` as arguments. Requires a product name. Excludes `--json`. Requires envy 0.8.0. |

The forms differ in stream and in effect:

| Form | Goes to | Installs |
| --- | --- | --- |
| `envy product cmake` | stdout, one line, safe to capture | yes, the provider and its dependencies |
| `envy product` | stderr, an aligned table | no |
| `envy product --json` | stdout | no, paths are computed rather than created |
| `envy product --run cmake -- --version` | the tool's own streams | yes, then runs the tool |

A cache hit prints nothing to stderr, so `$(envy product cmake)` stays quiet in
a log. An install still reports its row.

`--json` resolves the graph without running it, so it answers "where will
everything be" immediately. The paths it prints do not exist until something
installs them. Run [`sync`](./sync.md) or [`install`](./install.md) first if a
consumer needs the files on disk.

An unknown product name is an error: `'x' has no provider in resolved dependency
graph`.

A [command product](/concepts/specs/products#commands) prints as a command line,
quoted for the platform's shell. `--json` lists it as an array of arguments, or
`null` on a platform its `platforms` leave out:

```shell-session
$ envy product yarn
/Users/you/Library/Caches/envy/packages/acme.node@r0/darwin-arm64-blake3-.../pkg/bin/node /Users/you/Library/Caches/envy/packages/acme.yarn@r0/darwin-arm64-blake3-.../pkg/lib/yarn.cjs
```

## Running a product

`envy product --run <name> -- <args>` is what every deployed
[product script](/concepts/environment/product-scripts) calls. It installs the
provider and its dependencies, then runs the tool with the arguments after `--`:

- **In the project's activation.** The tool gets the bin directory on `PATH`,
  `ENVY_PROJECT_ROOT`, and every installed package's
  [`ENV`](/concepts/environment/package-env). A caller already in this project's
  activation keeps its environment, plus any of the tool's own `ENV` it lacks.
  Any other caller gets a fresh activation for the tool.
- **With stdout to itself.** envy's messages, and anything a spec prints while
  installing, go to stderr.
- **With its own exit code.** On macOS and Linux envy replaces itself with the
  tool. On Windows it waits and returns the tool's code. A `.bat` or `.cmd`
  program runs through `cmd.exe`.
- **On host packages only**, as `install` resolves them.

A command product runs its argv with your arguments appended. A program given as
a relative path, such as a user-managed value, is resolved from the project
root. A bare name is searched on `PATH`, skipping the product's own wrapper.

## Examples

### To get the absolute path of a tool

```bash
envy product cmake
# /Users/you/Library/Caches/envy/packages/envy.cmake@r0/darwin-arm64-blake3-49a9b2620de8c380/pkg/CMake.app/Contents/bin/cmake
```

The package installs first if it is not cached, so the path always points at
something real.

### To point a build system at project tools

```bash
CC="$(envy product arm-none-eabi-gcc)"
CMAKE="$(envy product cmake)"
"$CMAKE" -DCMAKE_C_COMPILER="$CC" -S . -B build
```

```powershell
$env:CMAKE = (bin\envy.bat product cmake)
& $env:CMAKE -S . -B build
```

No `PATH` manipulation and no wrapper indirection. The resolved path is native
to the platform you ask on. A Windows answer ends in `.exe`, because the spec
built its product value with `envy.EXE_EXT`.

### To locate a header-only library, which has no executable

```bash
envy product doctest_cpp_h    # .../pkg/doctest.h
envy product doctest_cpp_dir  # .../pkg
```

Products with `script = false` never get a wrapper, so `envy product` is the
only way to reach them. Both forms are common: the include directory for a
compiler flag, and the file itself for a dependency edge.

### To see everything the project offers

```bash
envy product
# cmake          bin/cmake          envy.cmake@r0{["version"]="4.2.3"}
# ctest          bin/ctest          envy.cmake@r0{["version"]="4.2.3"}
# doctest_cpp_h  doctest.h          envy.doctest-cpp@r0
# python3        bin/python3        envy.python@r1{["version"]="3.13.14"}
```

Product name, the spec-relative value, and the canonical key of the providing
package. User-managed packages are marked `(user-managed)`, and their value is
whatever the spec resolved on this machine rather than a cache path.

### To feed a whole toolchain into a generator

```bash
envy product --json > build/envy-products.json
```

One object, one process, no per-tool invocation. This is the recommended shape
for CMake, Bazel, and Meson glue. See
[Build Systems](/guides/integrations/build-systems).

### To check what a wrapper will run

```bash
tail -1 bin/cmake    # exec "$ENVY_SCRIPT_DIR/envy" product --run "cmake" -- "$@"
envy product cmake   # the path that runs
```

## See also

- [Products](/concepts/specs/products) for declaring them in a spec.
- [`envy package`](./package.md) for a package's whole tree instead of one entry point.
- [Build Systems](/guides/integrations/build-systems)
