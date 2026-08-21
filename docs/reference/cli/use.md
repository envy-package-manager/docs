---
sidebar_position: 8
title: envy use
---

# `envy use`

> **Placeholder content.** Verify flags and semantics against sources.

Retarget the manifest's pinned envy version — rewrites `@envy version` and
refreshes `@envy sha256sums` to match. The supported way to upgrade (or
downgrade) envy for a project. In superproject trees, run once per manifest
that carries its own pin.

## Usage

```
envy use <version> [--manifest=<path>] [--subproject] [--mirror=<url>]
         [--pin-sums | --no-pin-sums] [--force]
```

## Arguments & flags

| Argument / flag | Meaning |
| --- | --- |
| `version` | The envy version to pin. |
| `--manifest <path>` | Target this manifest instead of discovery. |
| `--subproject` | Target the nearest manifest; don't walk up. |
| `--mirror <url>` | Fetch release metadata from this mirror. |
| `--pin-sums` / `--no-pin-sums` | Add or drop the `sha256sums` checksum pin. |
| `--force` | Proceed despite warnings (e.g. re-pinning the same version). |

## Examples

```bash
./bin/envy use 0.2.0                 # upgrade this project
./bin/envy use 0.2.0 --subproject    # upgrade just the nearest manifest
```

## See also

- [Pinning & Updating](/guides/pinning)
- [Reproducibility](/concepts/reproducibility) — the envy trust chain.
