---
sidebar_position: 8
title: Shells & Scripts
---

# Shells & Scripts

> **Placeholder content.** Outline for review; verify against sources.

Whenever a verb is a string — or a function returns one — envy runs it as a
shell script. This page defines "as a shell script."

Will cover:

- Defaults per platform, and the built-in shells: `ENVY_SHELL.BASH`,
  `ENVY_SHELL.SH`, `ENVY_SHELL.CMD`, `ENVY_SHELL.POWERSHELL`.
- Changing the project-wide default with the manifest's `DEFAULT_SHELL`:
  - a built-in constant;
  - a file-based interpreter (`{ file = "/usr/bin/tclsh", ext = ".tcl" }`);
  - an inline interpreter (`{ inline = { "/usr/bin/python3", "-c" } }`);
  - a function, so the interpreter can itself be an envy-managed package —
    write every build script in Python without assuming Python is installed.
- The bootstrap caveat: specs that provide the interpreter (e.g. Python
  itself) must stick to built-in shells.
- Working directories per verb (where your script starts).
- `envy.run` for explicit process control from function verbs: single
  command or list, `quiet`, `check`, `capture`, `interactive`, `env`.
- Failure semantics: non-zero exit fails the verb (unless `check = false`).
