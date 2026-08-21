---
sidebar_position: 7
title: SETUP
---

# SETUP

> **Placeholder content.** Outline for review; verify against sources.

Post-install work on the *host machine* — the escape hatch for things that
can't live inside an immutable package directory: udev rules, OS package
installs, license activation.

Will cover:

- The shape — named CHECK/INSTALL pairs:

```lua
SETUP = {
  udev_rules = {
    PLATFORMS = { "linux" },
    CHECK = function(pkg_dir, opts)
      local r = envy.run("cmp -s " .. pkg_dir .. "99-jlink.rules /etc/udev/rules.d/99-jlink.rules",
                         { quiet = true, check = false })
      return r.exit_code == 0
    end,
    INSTALL = function(pkg_dir, opts)
      envy.run({
        "sudo cp " .. pkg_dir .. "99-jlink.rules /etc/udev/rules.d/",
        "sudo udevadm control -R",
      }, { interactive = true })
    end,
  },
}
```

- The semantics: CHECK asks "is the host already right?"; INSTALL makes it
  so; CHECK runs again before INSTALL to avoid redundant work.
- Verb shapes within a pair: CHECK as a shell string (exit 0 = satisfied) or
  a function returning a boolean or a script string; INSTALL as a string, or
  a function optionally returning a script string.
- **Selection is explicit and lives in the manifest**: nothing runs unless an
  entry says `setup = { "udev_rules" }`. The conditional-selection idiom:
  `setup = not ci and { "udev_rules" } or nil` — skip host mutation in CI.
- The key design property: setup selection **does not change the package's
  identity or hash**. The same cached/depot package serves every selection;
  pairs are re-CHECKed instead.
- Per-pair `PLATFORMS`, and pair-to-pair ordering with `DEPENDS`.
- The `interactive` flag on `envy.run` — when your INSTALL needs `sudo`
  prompts or other terminal interaction.
- Pure-setup specs ([user-managed](./user-managed.md)): Homebrew, apt — no
  fetch/build at all, just pairs.
