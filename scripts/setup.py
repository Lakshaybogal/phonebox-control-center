#!/usr/bin/env python3
"""Build the control center into a running PhoneBox agent (http://127.0.0.1:8765).

Usage: setup.py [--wifi N] [--bt N] [--no-home] [--no-ai] [--no-media] [--theme mono-black]

Reads this Mac's saved Wi-Fi networks and paired Bluetooth devices, then adds through PhoneBox's own settings API:
  - a Controls page (Wi-Fi, Bluetooth, Speaker, Microphone, Theme, Rotate) with panels that open in place,
  - a Media page that only shows while something is playing or paused (needs media-watch running),
  - a monochrome Claude quota card on the AI page,
  - monochrome CPU / memory / network tiles and a Mac battery tile on the Home page,
  - no automatic return to Home, auto rotation on, and the chosen theme.
It keeps your other pages and shortcuts. Run it again any time (for example after pairing a new device).
A copy of the previous settings is saved next to PhoneBox's config.json first.
"""
import os
import argparse
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

BASE = os.environ.get("PHONEBOX_URL", "http://127.0.0.1:8765")
HERE = Path(__file__).resolve().parent
PY = "/usr/bin/python3"
NETWORKSETUP = "/usr/sbin/networksetup"
BLUEUTIL = "/opt/homebrew/bin/blueutil"
CONFIG = Path.home() / "Library/Application Support/PhoneBox/config.json"
CONTROL_IDS = ("open-", "wf-", "bt-", "out-", "in-", "miclvl-")
CONTROL_KEYS = {"wifi", "bluetooth", "theme", "rotate", "media-page"}


def api(path, data=None, method="GET", version=None):
    headers = {"Content-Type": "application/json"}
    if version:
        headers["X-Config-Version"] = version
    req = urllib.request.Request(BASE + path, data=None if data is None else json.dumps(data).encode(),
                                 headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.headers.get("X-Config-Version"), json.load(r)


def run(*cmd):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=20).stdout


def script(name, *args):
    return '-I "%s"%s' % (HERE / name, "".join(" " + a for a in args))


def key(sid, label, icon, cmd, args, toggle=False, off_cmd=None, off_args=None):
    k = {"id": sid, "label": label, "icon": icon, "color": "#1C1C1C", "cmd": cmd, "args": args, "toggle": toggle}
    if toggle:
        k.update(offCmd=off_cmd, offArgs=off_args)
    return k


def wifi_interface():
    m = re.search(r"Hardware Port: Wi-Fi\s*\nDevice: (\S+)", run(NETWORKSETUP, "-listallhardwareports"))
    return m.group(1) if m else "en0"


def wifi_keys(n):
    iface = wifi_interface()
    lines = run(NETWORKSETUP, "-listpreferredwirelessnetworks", iface).splitlines()[1:]
    names = [l.strip() for l in lines if l.strip()][:n]
    keys = [key("wf-%d" % i, name, "≋", NETWORKSETUP, '-setairportnetwork %s "%s"' % (iface, name.replace('"', "")))
            for i, name in enumerate(names, 1)]
    keys.append(key("wifi", "Wi-Fi On/Off", "⏻", NETWORKSETUP, "-setairportpower %s on" % iface, True,
                    NETWORKSETUP, "-setairportpower %s off" % iface))
    return keys, names


def bt_keys(n):
    try:
        devices = json.loads(run(BLUEUTIL, "--paired", "--format", "json") or "[]")[:n]
    except (FileNotFoundError, json.JSONDecodeError):
        devices = []
    keys = [key("bt-%d" % i, d.get("name") or d["address"], "♪", BLUEUTIL, "--power 1 --connect " + d["address"], True,
                BLUEUTIL, "--disconnect " + d["address"]) for i, d in enumerate(devices, 1)]
    keys.append(key("bluetooth", "Bluetooth On/Off", "⏻", BLUEUTIL, "--power 1", True, BLUEUTIL, "--power 0"))
    return keys, [d.get("name") for d in devices]


