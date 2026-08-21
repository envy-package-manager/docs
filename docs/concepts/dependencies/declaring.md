---
sidebar_position: 2
title: Declaring Dependencies
---

# Declaring Dependencies

> **Placeholder content.** Outline for review. Verify against sources.

Will cover the four kinds of dependency, with examples.

**Strong**: I need exactly this, from exactly here. It carries its own `source`
or `bundle`, and envy instantiates it unconditionally.

```lua
DEPENDENCIES = {
  { spec = "acme.brew@r0", source = "acme.brew.lua", setup = { "brew" } },
}
```

`source` here resolves relative to the spec file that declares it.

**Product**: I need something that provides `ninja`, and I do not care what.

```lua
DEPENDENCIES = { { product = "ninja" }, { product = "cmake" } }
```

The project decides which package provides each product, so the spec stays
decoupled.

**Weak**: use the project's, or fall back to mine. A query plus a
`weak = { ... }` fallback spec. The fallback is instantiated only if nothing in
the project already satisfies the query. A spec can therefore work standalone
without forcing its choice on projects that have opinions.

**Reference-only**: someone else must be providing this. A bare query with no
source and no fallback. An unresolvable reference is an error that names the
missing thing.

Also to cover:

- Dependency entries accept the same shaping fields as manifest entries:
  `options`, `setup` to select the dependency's setup pairs, and `needed_by`,
  covered on the [next page](./ordering.md).
- Scoping. Dependencies of dependencies compose transitively, and shared
  packages with the same identity and options are instantiated once.
- Namespace hygiene. Shared specs cannot depend on `local.*` project specs.
