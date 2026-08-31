#!/usr/bin/env bash
# Render casts/<name>.cast to an animated SVG under static/screencasts/.
# Usage: ./render.sh [name ...]   (no arguments renders every cast)
set -Eeuo pipefail
cd "$(dirname "$0")"

out="../static/screencasts"
mkdir -p "$out"

names=("$@")
if [[ ${#names[@]} -eq 0 ]]; then
  names=()
  for f in casts/*.cast; do names+=("$(basename "$f" .cast)"); done
fi

for name in "${names[@]}"; do
  cast="casts/$name.cast"
  [[ -f "$cast" ]] || { echo "no such cast: $cast" >&2; exit 1; }

  # One SVG frame is emitted per cast event, so envy's ~30Hz progress repaints
  # dominate the file size. capfps.py buckets those to 15fps and leaves
  # keystroke echoes alone; see its docstring.
  capped="$(mktemp -t "envy-cast-$name")"
  trap 'rm -f "$capped"' EXIT
  python3 capfps.py "$cast" "$capped" 15 32

  # svg-term-cli renders every cell as a <text> glyph run and animates the
  # whole strip with one @keyframes, so the result stays sharp at any size and
  # needs no JavaScript. It reads asciicast v2, which is why record.sh writes v2.
  npx --yes svg-term-cli@2.1.1 \
    --in "$capped" \
    --out "$out/$name.svg" \
    --window \
    --padding 16

  rm -f "$capped"
  printf '%-26s %s\n' "$out/$name.svg" "$(du -h "$out/$name.svg" | cut -f1)"
done

# Always regenerated from every SVG present, not just the ones rendered above,
# so a partial re-render cannot leave a stale entry behind.
python3 dimensions.py "$out" ../src/components/Screencast/dimensions.json
