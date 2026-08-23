---
sidebar_position: 5
title: Resolution
---

# Resolution

How the package graph settles. Everything here is observable behavior, either an
outcome you can see or an error message you can read.

## The graph is discovered

envy reads the manifest, fetches those specs, reads their `DEPENDENCIES`, fetches
*those* specs, and keeps going until nothing new appears. A spec three levels down
can introduce packages nobody named at the top.

Two things follow. Envy cannot know the full package set before it starts, so
progress output grows as specs load. And a question like "does this project
already have a Python?" cannot be answered early, which is why weak references
settle late.

## Weak reference outcomes

A weak or reference-only entry is a query. Once the picture is complete enough,
envy matches it against every package in the graph, using the same
[query matching](../../reference/cli/index.md#package-queries) the CLI uses.

| Matches | Outcome |
| --- | --- |
| Exactly one | That package is used, and the fallback if any is never built. |
| None, fallback present | The fallback is instantiated as a normal strong dependency. |
| None, no fallback | Error: `Reference '<query>' in spec '<spec>' was not found`. |
| Several | Error listing every candidate by canonical key. envy never guesses. |

The ambiguity error is worth seeing, because it names the exact packages that
collided:

```
Reference 'local.dupe' in spec 'local.consumer@v1' is ambiguous: local.dupe@v1, local.dupe@v2
```

The fix is to make the query more specific, or to stop declaring two packages
that both answer to it.

## Products

A product name is a project-wide registry entry, and the rules are strict on
purpose:

- **At most one provider per name.** Two specs providing `cmake` is an error
  naming both: `Product 'cmake' provided by multiple specs: acme.cmake@r0,
  envy.cmake@r0`. There are no priority rules, because a silent winner would be
  worse than a failure.
- **A constrained product must come from its named provider.** An entry that
  carries both `product` and `spec` pins the provider, and a mismatch is an error:
  `Product 'jf' in spec '<x>' must come from 'tools.jfrog-cli@r1', but provider
  is '<other>'`.
- **Options exist so a spec can decline a generic name.** This is how two Pythons
  coexist: only the entry that sets `provide_python3 = true` claims `python3`. See
  [Products](../specs/products.md).

## Platform filtering happens first

An entry whose `platforms` filter excludes the host is dropped before resolution,
so it contributes no node, no product, and no weak-reference candidate. That is
what makes a per-platform graph work without conditionals:

- A Windows-only helper and a Linux-only helper can both provide the same product
  name, because only one of them is ever in the graph.
- A weak reference that would be ambiguous on one platform can be unambiguous on
  another.
- A product that only some platforms ship is simply absent elsewhere, and
  `envy product <name>` reports it has no provider rather than resolving to
  nothing.

So the same manifest produces three different graphs on macOS, Linux, and
Windows, and each is validated on its own terms. See
[Platforms](../specs/platforms.md).

## De-duplication

An identical `(identity, options, platform)` anywhere in the graph is one package.
A manifest entry and three specs that all want `envy.cmake@r0` at version 4.4.0
produce one install, one cache entry, and one row of output.

Change one option and you have named a second package, which installs alongside
the first rather than replacing it.

## Cycles

Detected and reported, with the path:

- Strong cycles are caught as the graph grows:
  `Dependency cycle detected: a -> b`.
- A weak reference that resolves to something already depending on you is caught
  too: `Weak dependency cycle detected: <a> -> <b> (which already depends on
  <a>)`.
- Fetch-dependency cycles are checked separately, since they order spec
  acquisition rather than phases.

## Validation that happens along the way

- **Setup selections are checked against the spec that defines them.** An unknown
  pair name is an error, not a no-op.
- **Bundle redeclaration must agree.** Declaring the same bundle identity twice
  with different sources or refs is an error rather than a silent winner.
- **A spec must declare the identity it was fetched as.** A bundle promising
  `acme.cmake@r0` and a file declaring something else is an error.
- **Platform filters intersect.** An entry whose manifest `platforms` and spec
  `PLATFORMS` share nothing simply never instantiates, with no error. See
  [Platforms](../specs/platforms.md).

## Determinism

The same manifest, the same specs, and the same platform produce the same graph.
Nothing in resolution depends on timing, on network latency, or on the order
threads happen to finish.

Where an outcome would otherwise be scheduling-dependent, envy sorts before
reporting, so error messages naming two colliding providers name them in a stable
order. Repeated runs produce the same message, which matters when the message is
in a CI log.

## See also

- [Declaring Dependencies](./declaring.md) for the kinds of edge being resolved.
- [Phase Ordering](./ordering.md) for the `needed_by` attached to each.
- [The Cache](../cache.md) for what an identity plus options actually names.
