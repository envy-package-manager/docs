---
sidebar_position: 18
title: envy merge-depot
---

# `envy merge-depot`

Merge depot index files into one and print the result to stdout, sorted by path.
This is the step between per-platform [`export`](./export.md) jobs and publishing
a single `packages.txt`. Each OS's CI runner sees only its own artifacts, and the
depot needs all of them in one file.

It also handles the awkward parts of a long-lived depot: carrying forward entries
nobody rebuilt this cycle, and dropping entries whose objects are gone.

## Usage

```
envy merge-depot <depot-manifests...> [--existing=<path|url>]
                 [--retain=<path|url> | --retain-s3-ls=<path|url>]
                 [--retain-prefix=<prefix>] [--strict]
```

## Arguments and flags

| Argument or flag | Meaning |
| --- | --- |
| `depot_manifests` | Index files from this cycle's `export` jobs, one per platform. At least one is required, and each must exist. |
| `--existing <path\|url>` | The depot's currently published index, as a local path or a URL. A URL is fetched. Its entries are the starting set. |
| `--retain <path\|url>` | A list of paths that still exist in the depot. Anything in the merged set that is neither listed nor new this run is pruned. |
| `--retain-s3-ls <path\|url>` | The same, parsing raw `aws s3 ls` output. Skips `PRE` lines and takes the key from each object line. Mutually exclusive with `--retain`. |
| `--retain-prefix <prefix>` | Prepend this to each retain entry before comparing, because `aws s3 ls` gives keys while the index holds full URLs. Requires a retain list. |
| `--strict` | Treat a hash change against `--existing` as an error instead of a warning. |

Merge rules:

- This cycle's entries win over `--existing` entries for the same path.
- A hash change for an existing path warns, or fails with `--strict`. The same
  artifact path with different bytes usually means a non-reproducible build.
- Two input manifests disagreeing about one path is always an error, never a
  warning. Nothing can arbitrate between two runners in the same cycle.
- Malformed lines are skipped with a warning. A line is well-formed when it is 64
  hex characters, two spaces, then a path. Blank lines and `#` comments are
  ignored.

## Examples

### To publish one index from per-platform CI jobs

```bash
envy merge-depot exports/macos-packages.txt \
                       exports/linux-packages.txt \
                       exports/windows-packages.txt \
  --existing https://packages.acme.example/envy/packages.txt \
  > packages.txt
```

Entries from all three runners, plus everything already published that nobody
rebuilt.

### To drop entries whose objects were deleted from the bucket

```bash
aws s3 ls --recursive s3://acme-envy-packages/ > retain.txt
envy merge-depot exports/*-packages.txt \
  --existing s3://acme-envy-packages/packages.txt \
  --retain-s3-ls retain.txt \
  --retain-prefix s3://acme-envy-packages/ \
  > packages.txt
```

The retain list is what the bucket actually holds. Anything the index claims and
the bucket lacks is pruned, so consumers never chase a 404. `--retain-prefix`
bridges the two namings: keys in the listing, full `s3://` URLs in the index.

### To fail the pipeline when a rebuild is not reproducible

```bash
envy merge-depot exports/*-packages.txt --existing packages.txt --strict
```

Without `--strict` a changed hash is a warning and the new hash wins. With it,
the job stops so a human can decide whether the change is legitimate, such as a
spec revision bump, or a reproducibility bug.

### To merge from a plain keep-list

```bash
envy merge-depot exports/*-packages.txt \
  --existing packages.txt --retain live-paths.txt > merged.txt
```

`--retain` expects one path per line, already in the index's naming. Use it when
your storage is not S3, or when a script already produced the list.

### To inspect a merge before publishing

```bash
envy merge-depot exports/*-packages.txt --existing packages.txt \
  | diff packages.txt - | head
```

Output is deterministic and path-sorted, so a diff against the live index is the
change set you are about to publish.

## See also

- [Running a Package Depot](/guides/package-depots) for where this sits in the nightly pipeline.
- [`envy export`](./export.md) and [`envy hash`](./hash.md) for where index lines come from.
- [Package Depots](/concepts/depots)
