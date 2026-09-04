---
sidebar_position: 2
title: Build Systems
---

# Build Systems

envy resolves tools. Your build system consumes paths. The seam between them is
one command.

## The interface

[`envy product`](../../reference/cli/product.md) is the whole integration
surface. It has three forms, and the differences matter when you wire it into a
generator:

| Form | Output | Installs |
| --- | --- | --- |
| `envy product cmake` | one absolute path on stdout | yes, the provider and its dependencies |
| `envy product` | an aligned table on stderr | no |
| `envy product --json` | every product as one JSON object on stdout | no, paths are computed rather than created |

The table form is for humans:

```shell-session
$ ./bin/envy product
cmake            CMake.app/Contents/bin/cmake  envy.cmake@r0{version="4.4.0"}
cpack            CMake.app/Contents/bin/cpack  envy.cmake@r0{version="4.4.0"}
ctest            CMake.app/Contents/bin/ctest  envy.cmake@r0{version="4.4.0"}
doctest_cpp_dir  .                             envy.doctest-cpp@r0{version="2.5.3"}
doctest_cpp_h    doctest.h                     envy.doctest-cpp@r0{version="2.5.3"}
ninja            ninja                         envy.ninja@r0{version="1.13.2"}
```

`--json` is for generators. One process gives you every path:

```shell-session
$ ./bin/envy -q product --json
{
  "cmake": "/Users/you/Library/Caches/envy/packages/envy.cmake@r0/darwin-arm64-blake3-49a9b2620de8c380/pkg/CMake.app/Contents/bin/cmake",
  "cpack": "...",
  "ctest": "...",
  "doctest_cpp_dir": "/Users/you/Library/Caches/envy/packages/envy.doctest-cpp@r0/darwin-arm64-blake3-1a46f3b186252763/pkg/.",
  "doctest_cpp_h": "/Users/you/Library/Caches/envy/packages/envy.doctest-cpp@r0/darwin-arm64-blake3-1a46f3b186252763/pkg/doctest.h",
  "ninja": "/Users/you/Library/Caches/envy/packages/envy.ninja@r0/darwin-arm64-blake3-846f6979e3402fea/pkg/ninja"
}
```

Two things to know about that output:

- **`-q` matters.** Progress lines like `[envy.cmake@r0] cache hit` go to stderr,
  so JSON on stdout parses either way. `-q` keeps them out of your build log.
