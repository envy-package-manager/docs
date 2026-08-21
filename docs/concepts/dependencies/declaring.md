---
sidebar_position: 2
title: Declaring Dependencies
---

# Declaring Dependencies

> **Placeholder content.** Outline for review; verify against sources.

Will cover — the four kinds of dependency, with real examples:

- **Strong** — "I need exactly this, from exactly here." Carries its own
  `source` (or `bundle`); envy instantiates it unconditionally:

```lua
DEPENDENCIES = {
  { spec = "fi.brew@r0", source = "fi.brew.lua", setup = { "brew" } },
}
```

  (Note `source` here resolves relative to the *spec file* declaring it.)

- **Product** — "I need something that provides `ninja`; I don't care what":

```lua
DEPENDENCIES = { { product = "ninja" }, { product = "cmake" } }
```

  The project decides which package provides each product; the spec stays
  decoupled.

- **Weak** — "use the project's, or fall back to mine": a query plus a
  `weak = { ... }` fallback spec that's instantiated only if nothing in the
  project already satisfies the query. Lets a spec work standalone without
  forcing its choice on projects that have opinions.

- **Reference-only** — "someone else must be providing this": a bare query
  with no source and no fallback; unresolvable references are errors that
  name the missing thing.

- Dependency entries accept the same shaping fields as manifest entries:
  `options`, `setup` (select the dependency's setup pairs), `needed_by`
  ([next page](./ordering.md)).
- Scoping rules: dependencies of dependencies compose transitively; shared
  packages (same identity + options) are instantiated once.
- Namespace hygiene: shared specs cannot depend on `local.*` project specs.
