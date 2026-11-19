#!/usr/bin/env python3
"""The PhoneBox Controls page: one row of keys, and the panel of the key you tap opens below it.

Usage: controls-toggle.py wifi|bt|spk|mic   -> open that panel (or close it when it is already open)
       controls-toggle.py set-output NAME   -> switch the Mac's speaker, keep the Speaker panel open
       controls-toggle.py set-input NAME    -> switch the Mac's microphone, keep the Microphone panel open
       controls-toggle.py set-mic LEVEL     -> set the microphone level (0-100), keep the Microphone panel open

Only one panel is open at a time. The open panel's key shows a dot and the theme's highlight colour; so do the
speaker, microphone and level in use. Speaker and microphone lists are rebuilt from the Mac every time
(Bluetooth devices come and go). The Wi-Fi and Bluetooth keys (wf-*, bt-*) are created by setup.py.
"""
import os
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

BASE = os.environ.get("PHONEBOX_URL", "http://127.0.0.1:8765")
SWITCH_AUDIO = "/opt/homebrew/bin/SwitchAudioSource"
SELF = str(Path(__file__).resolve())
DOT = "● "
MAX_DEVICES = 6
MIC_LEVELS = [0, 25, 50, 75, 100]
OPENERS = {  # panel -> (key id, label)
    "wifi": ("open-wifi", "Wi-Fi"),
    "bt": ("open-bt", "Bluetooth"),
    "spk": ("open-spk", "Speaker"),
    "mic": ("open-mic", "Microphone"),
}
TOP_KEYS = ["open-wifi", "open-bt", "open-spk", "open-mic", "theme", "rotate"]


def run(*cmd):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=10).stdout.strip()


def audio(*args):
    return run(SWITCH_AUDIO, *args)


def mic_level():
    try:
        return int(run("/usr/bin/osascript", "-e", "input volume of (get volume settings)"))
    except ValueError:
        return None


def keys_widget(wid, x, y, w, h, ids, columns=1):
    return {"id": wid, "type": "shortcuts", "x": x, "y": y, "w": w, "h": h, "options": {"columns": columns, "ids": ids}}


def halves(wid, y, h, ids, columns=1):
    """The ids in two side-by-side halves: one row in landscape, stacked (full screen) in portrait."""
    mid = (len(ids) + 1) // 2
    return [keys_widget(wid, 0, y, 6, h, ids[:mid], columns), keys_widget(wid + "-2", 6, y, 6, h, ids[mid:], columns)]


def colours(cfg):
    by_id = {s.get("id"): s for s in cfg.get("shortcuts", [])}
    plain = by_id.get("terminal", {}).get("color", "#1C1C1C")   # the theme's normal key colour
    strong = by_id.get("lock", {}).get("color", "#FFFFFF")      # the theme's highlight colour
    soft = by_id.get("theme", {}).get("color", "#3A3A3A")       # the theme's colour for panel keys
    return plain, strong, soft


def numbered(cfg, prefix):
    ids = [s["id"] for s in cfg.get("shortcuts", []) if s.get("id", "").startswith(prefix)]
    return sorted(ids, key=lambda i: int(i[len(prefix):]) if i[len(prefix):].isdigit() else 999)


def device_keys(cfg, prefix, kind, setter):
    """One key per current speaker (kind "output") or microphone ("input"); returns their ids."""
    names = [n for n in audio("-a", "-t", kind).splitlines() if n.strip()][:MAX_DEVICES]
    current = audio("-c", "-t", kind)
    plain, strong, _ = colours(cfg)
    cfg["shortcuts"] = [s for s in cfg["shortcuts"] if not s.get("id", "").startswith(prefix)]
    ids = []
    for i, name in enumerate(names, 1):
        on = name == current
        sid = "%s%d" % (prefix, i)
        cfg["shortcuts"].append({"id": sid, "label": (DOT if on else "") + name,
                                 "icon": "♪" if kind == "output" else "◉",
                                 "color": strong if on else plain, "cmd": "/usr/bin/python3",
                                 "args": '-I "%s" %s "%s"' % (SELF, setter, name.replace('"', "")), "toggle": False})
        ids.append(sid)
    return ids


