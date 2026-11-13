---
sidebar_position: 8
title: Glossary
---

# Glossary

- **Activation**: applying a project to a shell: its bin directory on `PATH`,
  `ENVY_PROJECT_ROOT`, and every installed package's `ENV`. Done by the shell
  hook or `envy activate`, undone by `envy deactivate`.
- **Bundle**: a versioned container distributing many specs behind one pin.
- **Cache**: the per-user, content-addressed store shared by all projects.
- **Depot**: an optional remote store of prebuilt package artifacts.
- **ENV**: a spec global naming the environment variables a package sets for
  activated shells and for the builds of packages that depend on it.
- **Fetch dependency**: a package installed before another package's *spec* can
  be fetched, declared in `source.dependencies`.
- **Identity**: a spec's namespaced, versioned name, `ns.name@rev`. The revision
  versions the spec, not the payload.
- **Manifest**: `envy.lua`, a project's pinned toolchain declaration.
- **Options**: per-entry configuration passed to every verb. Part of the
  package's identity.
- **Package**: one installed instance of a spec, keyed by `(identity, options,
  platform)`.
- **Platform**: an OS name, `darwin`, `linux`, or `windows`, optionally with an
  architecture, `arm64` or `x86_64`. Part of every package's cache key, and the
  thing platform filters match against.
- **Product**: a named capability a package exposes, either an executable path
  or a plain value.
- **Product script**: a deployed wrapper in the project bin dir that resolves
  and runs an executable product.
- **Root manifest**: the manifest that governs. Manifests with
  `@envy root "false"` defer upward.
- **Setup pair**: a named CHECK/INSTALL couple that performs host-state work,
  selected per manifest entry.
- **Spec**: the Lua file describing how to obtain one kind of package.
- **Superproject and subproject**: a root manifest that loads nested manifests
  with `envy.subproject`, and the manifests it loads.
- **User-managed package**: a package whose state lives on the host rather than
  in the cache, such as Homebrew or apt.
- **Vendoring**: copying a package's installed files out of the cache and into
  the project tree, for build systems that can only read inputs from inside the
  project.
- **Verb**: one of `FETCH`, `STAGE`, `BUILD`, `INSTALL`, `SETUP`. Each is a
  string, a table, a function, or omitted.
- **Weak reference**: a dependency query with a fallback, used only when the
  project does not already provide a match.
