---
sidebar_position: 3
title: Writing a Spec
---

# Writing a Spec

> **Placeholder content.** Outline for review; verify against sources.

Tutorial: author a spec that fetches, verifies, and installs a prebuilt tool,
then grow it into something smarter. (The [Concepts → Specs](/concepts/specs)
section is the reference companion to this guide.)

Will cover:

- Minimal viable spec: `IDENTITY` plus a string `FETCH` — done. envy's
  defaults extract and install it.
- Adding integrity: per-platform download tables with `sha256` fingerprints.
- Adding `OPTIONS` so consumers can pick versions.
- Advertising `PRODUCTS` so consumers get wrapper scripts and
  `envy product` resolution.
- Platform-dependent behavior with `envy.PLATFORM` / `envy.ARCH`.
- Building from source: a `BUILD` verb returning a shell script via
  `envy.template`.
- Iterating locally with a `local.*` spec, then promoting it to a shared
  location or bundle ([Creating a Bundle](./creating-bundles.md)).
- Worked example (draft below, carried over from the earlier skeleton):

```lua title="local.cmake@r0.lua"
-- @envy schema "1"
IDENTITY = "local.cmake@r0"
EXPORTABLE = true

OPTIONS = { version = { required = true } }

local sha256_fingerprints = {
  ["4.2.3-macos-universal"] =
  "c2302d3e9c48daabee5ea7c4db4b2b93b989bcc89dae8b760880e00120641b5b",
  ["4.2.3-linux-x86_64"] =
  "5bb505d5e0cca0480a330f7f27ccf52c2b8b5214c5bba97df08899f5ef650c23",
  ["4.2.3-windows-x86_64"] =
  "eb4ebf5155dbb05436d675706b2a08189430df58904257ae5e91bcba4c86933c",
}

FETCH = function(tmp_dir, opts)
  local platform_arch = ({
    darwin = "macos-universal",
    linux = "linux-" .. envy.ARCH,
    windows = "windows-" .. envy.ARCH,
  })[envy.PLATFORM]
  local name = "cmake-" .. opts.version .. "-" .. platform_arch
  return {
    source = "https://github.com/Kitware/CMake/releases/download/v"
      .. opts.version .. "/" .. name .. (envy.PLATFORM == "windows" and ".zip" or ".tar.gz"),
    sha256 = sha256_fingerprints[opts.version .. "-" .. platform_arch],
  }
end

STAGE = { strip = 1 }

PRODUCTS = {
  cmake = envy.PLATFORM == "darwin" and "CMake.app/Contents/bin/cmake"
    or ("bin/cmake" .. envy.EXE_EXT),
}
```
