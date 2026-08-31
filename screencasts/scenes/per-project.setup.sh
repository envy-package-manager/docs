#!/usr/bin/env bash
# Two projects on one machine that need two different pythons, and a machine
# python that is neither. Both projects are already synced: the scene is about
# switching between them, not about installing them.
source "$(dirname "$0")/../lib/common.sh"

demo_reset
demo_hook

make_service() {
  demo_project "$DEMO_HOME/work/$1" <<LUA
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
  { spec = "envy.python@r1", bundle = "first-party",
    options = { version = "$2", release = "20260623", provide_python3 = true } },
}
LUA
}

make_service service-a 3.13.14
make_service service-b 3.14.6
