---
sidebar_position: 4
title: Lua API
---

# Lua API

> **Placeholder content.** Function list verified at skeleton time; each entry
> needs full signature, semantics, and an example.

The `envy` table available in manifests and specs.

## Constants

`envy.PLATFORM` (`"darwin" | "linux" | "windows"`), `envy.ARCH`
(`"arm64" | "x86_64"`), `envy.PLATFORM_ARCH`, `envy.EXE_EXT` (`".exe"` or
`""`). Shell constants: `ENVY_SHELL.BASH`, `ENVY_SHELL.SH`, `ENVY_SHELL.CMD`,
`ENVY_SHELL.POWERSHELL`.

## Processes

- `envy.run(cmd | {cmds}, opts?)` — run command(s); opts: `quiet`, `check`,
  `capture`, `interactive`, `env`. Documented in detail: `interactive` for
  sudo/license prompts; `check = false` to inspect exit codes.

## Fetching (FETCH-phase)

- `envy.fetch(...)` — imperative download.
- `envy.commit_fetch(...)` — commit an imperatively fetched file.
- `envy.verify_hash(...)` — explicit hash check.

## Archives & files

- `envy.extract(archive, dest, { strip })`
- `envy.extract_all(src_dir, dest, { strip, only })`
- `envy.copy`, `envy.move`, `envy.remove`, `envy.exists`, `envy.is_file`,
  `envy.is_dir`
- `envy.path.join`, `.basename`, `.dirname`, `.stem`, `.extension`,
  `.abspath`

## Packages & products

- `envy.product(name)` — resolve a declared product dependency.
- `envy.package(identity)` — resolve a declared package dependency's
  directory.
- `envy.loadenv(module)`, `envy.loadenv_spec(identity, module)` — load
  manifest/spec Lua modules (composition).

## Misc

- `envy.template(str, vars)` — `{{var}}` interpolation for scripts.
- `envy.extend(dst, src)` — append array entries.
- `envy.options(schema)` — validate options from an `OPTIONS` function.
- `envy.debug/info/warn/error/stdout` — logging; `print` routes to the log.

Access rules worth documenting: `envy.product` / `envy.package` only resolve
*declared* dependencies, and only once the dependency is guaranteed ready for
your current phase — undeclared or too-early access is an error, not a race.
