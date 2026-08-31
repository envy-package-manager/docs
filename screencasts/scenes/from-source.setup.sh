#!/usr/bin/env bash
# A project whose one package has no prebuilt binary anywhere. Its spec says so
# by declaring the two tools it needs to make one, neither of which is on the
# machine either.
source "$(dirname "$0")/../lib/common.sh"

demo_reset
demo_hook

proj="$DEMO_HOME/work/codec"
mkdir -p "$proj/envy"
cp "$SCREENCASTS_DIR/lib/brotli-spec.lua" "$proj/envy/local.brotli@r0.lua"

demo_project "$proj" <<LUA
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
  { spec = "local.brotli@r0", source = envy.abspath("envy/local.brotli@r0.lua"),
    options = { version = "1.1.0" } },

  -- What local.brotli@r0's DEPENDENCIES resolve to. The spec asks for the
  -- products; the project decides which packages provide them.
  { spec = "envy.cmake@r0", bundle = "first-party", options = { version = "4.4.0" } },
  { spec = "envy.ninja@r0", bundle = "first-party", options = { version = "1.13.2" } },
}
LUA

demo_cold_cache
