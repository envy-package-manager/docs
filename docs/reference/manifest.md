---
sidebar_position: 2
title: Manifest Reference
---

# Manifest Reference

> **Placeholder content.** Skeleton tables; fill and verify against sources.

Terse companion to [Concepts → The Manifest](/concepts/projects/manifest).

## `@envy` header directives

| Directive | Required | Meaning |
| --- | --- | --- |
| `schema "N"` | no | Manifest/spec schema version. |
| `version "x.y.z"` | recommended | Pinned envy version. |
| `sha256sums "<hex>"` | no | Checksum pin for the envy release; requires `version`. |
| `bin "<relpath>"` | **yes** | Project bin directory, relative to the manifest. |
| `deploy "true\|false"` | no (default false) | Enable product-script deployment. |
| `root "true\|false"` | no (default true) | Superproject boundary marker. |
| `mirror "<url>"` | no | envy release mirror (https or s3). |
| `cache-posix "<path>"` / `cache-win "<path>"` | no | Cache-root override per platform family. |

Header rules: directives are comments before the first line of Lua code;
last occurrence wins.

## Globals

| Global | Type | Meaning |
| --- | --- | --- |
| `PACKAGES` | table (required) | Package entries. |
| `BUNDLES` | table | Bundle alias → `{ identity, source, ref }`. |
| `PACKAGE_DEPOTS` | table | Depot index URIs, or `{ DEPENDS, FETCH }` tables. |
| `DEFAULT_SHELL` | constant \| table \| function | Shell for string verbs ([Shells & Scripts](/concepts/specs/shells)). |

## Package entry fields

| Field | Type | Notes |
| --- | --- | --- |
| `spec` | string | Required. `ns.name@ver`. |
| `source` | string \| table | URL/path/git; or `{ fetch, dependencies }` ([fetch deps](/concepts/dependencies/fetch-dependencies)). Mutually exclusive with `bundle`. |
| `bundle` | string \| table | Bundle alias or inline bundle. |
| `sha256` | string | Spec download pin. |
| `ref` | string | Commit pin; required for git sources. |
| `subdir` | string | Spec path within fetched tree. |
| `options` | table | No functions allowed; part of package identity. |
| `platforms` | table | Entry-level platform filter. |
| `setup` | table | Setup-pair selection. |
| `needed_by` | string | `check\|import\|fetch\|stage\|build\|install`; default `build`. |
| `product` | string | Product-dependency form. |
| `weak` | table | Fallback spec; mutually exclusive with `source`. |
