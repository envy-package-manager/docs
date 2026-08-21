---
sidebar_position: 15
title: envy lua
---

# `envy lua`

> **Placeholder content.** Verify flags and semantics against sources.

Run a Lua script inside envy's runtime — with the full `envy.*` API loaded.
The spec author's scratchpad: exercise helpers (`envy.template`,
`envy.path.*`, `envy.run`) outside a real spec.

## Usage

```
envy lua <script>
```

## Arguments

| Argument | Meaning |
| --- | --- |
| `script` | Path to a Lua file. Required; must exist (there is no REPL). |

## Examples

```bash
cat > /tmp/probe.lua <<'EOF'
envy.info(envy.PLATFORM_ARCH)
envy.info(envy.template("hello {{who}}", { who = "envy" }))
EOF
envy lua /tmp/probe.lua
```

## See also

- [Lua API](../lua-api.md)
