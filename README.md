# PhoneBox Control Center

A monochrome control center for [PhoneBox](https://github.com/ersinkoc/phonebox), the open-source app that turns an old Android phone into a desk panel for your Mac.

It adds pages and keys to PhoneBox through its own settings API. It doesn't change PhoneBox itself, and your other pages stay as they are.

| What you get | What it does |
|---|---|
| **Controls page** | Six keys: Wi-Fi · Bluetooth · Speaker · Microphone · Theme · Rotate. Tap one and its panel opens in place. The open key shows ● and a highlight. Tap it again to close. |
| Wi-Fi panel | Your first 5 saved networks (tap to join) and Wi-Fi On/Off. |
| Bluetooth panel | Your first 5 paired devices (tap to connect, tap again to disconnect) and Bluetooth On/Off. |
| Speaker panel | Volume slider and mute, plus every speaker output. ● marks the one in use; tap another to switch. |
| Microphone panel | Mic level (Off, 25, 50, 75, 100%), plus every microphone, with ● on the one in use. |
| **Themes** | Mono Black, Mono Graphite, Mono Soft and Mono Red. One tap on Theme switches; keys, cards and the custom tiles all follow. |
| **Rotation** | Auto rotate by default. One tap locks it to horizontal. |
| **Media page** | Shows only while something is playing or paused on the Mac, and jumps there. Hides about 10 s after the media is gone. |
| **Claude quota card** | 5-hour and weekly limits as dot-matrix numbers with 24-dot bars. Marked HIGH over 80%. |
| **Home tiles** | Monochrome CPU, memory and network tiles, plus a Mac battery tile. |
| Calm panel | PhoneBox no longer jumps back to Home after 90 s of no touch. |

Every page is laid out for both orientations. In portrait the halves stack, so the screen stays full.

## Requirements

- An Apple Silicon Mac (the helpers are expected in `/opt/homebrew`) with [Homebrew](https://brew.sh).
- [PhoneBox](https://github.com/ersinkoc/phonebox) installed and running, with your phone paired over USB or Wi-Fi.
- Python 3 at `/usr/bin/python3`, which comes with the Xcode Command Line Tools.

The installer adds three small Homebrew tools: `blueutil` (Bluetooth), `switchaudio-osx` (speaker and microphone switching) and `nowplaying-cli` (media detection).

## Install

```bash
git clone https://github.com/Lakshaybogal/phonebox-control-center.git
cd phonebox-control-center
./install.sh
```

The installer:

1. checks that PhoneBox is running,
2. installs the three tools,
3. copies the scripts to `~/Library/Application Support/PhoneBox/control-center/`,
4. starts two background helpers at login: media detection and battery,
5. runs `setup.py`, which reads your Wi-Fi networks and Bluetooth devices and builds the pages.

`setup.py` saves a backup of your PhoneBox settings first, as `config.json.before-control-center-<time>`.

Options are passed through to `setup.py`:

```bash
./install.sh --wifi 3 --bt 4        # show fewer networks / devices
./install.sh --theme mono-graphite  # start with another theme
./install.sh --no-home --no-ai      # leave those pages alone
```

After pairing a new Bluetooth device or saving a new Wi-Fi network, run `./install.sh` again to update the panels.

## Use

- **Controls page:** swipe right from Home. Tap a key to open its panel, and tap it again to close it.
- **Theme:** each tap moves to the next look. The key's label names the one in use.
- **Rotate:** switches between ↻ Auto rotate and ⊘ Rotation locked.
- **Media:** play anything on the Mac (Spotify, Music, a browser video). The Media page appears, and it stays while paused.

The first time a key runs, macOS may ask whether python3 or Terminal may control audio or "System Events". Allow it.

## Be careful with

- **Wi-Fi Off, or joining another network, disconnects a phone that's connected to PhoneBox over Wi-Fi.** Keep USB connected, or use Tailscale, if you rely on Wi-Fi.
- **Bluetooth Off disconnects Bluetooth keyboards, mice and headphones.**
- **Joining a network can ask for its password** if macOS doesn't share the saved one with `networksetup`.

## How it works

PhoneBox stores its layout in `config.json` and serves it at `GET/PUT /api/settings` on `127.0.0.1:8765`, available only on the Mac itself. Each key runs one of these scripts:

| File | Job |
|---|---|
| `scripts/setup.py` | Builds the keys and pages once |
| `scripts/controls-toggle.py` | Rewrites the Controls page when a panel opens or closes, and switches speaker, microphone and mic level |
| `scripts/theme-cycle.py` | Applies a theme: PhoneBox theme, accent, card style, key colours and the custom tiles' colours |
| `scripts/orientation-cycle.py` | Auto rotate or locked |
| `scripts/media-page.py`, `scripts/media-watch.py` | Show and hide the Media page |
| `scripts/battery-watch.py` | Sends the Mac battery to PhoneBox as the pushed value `mac-battery` |
| `scripts/claude-quota.html`, `scripts/mono-stat.html` | Custom HTML widgets. Their `/*THEME*/` block is recoloured by the theme script. |

After a change, each script calls `POST /api/refresh`, so the phone redraws at once.

To add a theme, add an entry to `THEMES` in `scripts/theme-cycle.py` and run `./install.sh` again.

## Uninstall

```bash
./uninstall.sh
```

This removes the helpers and the scripts. Your PhoneBox pages stay. To restore your old pages, stop PhoneBox, copy a `config.json.before-control-center-*` backup over `config.json`, and start PhoneBox again.

## Set it up with an AI assistant

[`docs/AI_SETUP_PROMPT.md`](docs/AI_SETUP_PROMPT.md) has a prompt to paste into Claude Code or another coding assistant. It installs PhoneBox and this add-on on your Mac, step by step, asking before anything that changes the system.

## Credits and licence

Built on [PhoneBox](https://github.com/ersinkoc/phonebox) by ersinkoc (MIT). This add-on is not affiliated with PhoneBox. MIT licence: see [LICENSE](LICENSE).
