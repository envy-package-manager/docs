---
sidebar_position: 9
title: envy shell
---

# `envy shell`

> **Placeholder content.** Verify flags and semantics against sources.

Print the one line to add to your shell profile to enable
[shell hooks](/concepts/environment/shell-hooks) — automatic per-project
`PATH` management on `cd`.

## Usage

```
envy shell <bash|zsh|fish|powershell>
```

## Behavior

- Prints a `source` line pointing at the hook file envy maintains in its
  cache; add it to `.zshrc` / `.bashrc` / `config.fish` / PowerShell profile.
- The hook itself is pure shell: zero startup cost, no envy invocation on
  `cd`, self-updating across envy versions.

## Examples

```bash
./bin/envy shell zsh >> ~/.zshrc
./bin/envy shell fish >> ~/.config/fish/config.fish
```

## See also

- [Shell Integration](/getting-started/shell-integration) — setup, prompt
  marker, opt-out env vars.
