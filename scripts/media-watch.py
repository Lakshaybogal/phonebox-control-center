#!/usr/bin/env python3
"""Keep the PhoneBox Media page shown while any media is loaded on the Mac, playing or paused.

Runs in the background (launchd: net.oxog.phonebox.media-watch). Every 3 seconds it asks nowplaying-cli for the
current title; when media appears it runs media-page.py on, when it is gone for 10 seconds it runs media-page.py off.
"""
import subprocess
import sys
import time
from pathlib import Path

NOWPLAYING = "/opt/homebrew/bin/nowplaying-cli"
PAGE_SCRIPT = str(Path(__file__).with_name("media-page.py"))
POLL_SEC = 3
GONE_SEC = 10  # a track change briefly reports nothing; do not hide the page for that


def media_loaded():
    try:
        out = subprocess.run([NOWPLAYING, "get", "title"], capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:
        return None  # unknown: keep the current state
    return bool(out) and out.lower() != "null"


def set_page(on):
    r = subprocess.run([sys.executable, "-I", PAGE_SCRIPT, "on" if on else "off"], capture_output=True, text=True)
    return r.returncode == 0


def main():
    shown = None
    gone_since = None
    while True:
        loaded = media_loaded()
        if loaded is True:
            gone_since = None
            if shown is not True and set_page(True):
                shown = True
        elif loaded is False:
            gone_since = gone_since or time.monotonic()
            if shown is not False and time.monotonic() - gone_since >= GONE_SEC and set_page(False):
                shown = False
        time.sleep(POLL_SEC)


if __name__ == "__main__":
    main()
