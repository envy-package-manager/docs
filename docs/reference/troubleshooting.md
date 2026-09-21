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
error: manifest not found (discovery from /Users/you/tmp)
```

You are outside a project, or every candidate directory above the anchor lacks
`envy.lua`. The message names the directory the walk started from. Pass
`--project <dir>`, `--manifest <path>`, or run from inside the project.

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

**A flaky network fails the run**

envy already retries a download that dies on the transport: connect, TLS, and
DNS failures, a connection dropped mid-body, a stall, and HTTP 5xx or 429. Three
attempts by default, with exponential jittered backoff. A 404 or a 403 is not
retried, because a replay will not change the answer.

If the failure survives that, raise the attempt count rather than re-running the
whole build:

```bash
ENVY_FETCH_ATTEMPTS=6 envy install
```

`--verbose` shows each retry as `fetch: attempt N of M failed`, and `--trace`
emits a `download_retry` event carrying the classification. See
[Download retries](./environment-variables.md#download-retries).

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
| `... cycle detected: a@r1 -> b@r1 -> a@r1` | A dependency loop, named end to end. Fetch dependencies can form one too. | Break the loop, usually by lowering a `needed_by`. |
| `envy.package: pkg 'top@v1' has no strong dependency on 'base@v1'` | `base` is in the graph, but only through someone else's edge. | Declare `base` in `top` as well. The two entries name one package. |
| `spec 'x@r1' depends on 'y@r1' twice with different options` | One dependency list names an identity under two option sets. | Pick one, or give the second a distinct spec revision. |
| `Dependency cannot specify 'platforms'` | `platforms` filters manifest `PACKAGES` entries only. | Wrap the entry in `if envy.PLATFORM == ... then`. |
| `Package: unknown key 'x'; allowed keys are ...` | A typo, or a field that belongs on a different entry shape. | The message lists what this shape accepts. |
| `envy.import: <file> sets DEFAULT_SHELL, which is read only from the root manifest` | An imported manifest declared a root-only global. | Splice it up: `DEFAULT_SHELL = envy.import("sub").DEFAULT_SHELL`. |
| `spec 'x@r1' is declared with conflicting sources in a and b` | Two declarations of one identity name different payloads. | Correct one. The two files named are the ones that wrote the entries. |
| `Deadlock: no task is running while N wait(s) are blocked:` | A scheduling bug, not a manifest error. | The report lists every blocked wait and what it waits for. File it with the manifest and that list. |

An ambiguous weak reference means the project provides two candidates, and envy
refuses to guess which one you meant. See
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

They also answer from the spec's own `DEPENDENCIES` and nothing further. A
package you reach only through a dependency of a dependency is refused by name.
Declare it yourself, and the two entries still name one package.

**Everything with options rebuilt after upgrading to envy 0.3.1**

Expected, once. The canonical key spells option names `{["version"]="4.4.0"}`
where it used to write `{version="4.4.0"}`, so every package carrying options
names a new cache entry. The old entries stay on disk until you delete the
cache. A saved full-canonical-key query needs the new spelling too.

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

Discovery walks up from an anchor and stops at the first manifest that is a
root. A component manifest with `@envy root "false"` defers upward. Ask envy
which project it picked and what anchored the choice:

```bash
envy --trace=stderr product 2>&1 | grep manifest_resolved
```

A bin directory decides its own project: `../other/bin/cmake` and
`../other/bin/envy sync` act on `../other`, not on the directory you are
standing in, because those scripts inject `--project`. To force a different
answer, pass `--project <dir>` yourself, or `--subproject` for the nearest
manifest to the current directory. See
[Manifest discovery](/concepts/projects#manifest-discovery).

**`run: exec failed: No such file or directory`**

`envy run` did not find that program. It prepends the project's bin directory to
`PATH` and execs, so this means the name is not deployed and not on the ambient
`PATH` either.

**A wrapper script points at the wrong thing**

Run `envy deploy`. Scripts are regenerated from the current manifest. A script
you [took ownership of](/concepts/environment/product-scripts#taking-ownership-of-a-name)
is never touched, which is exactly the situation where a stale one can persist.

## Output

**`envy sync` printed nothing at all**

It worked. Since envy 0.4.2 a package only gets a line when it did something, so
a run that found everything cached and copied nothing has nothing to report. Use
`--verbose` to see the decision behind each package anyway, and see [a run with
no work is silent](./observability.md#a-run-with-no-work-is-silent).

**A CI log and my terminal disagree about which packages ran**

Both are correct. A terminal omits the rows for packages that did no work; a
redirected stream keeps all of them, so the log lists every package. The run
itself is the same.

**Several rows in my log are the same `[identity]` and I cannot tell them apart**

That is one spec instantiated several times. Give the spec a
[`DISPLAY`](./spec-globals.md#display) — a function of its options — and each
row will name the instance it is working on.

**`DISPLAY must be a single line of printable text`**

A `DISPLAY` string contained a control character: a newline, a tab, a NUL, or
an escape. envy measures each row's width in order to erase it later, so any
byte below `0x20`, and `0x7f`, is rejected. If you were aligning text, note that
envy already pads the column for you.

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

**`envy shell` says the hook file is missing**

Hooks live only in the user-wide cache. A project on its own tree
(`@envy cache-local`, or `envy cache --local`) writes none, by design. Run any
envy command in a project on the user-wide cache, or set `ENVY_CACHE_ROOT`.
`envy cache --user-wide-root` prints the tree the hook would live in. If an
older envy left a `shell/` directory inside the project, `envy shell` names it so
you can delete it. See
[Shell Hooks](/concepts/environment/shell-hooks#hooks-are-a-user-wide-feature).

**A project-local cache re-downloads envy on every clone**

It should not: a local tree with no `@envy sha256sums` borrows an
already-downloaded envy binary out of the user-wide tree before falling back to
the network. A sums pin turns that off, because the fast path never
re-hashes what it finds and the user-wide tree is written by every other project
on the machine. That is the tradeoff a pin makes. See
[The Cache](/concepts/cache#a-local-tree-reads-the-user-wide-one).

**Network filesystems**

The cache uses file locks and hard links. Both work on local disks and are
unreliable on NFS and SMB. Keep the cache on local disk, and point CI at a
workspace path.

## Windows

**`bin\envy.bat` is missing, or points at an old version**

The bootstrap scripts are per platform, and a plain `sync` restamps only the host
flavor. Whoever last bumped the pin on macOS or Linux left the `.bat` behind. Fix
it from any machine:

```shell-session
$ envy sync --platform all
Updated bootstrap script
```

Same for wrappers. `bin\cmake.bat` only exists if someone ran
`--platform windows` or `--platform all`. See
[Product Scripts](/concepts/environment/product-scripts#the-windows-twin).

**Every deploy reports scripts as updated, and Git shows the whole bin directory
as modified**

Git line-ending conversion. envy writes CRLF for `.bat` and LF for everything
else, `core.autocrlf` rewrites the POSIX scripts to CRLF on checkout, and envy
writes them back:

```shell-session
$ envy deploy --platform all
deploy: 8 product script(s) (0 created, 1 updated, 7 unchanged, 0 removed)
```

Turn conversion off for the directory with `bin/** -text` in `.gitattributes`.
`*.bat eol=crlf` is compatible with what envy writes. See
[Line endings and file modes](/concepts/environment/product-scripts#line-endings-and-file-modes).

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

## Vendoring

**A vendored directory is rewritten on every run**

Something in it does not match the package, and envy repairs the whole directory
rather than reconciling it. Find out what by hashing it:

```bash
envy hash --tree third_party/nanocobs     # before a sync
envy sync
envy hash --tree third_party/nanocobs     # after
```

`envy vendor --all --dry-run` answers the same question in one step, and names
every destination that would be repaired.

Common causes are an editor writing a `.DS_Store` or a `.vscode` directory
inside it, a build system generating output there, and a `.gitattributes` rule
rewriting line endings on checkout. A stray file counts as drift, because the
whole destination is hashed. Move the extra files to a sibling directory, or use
`vendor = { auto_sync = false }` if the edits are deliberate. See
[Staying in sync](/concepts/vendoring#staying-in-sync).

**`package 'x' asks to be vendored, but the manifest sets no VENDOR_ROOT`**

`vendor = true` derives a directory name and needs somewhere to put it. Add
`VENDOR_ROOT = "third_party"` to the root manifest, or give the entry an explicit
path with `vendor = "third_party/x"`, which needs no root.

**`nested vendor destinations` or `vendor destination collision`**

Two packages want the same directory, or one wants a directory inside another's.
envy refuses before writing anything, because repairing the outer one would erase
the inner one. Give at least one of them an explicit path.

**A vendored tree reappears after I deleted it**

That is the repair working. envy copies a missing destination back on the next
`install` or `sync`. To stop vendoring a package, remove its `vendor` key, then
delete the directory. envy never prunes a destination it no longer writes.

**A vendored tree is missing or wrong, and I do not want to run a whole sync**

```bash
envy vendor nanocobs
```

[`envy vendor`](./cli/vendor.md) runs the vendor step for the packages you name.
Add `--all` for every vendored package, `--dry-run` to see the verdict without
changing anything, and `--force` to repair a destination that
`vendor.auto_sync = false` would otherwise leave alone.

**`envy vendor` says a package is not vendored**

The query matched a `PACKAGES` entry with no `vendor` field. Add one, or name a
different package. `--all` skips non-vendored entries rather than complaining,
so it is the right form when you want "whatever this manifest vendors".

**A vendored destination that was a symlink is now a real directory**

Expected. envy owns a vendored destination, and the repair deletes it before
copying. When the destination is a symlink, the link is what gets removed and
whatever it pointed at is left whole, so nothing outside is lost. Pointing a
vendor destination at a directory you maintain is not a way to share it.

**`vendor: 'x' resolves to <path>, outside the project`**

A component of the path is a symlink pointing out of the project. Vendoring
wipes a destination before copying into it, so envy resolves the real path first
and refuses one that leaves the project.

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

## S3

envy has the AWS SDK compiled in, so `s3://` sources, mirrors, and depots use
your ambient credentials and region config. There is no AWS CLI in the loop. See
[`AWS_*`](./environment-variables.md).

**`no usable AWS credentials`**

```text
error: mirror-envy: no usable AWS credentials
  SSOCredentialsProvider: Cached Token expired at 2026-08-14T18:22:03Z
  Hint: run 'aws sso login' (honoring AWS_PROFILE), or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.
```

The indented lines are the AWS SDK's own account of why each provider it tried
failed, tagged with the provider's name. An expired SSO session is the usual
one, and `aws sso login` is the fix.

`envy mirror-envy` resolves credentials up front when the destination is
`s3://`, before it downloads anything, so this fails in a second rather than
after six archives.

**`unrecognized S3 error code NotImplemented (HTTP 501)` on an upload**

S3 answers an unsigned write with `NotImplemented`. Either the session expired
partway through the run, in which case `aws sso login` and retry, or the
endpoint is an S3-compatible one that does not implement the operation.

**`PermanentRedirect`, or `AuthorizationHeaderMalformed`, or HTTP 301**

The bucket is in a different region. The SDK falls back to `us-east-1` when no
region is configured, so a bucket elsewhere fails as a redirect rather than as
"region not set". Set `AWS_REGION` or a profile region.

**HTTP 403 on an upload**

The credentials resolved, but they lack `s3:PutObject` on that prefix. Check the
bucket policy, or the role the profile assumes.

**`NoSuchBucket`**

envy never creates buckets. Create it first.

## Getting help

Include the manifest, `envy version`, the `--verbose` output, and a trace file.
See [Filing a bug report](./observability.md#filing-a-bug-report).
