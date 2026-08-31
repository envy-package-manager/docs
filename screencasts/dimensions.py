#!/usr/bin/env python3
"""Write the rendered screencasts' pixel dimensions for the site to import.

The <Screencast> component needs each SVG's aspect ratio to reserve its box
before the image loads. Inside the landing page's <Tabs lazy>, a panel mounts
its image on first click, and with no reserved height everything below it jumps
up for a frame.

Generated rather than hand-maintained: a scene's cols/rows are a recording
decision, and a stale number here is a layout bug nothing would catch.

Usage: dimensions.py <svg-dir> <out.json>
"""

import json
import pathlib
import re
import sys


def main() -> int:
    src, dst = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])

    dims = {}
    for svg in sorted(src.glob("*.svg")):
        with svg.open() as f:
            head = f.read(400)
        m = re.match(r'<svg[^>]*\bwidth="([\d.]+)"[^>]*\bheight="([\d.]+)"', head)
        if not m:
            print(f"dimensions.py: no width/height in {svg}", file=sys.stderr)
            return 1
        dims[svg.stem] = [float(m.group(1)), float(m.group(2))]

    dst.write_text(json.dumps(dims, indent=2, sort_keys=True) + "\n")
    print(f"{dst}: {len(dims)} screencasts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
