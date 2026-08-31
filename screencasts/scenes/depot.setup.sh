#!/usr/bin/env bash
# Same project as the from-source scene, plus a depot that already has the built
# brotli in it. The depot is a directory of .tar.zst files and one index, served
# by python's http.server: there is no depot software to install, and that is
# the point of the scene.
source "$(dirname "$0")/../lib/common.sh"

DEPOT_PORT=8181
DEPOT_URL="http://localhost:$DEPOT_PORT"
DEPOT_DIR="$DEMO_HOME/depot"

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

PACKAGE_DEPOTS = { "$DEPOT_URL/packages.txt" }

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

  { spec = "envy.cmake@r0", bundle = "first-party", options = { version = "4.4.0" } },
  { spec = "envy.ninja@r0", bundle = "first-party", options = { version = "1.13.2" } },
}
LUA

# Publish, the way the nightly job in the docs does it: export the cache as
# archives, merge the per-platform index into the published one, upload. Here
# "upload" is a directory a web server points at.
rm -rf "$DEPOT_DIR"
mkdir -p "$DEPOT_DIR"
( cd "$proj" && envy_run export --ignore-depot \
    --output-dir "$DEPOT_DIR" --depot-prefix "$DEPOT_URL/" \
    > "$DEPOT_DIR/darwin-arm64-packages.txt" )
( cd "$DEPOT_DIR" && envy_run merge-depot darwin-arm64-packages.txt > packages.txt )
rm -f "$DEPOT_DIR/darwin-arm64-packages.txt"

pkill -f "http.server $DEPOT_PORT" 2>/dev/null || true
( cd "$DEPOT_DIR" && nohup python3 -m http.server "$DEPOT_PORT" \
    >/dev/null 2>&1 & echo $! > "$DEPOT_DIR/.pid" )

# Wait for it, so the recording never races the server's first accept.
for _ in $(seq 40); do
  curl -fsS "$DEPOT_URL/packages.txt" >/dev/null 2>&1 && break
  sleep 0.25
done

demo_cold_cache
