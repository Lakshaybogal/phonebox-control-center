#!/usr/bin/env bash
# PhoneBox Control Center installer (macOS).
#   ./install.sh              install or update, then build the pages
#   ./install.sh --wifi 3     any setup.py option is passed through (see scripts/setup.py --help)
# Run it as yourself, not with sudo. Safe to run again.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
dest="$HOME/Library/Application Support/PhoneBox/control-center"
agents="$HOME/Library/LaunchAgents"

step() { printf '\n==> %s\n' "$1"; }
die() { printf '\nSetup stopped: %s\n' "$1" >&2; exit 1; }

[ "$(uname -s)" = Darwin ] || die "this add-on is for macOS."
[ "$(id -u)" != 0 ] || die "run it as yourself, not with sudo."

step "Checking PhoneBox"
if ! curl -fsS --max-time 3 http://127.0.0.1:8765/api/info >/dev/null; then
  die "PhoneBox is not running on this Mac. Install it first (https://github.com/ersinkoc/phonebox#quick-start), open its settings once, then run this again."
fi
echo "    OK  PhoneBox is running"

step "Installing helpers with Homebrew"
command -v brew >/dev/null || die "Homebrew is needed: https://brew.sh"
for f in blueutil switchaudio-osx nowplaying-cli; do
  if brew list --formula "$f" >/dev/null 2>&1; then echo "    OK  $f"; else brew install "$f" >/dev/null && echo "    OK  $f installed"; fi
done

step "Copying the scripts to $dest"
mkdir -p "$dest"
cp "$here"/scripts/*.py "$here"/scripts/*.html "$dest/"
echo "    OK"

step "Starting the background helpers"
mkdir -p "$agents"
for name in media-watch battery-watch; do
  plist="$agents/net.oxog.phonebox.$name.plist"
  launchctl unload "$plist" 2>/dev/null || true
  cat > "$plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>net.oxog.phonebox.$name</string>
  <key>ProgramArguments</key><array><string>/usr/bin/python3</string><string>-I</string><string>$dest/$name.py</string></array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardErrorPath</key><string>$dest/$name.log</string>
</dict></plist>
EOF
  launchctl load "$plist"
  echo "    OK  $name"
done

step "Building the pages"
/usr/bin/python3 -I "$dest/setup.py" "$@"

cat <<'EOF'

Installed. On the phone: open the Controls page (swipe right from Home).
  - Tap Wi-Fi, Bluetooth, Speaker or Microphone to open its panel; tap again to close.
  - Theme switches between the monochrome looks; Rotate switches auto rotation / locked.
  - macOS may ask once to allow Terminal / python3 to control "System Events" or audio: allow it.
Uninstall: ./uninstall.sh
EOF
