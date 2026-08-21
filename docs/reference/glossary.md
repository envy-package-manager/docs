---
sidebar_position: 8
title: Glossary
---

# Glossary

> **Placeholder content.** Definitions drafted. Tighten wording during review.

- **Bundle**: a versioned container distributing many specs behind one pin.
- **Cache**: the per-user, content-addressed store shared by all projects.
- **Depot**: an optional remote store of prebuilt package artifacts.
- **Fetch dependency**: a package installed before another package's *spec* can
  be fetched, declared in `source.dependencies`.
- **Identity**: a spec's namespaced, versioned name, `ns.name@rev`. The revision
  versions the spec, not the payload.
- **Manifest**: `envy.lua`, a project's pinned toolchain declaration.
- **Options**: per-entry configuration passed to every verb. Part of the
  package's identity.
- **Package**: one installed instance of a spec, keyed by `(identity, options,
  platform)`.
- **Product**: a named capability a package exposes, either an executable path
  or a plain value.
- **Product script**: a deployed wrapper in the project bin dir that resolves
  and runs an executable product.
- **Root manifest**: the manifest that governs. Manifests with
  `@envy root "false"` defer upward.
- **Setup pair**: a named CHECK/INSTALL couple that performs host-state work,
  selected per manifest entry.
- **Spec**: the Lua file describing how to obtain one kind of package.
- **Superproject and subproject**: manifests composing across nested
  directories.
- **User-managed package**: a package whose state lives on the host rather than
  in the cache, such as Homebrew or apt.
- **Verb**: one of `FETCH`, `STAGE`, `BUILD`, `INSTALL`, `SETUP`. Each is a
  string, a table, a function, or omitted.
- **Weak reference**: a dependency query with a fallback, used only when the
  project does not already provide a match.
