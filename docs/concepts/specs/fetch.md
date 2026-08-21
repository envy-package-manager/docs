---
sidebar_position: 3
title: FETCH
---

# FETCH

> **Placeholder content.** Outline for review; verify against sources.

Get the bytes. `FETCH` describes what to download — as data when that's
enough, as code when it isn't.

Will cover — the four shapes:

| Shape | Meaning |
| --- | --- |
| string | One URL. Simplest possible spec. |
| table | One or more downloads with verification: `{ source, sha256?, ref?, dest?, post_data? }`, or an array of URLs/tables fetched concurrently. |
| function `FETCH(tmp_dir, opts)` | Compute the download set from options/platform, and/or fetch imperatively with `envy.fetch`. Returning a string or table means "now do this declaratively." |
| omitted | Nothing to fetch — only valid for [user-managed](./user-managed.md) specs; everything else must say how to get its bytes. |

- Real examples of each shape, including the platform-fingerprint-table
  idiom and a two-artifact Windows fetch (installer + unzipper).
- `sha256` semantics: verified on download; verified files are reused from
  cache on later runs; **files without a hash are re-downloaded every time**.
- git sources: `ref` (full commit) required; fetched trees flow into staging.
- `post_data` for endpoints that want a POST (license-acceptance downloads).
- `dest` to rename a download whose URL basename is unhelpful.
- Supported schemes and authentication notes.
- When a tool must exist before FETCH can run at all — that's a
  [fetch dependency](/concepts/dependencies/fetch-dependencies), declared in
  the manifest entry, not in the spec.
