---
sidebar_position: 19
title: envy mirror-envy
---

# `envy mirror-envy`

> **Placeholder content.** Verify flags and semantics against sources.

Mirror an envy release — every platform archive, the checksums file, and the
`latest` marker — to a directory or S3 prefix. For orgs whose machines can't
(or shouldn't) reach envy's public releases.

## Usage

```
envy mirror-envy <version> <destination> [--from=<url>]
```

## Arguments & flags

| Argument / flag | Meaning |
| --- | --- |
| `version` | Release version to mirror. |
| `destination` | Directory or `s3://` prefix. |
| `--from <url>` | Source to mirror from (default: envy's GitHub releases). |

The mirrored `SHA256SUMS` is copied byte-for-byte and all platform archives
are verified against it before publishing — a `sha256sums`-pinned manifest
trusts a mirror exactly as much as the original.

## Examples

```bash
envy mirror-envy 0.1.9 s3://acme-envy-mirror
envy mirror-envy 0.1.9 /srv/mirrors/envy --from https://old-mirror.example.com
```

Point projects at it with `@envy mirror` or `ENVY_MIRROR`.

## See also

- [Reproducibility](/concepts/reproducibility) — the envy trust chain.
