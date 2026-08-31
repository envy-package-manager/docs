#!/usr/bin/env bash
# No project and no manifest. envy is just on PATH, the way it would be after
# untarring a release, and the scene uses it as a download-and-unpack tool.
source "$(dirname "$0")/../lib/common.sh"

demo_reset
demo_hook

mkdir -p "$DEMO_HOME/.local/bin" "$DEMO_HOME/scratch"
cp "$(envy_tool)" "$DEMO_HOME/.local/bin/envy"
