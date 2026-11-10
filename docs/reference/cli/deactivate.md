---
sidebar_position: 10
title: envy deactivate
---

# `envy deactivate`

Print shell code that undoes [`envy activate`](./activate.md): every variable
activation touched goes back to its old value, byte for byte, and the
`ENVY_ACTIVATE_*` state is removed. Requires envy 0.6.0.

The [shell hook](/concepts/environment/shell-hooks) runs this when you leave the
last project.

## Usage

```
envy deactivate <bash|zsh|fish|powershell>
```

Load the output the same way as `activate`: `eval "$(envy deactivate zsh)"`,
`envy deactivate fish | source`, or
`envy deactivate powershell | Out-String | Invoke-Expression`.

## Behavior

| Aspect | Detail |
| --- | --- |
| Reads | Only the `ENVY_ACTIVATE_*` variables in its environment. No manifest, no Lua, no network. |
| Output | Shell code on stdout. Nothing when no activation is present. On a terminal it prints how to load the script instead. |
| Status line | `envy: leaving proj — environment restored` on stderr. `ENVY_SHELL_NO_ENTER_EXIT_ANNOUNCE=1` silences it. |
| Windows | `powershell` only. |

The restore is wholesale. A variable activation touched returns to its value from
before activation, even if you changed it inside the project.

State written by a different state format is refused:

```text
activation state schema '2' was written by a different envy; restart your shell
```

## See also

- [`envy activate`](./activate.md)
- [Activation state](../environment-variables.md#activation-state) for the variables it reads.
- [Package Environment](/concepts/environment/package-env) for what activation applies.
