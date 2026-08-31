# Screencasts

The animated terminal captures on the site. Every one is a real session against
a real machine: a scene script types into a real zsh, envy really downloads and
builds, and the elapsed times on screen are the ones the machine took. Nothing
here fakes output.

```
drive.py              types a scene into a real shell inside a pty
record.sh <name>      runs the scene under asciinema -> casts/<name>.cast
render.sh [name ...]  renders casts -> ../static/screencasts/<name>.svg
capfps.py             caps redraw frame rate, called by render.sh
scenes/<name>.scene       the scene: settings, commands, pauses
scenes/<name>.setup.sh    the machine state the scene starts from, off camera
lib/common.sh             shared setup helpers
lib/brotli-spec.lua       the demo spec two scenes build from source
casts/                    recorded sessions, committed
.tools/                   the pinned envy release, downloaded on demand
```

## Regenerating

```bash
./record.sh hero      # re-record one scene (needs network; takes a minute)
./render.sh hero      # re-render its SVG
./render.sh           # re-render every SVG from the committed casts
```

`render.sh` needs no network beyond `npx svg-term-cli` and touches nothing but
`static/screencasts/`, so a rendering tweak is a cheap change. `record.sh` is
the expensive half: it downloads toolchains and runs real builds.

Recording writes `casts/<name>.cast`, which is committed. That is deliberate:
re-rendering should not require re-running a five-minute build, and a diff of a
cast is a readable record of what changed in a session.

## Why these tools

`asciinema` records the terminal as text plus timings, not pixels, so a cast is
tens of kilobytes and stays diffable. `svg-term-cli` turns one into an animated
SVG: text rendered as `<text>`, the whole timeline as one CSS `@keyframes`. It
needs no JavaScript, works inside a plain `<img>`, and stays sharp at any zoom,
which a GIF of the same session does not. `agg` renders the same casts to GIF if
a GIF is ever needed.

Recording is asciicast **v2**, not v3: `agg` reads both, `svg-term-cli` reads
only v2.

`render.sh` pipes each cast through `capfps.py` first. svg-term emits one SVG
frame per cast event, and envy repaints its progress bars about 30 times a
second, so an uncapped 13-second download was most of a 340 KB file. Bucketing
repaints to 15fps brings that to 196 KB. Keystroke echoes are exempt by payload
size, so typing still advances one character at a time; the tool verifies that
the concatenated output is byte for byte unchanged.

## How a scene works

`drive.py` runs inside the pty asciinema is recording, and owns a second pty
running `zsh -f`. It writes keystrokes into that shell one character at a time
with jittered delays, and forwards everything the shell prints to its own
stdout. The shell echoes the keystrokes itself, so what the recording shows is
a real shell being typed at rather than a transcript being replayed.

That is what makes the envy [shell hook](../docs/getting-started/shell-integration.md)
demonstrable: `cd` really fires it, `PATH` really changes, and a missing tool
really is a "command not found".

Prompt detection uses a private pipe on fd 9, written by a `precmd` hook, so
nothing in the recorded stream exists to serve the recorder.

### Scene syntax

| Line | Meaning |
| --- | --- |
| `!<key> <value>` | A setting. Header only, before the first step. |
| `!setup <cmd>` | Run before recording starts, off camera. |
| `!teardown <cmd>` | Run after recording ends, off camera. |
| `$ <cmd>` | Type it, press Enter, wait for the next prompt. |
| `# <text>` | Type it as a shell comment: narration, on camera. |
| `> <text>` | Type it without pressing Enter. |
| `^ <key>` | Send a control key: `c`, `d`, `enter`, `tab`. |
| `~ <seconds>` | Hold still. |
| `!clear` | Clear the screen without showing a command doing it. |
| `-- <text>` | A comment in the scene file itself. |

`python3 drive.py scenes/hero.scene --print-setting cols` prints one resolved
setting; that is how `record.sh` sizes asciinema's pty to match the scene.

Settings and their defaults are the `SETTINGS` table at the top of `drive.py`.
The ones that matter per scene are `cols`, `rows`, `home`, `cwd`, `wpm`, and the
`think`/`settle`/`outro` pauses.

### Setup scripts

A scene's setup builds the machine state the recording claims to start from: a
project directory that looks freshly cloned, a cold or warm cache, a depot with
artifacts already in it. It runs before asciinema starts, because otherwise a
two-minute download would be two minutes of blank screen at the head of the SVG.

Setup runs against a throwaway `$HOME` under `/tmp`, so the recorded prompt is
always `~/work/<project>` and no path off the recording machine appears. It uses
the pinned envy release from `.tools/`, never a local build, so what the
recordings show is what a reader would get.

`demo_cold_cache` empties the cache directories rather than removing them, for
the same reason. envy prints a one-time "caching packages in `<path>`" notice
when `<root>/packages` is missing, and the path it would name here is this
machine's throwaway `/tmp` tree. An empty `packages/` is still a cold cache, so
the recordings stay honest without putting that path on screen. A reader running
these steps on a machine that has never run envy will see the notice; nothing
else differs.

## Pinned versions

`lib/common.sh` pins the envy release the demo projects use and the
`package-specs` commit their bundles name. Bump them together, then re-record.

Scene widths differ on purpose: `depot` is 120 columns because a depot index
line is a sha256 and a URL, and the rest are 88 to 96. The site renders them all
at container width.