def html_widget(wid, x, y, w, h, file, metric=None):
    html = (HERE / file).read_text()
    opts = {"html": html.replace("__METRIC__", metric) if metric else html, "transparent": False}
    if metric:
        opts["_metric"] = metric
    return {"id": wid, "type": "html", "x": x, "y": y, "w": w, "h": h, "options": opts}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--wifi", type=int, default=5, help="saved Wi-Fi networks to show (default 5)")
    ap.add_argument("--bt", type=int, default=5, help="paired Bluetooth devices to show (default 5)")
    ap.add_argument("--no-home", action="store_true", help="leave the Home page as it is")
    ap.add_argument("--no-ai", action="store_true", help="leave the AI page as it is")
    ap.add_argument("--no-media", action="store_true", help="do not add the Media page")
    ap.add_argument("--theme", default="mono-black", help="mono-black, mono-graphite, mono-soft or mono-red")
    a = ap.parse_args()

    try:
        version, cfg = api("/api/settings")
    except Exception as e:
        sys.exit("PhoneBox is not answering on %s (%s). Start PhoneBox first." % (BASE, e))
    if CONFIG.exists() and "PHONEBOX_URL" not in os.environ:
        backup = CONFIG.with_name("config.json.before-control-center-%d" % int(time.time()))
        shutil.copy2(CONFIG, backup)
        print("backup:", backup)

    wf, wf_names = wifi_keys(a.wifi)
    bt, bt_names = bt_keys(a.bt)
    print("Wi-Fi networks:", ", ".join(wf_names) or "none found")
    print("Bluetooth devices:", ", ".join(n or "?" for n in bt_names) or "none found")

    new_keys = wf + bt + [
        key("open-wifi", "Wi-Fi", "≋", PY, script("controls-toggle.py", "wifi")),
        key("open-bt", "Bluetooth", "ᛒ", PY, script("controls-toggle.py", "bt")),
        key("open-spk", "Speaker", "♪", PY, script("controls-toggle.py", "spk")),
        key("open-mic", "Microphone", "◉", PY, script("controls-toggle.py", "mic")),
        key("theme", "Theme", "◐", PY, script("theme-cycle.py")),
        key("rotate", "Auto rotate", "↻", PY, script("orientation-cycle.py")),
        key("media-page", "Media page", "♫", PY, script("media-page.py", "on"), True, PY, script("media-page.py", "off")),
    ]
    ids = {k["id"] for k in new_keys}
    cfg["shortcuts"] = [s for s in cfg.get("shortcuts", []) if s.get("id") not in ids
                        and not s.get("id", "").startswith(CONTROL_IDS)] + new_keys

    pages = cfg.setdefault("pages", [])
    by_id = {p.get("id"): p for p in pages}
    controls = {"id": "controls", "title": "Controls", "icon": "◑", "enabled": True, "widgets": []}
    if "controls" in by_id:
        by_id["controls"].update(controls)
    else:
        home_at = next((i for i, p in enumerate(pages) if p.get("id") == "home"), -1)
        pages.insert(home_at + 1, controls)

    if not a.no_media:
        media = {"id": "media", "title": "Media", "icon": "♫", "enabled": False, "widgets": [
            {"id": "md-player", "type": "media", "x": 0, "y": 0, "w": 6, "h": 6},
            {"id": "md-seek", "type": "media-seek", "x": 6, "y": 0, "w": 6, "h": 2, "options": {"title": ""}},
            {"id": "md-modes", "type": "media-modes", "x": 6, "y": 2, "w": 6, "h": 2, "options": {"title": ""}},
            {"id": "md-volume", "type": "volume", "x": 6, "y": 4, "w": 6, "h": 2}]}
        if "media" in by_id:
            by_id["media"].update(media)
        else:
            pages.insert(2, media)

    if not a.no_ai:
        ai = by_id.get("ai")
        quota = html_widget("ai-quota", 0, 0, 6, 6, "claude-quota.html")
        if ai is None:
            pages.append({"id": "ai", "title": "AI", "icon": "◆", "enabled": True,
                          "widgets": [quota, {"id": "ai-sessions", "type": "sessions", "x": 6, "y": 0, "w": 6, "h": 6}]})
        else:
            ai["widgets"] = [quota] + [w for w in ai.get("widgets", []) if w.get("type") != "quotas" and w.get("id") != "ai-quota"]
            for w in ai["widgets"][1:]:
                if w.get("x", 0) < 6:
                    w.update(x=6, w=min(w.get("w", 6), 6))

    if not a.no_home and "home" in by_id:
        for i, w in enumerate(by_id["home"].get("widgets", [])):
            metric = (w.get("options") or {}).get("metric") if w.get("type") == "stat" else (w.get("options") or {}).get("_metric")
            if metric in ("cpu", "ram", "net"):
                by_id["home"]["widgets"][i] = html_widget(w["id"], w["x"], w["y"], w["w"], w["h"], "mono-stat.html", metric)
            elif metric == "gpu" or (w.get("type") == "push" and (w.get("options") or {}).get("key") == "mac-battery"):
                by_id["home"]["widgets"][i] = {"id": w["id"], "type": "push", "x": w["x"], "y": w["y"], "w": w["w"], "h": w["h"],
                                               "options": {"key": "mac-battery", "title": "Battery", "style": "big", "unit": "%"}}

    for p in pages:  # keep the control keys off a page that shows "all shortcuts"
        if p.get("id") == "controls":
            continue
        for w in p.get("widgets", []):
            if w.get("type") == "shortcuts" and not (w.get("options") or {}).get("ids"):
                w.setdefault("options", {})["ids"] = [s["id"] for s in cfg["shortcuts"]
                                                      if s["id"] not in CONTROL_KEYS and not s["id"].startswith(CONTROL_IDS)]

    d = cfg.setdefault("display", {})
    d["idleReturnSec"] = 0
    d["orientation"] = "auto"
    for p in pages:
        p.pop("idleSec", None)

    api("/api/settings", cfg, "PUT", version)
    subprocess.run([PY, "-I", str(HERE / "theme-cycle.py"), a.theme], check=True)
    subprocess.run([PY, "-I", str(HERE / "controls-toggle.py"), "close"], check=True)
    print("Done. Open the Controls page on the phone.")


if __name__ == "__main__":
    main()
