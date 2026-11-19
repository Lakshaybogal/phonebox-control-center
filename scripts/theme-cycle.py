#!/usr/bin/env python3
"""Switch the PhoneBox panel look.

Usage: theme-cycle.py            -> next theme
       theme-cycle.py <name>     -> that theme (mono-black, mono-graphite, mono-soft, mono-red)
The Theme key's label shows the theme in use.
"""
import os
import json
import sys
import re
import urllib.request
from pathlib import Path

BASE = os.environ.get("PHONEBOX_URL", "http://127.0.0.1:8765")
STATE = Path(__file__).with_name("theme-current.txt")
QUOTA_HTML = Path(__file__).with_name("claude-quota.html")
QUOTA_WIDGET = "ai-quota"
FONTS = {"mono": 'ui-monospace,"Roboto Mono",Menlo,monospace', "sans": 'Roboto,"Segoe UI",system-ui,sans-serif'}


def recolour(html, q):
    """html with this theme's colours in its /*THEME*/ block."""
    css = ":root{--fg:%s;--dim:%s;--muted:%s;--font:%s}" % (q["fg"], q["dim"], q["muted"], FONTS[q["font"]])
    return re.sub(r"/\*THEME\*/.*?/\*END\*/", lambda m: "/*THEME*/" + css + "/*END*/", html, count=1, flags=re.S)


def quota_html(q):
    return recolour(QUOTA_HTML.read_text(), q)

THEMES = {
    "mono-black": {
        "label": "Mono Black",
        "display": {"theme": "amoled", "accent": "#FFFFFF"},
        "appearance": {"style": "cards", "radius": 22, "gap": 8, "padding": 14, "pagePadding": 12,
                       "border": True, "shadow": False, "font": "mono"},
        "key": "#1C1C1C", "strong": "#FFFFFF", "soft": "#3A3A3A",
        "quota": {"fg": "#FFFFFF", "dim": "#2A2A2A", "muted": "#8A8A8A", "font": "mono"},
    },
    "mono-graphite": {
        "label": "Mono Graphite",
        "display": {"theme": "graphite", "accent": "#E5E5E5"},
        "appearance": {"style": "flat", "radius": 16, "gap": 10, "padding": 14, "pagePadding": 12,
                       "border": False, "shadow": False, "font": "mono"},
        "key": "#3A3A3A", "strong": "#E5E5E5", "soft": "#525252",
        "quota": {"fg": "#E5E5E5", "dim": "#4A4A4A", "muted": "#9A9A9A", "font": "mono"},
    },
    "mono-soft": {
        "label": "Mono Soft",
        "display": {"theme": "amoled", "accent": "#A3A3A3"},
        "appearance": {"style": "borderless", "radius": 28, "gap": 12, "padding": 16, "pagePadding": 14,
                       "border": False, "shadow": False, "font": "sans"},
        "key": "#262626", "strong": "#A3A3A3", "soft": "#333333",
        "quota": {"fg": "#D4D4D4", "dim": "#2E2E2E", "muted": "#7A7A7A", "font": "sans"},
    },
    "mono-red": {
        "label": "Mono Red",
        "display": {"theme": "amoled", "accent": "#D71921"},
        "appearance": {"style": "cards", "radius": 22, "gap": 8, "padding": 14, "pagePadding": 12,
                       "border": True, "shadow": False, "font": "mono"},
        "key": "#262626", "strong": "#D71921", "soft": "#3A3A3A",
        "quota": {"fg": "#D71921", "dim": "#2A2A2A", "muted": "#8A8A8A", "font": "mono"},
    },
}
ORDER = list(THEMES)
STRONG = {"lock"}                               # always highlighted (locks the Mac)
SOFT = {"open-wifi", "open-bt", "open-spk", "open-mic", "theme", "rotate"}        # keys that open something on the panel


def main():
    with urllib.request.urlopen(BASE + "/api/settings", timeout=5) as r:
        version = r.headers.get("X-Config-Version")
        cfg = json.load(r)
    current = STATE.read_text().strip() if STATE.exists() else ""
    if len(sys.argv) > 1:
        name = sys.argv[1]
        if name not in THEMES:
            sys.exit("unknown theme; choose one of: " + ", ".join(ORDER))
    else:
        name = ORDER[(ORDER.index(current) + 1) % len(ORDER)] if current in ORDER else ORDER[0]
    t = THEMES[name]
    d = cfg.setdefault("display", {})
    d.update(t["display"])
    d["artTint"] = False
    d["appearance"] = dict(t["appearance"])
    for s in cfg.get("shortcuts", []):
        sid = s.get("id", "")
        active = str(s.get("label", "")).startswith("\u25CF")  # open panel / device in use
        s["color"] = t["strong"] if sid in STRONG or active else t["soft"] if sid in SOFT else t["key"]
        if sid == "theme":
            s["label"] = t["label"]
    for page in cfg.get("pages", []):
        for w in page.get("widgets", []):
            if w.get("id") == QUOTA_WIDGET and QUOTA_HTML.exists():
                w.setdefault("options", {})["html"] = quota_html(t["quota"])
            elif w.get("type") == "html" and "/*THEME*/" in w.get("options", {}).get("html", ""):
                w["options"]["html"] = recolour(w["options"]["html"], t["quota"])  # mono stat tiles
    headers = {"Content-Type": "application/json"}
    if version:
        headers["X-Config-Version"] = version
    req = urllib.request.Request(BASE + "/api/settings", data=json.dumps(cfg).encode(), headers=headers, method="PUT")
    urllib.request.urlopen(req, timeout=5).read()
    urllib.request.urlopen(urllib.request.Request(BASE + "/api/refresh", data=b"", method="POST"), timeout=5).read()
    STATE.write_text(name)
    print(t["label"])


if __name__ == "__main__":
    main()
