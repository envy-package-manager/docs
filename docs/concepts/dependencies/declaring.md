---
sidebar_position: 2
title: Declaring Dependencies
---

# Declaring Dependencies

A spec declares dependencies in `DEPENDENCIES`, an array of entries. Manifest
[package entries](../projects#package-entries) accept the same dependency-shaped
fields, so the two sides look alike.

There are four kinds, and the difference between them is who provides the thing
and how hard the spec insists.

## Strong

"I need exactly this, from exactly here." The entry carries its own `source` or
`bundle`, and envy instantiates it unconditionally.

```lua
DEPENDENCIES = {
  { spec = "acme.brew@r0", source = "acme.brew.lua", setup = { "brew" } },
}
```

`source` resolves relative to the spec file that declares it, not to the
manifest or the working directory. A strong dependency is the default choice: it
is unambiguous and it cannot fail to resolve.

## Product

"I need something that provides `ninja`, and I do not care what."

```lua
DEPENDENCIES = { { product = "ninja" }, { product = "cmake" } }
```

The project decides which package provides each product, so the spec stays
decoupled from that choice. This is the form to reach for when a spec needs a
tool rather than a specific package.

A product entry can also carry a `spec` and `source`, which makes it a strong
product dependency: the provider is fixed, and the product name is still how the
spec refers to it.

```lua
DEPENDENCIES = {
  { spec = "tools.jfrog-cli@r1", product = "jf", source = "tools.jfrog-cli.lua" },
}
```

Both forms make `envy.product("ninja")` legal inside the verbs of this spec. See
[Products](../specs/products.md).

## Weak

"Use the project's, or fall back to mine." A query plus a `weak` fallback, where
the fallback is instantiated only if nothing in the project already satisfies the
query:

```lua
DEPENDENCIES = {
  { spec = "acme.python", weak = { spec = "acme.python@r1", source = "python.lua" } },
}
```

Note the query is deliberately looser than the fallback. `acme.python` matches
any revision, so a project that already pins `acme.python@r2` satisfies it and
the fallback is never built.

This lets a spec work standalone without forcing its choice on a project that has
opinions. It is the polite form, and the right one for a spec you publish.

## Reference-only

"Someone else must be providing this." A bare query, with no source and no
fallback:

```lua
DEPENDENCIES = {
  { spec = "acme.python" },
}
```

If nothing matches, envy reports `Reference 'acme.python' in spec '<yours>' was
not found`. Use it to assert a project-level requirement that this spec cannot
sensibly satisfy itself, such as a toolchain the project must choose.

## Shaping fields

Every entry accepts the same shaping fields a manifest entry does:

| Field | Meaning |
| --- | --- |
| `options` | The options the dependency is built with. Part of its identity, so two option sets are two packages. |
| `setup` | Which of the dependency's [SETUP](../specs/setup.md) pairs to select. Selections union across everyone who asks. |
| `needed_by` | How early the dependency must be ready. See [Phase Ordering](./ordering.md). Defaults to `build`. |
| `weak` | The fallback described above. Mutually exclusive with `source`. |
| `bundle` | Take the spec from a bundle instead of a source. Resolved against the declaring file's own `BUNDLES`. |

The `setup` field is how a spec insists on host state it needs. This entry says
"install Homebrew before you install me", without the project having to know:

```lua
DEPENDENCIES = {
  { spec = "acme.brew@r0", source = "acme.brew.lua", setup = { "brew" } },
}
```

## Scoping and hygiene

- **Dependencies compose transitively.** Your dependency's dependencies are in
  the graph too, and you do not declare them.
- **Identical packages are shared.** The same `(identity, options, platform)`
  anywhere in the graph is one package, whether it arrived from a manifest entry
  or from three specs that each wanted it.
- **`bundle` aliases are file-scoped.** A spec's `DEPENDENCIES` resolves
  `bundle = "acme"` against that spec's own `BUNDLES` table, not the manifest's.
- **Published specs cannot reach into projects.** A spec outside the `local.*`
  namespace may not depend on a `local.*` spec. envy rejects it with
  `non-local spec '<a>' cannot depend on local spec '<b>'`.

## See also

- [Phase Ordering](./ordering.md) for `needed_by`.
- [Resolution](./resolution.md) for what happens when a weak query matches zero or many.
- [Fetch Dependencies](./fetch-dependencies.md) for dependencies needed before a spec can be fetched.
