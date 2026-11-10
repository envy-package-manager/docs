---
sidebar_position: 10
title: envy activate
---

# `envy activate`

Print shell code that activates the project: its bin directory on `PATH`,
`ENVY_PROJECT_ROOT`, and the [`ENV`](/concepts/environment/package-env) of every
installed package. Requires envy 0.6.0.

The [shell hook](/concepts/environment/shell-hooks) runs this for every project
you `cd` into. Run it yourself where there is no hook.

## Usage

```
envy activate <bash|zsh|fish|powershell>
```

Load the output with your shell:

| Shell | Command |
| --- | --- |
| bash, zsh | `eval "$(envy activate zsh)"` |
| fish | `envy activate fish \| source` |
| PowerShell | `envy activate powershell \| Out-String \| Invoke-Expression` |

## Behavior

| Aspect | Detail |
| --- | --- |
| Output | Shell code on stdout. Status lines and warnings on stderr. |
| On a terminal | Prints how to load the script instead of the script: `activate prints shell code; load it with: eval "$(envy activate zsh)"`. |
| Prior activation | Undone first, whichever project set it. Running it again in the same project refreshes. |
| Installs | None. It reads the cache, and never fetches, installs, or waits on a lock. A package that is not installed is skipped with `warning: activate: 1 package not installed; run 'envy install'`. |
| Lua output | A spec's `envy.stdout` or `io.write` goes to stderr, so it cannot corrupt the script. |
| Re-exec | Runs as the version the manifest pins. |
| Windows | `powershell` only. |
| Exit code | 0, even when packages were skipped. |

The status line names the project and how many variables changed:

```text
envy: entering proj — 4 variables set
```

It says `refreshed` when the project was already active, and prints
`envy: leaving <other> — environment restored` first when another project was.
`ENVY_SHELL_NO_ENTER_EXIT_ANNOUNCE=1` silences it. In a non-UTF-8 locale the
dash is `--`.

The script also exports a set of `ENVY_ACTIVATE_*` variables, the record
[`envy deactivate`](./deactivate.md) restores from. See
[Activation state](../environment-variables.md#activation-state).

## Examples

### To activate a project without the shell hook

```shell-session
$ eval "$(envy activate zsh)"
envy: entering proj — 4 variables set
$ echo $CARGO_HOME
/Users/you/work/proj/.cargo
$ eval "$(envy deactivate zsh)"
envy: leaving proj — environment restored
```

On Windows:

```powershell
envy activate powershell | Out-String | Invoke-Expression
envy deactivate powershell | Out-String | Invoke-Expression
```

### To pick up packages you just installed

```bash
envy install
eval "$(envy activate zsh)"
```

With the shell hook this happens on its own. `envy install` and `envy sync` mark
the project, and every activated shell in it refreshes at its next prompt.

### To see what activation changes

```bash
envy activate bash | grep -v '^export ENVY_ACTIVATE_'
```

```text
export CARGO_HOME='/Users/you/work/proj/.cargo'
export ENVY_PROJECT_ROOT='/Users/you/work/proj'
export PATH='/Users/you/work/proj/bin:/Users/you/Library/Caches/envy/packages/acme.rust@r0/darwin-arm64-blake3-a745fbca66556c1f/pkg/bin:/usr/bin:/bin'
export RUSTUP_HOME='/Users/you/Library/Caches/envy/packages/acme.rust@r0/darwin-arm64-blake3-a745fbca66556c1f/pkg/rustup'
```

Piping makes stdout something other than a terminal, so the script prints.

## See also

- [Package Environment](/concepts/environment/package-env) for `ENV` and the activation rules.
- [`envy deactivate`](./deactivate.md) for the way back.
- [`envy run --activate`](./run.md) for one command in the activated environment.
