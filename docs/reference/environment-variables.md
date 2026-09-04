---
sidebar_position: 5
title: Environment Variables
---

# Environment Variables

Everything envy reads from or writes to the environment. Most projects set none
of these.

## Read by envy

| Variable | Effect |
| --- | --- |
| `ENVY_CACHE_ROOT` | Cache root. Same as `--cache-root`, and the highest-priority tier. Read by the binary and by the committed bootstrap scripts. |
| `ENVY_MIRROR` | Where to download envy releases from. Overrides the `@envy mirror` directive. `https://` and `s3://` both work. |
| `ENVY_IGNORE_DEPOT` | Set to skip [depot](/concepts/depots) lookups and build from source. Same as `--ignore-depot`, honored by `sync`, `install`, `package`, and `export`. |
| `ENVY_NO_REEXEC` | Set to stop envy from re-executing into the version the manifest pins. Debugging only. |
| `ENVY_FETCH_ATTEMPTS` | How many times a transient download failure is retried, counting the first try. Default 3, clamped to 1 through 10. See [retries](#download-retries). |
| `ENVY_FETCH_RETRY_BASE_MS` | Base backoff between those attempts, in milliseconds. Default 1000, clamped to 0 through 60000. `0` disables the wait. |

Both fetch knobs are read once per process. They exist for CI and for tests that
cannot afford real backoff.

## Written by envy

| Variable | Set by | Value |
| --- | --- | --- |
| `ENVY_PROJECT_ROOT` | [`envy run`](./cli/run.md), the [shell hook](/concepts/environment/shell-hooks), and each deployed [product script](/concepts/environment/product-scripts) | The governing manifest's directory. A product script stamps it as a hop relative to its own bin directory, and only for a root manifest. |
| `PATH` | `envy run`, the shell hook, and each deployed product script | The project's bin directory, prepended. |

`envy run` sets both for the child process only. The shell hook sets both in your
interactive shell and undoes them when you leave the project. A product script
sets them for the tool it execs, so a tool that shells out to a sibling product
finds it.

Nothing else is injected. A phase's `envy.run` inherits the ambient environment,
plus whatever you pass in `opts.env`.

## Shell hook controls

Read by the hook scripts, not by the binary. See
[Shell Hooks](/concepts/environment/shell-hooks).

| Variable | Effect when set to `1` |
| --- | --- |
| `ENVY_SHELL_HOOK_DISABLE` | The hook does nothing. Useful in scripts and in CI where the hook is installed but unwanted. |
| `ENVY_SHELL_NO_ENTER_EXIT_ANNOUNCE` | No `entering`/`leaving` messages on stderr. |
| `ENVY_SHELL_NO_ICON` | No 🦝 prompt marker. |

Variables the hook keeps for itself, such as `_ENVY_BIN_DIR` and
`_ENVY_ORIG_PS1`, start with an underscore and are not exported. Do not set them.

## Windows

The variables are the same. Three details differ:

- Set them the usual PowerShell way, `$env:ENVY_CACHE_ROOT = "C:\envy-cache"`, or
  `set ENVY_CACHE_ROOT=C:\envy-cache` in `cmd`.
- `ENVY_CACHE_ROOT` and `ENVY_MIRROR` are read by `bin\envy.bat` as well as by
  the binary, so they steer the bootstrap download too.
- The hook variables apply to the PowerShell hook. `cmd.exe` has no hook, so
  nothing there reads them.

## Cache root precedence

Highest to lowest:

1. `--cache-root` or `ENVY_CACHE_ROOT`. Must be absolute.
2. A `.envy-cache-local` or `.envy-cache-shared` marker written by
   [`envy cache --local/--shared`](/reference/cli/cache).
3. `@envy cache-mode` in the manifest.
4. `@envy cache-local` being present at all, which means local. Relative to the
   manifest's directory, with no expansion of any kind.
5. The platform default.

| Platform | Default |
| --- | --- |
| macOS | `$HOME/Library/Caches/envy` |
| Linux | `$XDG_CACHE_HOME/envy`, or `$HOME/.cache/envy` |
| Windows | `%LOCALAPPDATA%\envy`, or `%USERPROFILE%\AppData\Local\envy` |

Every tier resolves to an absolute path. A relative manifest directive anchors to
the manifest, not to your current directory, so one manifest always names one
cache tree.

## Mirror precedence

1. `ENVY_MIRROR`
2. `@envy mirror` in the manifest
3. GitHub releases

## Download retries

A download that dies on the transport is retried rather than failing the run:
DNS, connect, or TLS failures, a connection that dies mid-body, a stall below
the minimum transfer rate, and HTTP 5xx or 429. Every other 4xx is a statement
about the request that a replay will not change, and a malformed URL or a local
filesystem failure is fatal immediately.

Retrying is safe because everything envy fetches is an idempotent GET and every
payload is verified against its `sha256` after transport, so a replay cannot
launder bad bytes.

Backoff is exponential and jittered: 1x, 4x, then 16x `ENVY_FETCH_RETRY_BASE_MS`,
capped at 60 seconds, each spread over plus or minus 50%. envy runs a thread per
request, so without the jitter a batch that all failed against one bad mirror
would march back onto it in lockstep. `s3://` sources are not retried here,
because the AWS SDK already retries internally.

Each retry is a `download_retry` [trace event](./observability.md), and shows up
under `--verbose` as `fetch: attempt N of M failed`.

## Variables envy respects indirectly

| Variable | Where it matters |
| --- | --- |
| `HOME`, `XDG_CACHE_HOME`, `LOCALAPPDATA`, `USERPROFILE` | Default cache root, and the `~` in `.luarc.json` paths. |
| `TERM` | Whether output gets a live TUI or plain lines. |
| `LANG`, `LC_ALL`, `LC_CTYPE` | Whether the shell hook uses UTF-8 glyphs or ASCII fallbacks. |
| `AWS_*` | Ambient credentials for `s3://` sources, mirrors, and depots. envy uses the AWS SDK directly. |

## CI

Two settings cover most CI needs:

```yaml
env:
  ENVY_CACHE_ROOT: ${{ github.workspace }}/.envy-cache   # so the cache is cacheable
  ENVY_IGNORE_DEPOT: 1                                   # only in depot publish jobs
```

The first puts the cache somewhere the CI cache action can save and restore. The
second belongs only in jobs that publish a depot. See
[GitHub Actions](../guides/integrations/github-actions.md).

## See also

- [Global flags](./cli/index.md) for the CLI equivalents.
- [The Cache](/concepts/cache) for what lives under the cache root.
- [Manifest Reference](./manifest.md) for the `@envy` directives.