- **`--json` does not install.** It computes where each product will be from the
  resolved graph. Run [`sync`](../../reference/cli/sync.md) before a build that
  needs the files, which the [wrapper-script pattern](#one-wrapper-instead-of-two-steps)
  below does for you.

## CMake

Read the products at configure time and hand the paths to targets:

```cmake title="CMakeLists.txt"
cmake_minimum_required(VERSION 3.19)
project(demo CXX)

set(ENVY "${CMAKE_SOURCE_DIR}/bin/envy")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
             "${CMAKE_SOURCE_DIR}/envy.lua")

execute_process(
  COMMAND "${ENVY}" -q product --json
  OUTPUT_VARIABLE envy_products
  OUTPUT_STRIP_TRAILING_WHITESPACE
  RESULT_VARIABLE envy_result)
if(NOT envy_result EQUAL 0)
  message(FATAL_ERROR "envy product --json failed: ${envy_result}")
endif()

string(JSON doctest_dir GET "${envy_products}" doctest_cpp_dir)

add_executable(tests tests.cpp)
target_include_directories(tests PRIVATE "${doctest_dir}")
```

`string(JSON)` needs CMake 3.19. The `CMAKE_CONFIGURE_DEPENDS` line keeps this
correct over time. Bump a version in `envy.lua` and CMake reconfigures, so the
next build uses the new paths.

Configuring and building with the project's own CMake and Ninja:

```shell-session
$ ./bin/cmake -S . -B out -G Ninja -DCMAKE_MAKE_PROGRAM="$(./bin/envy -q product ninja)"
-- The CXX compiler identification is AppleClang 21.0.0.21000101
-- Configuring done (0.9s)
-- Generating done (0.0s)
-- Build files have been written to: /path/to/project/out
$ ./bin/ninja -C out
[2/2] Linking CXX executable tests
```

On Windows the same commands are `bin\cmake.bat` and `bin\ninja.bat`.

### Products that are not programs

`doctest_cpp_dir` above is a directory, not an executable. Its spec declares
`script = false`, so nothing lands in `bin/` and the only way to reach it is
`envy product`. Header-only libraries, include directories, sysroots, and linker
scripts all work this way. See [Products](/concepts/specs/products).

## GN

GN can run a script at generation time and parse its output, which is the same
`--json` ingestion with one wrinkle: GN identifiers cannot contain `-` or `+`, so
sanitize the keys.

```python title="gntools/envy_tools.py"
import argparse, json, pathlib, re, subprocess, sys

parser = argparse.ArgumentParser()
parser.add_argument("--envy-bin", type=pathlib.Path, required=True)
envy = str(parser.parse_args().envy_bin.resolve())

tools = json.loads(
    subprocess.run([envy, "-q", "product", "--json"],
                   capture_output=True, text=True, check=True).stdout)

sanitize = re.compile(r"[^a-zA-Z0-9_]").sub
collapse = re.compile(r"_+").sub
json.dump({collapse("_", sanitize("_", k)): v for k, v in tools.items()},
          sys.stdout, indent=2)
```

```python title="build/BUILDCONFIG.gn"
envy_inputs = [ "//envy.lua" ]

declare_args() {
  envy_tools = exec_script("//gntools/envy_tools.py",
                           [ "--envy-bin", rebase_path("//bin/envy${script_ext}") ],
                           "json",
                           envy_inputs)
}
```

Passing `envy_inputs` as the fourth argument to `exec_script` is the important
part. It tells GN that the script's output depends on those files, so editing a
manifest re-runs generation instead of leaving a stale toolchain wired in.

Then use the paths, and list the manifests as inputs on any action that runs an
envy-provided tool:

```python title="gntools/protoc.gni"
template("protoc") {
  action(target_name) {
    script = "//gntools/run.py"
    inputs = envy_inputs + invoker.sources
    args = [ envy_tools.protoc, "--cpp_out", rebase_path(target_gen_dir) ]
    # ...
  }
}
```

Without `inputs = envy_inputs`, a protobuf version bump changes the compiler and
nothing rebuilds.

## Make

```makefile title="Makefile"
ENVY := ./bin/envy
CMAKE := $(shell $(ENVY) -q product cmake)
NINJA := $(shell $(ENVY) -q product ninja)

out/build.ninja: CMakeLists.txt envy.lua
	$(CMAKE) -S . -B out -G Ninja -DCMAKE_MAKE_PROGRAM=$(NINJA)

.PHONY: build
build: out/build.ninja
	$(NINJA) -C out
```

`:=` runs each `envy product` once when the makefile is read, not once per use.
Listing `envy.lua` as a prerequisite reconfigures after a version bump. For more
than a handful of tools, generate an include file from `--json` instead of
running one process per variable.

## One wrapper instead of two steps

The patterns above assume packages are installed. Rather than asking everyone to
remember that, put it in a committed wrapper next to the envy bootstrap script:

```bash title="bin/build"
#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"$root/bin/envy" install
exec "$(./bin/envy -q product ninja)" -C "$root/out" "$@"
```

`install` rather than `sync`: this wrapper reaches its tools through
`envy product`, so it needs the packages and not the bin directory, and a build
that rewrites committed files would show up in everyone's `git status`. It is
fast when everything is cached, so paying it on every build is cheaper than
debugging a stale one. Ship a `bin/build.bat` alongside it for Windows. envy
will not touch either file, because it only manages scripts carrying its own
marker. See [Product Scripts](/concepts/environment/product-scripts#taking-ownership-of-a-name).

## On Windows

The bootstrap script has a different name, so anything that spells the path needs
a variable rather than a literal:

```cmake title="CMakeLists.txt"
if(WIN32)
  set(ENVY "${CMAKE_SOURCE_DIR}/bin/envy.bat")
else()
  set(ENVY "${CMAKE_SOURCE_DIR}/bin/envy")
endif()
```

```python title="build/BUILDCONFIG.gn"
script_ext = ""
if (host_os == "win") {
  script_ext = ".bat"
}

envy_tools = exec_script("//gntools/envy_tools.py",
                         [ "--envy-bin", rebase_path("//bin/envy${script_ext}") ],
                         "json",
                         envy_inputs)
```

```makefile title="Makefile"
ENVY := ./bin/envy
ifeq ($(OS),Windows_NT)
ENVY := bin/envy.bat
endif
```

Everything downstream is unchanged. `envy product --json` prints native paths, so
the values you get on Windows contain backslashes and are ready to hand to a
compiler. In CMake they work as-is. In a generated file that also treats `\` as an
escape, convert once at ingestion time:

```cmake
string(REPLACE "\\" "/" cmake_path "${raw_path}")
```

If you ship the wrapper-script pattern above, ship a `.bat` twin next to it:

```batch title="bin\build.bat"
@echo off
call "%~dp0envy.bat" sync || exit /b %ERRORLEVEL%
for /f "delims=" %%i in ('call "%~dp0envy.bat" -q product ninja') do set "NINJA=%%i"
call "%NINJA%" -C "%~dp0..\out" %*
exit /b %ERRORLEVEL%
```

envy leaves both alone, since neither carries the `envy-managed` marker.

## Rules

- **Never hardcode a cache path.** They contain a hash of the identity and
  options, so they move whenever a version or option changes. Always go through
  `envy product` or [`envy package`](../../reference/cli/package.md).
- **Declare the manifests as inputs.** Whatever your build system calls them,
  `CMAKE_CONFIGURE_DEPENDS`, `exec_script` inputs, or a prerequisite, a manifest
  edit has to invalidate the resolved paths.
- **Resolve at configure time, not per compile.** One `--json` call beats one
  `envy product` per target.

## See also

- [`envy product`](../../reference/cli/product.md) and [`envy package`](../../reference/cli/package.md)
- [Product Scripts](/concepts/environment/product-scripts) for the `bin/` wrappers
- [`envy run`](../../reference/cli/run.md) for running a tool with no wrapper deployed
