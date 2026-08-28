---
sidebar_position: 7
title: Troubleshooting
---

# Troubleshooting

Symptoms, causes, and the command that tells you which is which.

Two commands answer most questions. `--verbose` narrates the decisions, and
`--trace=file:t.jsonl` records them. See
[Logging & Tracing](./observability.md).

## Bootstrap

**`envy: command not found` from `envy`**

The bootstrap script is not executable, or the file is a Git LFS pointer, or the
line endings are CRLF on a Unix runner. Check `git ls-files --stage bin/envy` for
mode `100755`.

**The bootstrap script cannot download envy**

It prints the URL it tried. Work down the list:

1. The mirror. `@envy mirror` or `ENVY_MIRROR` may point somewhere unreachable
   from this network. Unset both to fall back to GitHub releases.
2. The version. `@envy version` names an exact release, and a release that was
   never published for this platform cannot be downloaded.
3. Proxies. The script uses `curl` on Unix and PowerShell on Windows, so both
   honor the usual proxy environment variables.

**`'@envy sha256sums' requires '@envy version'`**

A sums pin identifies one release's checksum file, so it cannot be combined with
a dynamically resolved version. Add the version or drop the pin.

**No manifest**

```text
error: manifest not found (discovery failed)
```

You are outside a project, or every candidate directory up the tree lacks
`envy.lua`. Pass `--manifest <path>`, or run from inside the project.

## Fetching

**`SHA256 mismatch`**

```text
error: Fetch failed for local.badhash@r1:
  /tmp/payload.tar.gz: SHA256 mismatch: expected 000000... but got 5235729f...
```

Three explanations, in order of likelihood: the spec's recorded hash is wrong,
the upstream artifact was re-published under the same URL, or something is
intercepting the download. Verify the bytes yourself before changing the spec:

```bash
envy fetch <url> /tmp/artifact
envy hash /tmp/artifact
```

If the hash upstream changed and you cannot explain why, do not just update the
spec. A URL whose contents changed is the shape of a supply-chain problem.

**It re-downloads every run**

The `FETCH` entry has no `sha256`. Without one, envy cannot prove the file in the
cache is the file you asked for, so it fetches again. Add the hash.

**A git source will not resolve**

A git source needs a full commit sha in `ref`. Branches and tags are not
reproducible, and a short sha can be ambiguous. Resolve it once:

```bash
envy git-resolve https://github.com/acme/specs refs/heads/main
```

## Resolution

| Message | Cause | Fix |
| --- | --- | --- |
| `Product 'x' provided by multiple specs: a@r1, b@r1` | Two packages export the same product name. | Remove one, or rename the product in a spec you own. |
| `Reference 'x' in spec 'y' is ambiguous: a@r1, b@r1` | A weak query matches more than one resolved package. | Narrow the query, or declare the exact identity. |
| `Product 'x' has no provider` | Nothing in the graph exports it. | Declare the dependency, or fix the product name. |
| `envy.product: pkg 'x' does not declare product dependency on 'y'` | A phase reached for a product it never declared. | Add it to `DEPENDENCIES` with the right `needed_by`. |
| `Unknown setup pair 'x' selected for y@r1` | A manifest entry selects a `SETUP` pair the spec does not define. | Check the spelling against the spec's `SETUP` table. |
| `Bundle alias 'x' not found in BUNDLES table for spec '...'` | The alias is missing, or declared in a different manifest. | Declare it in the manifest that owns the entry. |
| `... cycle detected: a@r1 -> b@r1 -> a@r1` | A dependency loop. Fetch dependencies can form one too. | Break the loop, usually by lowering a `needed_by`. |

