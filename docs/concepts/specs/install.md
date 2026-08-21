---
sidebar_position: 6
title: INSTALL
---

# INSTALL

Produce the final package directory: the `pkg/` tree that gets cached, shared
between projects, published to [depots](../depots.md), and resolved into by
[products](./products.md).

Once `INSTALL` succeeds, envy writes the completion marker and the package is
immutable. Consumers resolve into it from then on, and nothing edits it in
place. Work that has to touch the machine belongs in [SETUP](./setup.md).

## The three shapes

| Shape | Meaning |
| --- | --- |
| omitted | The staged tree becomes the package. |
| string | A shell script, run in `work/stage/`. |
| function `INSTALL(install_dir, stage_dir, fetch_dir, tmp_dir, opts)` | File surgery, platform installers, hand-assembled trees. May return a string to run as a script. |

### omitted

```lua
FETCH = "https://vendor.example/tool-1.2-linux-x86_64.tar.gz"
STAGE = { strip = 1 }
-- no INSTALL
```

Two things can happen, and neither costs a copy of the tree. If extraction
already went straight into `pkg/`, which is the usual case for a spec with no
function verbs, envy marks the entry complete. Otherwise it renames the staged
tree into place.

### string

```lua
BUILD = function(install_dir) return "./configure --prefix=" .. install_dir .. "\nmake -j" end
INSTALL = "make install"
```

The autotools pair. The script's working directory is `work/stage/`, so
`make install` finds the tree `BUILD` configured, and the `--prefix` from `BUILD`
sends the output into `pkg/`.

### function for file surgery

The most common reason to write `INSTALL` is that the vendor's layout is not the
layout you want.

```lua
-- The archive ships `taplo-darwin-aarch64`, but the product should be plain `taplo`.
INSTALL = function(install_dir, stage_dir, fetch_dir, tmp_dir, opts)
  local bin = envy.path.join(install_dir, "taplo" .. envy.EXE_EXT)
  if envy.PLATFORM == "windows" then
    envy.copy(envy.path.join(stage_dir, "taplo.exe"), bin)
  else
    local arch = (envy.ARCH == "arm64") and "aarch64" or envy.ARCH
    envy.copy(envy.path.join(stage_dir, "taplo-" .. envy.PLATFORM .. "-" .. arch), bin)
    envy.run("chmod +x " .. bin)
  end
end
```

Keeping only part of a build's output has the same shape:

```lua
INSTALL = function(install_dir, stage_dir, fetch_dir, tmp_dir, opts)
  local src = (envy.PLATFORM == "darwin") and envy.path.join(stage_dir, "build", "bin")
                                          or envy.path.join(stage_dir, "bin")
  for _, tool in ipairs(opts.tools) do
    envy.move(envy.path.join(src, tool .. envy.EXE_EXT),
              envy.path.join(install_dir, tool .. envy.EXE_EXT))
  end
end
```

### function running a platform installer

Some vendors ship only an installer. Run it, but point it at `install_dir` so
the result is still a normal cache-managed package:

```lua
INSTALL = function(install_dir, stage_dir, fetch_dir, tmp_dir, opts)
  if envy.PLATFORM == "darwin" then
    envy.run("installer -pkg " .. fetch_dir .. "AWSCLIV2.pkg" ..
             " -target CurrentUserHomeDirectory -applyChoiceChangesXML " ..
             tmp_dir .. "choices.xml")
  elseif envy.PLATFORM == "windows" then
    envy.run('msiexec.exe /a "' .. fetch_dir .. 'AWSCLIV2.msi" /qn TARGETDIR="' ..
             install_dir .. '"')
  else
    envy.run(stage_dir .. "aws/install --install-dir " .. install_dir .. "aws-cli" ..
             " --bin-dir " .. install_dir .. "bin")
  end
end
```

An installer that insists on a system location, or on running once per machine,
is not a package. See [user-managed](./user-managed.md).

### function returning a script

Same rule as `BUILD`. A returned string runs as a shell script with the working
directory set to `work/stage/`. Returning anything other than nil or a string is
an error.

## `EXPORTABLE`

```lua
EXPORTABLE = true
```

One boolean, evaluated when the spec loads, that decides what a
[depot](../depots.md) may publish for this package:

| Value | What a depot ships | Why |
| --- | --- | --- |
| `true` | The installed `pkg/` tree | The build is reproducible and relocatable, so consumers can skip it. |
| absent or `false` | The `fetch/` artifacts | The install has to run on each machine, for example a platform installer or a path baked in at install time. Sharing the download is still worthwhile. |

That is also why a non-exportable package keeps its `fetch/` directory after
completing, while an exportable one deletes it.

Because the value is evaluated at load time, a per-platform decision is ordinary
Lua:

```lua
EXPORTABLE = envy.PLATFORM ~= "windows"   -- the Windows installer is not relocatable
```

[User-managed](./user-managed.md) packages are never exported. There is nothing
in the cache to export.

## See also

- [The Package Lifecycle](./lifecycle.md) for where `pkg/` sits and what survives a failure.
- [Products](./products.md) for naming what is inside the tree.
- [SETUP](./setup.md) for work that belongs to the machine.
- [`envy export`](../../reference/cli/export.md) for `EXPORTABLE` from the publisher's side.
