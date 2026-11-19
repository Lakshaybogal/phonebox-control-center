#!/usr/bin/env python3
"""Send the Mac's battery to PhoneBox every 30 seconds as the pushed value "mac-battery".

The Home page shows it in a "push" widget (key mac-battery). Runs in the background
(launchd: net.oxog.phonebox.battery-watch).
"""
import os
import json
import re
import subprocess
import time
import urllib.request

BASE = os.environ.get("PHONEBOX_URL", "http://127.0.0.1:8765")
KEY = "mac-battery"
POLL_SEC = 30


def battery():
    out = subprocess.run(["/usr/bin/pmset", "-g", "batt"], capture_output=True, text=True, timeout=10).stdout
    m = re.search(r"(\d+)%;\s*([^;]+);\s*(\S+)?", out)
    if not m:
        return None
    pct, state, left = int(m.group(1)), m.group(2).strip(), (m.group(3) or "")
    on_ac = "AC Power" in out
    if state == "charged" or (on_ac and state != "charging"):
        sub = "Plugged in · full" if pct >= 100 else "Plugged in"
    elif state == "charging":
        sub = "Charging" + (" · %s to full" % left if re.match(r"\d+:\d\d", left) and left != "0:00" else "")
    else:
        sub = "On battery" + (" · %s left" % left if re.match(r"\d+:\d\d", left) and left != "0:00" else "")
    return {"value": pct, "unit": "%", "title": "Mac battery", "sub": sub}


def push(data):
    req = urllib.request.Request(BASE + "/api/push/" + KEY, data=json.dumps(data).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    urllib.request.urlopen(req, timeout=5).read()


def main():
    last = None
    while True:
        try:
            data = battery()
            if data and data != last:
                push(data)
                last = data
        except Exception:
            last = None  # PhoneBox restarting: send again next time
        time.sleep(POLL_SEC)


if __name__ == "__main__":
    main()
