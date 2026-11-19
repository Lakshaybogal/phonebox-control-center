#!/usr/bin/env python3
"""Rotation lock for the PhoneBox panel, like the phone's own: auto rotate (default) or locked.

Usage: orientation-cycle.py              -> switch between auto rotate and locked
       orientation-cycle.py auto|lock
Locked holds the panel horizontal (the layout the pages are designed for): the Mac cannot see which way the phone is
held, so it cannot lock "the current" orientation.
"""
import os
import json
import sys
import urllib.request

BASE = os.environ.get("PHONEBOX_URL", "http://127.0.0.1:8765")
LOCKED_TO = "landscape"
STATES = {
    "auto": {"orientation": "auto", "label": "Auto rotate", "icon": "↻"},
    "lock": {"orientation": LOCKED_TO, "label": "Rotation locked", "icon": "⊘"},
}


def main():
    with urllib.request.urlopen(BASE + "/api/settings", timeout=5) as r:
        version = r.headers.get("X-Config-Version")
        cfg = json.load(r)
    d = cfg.setdefault("display", {})
    if len(sys.argv) > 1:
        name = sys.argv[1]
        if name not in STATES:
            sys.exit("choose auto or lock")
    else:
        name = "lock" if d.get("orientation", "auto") == "auto" else "auto"
    st = STATES[name]
    d["orientation"] = st["orientation"]
    for s in cfg.get("shortcuts", []):
        if s.get("id") == "rotate":
            s["label"] = st["label"]
            s["icon"] = st["icon"]
    headers = {"Content-Type": "application/json"}
    if version:
        headers["X-Config-Version"] = version
    req = urllib.request.Request(BASE + "/api/settings", data=json.dumps(cfg).encode(), headers=headers, method="PUT")
    urllib.request.urlopen(req, timeout=5).read()
    urllib.request.urlopen(urllib.request.Request(BASE + "/api/refresh", data=b"", method="POST"), timeout=5).read()
    print(st["label"])


if __name__ == "__main__":
    main()
