#!/usr/bin/env python3
"""Show the Media page only while something plays.

Usage: media-page.py on    -> enable the Media page and switch the phone to it
       media-page.py off   -> hide the Media page again
Run by the "Media plays" rule through the media-page toggle shortcut.
"""
import os
import json
import sys
import time
import urllib.request

BASE = os.environ.get("PHONEBOX_URL", "http://127.0.0.1:8765")
PAGE = "media"


def call(path, data=None, method="POST", headers=None):
    req = urllib.request.Request(BASE + path, data=data, headers=headers or {}, method=method)
    return urllib.request.urlopen(req, timeout=5).read()


def main():
    want = sys.argv[1] if len(sys.argv) > 1 else ""
    if want not in ("on", "off"):
        sys.exit("usage: media-page.py on|off")
    with urllib.request.urlopen(BASE + "/api/settings", timeout=5) as r:
        version = r.headers.get("X-Config-Version")
        cfg = json.load(r)
    page = next((p for p in cfg["pages"] if p.get("id") == PAGE), None)
    if page is None:
        sys.exit("no media page")
    enabled = want == "on"
    if page.get("enabled", True) != enabled:
        page["enabled"] = enabled
        headers = {"Content-Type": "application/json"}
        if version:
            headers["X-Config-Version"] = version
        call("/api/settings", json.dumps(cfg).encode(), "PUT", headers)
        call("/api/refresh", b"")
    if enabled:
        time.sleep(1.5)  # let the phone load the page list before switching to it
        call("/api/goto/" + PAGE + "?countdown=0", b"")


if __name__ == "__main__":
    main()
