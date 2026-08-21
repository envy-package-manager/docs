---
sidebar_position: 18
title: envy merge-depot
---

# `envy merge-depot`

> **Placeholder content.** Verify flags and semantics against sources.

Merge per-platform depot index files into one, applying a retention policy —
the step between per-OS `export` jobs and uploading the final `packages.txt`.

## Usage

```
envy merge-depot <depot-manifests...> [--existing=<file>]
                 [--retain=<file> | --retain-s3-ls=<file>]
                 [--retain-prefix=<url>] [--strict]
```

## Arguments & flags

| Argument / flag | Meaning |
| --- | --- |
| `depot-manifests` | Per-platform index files from `envy export`. Required. |
| `--existing <file>` | The depot's current index; merged so unchanged entries survive. |
| `--retain <file>` / `--retain-s3-ls <file>` | Retention input: keep-list, or raw `aws s3 ls` output. Mutually exclusive. |
| `--retain-prefix <url>` | Prefix for retained entries. |
| `--strict` | Escalate merge inconsistencies to errors. |

Prints the merged index to stdout.

## Examples

```bash
./bin/envy merge-depot exports/*-packages.txt \
  --existing existing-packages.txt \
  --retain-s3-ls retain.txt --retain-prefix s3://acme-envy-packages/ \
  > exports/packages.txt
```

## See also

- [Running a Package Depot](/guides/package-depots) — where this sits in the
  nightly pipeline.