An ambiguous weak reference is worth understanding rather than working around. It
means the project genuinely provides two candidates, and envy refuses to guess
which one you meant. See
[Resolution](/concepts/dependencies/resolution#weak-reference-outcomes).

## Spec authoring

**`Spec must define 'FETCH': x@r1`**

Every cache-managed spec needs a `FETCH`. A spec that only mutates the host is
[user-managed](/concepts/specs/user-managed) and needs `USER_MANAGED = true`.

**`Spec x@r1 is user-managed (USER_MANAGED=true) but declares FETCH`**

User-managed specs define only `SETUP` pairs. The cache holds nothing for them.

**A phase cannot see a dependency**

`envy.product` and `envy.package` respect `needed_by`. A dependency declared
`needed_by = "build"` is not available in `FETCH`, by design, because it has not
been installed yet. Lower the `needed_by` to the earliest phase that needs it.

**My `BUILD` output is missing from the package**

`BUILD` runs in `install_dir` in the common case, but when a spec mixes
declarative and function verbs it is easy to write to `stage_dir` and never copy
it. Check the [lifecycle](/concepts/specs/lifecycle) for which directory each verb
owns, and look at the cache entry directly:

```bash
ls "$(envy package mytool)"
```

**`envy.template` errors**

```text
envy.template: missing value for placeholder 'a'
envy.template: unmatched '{{' (missing closing '}}')
```

Both are refusals to guess, not bugs. Every placeholder needs a value.

## Environment

**A tool is not on `PATH`**

Work down this list:

1. Is deployment on? Without `@envy deploy "true"` no product scripts exist:

   ```text
   warning: deployment is disabled in /path/to/envy.lua
   Add '-- @envy deploy "true"' to enable product script deployment
   ```

2. Does the product deploy a script? A product with `script = false` never gets
   one, on purpose. Use `envy product <name>`.
3. Is the [shell hook](/concepts/environment/shell-hooks) installed? Without it,
   nothing adds the bin directory to `PATH`. Call `<tool>` directly, or use
   [`envy run`](./cli/run.md).
4. Is `ENVY_SHELL_HOOK_DISABLE` set?

**The wrong project's tools are active**

Nested checkouts. Print what the hook thinks:

```bash
echo "$ENVY_PROJECT_ROOT"
```

Discovery walks up from the current directory and stops at the first manifest
that is a root. A component manifest with `@envy root "false"` defers upward. See
[Manifest discovery](/concepts/projects#manifest-discovery).

**`run: exec failed: No such file or directory`**

`envy run` did not find that program. It prepends the project's bin directory to
`PATH` and execs, so this means the name is not deployed and not on the ambient
`PATH` either.

**A wrapper script points at the wrong thing**

Run `envy deploy`. Scripts are regenerated from the current manifest. A script
you [took ownership of](/concepts/environment/product-scripts#taking-ownership-of-a-name)
is never touched, which is exactly the situation where a stale one can persist.

## Cache

**Out of disk**

```bash
envy cache            # what is using space
```

Deleting a whole cache entry directory is safe. envy re-creates what it needs on
the next `sync`, and nothing outside the cache points into it except through
`envy product`.

**Moving the cache**

Set `ENVY_CACHE_ROOT` for an absolute location, or `envy cache --local` to move
this project's packages into a tree inside it (`@envy cache-local` makes that the
project's default). Copying an existing cache to the new root is optional and
only saves re-downloading.

**Network filesystems**

The cache uses file locks and hard links. Both work on local disks and are
unreliable on NFS and SMB. Keep the cache on local disk, and point CI at a
workspace path.

## Windows

**`bin\envy.bat` is missing, or points at an old version**

The bootstrap scripts are per platform, and a plain `sync` restamps only the host
flavor. Whoever last bumped the pin on macOS or Linux left the `.bat` behind. Fix
it from any machine:

```console
$ envy sync --platform all
Updated bootstrap script
```

Same for wrappers. `bin\cmake.bat` only exists if someone ran
`--platform windows` or `--platform all`. See
[Product Scripts](/concepts/environment/product-scripts#the-windows-twin).

**Every deploy reports scripts as updated, and Git shows the whole bin directory
as modified**

Git line-ending conversion. envy writes LF, `core.autocrlf` rewrites to CRLF on
checkout, and envy writes them back:

```console
$ envy deploy --platform all
deploy: 8 product script(s) (0 created, 1 updated, 7 unchanged, 0 removed)
```

Turn conversion off for the directory with `bin/** -text` in `.gitattributes`.

**The shell hook does nothing in PowerShell**

Three checks, in order. `$PROFILE` exists and contains the dot-source line that
`envy shell powershell` prints. Your execution policy allows running your own
profile, `RemoteSigned` being enough. And you are in PowerShell rather than
`cmd.exe`, which has no hook at all. In `cmd`, call `bin\envy.bat` and
`bin\<tool>.bat` directly.

**A spec's script works in my terminal and fails in envy**

envy runs PowerShell with `-NoProfile -NonInteractive`, so a function or alias
from your profile does not exist and a prompt fails instead of waiting. Pass
`interactive = true` for anything that legitimately needs input, such as an
elevation prompt.

The other common cause is fail-fast. envy injects it into generated PowerShell and
cmd scripts when `check` is true, so a line whose exit code you were ignoring now
stops the script. See
[How each built-in is invoked](/concepts/shells#how-each-built-in-is-invoked).

**A file will not delete, or an install fails partway with a sharing violation**

Defender or the Search indexer is holding a handle on a freshly written file.
envy already retries deletions with backoff, so a failure that survives that is
usually a real open handle, often an editor or a running binary out of the cache.
Excluding the cache root from real-time scanning also makes large installs
noticeably faster.

**Long paths**

envy opts out of `MAX_PATH` for its own cache scans, so deep cache entries are
fine. A build tool running inside a package is not covered by that, so a
toolchain that hits the limit is usually fighting `MAX_PATH` itself. Either enable
the system-wide long-path policy or move the cache nearer the drive root with
`ENVY_CACHE_ROOT=C:\envy-cache`.

**Redirecting envy output produces a file nothing can parse**

PowerShell's `>` writes UTF-16. Use
`| Out-File -Encoding ascii` for depot indexes and `-Encoding utf8` for JSON. See
[the stdout contract](./observability.md#stdout-is-a-contract).

## Depots

**Everything builds from source with a depot configured**

That is a key mismatch, not a failure. Compare the two:

```bash
envy -q package cmake    # .../envy.cmake@r0/darwin-arm64-blake3-49a9b26.../pkg
grep 49a9b26 packages.txt      # is that artifact published?
```

Options, a spec revision, or a weak dependency changed since the export. See
[Verify and debug](../guides/package-depots.md#verify-and-debug).

**A depot warning, then a normal build**

```text
warning: depot: failed to fetch manifest https://depot.invalid/packages.txt: curl_easy_perform failed: Couldn't resolve host name
```

Expected behavior. A depot is an accelerator, so an unreachable one warns and
falls back to source. The same happens on a download failure or a hash mismatch.

**Publishing keeps republishing the same artifacts**

Set `ENVY_IGNORE_DEPOT=1` in the publish job. Otherwise it imports from the depot
and exports what it just imported.

## Getting help

Include the manifest, `envy version`, the `--verbose` output, and a trace file.
See [Filing a bug report](./observability.md#filing-a-bug-report).
