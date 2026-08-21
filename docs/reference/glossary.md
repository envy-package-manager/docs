---
sidebar_position: 8
title: Glossary
---

# Glossary

> **Placeholder content.** Definitions drafted; tighten wording during review.

- **Bundle** — a versioned container distributing many specs behind one pin.
- **Cache** — the per-user, content-addressed store shared by all projects.
- **Depot** — optional remote store of prebuilt package artifacts.
- **Fetch dependency** — a package installed before another package's *spec*
  can even be fetched (`source.dependencies`).
- **Identity** — a spec's namespaced, versioned name (`ns.name@ver`); `@ver`
  versions the spec, not the payload.
- **Manifest** — `envy.lua`; a project's pinned toolchain declaration.
- **Options** — per-entry configuration passed to every verb; part of the
  package's identity.
- **Package** — one installed instance of a spec:
  `(identity, options, platform)`.
- **Product** — a named capability a package exposes (executable path or
  plain value).
- **Product script** — a deployed wrapper in the project bin dir that
  resolves and runs an executable product.
- **Root manifest** — the manifest that governs; `@envy root "false"`
  manifests defer upward.
- **Setup pair** — a named CHECK/INSTALL couple performing host-state work,
  selected explicitly per manifest entry.
- **Spec** — the Lua file describing how to obtain one kind of package.
- **Superproject / subproject** — composing manifests across nested repos.
- **User-managed package** — a package whose state lives on the host, not in
  the cache (Homebrew, apt).
- **Verb** — one of `FETCH`, `STAGE`, `BUILD`, `INSTALL`, `SETUP` — each a
  string, table, function, or omitted.
- **Weak reference** — a dependency query with a fallback, used only when the
  project doesn't already provide a match.
