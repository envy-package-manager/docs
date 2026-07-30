---
sidebar_position: 3
title: Concepts
---

# Concepts

> **Placeholder content.** Verify against the envy sources before publishing.

**Manifest** — `envy.lua`, checked into the project. Exports a `PACKAGES` table
and carries `-- @envy <key> "<value>"` directives in its first 20 lines, read by
both the bootstrap scripts and the binary. Single source of truth for the
toolchain.

**Spec** — a Lua file (or a directory containing `recipe.lua`) that declares an
`IDENTITY` plus the verbs describing how to acquire, build, and install one
package.

**Identity** — a namespaced, versioned spec name like `arm.gcc@v2`. The `@`
denotes the *spec* version, not the asset version. `local.*` is reserved for
project-local specs.

**Package** — one concrete installation of a spec, keyed by
`(identity, options, platform)`. Cache-managed packages store artifacts in the
cache; specs marked `USER_MANAGED = true` mutate host state instead.

**Options** — the per-entry `options = { ... }` table in the manifest. Passed to
every verb and hashed into the cache key, so `version = "3.13.11"` and
`"3.14.2"` coexist as separate packages.

**Product** — a named entry point a spec advertises via
`PRODUCTS = { cmake = "bin/cmake" }`. Consumers ask for the *capability*, not the
identity: `envy product cmake` on the CLI, `envy.product(name)` in Lua. `envy
sync` deploys product scripts into the manifest's `@envy bin` directory.

**Bundle** — related specs distributed together behind one `envy-bundle.lua`
(`BUNDLE = "acme.toolchain@v1"`, `SPECS = { ... }`). A manifest entry references
it with `bundle = "..."` in place of `source = "..."`.

**Cache** — the user-wide, content-addressed store holding envy's own versioned
binaries, specs, bundles, locks, and installed package trees under
`identity/platform-arch-blake3-hash`. Shared across every project on the
machine, and safe to delete.

**Depot** — optional. `PACKAGE_DEPOTS` lists sources of prebuilt `.tar.zst`
artifacts consulted before building; a hit skips fetch and build entirely.
`--ignore-depot` or `ENVY_IGNORE_DEPOT` forces a source build.
