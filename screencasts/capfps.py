#!/usr/bin/env python3
"""Cap the frame rate of an asciicast's bulk redraws.

envy's TUI repaints its progress bars about 30 times a second. Every repaint is
a recorded event, and svg-term emits the whole terminal for each one, so a
13-second download alone was most of a 340 KB SVG. Bucketing those repaints to
15fps halves the file and changes nothing anyone can see -- this is what agg's
--fps-cap does.

Keystroke echoes are exempt, which is the point of --min-bytes. The two kinds of
event are cleanly separable by size: a repaint of this terminal is 150 bytes of
escape sequences, an echoed keystroke is one or two. Merging those would turn
character-by-character typing into visible two-character jumps, which is the one
thing these recordings are careful about.

Content is never altered. Events in a bucket are concatenated in order and
emitted at the first one's timestamp, so the terminal state at every retained
frame is byte for byte what it would have been.

Usage: capfps.py <in.cast> <out.cast> [fps] [min-bytes]
"""

import json
import sys


def main() -> int:
    src, dst = sys.argv[1], sys.argv[2]
    fps = float(sys.argv[3]) if len(sys.argv) > 3 else 15.0
    min_bytes = int(sys.argv[4]) if len(sys.argv) > 4 else 32
    frame = 1.0 / fps

    with open(src) as f:
        lines = f.read().splitlines()

    header, events = lines[0], [json.loads(line) for line in lines[1:] if line.strip()]

    def bulk(event) -> bool:
        # Only output events are candidates at all. Input, resize and marker
        # events are discrete things that happened, and coalescing loses them.
        return event[1] == "o" and len(event[2]) >= min_bytes

    out, pending = [], None
    for event in events:
        time, kind, data = event
        if pending and bulk(event) and time - pending[0] < frame:
            pending[2] += data
            continue
        if pending:
            out.append(pending)
        pending = [time, kind, data] if bulk(event) else None
        if pending is None:
            out.append(event)

    if pending:
        out.append(pending)

    print(f"{len(events)} -> {len(out)} events, {fps:g}fps above {min_bytes}B",
          file=sys.stderr)

    with open(dst, "w") as f:
        f.write(header + "\n")
        for e in out:
            f.write(json.dumps(e, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
