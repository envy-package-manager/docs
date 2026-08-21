---
sidebar_position: 4
title: STAGE
---

# STAGE

> **Placeholder content.** Outline for review; verify against sources.

Turn fetched files into a working tree — usually "unpack the archive," which
is why most specs never write this verb.

Will cover — the four shapes:

| Shape | Meaning |
| --- | --- |
| omitted | Extract every fetched archive. The default that usually just works. |
| table | Extraction with options: `{ strip = N, only = { "glob", ... } }` — strip leading path components, extract selectively. |
| string | A shell script run in the staging directory. |
| function `STAGE(fetch_dir, stage_dir, tmp_dir, opts)` | Full control: conditional extraction, platform-dependent handling, `envy.extract` / `envy.extract_all` calls. |

- Where staged files land — and the subtlety worth a callout: for fully
  declarative specs (no function verbs downstream), extraction goes straight
  into the final package directory; there is no separate staging copy.
- Glob rules for `only` (`*`, `**`, `?`, character classes); a selector that
  matches nothing is an error, not a silent no-op.
- Archive format support (tar, zip, zstd, and friends — everything
  libarchive speaks).
- Conditional no-op staging (`if envy.PLATFORM ~= "windows" then return end`).
