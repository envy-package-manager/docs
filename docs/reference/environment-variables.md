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

## Written by envy

| Variable | Set by | Value |
| --- | --- | --- |
| `ENVY_PROJECT_ROOT` | [`envy run`](./cli/run.md) and the [shell hook](/concepts/environment/shell-hooks) | The governing manifest's directory. |
| `PATH` | `envy run` and the shell hook | The project's bin directory, prepended. |

`envy run` sets both for the child process only. The shell hook sets both in your
interactive shell and undoes them when you leave the project.

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

## Cache root precedence

Highest to lowest:

1. `--cache-root` or `ENVY_CACHE_ROOT`, resolved against the current directory.
2. `@envy cache-posix` or `@envy cache-win` in the manifest, resolved against the
   manifest's directory. `~` and `$VAR` or `${VAR}` are expanded.
3. The platform default.

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
