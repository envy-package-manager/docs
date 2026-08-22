---
sidebar_position: 4
title: Lua API
---

# Lua API

> **Placeholder content.** Function list verified at skeleton time. Each entry
> needs a full signature, semantics, and an example.

The `envy` table available in manifests and specs.

## Constants

`envy.PLATFORM` is `"darwin"`, `"linux"`, or `"windows"`. `envy.ARCH` is
`"arm64"` or `"x86_64"`. `envy.PLATFORM_ARCH` joins them. `envy.EXE_EXT` is
`".exe"` on Windows and `""` elsewhere. The shell constants are
`ENVY_SHELL.BASH`, `ENVY_SHELL.SH`, `ENVY_SHELL.CMD`, and
`ENVY_SHELL.POWERSHELL`.

## Processes

- `envy.run(script | {lines}, opts?)` runs shell script text. Options:
  `capture`, `check`, `quiet`, `interactive`, `cwd`, `env`, `shell`. Returns
  `{exit_code, stdout, stderr}`. Use `interactive` for sudo and license
  prompts, and `check = false` to inspect exit codes yourself.

## Fetching, during the FETCH phase

- `envy.fetch(source | {sources}, { dest = <dir> })` downloads into a directory
  and returns the basename it wrote.
- `envy.commit_fetch(name | {names} | {filename, sha256})` moves files from
  `tmp_dir` into the durable fetch directory, verifying hashes.
- `envy.verify_hash(path, sha256)` checks a file without committing it.

## Archives and files

- `envy.extract(archive, dest, { strip, only })`
- `envy.extract_all(src_dir, dest, { strip, only })`
- `envy.copy`, `envy.move`, `envy.remove`, `envy.exists`, `envy.is_file`,
  `envy.is_dir`
- `envy.path.join`, `.basename`, `.dirname`, `.stem`, `.extension`, and
  `envy.abspath`

## Packages and products

- `envy.product(name)` resolves a declared product dependency.
- `envy.package(identity)` resolves a declared package dependency's directory.
- `envy.loadenv(module)` loads a sibling Lua file for manifest composition.
- `envy.loadenv_spec(identity, module)` loads a Lua module out of a declared
  dependency, resolving inside the bundle root when that dependency came from a
  bundle. Phase functions only, and subject to `needed_by`. It returns the
  module's sandbox globals rather than its return value. See
  [Shipping an API with your specs](/concepts/dependencies/bundles#shipping-an-api-with-your-specs).

## Other

- `envy.template(str, vars)` interpolates `{{var}}` for scripts.
- `envy.extend(dst, src)` appends array entries.
- `envy.options(schema)` validates options from an `OPTIONS` function.
- `envy.debug`, `.info`, `.warn`, `.error`, and `.stdout` handle output.
  `print` routes to the log.

Access rules worth documenting: `envy.product` and `envy.package` resolve
declared dependencies only, and only once the dependency is ready for your
current phase. Undeclared or too-early access is an error rather than a race.
