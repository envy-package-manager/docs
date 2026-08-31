#!/usr/bin/env python3
"""Type a scene into a real shell, so asciinema records a real session.

Run under `asciinema rec -c "python3 drive.py <scene>"`. This process owns a
second pty running zsh; everything the shell prints is forwarded to stdout,
which is the pty asciinema is recording. Keystrokes are written to the shell
one character at a time with jittered delays, so the capture looks typed
rather than pasted, and the shell echoes them itself.

The shell is real: the envy hook fires on `cd`, PATH is really rewritten, and a
missing tool really is a "command not found". Nothing in a scene is staged
output.

Scene syntax, one directive per line:

    !<key> <value>   scene setting, header only (see SETTINGS)
    !setup <cmd>     run before recording starts, off camera
    !teardown <cmd>  run after recording ends, off camera
    $ <cmd>          type it, press Enter, wait for the next prompt
    # <text>         type it as a shell comment: narration, on camera
    > <text>         type it, no Enter (pair with ^ or another >)
    ^ <key>          send a control key: c, d, enter, tab
    ~ <seconds>      hold still
    !clear           clear the screen without showing the command

Blank lines and lines starting with `--` are ignored.
"""

from __future__ import annotations

import argparse
import os
import pty
import random
import select
import shlex
import signal
import struct
import subprocess
import sys
import termios
import time
from dataclasses import dataclass, field
from pathlib import Path

# Scene settings and their defaults. Every one is overridable per scene with
# `!<key> <value>`; `record.sh` reads cols/rows back out to size asciinema's pty
# to match, so the two never disagree.
SETTINGS: dict[str, str] = {
    "cols": "98",
    "rows": "26",
    "home": "",           # HOME for the recorded shell; required
    "cwd": "",            # starting directory, relative to home unless absolute
    "wpm": "230",         # typing speed, words per minute (5 chars per word)
    "think": "0.45",      # pause before typing a command
    "settle": "0.7",      # pause after a command's output stops
    "outro": "1.6",       # pause on the final prompt before exiting
    "path": "",           # directories prepended to PATH, colon separated
    "hook": "1",          # source the envy shell hook
    "seed": "1989",       # typing jitter seed, so re-records stay comparable
}

# A no-op sequence the shell echoes nowhere: written to a private fd, never the
# pty, so prompt detection adds nothing to the recording.
READY = b"\x01"


@dataclass
class Scene:
    settings: dict[str, str] = field(default_factory=lambda: dict(SETTINGS))
    setup: list[str] = field(default_factory=list)
    teardown: list[str] = field(default_factory=list)
    steps: list[tuple[str, str]] = field(default_factory=list)

    def get(self, key: str) -> str:
        return self.settings[key]

    def num(self, key: str) -> float:
        return float(self.settings[key])


def parse_scene(path: Path) -> Scene:
    scene = Scene()
    for lineno, raw in enumerate(path.read_text().splitlines(), 1):
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("--"):
            continue

        verb, _, rest = line.partition(" ")
        rest = rest.strip()

        if verb == "!setup":
            scene.setup.append(rest)
        elif verb == "!teardown":
            scene.teardown.append(rest)
        elif verb == "!clear":
            scene.steps.append(("clear", ""))
        elif verb.startswith("!"):
            key = verb[1:]
            if key not in SETTINGS:
                raise SystemExit(f"{path}:{lineno}: unknown setting !{key}")
            if scene.steps:
                raise SystemExit(f"{path}:{lineno}: !{key} must precede the first step")
            scene.settings[key] = rest
        elif verb in ("$", "#", ">", "^", "~"):
            scene.steps.append((verb, rest))
        else:
            raise SystemExit(f"{path}:{lineno}: unknown directive {verb!r}")

    if not scene.get("home"):
        raise SystemExit(f"{path}: !home is required")
    return scene


class Typist:
    """Per-character delays with the shape of someone actually typing."""

    def __init__(self, wpm: float, rng: random.Random) -> None:
        self.base = 60.0 / (wpm * 5.0)
        self.rng = rng

    def delays(self, text: str) -> list[float]:
        out = []
        for i, ch in enumerate(text):
            d = self.base * self.rng.lognormvariate(0.0, 0.42)
            # The reach for a new word, and for the shifted characters that
            # show up in paths and flags, is the slow part of real typing.
            if i and text[i - 1] == " ":
                d *= 1.6
            elif ch in "-_/@.:\"'":
                d *= 1.35
            out.append(min(max(d, 0.012), 0.24))
        return out


