---
sidebar_position: 11
title: envy git-resolve
---

# `envy git-resolve`

Resolve a git ref, whether branch, tag, or sha, in a remote repository to its
full commit sha, and print it to stdout. There is no clone, no `git` binary, and
no working tree. envy reads the remote's ref advertisement through libgit2 and
disconnects.

This is the authoring-time tool behind every pinned `ref` in a manifest or spec.
Resolve the mutable name once, commit the sha, and leave the command in a comment
so the next person knows how to re-resolve it.

## Usage

```
envy git-resolve <url> <ref>
```

## Arguments

| Argument | Meaning |
| --- | --- |
| `url` | Remote repository URL: `https://`, `git://`, `ssh://`, or a local path. Required. |
| `ref` | What to resolve: a fully-qualified ref, a bare tag or branch name, or a full sha. Required. |

Resolution rules:

- Fully-qualified names are matched exactly, for example `refs/tags/v1.5.23` or
  `refs/heads/main`. Prefer these.
- A bare name matches by trailing segment when that is unambiguous. `v1.5.23`
  finds `refs/tags/v1.5.23`. If a branch and a tag share the name and point at
  different commits, the run fails and lists both.
- Annotated tags peel to their commit, so you pin the commit rather than the tag
  object.
- A full 40 or 64 hex sha is echoed back lowercased with no network access. The
  command is therefore safe to call unconditionally in a script.

## Examples

### To pin a bundle at a specific commit

```bash
envy git-resolve https://github.com/envy-package-manager/package-specs main
# ded36a39bbf13744f5a0e539f2f4741fecb61dd0
```

```lua title="envy.lua"
BUNDLES = {
  envy = {
    identity = "envy.package-specs@r3",
    source = "https://github.com/envy-package-manager/package-specs.git",
    -- envy git-resolve https://github.com/envy-package-manager/package-specs main
    ref = "ded36a39bbf13744f5a0e539f2f4741fecb61dd0",
  },
}
```

Record the command in a comment. It documents what was resolved and how to
advance it.

### To pin a release tag unambiguously

```bash
envy git-resolve https://github.com/org/tool refs/tags/v1.5.23
```

Fully qualified, so a same-named branch cannot shadow it.

### To update a pin during a dependency bump

```bash
envy git-resolve https://github.com/org/tool refs/heads/main
# then paste the sha over the old `ref = "..."` in specs/tool.lua
```

The output is one bare line on stdout, so scripting the edit is easy in whatever
your repo already uses. There is no envy-specific parsing.

### To pin a git source inside a spec's `FETCH`

```bash
envy git-resolve https://github.com/protocolbuffers/protobuf refs/tags/v33.5
```

Then use the sha as the spec's `ref`. A spec that fetches a branch name is not
reproducible. One that fetches a sha is.

### To normalize a sha you were handed

```bash
envy git-resolve https://github.com/org/tool 9BDB0A11CEFA3E83418CFF37DC68EA755C07A237
# 9bdb0a11cefa3e83418cff37dc68ea755c07a237
```

Offline and idempotent, which is handy in a script that accepts either a tag or a
sha.

## No git required

Resolution goes through libgit2, so there is no `git` binary involved on any
platform. That matters most on Windows and on minimal CI images, where a project
can pin git sources without installing Git for Windows first.

## See also

- [Pinning & Updating](/guides/pinning)
- [FETCH](/concepts/specs/fetch) for git sources and their `ref` requirement.
- [Bundles](/concepts/dependencies/bundles)