def mic_level_keys(cfg):
    level = mic_level()
    nearest = min(MIC_LEVELS, key=lambda x: abs(x - level)) if level is not None else None
    plain, strong, _ = colours(cfg)
    cfg["shortcuts"] = [s for s in cfg["shortcuts"] if not s.get("id", "").startswith("miclvl-")]
    ids = []
    for v in MIC_LEVELS:
        on = v == nearest
        sid = "miclvl-%d" % v
        cfg["shortcuts"].append({"id": sid, "label": (DOT if on else "") + ("Off" if v == 0 else "%d%%" % v),
                                 "icon": "○" if v == 0 else "◉", "color": strong if on else plain,
                                 "cmd": "/usr/bin/python3", "args": '-I "%s" set-mic %d' % (SELF, v), "toggle": False})
        ids.append(sid)
    return ids


def layout(cfg, panel):
    """Widgets for the Controls page with this panel open (None = all closed); also marks the open key."""
    plain, strong, soft = colours(cfg)
    by_id = {s.get("id"): s for s in cfg["shortcuts"]}
    for name, (sid, label) in OPENERS.items():
        if sid in by_id:
            by_id[sid]["label"] = (DOT if name == panel else "") + label
            by_id[sid]["color"] = strong if name == panel else soft
    if panel is None:  # big tiles: 3 x 2 in landscape, a full-height list in portrait
        return halves("cc-keys", 0, 6, TOP_KEYS)
    top = halves("cc-keys", 0, 2, TOP_KEYS, columns=3)  # one row of six in landscape
    if panel == "wifi":
        return top + halves("cc-wifi", 2, 4, numbered(cfg, "wf-") + ["wifi"])
    if panel == "bt":
        return top + halves("cc-bt", 2, 4, numbered(cfg, "bt-") + ["bluetooth"])
    if panel == "spk":
        return top + [{"id": "cc-volume", "type": "volume", "x": 0, "y": 2, "w": 6, "h": 4},
                      keys_widget("cc-spk", 6, 2, 6, 4, device_keys(cfg, "out-", "output", "set-output"))]
    if panel == "mic":
        return top + [keys_widget("cc-miclvl", 0, 2, 6, 4, mic_level_keys(cfg), columns=3),
                      keys_widget("cc-mic", 6, 2, 6, 4, device_keys(cfg, "in-", "input", "set-input"))]
    raise ValueError(panel)


def open_panel(page):
    for name in OPENERS:
        if any(w.get("id") == "cc-" + name for w in page.get("widgets", [])):
            return name
    return None


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    arg = sys.argv[2] if len(sys.argv) > 2 else None
    keep = {"set-output": "spk", "set-input": "mic", "set-mic": "mic"}
    if cmd in keep:
        if arg is None:
            sys.exit("missing value")
        if cmd == "set-output":
            audio("-t", "output", "-s", arg)
        elif cmd == "set-input":
            audio("-t", "input", "-s", arg)
        else:
            run("/usr/bin/osascript", "-e", "set volume input volume %d" % max(0, min(100, int(arg))))
    elif cmd not in OPENERS and cmd != "close":
        sys.exit(__doc__)
    with urllib.request.urlopen(BASE + "/api/settings", timeout=5) as r:
        version = r.headers.get("X-Config-Version")
        cfg = json.load(r)
    page = next(p for p in cfg["pages"] if p.get("id") == "controls")
    if cmd in keep:
        panel = keep[cmd]
    elif cmd == "close":
        panel = None
    else:
        panel = None if open_panel(page) == cmd else cmd
    page["widgets"] = layout(cfg, panel)
    headers = {"Content-Type": "application/json"}
    if version:
        headers["X-Config-Version"] = version
    req = urllib.request.Request(BASE + "/api/settings", data=json.dumps(cfg).encode(), headers=headers, method="PUT")
    urllib.request.urlopen(req, timeout=5).read()
    urllib.request.urlopen(urllib.request.Request(BASE + "/api/refresh", data=b"", method="POST"), timeout=5).read()


if __name__ == "__main__":
    main()
