#!/usr/bin/env bash
# Removes the PhoneBox Control Center add-on: background helpers and scripts.
# Your PhoneBox pages stay as they are; to get the old ones back, copy a
# config.json.before-control-center-* backup over PhoneBox's config.json while PhoneBox is stopped.
set -euo pipefail
for name in media-watch battery-watch; do
  plist="$HOME/Library/LaunchAgents/net.oxog.phonebox.$name.plist"
  if [ -f "$plist" ]; then launchctl unload "$plist" 2>/dev/null || true; rm -f "$plist"; echo "removed $name"; fi
done
rm -rf "$HOME/Library/Application Support/PhoneBox/control-center"
echo "Scripts removed. Backups of your old PhoneBox settings:"
ls -1 "$HOME/Library/Application Support/PhoneBox/" | grep before-control-center || echo "  (none)"
