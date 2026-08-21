---
sidebar_position: 19
title: envy mirror-envy
---

# `envy mirror-envy`

Mirror an envy release into a local directory or an S3 prefix: every platform's
archive, the release's `SHA256SUMS`, and a `latest` marker. For organizations
whose machines cannot reach envy's public releases, and for anyone who wants
project bootstrap to depend on infrastructure they control.

envy verifies every archive against the `SHA256SUMS` fetched from the same source
before republishing anything. A mirror that passed on corrupt bytes would turn
one bad upstream fetch into a bad artifact for every consumer downstream. A
project pinning that `SHA256SUMS` would then be attesting garbage.

The checksum file itself is copied byte for byte rather than regenerated. Any
reformatting would change the file's own hash and make the pin mirror-specific.
Copying it verbatim is what makes one `@envy sha256sums` pin work against the
mirror and against upstream.

## Usage

```
envy mirror-envy <version> <destination> [--from=<url>]
```

## Arguments and flags

| Argument or flag | Meaning |
| --- | --- |
| `version` | Release to mirror, for example `0.2.0`. Required, and validated before any network access. |
| `destination` | A local directory or an `s3://bucket/prefix`. Required. Anything else, such as git, ssh, or http, is rejected up front. |
| `--from <url>` | Source mirror to read the release from. Defaults to envy's GitHub releases. Use it to chain mirrors, for example seeding a regional copy from a central one. |

## What lands in the destination

```
v0.2.0/envy-darwin-arm64.tar.gz
v0.2.0/envy-darwin-x86_64.tar.gz
v0.2.0/envy-linux-arm64.tar.gz
v0.2.0/envy-linux-x86_64.tar.gz
v0.2.0/envy-windows-arm64.zip
v0.2.0/envy-windows-x86_64.zip
v0.2.0/SHA256SUMS
latest
```

`latest` sits at the mirror root and holds the bare version string. A bootstrap
script for an unpinned project can therefore resolve the newest version from the
mirror instead of probing GitHub. Running `mirror-envy` for a newer version
advances it.

For an S3 destination, archives are staged in a private temporary directory and
removed after upload. Use a local destination to keep the staged bytes.

## Examples

### To stand up a private mirror

```bash
envy mirror-envy 0.2.0 s3://acme-envy-mirror
# mirrored envy 0.2.0 (8 objects) to s3://acme-envy-mirror
# point envy.lua at it with:
#   -- @envy version "0.2.0"
#   -- @envy mirror "s3://acme-envy-mirror"
#   -- @envy sha256sums "a17e...c93f"
```

The printed directives are the handoff. Paste them into a manifest, or pass the
mirror to [`envy init --mirror`](./init.md) for new projects and
[`envy use --mirror`](./use.md) for existing ones.

### To mirror onto an internal web server

```bash
envy mirror-envy 0.2.0 /srv/www/envy
```

Serve `/srv/www/envy` over HTTPS and point projects at
`https://mirror.acme.example/envy`. The layout is what bootstrap expects, so no
rewrite rules are needed.

### To add a version without disturbing the old ones

```bash
envy mirror-envy 0.2.1 s3://acme-envy-mirror
```

Versions live in their own `v<version>/` prefixes, and only `latest` is
rewritten. Projects pinned to `0.2.0` keep working.

### To seed a regional mirror from the central one

```bash
envy mirror-envy 0.2.0 s3://acme-envy-eu --from https://mirror.acme.example/envy
```

Verification happens against the `SHA256SUMS` at `--from`, and the file is copied
through unchanged, so a pin taken from the central mirror still verifies here.

### To air-gap a release onto removable media

```bash
envy mirror-envy 0.2.0 /media/usb/envy-mirror
# staged envy 0.2.0 (7 objects) in /media/usb/envy-mirror
# attest against it with:
#   -- @envy sha256sums "a17e...c93f"
```

Carry it across, then copy it to an internal server or use the directory directly
as `@envy mirror`.

## See also

- [Reproducibility](/concepts/reproducibility) for the envy trust chain.
- [`envy use`](./use.md) for retargeting a project at a version on your mirror.
- [`envy init`](./init.md) for stamping `@envy mirror` into a new project.
