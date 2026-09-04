---
sidebar_position: 12
title: User-Managed Packages
---

# User-Managed Packages

Some things a project depends on are not files envy can own: Homebrew itself, an
apt package, a udev rule, a system daemon. They live in host state, are
installed once per machine, and sit in locations envy should not manage.
`USER_MANAGED` tells envy to orchestrate them without owning them.

The contract flips:

| | Cache-managed (normal) | User-managed |
| --- | --- | --- |
| Must define | `FETCH` | at least one [`SETUP`](./setup.md) pair |
| Must not define | nothing | `FETCH`, `STAGE`, `BUILD`, `INSTALL` |
| Where the result lives | the cache, immutably | the host machine |
| Cached | yes | no, `CHECK` is the only gate |
| Exportable to a [depot](../depots.md) | yes, if `EXPORTABLE` | no |
| `pkg_dir` in `SETUP` verbs | the package directory | `nil` |

Declaring a phase verb alongside `USER_MANAGED = true` is an error that names
the verb. The two models cannot be mixed in one spec.

## A complete example

```lua title="acme.brew.lua"
-- @envy schema "1"
IDENTITY = "acme.brew@r0"
PLATFORMS = { "darwin" }
USER_MANAGED = true

SETUP = {
  brew = {
    CHECK = "brew --version",

    INSTALL = function(pkg_dir, opts)
      envy.run({
        "sudo -v",
        'curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh | bash',
      }, {
        env = { NONINTERACTIVE = "1" },
        interactive = true,
      })
    end,
  },
}
```

```lua title="envy.lua"
PACKAGES = {
  { spec = "acme.brew@r0", source = envy.abspath("envy/acme.brew.lua"),
    platforms = { "darwin" },
    setup = { "brew" } },
}
```

macOS only. Nothing is cached. One pair named `brew`. Its `CHECK` is a bare
command whose exit status is the answer. Its `INSTALL` runs the official installer
interactively, because the installer wants a `sudo` password. Without
`setup = { "brew" }` in the manifest, nothing happens.

### The same shape on Windows

Host mutation on Windows goes through a package manager the same way, and the
`CHECK` is still a command whose exit status answers the question:

```lua title="acme.winget-cmake.lua"
-- @envy schema "1"
IDENTITY = "acme.winget-cmake@r0"
PLATFORMS = { "windows" }
USER_MANAGED = true

SETUP = {
  cmake = {
    CHECK = "winget list --exact --id Kitware.CMake",
    INSTALL = "winget install --exact --id Kitware.CMake --accept-package-agreements",
  },
}
```

Those strings run under PowerShell, the Windows default. `winget list` exits
non-zero when the package is absent, which is exactly the contract `CHECK` wants.
A pair that needs administrator rights should set `interactive = true` through the
function form, since an elevation prompt in a non-interactive PowerShell fails
instead of asking:

```lua
INSTALL = function(pkg_dir, opts)
  envy.run("winget install --exact --id Kitware.CMake", { interactive = true })
end
```

Most projects want the cache-managed version of a tool instead. Reach for a
user-managed spec when the thing belongs to the machine, such as a driver, a
service, or a system SDK.

## What envy still provides

- **Dependency ordering.** Another spec declares
  `{ spec = "acme.brew@r0", source = "acme.brew.lua", setup = { "brew" } }`, and
  can then rely on Homebrew existing before its own install runs.
- **Idempotence.** `CHECK` runs, envy takes a cross-process lock, `CHECK` runs
  again, then `INSTALL`. Two concurrent syncs do not both install.
- **Platform filtering.** On the spec, the entry, or the pair.
- **Parallelism.** Unrelated pairs run concurrently with everything else.
- **Products.** Values are used verbatim rather than resolved against a cache
  path.

What it does not provide: caching, depot export, uninstall, and rollback. The
host owns that state.

## Products from host state

Values pass through as-is, which for a host package manager usually means the
name of the thing you asked for:

```lua
PRODUCTS = function(opts)
  local result = {}
  for _, pkg in ipairs(opts.packages) do
    result[pkg] = { value = pkg, script = false }
  end
  return result
end
```

`script = false` matters, because there is no cache path to wrap and no wrapper
script to deploy. `envy product libusb` answers `libusb`, which is what a build
system passing `-l` flags needs.

## A package-manager spec

Driving apt or brew for a list of packages follows one shape. `CHECK` asks the
host what is already installed and records what is not. `INSTALL` installs the
difference.

```lua
OPTIONS = { packages = { required = true, type = "list" } }

local missing = {}

SETUP = {
  packages = {
    CHECK = function(pkg_dir, opts)
      local res = envy.run("brew list", { capture = true, quiet = true, check = false })
      if res.exit_code ~= 0 then return false end

      local installed = {}
      for name in res.stdout:gmatch("%S+") do installed[name] = true end

      missing = {}
      for _, name in ipairs(opts.packages) do
        if not installed[name] then table.insert(missing, name) end
      end
      return #missing == 0
    end,

    INSTALL = function(pkg_dir, opts)
      return "brew install " .. table.concat(missing, " ")
    end,
  },
}
```

Two details. `missing` is a file-local variable written by `CHECK` and read by
`INSTALL`. That is legal, and it is why `CHECK` should decide what work remains
rather than only whether there is any. `INSTALL` also returns a string instead of
calling `envy.run`, which is the shortest form when no interactivity is needed.

For apt, the same skeleton with `dpkg-query -W -f='${Status} ${Package}\n' ...`
in `CHECK` and `sudo apt-get install -y` in `INSTALL`.

## `USER_MANAGED` as a function

A boolean is usual. A function, which must return a boolean, decides at load
time. Use it for a spec that owns files on one platform and drives host state on
another:

```lua
USER_MANAGED = function()
  return envy.PLATFORM == "linux"     -- apt on Linux, a real download elsewhere
end
```

Use it sparingly. The two halves of such a spec share nothing but a name, and
two specs are usually clearer.

## See also

- [SETUP](./setup.md) for pair semantics, selection, and the lock protocol.
- [Products](./products.md) for `script = false` and raw values.
- [Declaring Dependencies](../dependencies/declaring.md) for demanding a pair from a dependency.
