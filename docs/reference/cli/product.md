---
sidebar_position: 4
title: envy product
---

# `envy product`

Resolve a named product to its concrete path or value. This is envy's
integration primitive. The deployed wrappers are built on it, build systems
consume it, and CI scripts use it instead of hardcoding cache paths.

Naming one product installs its provider on demand and prints the resolved value
to stdout. Naming none lists every product in the manifest with its provider.

## Usage

```
envy product [<product>] [--manifest=<path>] [--json]
```

## Arguments and flags

| Argument or flag | Meaning |
| --- | --- |
| `product` | Product name, spelled as the spec's `PRODUCTS` table spells it. Omit to list all. |
| `--manifest <path>` | Use this manifest instead of [discovery](/concepts/projects#manifest-discovery). |
| `--json` | Print every product as a JSON object, name to resolved value, on stdout. |

The three forms differ in stream and in effect:

| Form | Goes to | Installs |
| --- | --- | --- |
| `envy product cmake` | stdout, one line, safe to capture | yes, the provider and its dependencies |
| `envy product` | stderr, an aligned table | no |
| `envy product --json` | stdout | no, paths are computed rather than created |

`--json` resolves the graph without running it, so it answers "where will
everything be" immediately. The paths it prints do not exist until something
installs them. Run [`sync`](./sync.md) or [`install`](./install.md) first if a
consumer needs the files on disk.

An unknown product name is an error: `'x' has no provider in resolved dependency
graph`.

## Examples

### To get the absolute path of a tool

```bash
./bin/envy product cmake
# /Users/you/Library/Caches/envy/packages/envy.cmake@r0/darwin-arm64-blake3-49a9b2620de8c380/pkg/bin/cmake
```

The package installs first if it is not cached, so the path always points at
something real.

### To point a build system at project tools

```bash
CC="$(./bin/envy product arm-none-eabi-gcc)"
CMAKE="$(./bin/envy product cmake)"
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
./bin/envy product doctest_cpp_h    # .../pkg/doctest.h
./bin/envy product doctest_cpp_dir  # .../pkg
```

Products with `script = false` never get a wrapper, so `envy product` is the
only way to reach them. Both forms are common: the include directory for a
compiler flag, and the file itself for a dependency edge.

### To see everything the project offers

```bash
./bin/envy product
# cmake          bin/cmake          envy.cmake@r0{version="4.2.3"}
# ctest          bin/ctest          envy.cmake@r0{version="4.2.3"}
# doctest_cpp_h  doctest.h          envy.doctest-cpp@r0
# python3        bin/python3        envy.python@r1{version="3.13.14"}
```

Product name, the spec-relative value, and the canonical key of the providing
package. User-managed packages are marked `(user-managed)`, and their value is
whatever the spec resolved on this machine rather than a cache path.

### To feed a whole toolchain into a generator

```bash
./bin/envy product --json > build/envy-products.json
```

One object, one process, no per-tool invocation. This is the recommended shape
for CMake, Bazel, and Meson glue. See
[Build Systems](/guides/integrations/build-systems).

### To check what a wrapper will run

```bash
cat bin/cmake                       # exec "$("$SCRIPT_DIR/envy" product "cmake")" "$@"
./bin/envy product cmake            # the same path the wrapper resolves
```

## See also

- [Products](/concepts/specs/products) for declaring them in a spec.
- [`envy package`](./package.md) for a package's whole tree instead of one entry point.
- [Build Systems](/guides/integrations/build-systems)