class Session:
    """The recorded shell, plus the plumbing to type at it."""

    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.rng = random.Random(int(scene.get("seed")))
        self.typist = Typist(scene.num("wpm"), self.rng)
        self.out = sys.stdout.buffer

    # -- lifecycle ---------------------------------------------------------

    def start(self) -> None:
        scene = self.scene
        # Realpath, so zsh's %~ recognizes $PWD as $HOME. On macOS a demo home
        # under /tmp is really /private/tmp, and the prompt would spell it out.
        home = Path(os.path.realpath(Path(scene.get("home")).expanduser()))
        cwd = scene.get("cwd") or str(home)
        cwd = str(home / cwd) if not os.path.isabs(cwd) else cwd

        ready_r, ready_w = os.pipe()
        os.set_inheritable(ready_w, True)
        self.ready_r = ready_r

        self.pid, self.master = pty.fork()
        if self.pid == 0:
            os.dup2(ready_w, 9)
            os.set_inheritable(9, True)
            os.chdir(cwd)
            os.execvpe("zsh", ["zsh", "-f"], self._child_env(home))
            os._exit(127)

        os.close(ready_w)
        self._set_winsize(int(scene.get("cols")), int(scene.get("rows")))
        self._configure_shell(home)

    def _child_env(self, home: Path) -> dict[str, str]:
        # A fixed base PATH rather than the recording machine's: the shell in a
        # scene should see the tools a stock macOS or Linux box has and nothing
        # else, so `python3` means the system python and a missing tool is
        # really missing.
        path = "/usr/bin:/bin:/usr/sbin:/sbin"
        if extra := self.scene.get("path"):
            path = os.path.expanduser(extra.replace("$HOME", str(home))) + ":" + path

        env = {
            "HOME": str(home),
            "PATH": path,
            "TERM": "xterm-256color",
            "LANG": "en_US.UTF-8",
            "LC_ALL": "en_US.UTF-8",
            "SHELL": "/bin/zsh",
            "USER": os.environ.get("USER", "you"),
            "ENVY_CACHE_ROOT": str(home / ".cache" / "envy"),
            # A pager or an editor opening mid-scene would hang the recording.
            "PAGER": "cat",
            "GIT_PAGER": "cat",
            "COLUMNS": self.scene.get("cols"),
            "LINES": self.scene.get("rows"),
        }
        return env

    def _configure_shell(self, home: Path) -> None:
        """Install the prompt, the ready signal, and the envy hook, off camera."""
        hook = home / ".cache" / "envy" / "shell" / "hook.zsh"
        lines = [
            "setopt promptsubst interactivecomments",
            "unsetopt promptcr",
            # %~ so the recording shows ~/work/..., never a real home directory.
            "PROMPT='%F{244}%~%f %F{78}$%f '",
            "RPROMPT=''",
            "_demo_ready() { print -n $'\\x01' >&9 }",
            "precmd_functions+=(_demo_ready)",
            # The pty owns the size; inherited values would fight the recording.
            "unset LINES COLUMNS",
        ]
        if self.scene.get("hook") == "1":
            if not hook.exists():
                raise SystemExit(f"drive.py: no shell hook at {hook} (run envy once, or !hook 0)")
            lines.append(f"source {shlex.quote(str(hook))}")

        self._drain(0.3, mirror=False)
        for line in lines:
            os.write(self.master, line.encode() + b"\n")

        # These are all instant, and _demo_ready is only registered partway
        # through, so settle on quiet rather than counting prompts.
        self._settle(mirror=False)

        # Ctrl-L is zsh's clear-screen widget: it wipes the screen and redraws
        # the prompt. Mirrored, that is the recording's first frame.
        self.clear_screen()

    def _settle(self, quiet: float = 0.3, limit: float = 20.0, mirror: bool = True) -> None:
        """Wait until the shell has been silent for `quiet` seconds."""
        deadline = time.monotonic() + limit
        last = time.monotonic()
        while time.monotonic() < deadline:
            if self._pump(0.05, mirror):
                last = time.monotonic()
            elif time.monotonic() - last > quiet:
                return

    def clear_screen(self) -> None:
        os.write(self.master, b"\x0c")
        self._settle(0.2)

    def close(self) -> None:
        os.write(self.master, b"exit\n")
        self._drain(0.4, mirror=False)
        try:
            os.kill(self.pid, signal.SIGHUP)
        except ProcessLookupError:
            pass
        os.waitpid(self.pid, 0)

    # -- pty plumbing ------------------------------------------------------

    def _set_winsize(self, cols: int, rows: int) -> None:
        packed = struct.pack("HHHH", rows, cols, 0, 0)
        import fcntl

        fcntl.ioctl(self.master, termios.TIOCSWINSZ, packed)

    def _pump(self, timeout: float, mirror: bool = True) -> bool:
        """Move one chunk of shell output to stdout. True if the shell is ready."""
        rlist, _, _ = select.select([self.master, self.ready_r], [], [], timeout)
        ready = False
        if self.master in rlist:
            try:
                data = os.read(self.master, 65536)
            except OSError:
                data = b""
            if data and mirror:
                self.out.write(data)
                self.out.flush()
        if self.ready_r in rlist:
            os.read(self.ready_r, 4096)
            ready = True
        return ready

    def _drain(self, seconds: float, mirror: bool = True) -> None:
        end = time.monotonic() + seconds
        while (left := end - time.monotonic()) > 0:
            self._pump(min(left, 0.05), mirror)

    def _wait_ready(self, mirror: bool = True, timeout: float = 3600.0) -> None:
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if self._pump(0.05, mirror):
                # The prompt is written after the ready signal; let it land.
                self._drain(0.06, mirror)
                return
        raise SystemExit("drive.py: timed out waiting for a prompt")

    # -- typing ------------------------------------------------------------

    def type_text(self, text: str) -> None:
        for ch, delay in zip(text, self.typist.delays(text)):
            os.write(self.master, ch.encode())
            self._drain(delay)

    def submit(self) -> None:
        self._drain(self.rng.uniform(0.14, 0.30))
        os.write(self.master, b"\r")

    # -- steps -------------------------------------------------------------

    def play(self) -> None:
        keys = {"c": b"\x03", "d": b"\x04", "enter": b"\r", "tab": b"\t"}
        scene = self.scene

        for verb, arg in scene.steps:
            if verb == "~":
                self._drain(float(arg))
            elif verb == "$":
                self._drain(scene.num("think"))
                self.type_text(arg)
                self.submit()
                self._wait_ready()
                self._drain(scene.num("settle"))
            elif verb == "#":
                self._drain(scene.num("think"))
                self.type_text("# " + arg)
                self.submit()
                self._wait_ready()
            elif verb == ">":
                self._drain(scene.num("think"))
                self.type_text(arg)
            elif verb == "^":
                os.write(self.master, keys[arg.lower()])
                self._drain(0.35)
            elif verb == "clear":
                self.clear_screen()

        self._drain(scene.num("outro"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("scene", type=Path)
    ap.add_argument("--print-setting", metavar="KEY",
                    help="print one resolved setting and exit (used by record.sh)")
    ap.add_argument("--setup-only", action="store_true",
                    help="run the scene's !setup lines and exit")
    ap.add_argument("--no-setup", action="store_true",
                    help="skip the scene's !setup lines (record.sh ran them already)")
    ap.add_argument("--teardown-only", action="store_true",
                    help="run the scene's !teardown lines and exit")
    args = ap.parse_args()

    scene = parse_scene(args.scene)

    if args.print_setting:
        print(scene.get(args.print_setting))
        return 0

    if args.teardown_only:
        for cmd in scene.teardown:
            subprocess.run(cmd, shell=True, check=False)
        return 0

    # Setup is minutes of downloading and syncing. record.sh runs it before
    # asciinema starts, so it does not become dead air at the head of the cast.
    if not args.no_setup:
        for cmd in scene.setup:
            subprocess.run(cmd, shell=True, check=True)
    if args.setup_only:
        return 0

    session = Session(scene)
    session.start()
    try:
        session.play()
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
