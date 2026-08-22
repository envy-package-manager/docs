---
sidebar_position: 7
title: SETUP
---

# SETUP

Post-install work on the host machine, for things that cannot live inside an
immutable package directory: udev rules, OS packages, license activation, a
system daemon.

`SETUP` is a table of named CHECK/INSTALL pairs. `CHECK` asks whether the host
is already correct. `INSTALL` makes it correct. Nothing in `SETUP` runs unless a
manifest entry names the pair.

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

```lua title="envy.lua: the pair runs only because the entry selects it"
{ spec = "acme.jlink@r1", source = specs .. "acme.jlink.lua",
  options = { version = "9.30" },
  setup = { "udev_rules" } },
```

## Pair fields

| Field | Required | Meaning |
| --- | --- | --- |
| `CHECK` | yes | Is the host already satisfied? |
| `INSTALL` | yes | Make it satisfied. |
| `PLATFORMS` | no | Restrict the pair, for example `{ "linux" }`. A pair that does not match is skipped rather than failed. |
| `DEPENDS` | no | Names of sibling pairs that must complete first. Unknown names and cycles are rejected when the spec loads. |

Any other field is an error, and so is a top-level `CHECK` outside a pair. Pair
names may contain alphanumerics, `_`, `.`, and `-`.

## Verb shapes

| Verb | string | function |
| --- | --- | --- |
| `CHECK` | Shell command. Exit 0 means already satisfied. | `CHECK(pkg_dir, opts)` returning `true` or `false`, or a string that runs as a shell command whose exit status decides. |
| `INSTALL` | Shell script. | `INSTALL(pkg_dir, opts)` returning nothing, or a string that runs as a shell script. |

`pkg_dir` is the installed package directory, with a trailing separator, for a
cache-managed package. It is `nil` for a [user-managed](./user-managed.md) one,
which has no package tree.

Both verbs run with the working directory set to the project root rather than a
cache directory, because host state is the subject.

A `CHECK` as a bare string is often enough:

```lua
SETUP = {
  brew = {
    CHECK = "brew --version",
    INSTALL = function(pkg_dir, opts)
      envy.run({
        "sudo -v",
        'curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh | bash',
      }, { env = { NONINTERACTIVE = "1" }, interactive = true })
    end,
  },
}
```

Pass `interactive = true` to `envy.run` when the command needs the terminal, for
example a `sudo` password prompt or a license agreement. Output streams through
instead of being captured.

## How a pair executes

1. Platform filter. A `PLATFORMS` mismatch skips the pair.
2. `CHECK`. If satisfied, nothing runs.
3. Lock. envy takes a cross-process lock for this `(package, pair)`, so two
   concurrent `envy sync` runs cannot both install the same udev rule.
4. `CHECK` again, because the other process may have just done the work.
5. `INSTALL`.

A pair is therefore idempotent, and `CHECK` is the only re-run gate. Nothing
about a pair is cached: its lock entry is ephemeral and always purged, so every
`sync` re-asks the question. Keep `CHECK` a fast query rather than a full audit.

## Selection lives in the manifest

Pairs are opt-in per project, by name:

```lua
-- Nothing runs: the spec's pairs are available but unselected.
{ spec = "acme.jlink@r1", source = specs .. "acme.jlink.lua", options = { version = "9.30" } },

-- Install udev rules on a developer machine, but not on a CI runner.
{ spec = "acme.jlink@r1", source = specs .. "acme.jlink.lua", options = { version = "9.30" },
  setup = not os.getenv("CI") and { "udev_rules" } or nil },
```

Selections union across everyone who asks. A spec can demand a pair from one of
its own dependencies:

```lua
DEPENDENCIES = {
  { spec = "acme.brew@r0", source = "acme.brew.lua", setup = { "brew" } },
}
```

So a spec that installs a Homebrew formula can insist Homebrew exists first,
without the project needing to know. Selecting a pair also selects everything it
`DEPENDS` on.

## Selection does not change identity

A pair selection is not part of the package's identity or hash. The same cached
package, and the same depot artifact, serves a machine that selected
`udev_rules` and one that did not. The selection only decides which host-side
questions get asked.

[Options](./options.md) behave the opposite way. Change an option and you get a
different package. Change a setup selection and you get the same package,
checked differently.

## Pure-setup specs

A spec can be nothing but pairs, with no fetch, no build, and nothing cached.
That is a [user-managed](./user-managed.md) package: Homebrew itself, apt
packages, a kernel module.

## See also

- [User-Managed Packages](./user-managed.md) for specs that are only `SETUP`.
- [Shells & Scripts](../shells.md) for `envy.run` options, including `interactive`.
- [Package Entries](../projects#package-entries) for the `setup = { ... }` field.
