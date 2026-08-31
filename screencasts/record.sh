#!/usr/bin/env bash
# Record one scene to casts/<name>.cast. Usage: ./record.sh hero
set -Eeuo pipefail
cd "$(dirname "$0")"

name="${1:?usage: record.sh <scene>}"
scene="scenes/$name.scene"
[[ -f "$scene" ]] || { echo "no such scene: $scene" >&2; exit 1; }

cols="$(python3 drive.py "$scene" --print-setting cols)"
rows="$(python3 drive.py "$scene" --print-setting rows)"

# Ahead of the recording: a scene's setup is minutes of downloading, and inside
# the recording it would be minutes of a blank screen.
python3 drive.py "$scene" --setup-only

mkdir -p casts
# asciicast-v2 rather than v3: agg reads both, svg-term-cli only reads v2.
asciinema rec \
  --headless --quiet --overwrite \
  --output-format asciicast-v2 \
  --window-size "${cols}x${rows}" \
  --title "envy: $name" \
  --command "python3 drive.py $scene --no-setup" \
  "casts/$name.cast"

python3 drive.py "$scene" --teardown-only

printf 'recorded casts/%s.cast (%sx%s, %s)\n' \
  "$name" "$cols" "$rows" "$(du -h "casts/$name.cast" | cut -f1)"
