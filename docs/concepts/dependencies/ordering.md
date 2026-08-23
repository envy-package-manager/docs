---
sidebar_position: 3
title: Phase Ordering & needed_by
---

# Phase Ordering & `needed_by`

A dependency edge in envy carries a time: the phase of the dependent that has to
wait. That is `needed_by`, and it is the difference between "install these in
some order" and "install these as concurrently as correctness allows".

## The idea

Consider a spec that builds from source with cmake. It needs cmake by the time
`BUILD` runs, and not before. Its own `FETCH` and `STAGE` have nothing to do with
cmake, so there is no reason for them to wait:

```lua
DEPENDENCIES = { { product = "cmake", needed_by = "build" } }
```

While cmake installs, this package downloads and unpacks its own sources. Only
`BUILD` blocks. On a cold cache with a wide manifest, that overlap is most of why
`envy sync` is fast.

Now consider a spec whose `FETCH` shells out to a tool, because the artifact is
behind a registry CLI. The tool has to exist earlier:

```lua
DEPENDENCIES = { { spec = "tools.jfrog-cli@r1", product = "jf",
                   source = "tools.jfrog-cli.lua", needed_by = "fetch" } }

FETCH = function(tmp_dir, opts)
  envy.run(envy.template("{{jf}} rt download --flat '{{path}}' '{{dest}}'", {
    jf = envy.product("jf"),
    path = "toolchains/gcc-" .. opts.version .. ".tar.zst",
    dest = envy.path.join(tmp_dir, "gcc.tar.zst"),
  }))
  envy.commit_fetch({ filename = "gcc.tar.zst", sha256 = hashes[opts.version] })
end
```

And a spec whose `INSTALL` invokes a companion tool needs `needed_by = "install"`.

## Valid values

| Value | The dependent's phase that waits |
| --- | --- |
| `check` | Cache lookup |
| `import` | Depot lookup |
| `fetch` | [FETCH](../specs/fetch.md) |
| `stage` | [STAGE](../specs/stage.md) |
| `build` | [BUILD](../specs/build.md), the default |
| `install` | [INSTALL](../specs/install.md) |

Anything else is rejected when the manifest or spec loads:
`'needed_by' must be one of: check, import, fetch, stage, build, install`.

## The default is `build`

Leaving `needed_by` off means `build`, which is right for the common case and
wrong in exactly one situation: a verb *earlier* than `BUILD` that uses the
dependency. Most often that is `FETCH`.

Getting it wrong is not a race, it is a clear error. `envy.product` and
`envy.package` check the gate before answering:

```
envy.product: product 'jf' needed_by 'build' but accessed during 'fetch'
```

So the failure mode is a message naming both phases, not a package that
mysteriously is not there yet.

## What "ready" means

The dependency is **fully complete**, through its own `SETUP` pairs, before the
gated phase of the dependent starts. Not merely fetched, and not merely
installed. If a dependency's setup pair installs a system library, that has
happened too.

Phases of the dependent that are not gated run concurrently with the dependency's
own work. That is the whole point of attaching a phase rather than a boolean.

## Where it can appear

On a spec's `DEPENDENCIES` entries, and on manifest
[package entries](/concepts/projects#package-entries), including inside a
`weak` fallback's parent entry. A `weak` fallback itself must not carry
`needed_by`, since it inherits the edge from the reference that selected it.

## The one thing `needed_by` cannot do

It cannot gate the acquisition of the dependent's own spec. Every phase in the
table above happens after envy has the spec in hand, because the spec is what
declares them.

For "this tool must be installed before that spec can even be fetched", see
[Fetch Dependencies](./fetch-dependencies.md), which is a different mechanism for
that reason.

## Seeing what waited

`--verbose` narrates each package's decisions, including what it blocked on.
`--trace` records the machinery, and a `dependency_added` event carries the
`needed_by` phase for every edge:

```bash
envy --trace=file:/tmp/sync.jsonl sync
```

See [Logging & Tracing](../../reference/observability.md).

## See also

- [Declaring Dependencies](./declaring.md) for the four kinds of edge.
- [The Package Lifecycle](../specs/lifecycle.md) for what each phase does.
- [Resolution](./resolution.md) for how the graph settles around these edges.
