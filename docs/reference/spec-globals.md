---
sidebar_position: 3
title: Spec Reference
---

# Spec Reference

> **Placeholder content.** Skeleton tables; fill and verify against sources.

Terse companion to [Concepts → Specs](/concepts/specs).

## Globals

| Global | Allowed forms | Default when omitted |
| --- | --- | --- |
| `IDENTITY` | string `"ns.name@ver"` | — required, always |
| `FETCH` | string \| table \| function | error unless `USER_MANAGED` |
| `STAGE` | string \| table \| function | extract all fetched archives |
| `BUILD` | string \| function | no-op |
| `INSTALL` | string \| function | staged tree becomes the package |
| `SETUP` | table of named pairs | no pairs |
| `OPTIONS` | schema table \| function | no validation |
| `PRODUCTS` | table \| function | no products |
| `DEPENDENCIES` | array of dependency tables | none |
| `PLATFORMS` | array of platform strings | all platforms |
| `USER_MANAGED` | boolean \| function | false |
| `EXPORTABLE` | boolean | false (fetched bytes preserved for export) |

## Verb signatures

```lua
FETCH(tmp_dir, options)
STAGE(fetch_dir, stage_dir, tmp_dir, options)
BUILD(install_dir, stage_dir, fetch_dir, tmp_dir, options)
INSTALL(install_dir, stage_dir, fetch_dir, tmp_dir, options)
SETUP.<name>.CHECK(pkg_dir, options)   -- pkg_dir is nil for user-managed
SETUP.<name>.INSTALL(pkg_dir, options)
PRODUCTS(options)
OPTIONS(options)
USER_MANAGED()
```

All directory arguments arrive with a trailing path separator.

## SETUP pair fields

| Field | Required | Forms |
| --- | --- | --- |
| `CHECK` | yes | string (exit 0 = satisfied) \| function → boolean or script string |
| `INSTALL` | yes | string \| function → nil or script string |
| `PLATFORMS` | no | per-pair platform filter |
| `DEPENDS` | no | names of sibling pairs to run first |

## FETCH table fields

| Field | Meaning |
| --- | --- |
| `source` | URL (required). |
| `sha256` | Verify + enable cached reuse. |
| `ref` | Commit hash; required for git sources. |
| `dest` | Rename the downloaded file. |
| `post_data` | HTTP POST body (https only). |

## OPTIONS schema fields

`required`, `type` (`string`, `int`, `float`, `boolean`, `table`, `list`,
`semver`), `choices`, `range`, `validate`.
