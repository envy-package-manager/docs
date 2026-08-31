#!/usr/bin/env bash
# The hero scene starts from a machine with no cmake and a project that was just
# cloned: envy.lua and bin/ are committed, and nothing is in the cache.
source "$(dirname "$0")/../lib/common.sh"

demo_reset
demo_hook

demo_project "$DEMO_HOME/work/blinky" <<LUA
-- @envy version "$ENVY_VERSION"
-- @envy schema "1"
-- @envy bin "bin"
-- @envy deploy "true"
-- @envy root "true"

BUNDLES = {
  ["first-party"] = {
    identity = "envy.package-specs@r3",
    source = "$SPECS_REPO",
    ref = "$SPECS_REF",
  },
}

PACKAGES = {
  { spec = "envy.cmake@r0", bundle = "first-party", options = { version = "4.4.0" } },
}
LUA

demo_cold_cache
