# Prompt: set up PhoneBox Control Center with an AI assistant

Copy everything in the box below into Claude Code, or another coding assistant that can run commands on your Mac. Have your Android phone and its USB cable ready.

```text
Set up PhoneBox and the PhoneBox Control Center add-on on this Mac for me.

Background:
- PhoneBox (https://github.com/ersinkoc/phonebox) turns an Android phone into a desk panel for this Mac.
  Its agent runs here and serves settings at http://127.0.0.1:8765 (GET/PUT /api/settings).
- PhoneBox Control Center (https://github.com/Lakshaybogal/phonebox-control-center) adds a monochrome
  Controls page (Wi-Fi, Bluetooth, Speaker, Microphone, Theme, Rotate), a Media page, a Claude quota card
  and Home tiles through that API.

Rules:
- Read every script before you run it: the PhoneBox setup.sh, and install.sh and scripts/setup.py from the add-on.
- Ask me before anything that changes the system (installing, starting background services) and before
  touching my phone. Never use sudo unless a script asks for it and I agree.
- Never put PhoneBox's tokens (config.json "lan.token", "webhookToken") in any file, commit or message.
- If something fails, show me the exact error, explain it in plain words and suggest the next step.
  Don't work around a security prompt.

Steps:
1. Check: macOS on Apple Silicon (`uname -m` = arm64), Homebrew installed, /usr/bin/python3 present.
2. PhoneBox: if `curl -fsS http://127.0.0.1:8765/api/info` fails, download
   https://raw.githubusercontent.com/ersinkoc/phonebox/main/setup.sh to a temporary folder, read it,
   then run it with bash. It installs the agent, adb and the phone app.
3. Phone: walk me through Developer options > USB debugging, plugging in and allowing the computer.
   Then check `adb devices`. On Xiaomi / Redmi / POCO, "Install via USB" must be on too. If the install is
   still refused, copy the APK to the phone's Download folder with `adb push` and I'll install it by tapping it.
4. Optional Wi-Fi use: in the PhoneBox settings page (http://127.0.0.1:8765, General > Wi-Fi & Tailscale),
   I turn on "Let the phone connect without the USB cable" and pair with the QR code. Check that
   `lsof -nP -iTCP:8766 -sTCP:LISTEN` shows the agent and that the macOS firewall allows PhoneBoxAgent.
5. Add-on: clone https://github.com/Lakshaybogal/phonebox-control-center, read install.sh and
   scripts/setup.py, tell me what they'll do, then run ./install.sh. Ask me first if I want fewer Wi-Fi
   networks or Bluetooth devices (--wifi N, --bt N), or to keep my Home / AI pages as they are (--no-home, --no-ai).
6. Verify: GET /api/settings has a page with id "controls"; `launchctl list | grep phonebox` shows
   media-watch and battery-watch; `curl -s http://127.0.0.1:8765/api/push` contains "mac-battery".
   Run `/usr/bin/python3 -I "$HOME/Library/Application Support/PhoneBox/control-center/controls-toggle.py" spk`
   and again to close it, and check that the Controls page widgets change and change back.
7. Tell me what was installed, where the backup of my old PhoneBox settings is, and how to uninstall
   (./uninstall.sh). Warn me that Wi-Fi Off on the Controls page disconnects a phone that uses Wi-Fi.
```

## What it asks the assistant to do

- **Before it starts:** read the scripts first, and ask before installing anything or using your phone.
- **Steps:** install PhoneBox, get the phone connected (including Xiaomi's extra "Install via USB" setting), optionally set up Wi-Fi, install this add-on, and check that everything works.
- **What it never does:** use `sudo` without asking, or copy PhoneBox's tokens anywhere.
