---
sidebar_position: 9
title: Options
---

# Options

> **Placeholder content.** Outline for review; verify against sources.

Options are how one spec serves many needs: the manifest passes
`options = { ... }`, the spec validates them, every verb receives them, and
they become part of the package's identity.

Will cover:

- The flow: manifest entry → validation against the spec's `OPTIONS` →
  `opts` argument to every verb.
- Identity participation: `version = "3.13"` and `version = "3.14"` are two
  separate packages, cached side by side. Changing any option produces a new
  package.
- Declaring `OPTIONS` as a schema table:

```lua
OPTIONS = {
  version = { required = true },
  tools = { type = "list" },
  release = { type = "string" },
}
```

  - Constraints: `required`, `type` (string, int, float, boolean, table,
    list, semver), `choices`, `range`, per-option `validate` functions.
  - Undeclared options are rejected — typos fail fast.
- Declaring `OPTIONS` as a function — compute the valid set dynamically
  (e.g. derive `choices` from a fingerprint table's keys), then call
  `envy.options(schema)`.
- Omitting `OPTIONS` entirely: no validation, options pass through.
- What options can't be: functions (they must hash cleanly).
