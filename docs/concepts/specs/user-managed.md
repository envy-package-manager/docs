---
sidebar_position: 12
title: User-Managed Packages
---

# User-Managed Packages

> **Placeholder content.** Outline for review; verify against sources.

Some "packages" aren't files envy can own — they're host state: Homebrew
itself, apt packages, kernel rules. `USER_MANAGED = true` tells envy to
orchestrate without owning.

Will cover:

- The contract flip: cache-managed packages install into the cache and must
  define `FETCH`; user-managed packages mutate the host, must define at least
  one [SETUP](./setup.md) pair, and must *not* define
  `FETCH`/`STAGE`/`BUILD`/`INSTALL`.
- `USER_MANAGED` as a boolean or a function (decide at load time).
- What envy still provides: dependency ordering, platform filtering,
  CHECK-before-INSTALL idempotence, products (as raw values), parallel
  execution.
- What envy can't provide: caching, export to depots, uninstall/rollback —
  the host owns the state.
- Real examples: `brew` (CHECK: `brew --version`; INSTALL: run the Homebrew
  installer), `apt` packages (CHECK parses `dpkg-query`; INSTALL builds one
  `apt install` command), udev rules.
- Using a user-managed package as a dependency: "make sure Homebrew exists
  before this spec installs its formula."
