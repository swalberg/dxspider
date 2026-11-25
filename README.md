# DXSpider Filters

A desktop script library for configuring a DXSpider node from Windows, macOS, or Linux.

## Run

On 64-bit Windows, download the versioned executable from the repository’s **Releases** page and double-click it. For example, release `v1.0.0` provides `DXSpider-Filters-v1.0.0-Windows-x64.exe`. The executable includes Python, Tk, and the starter scripts.

### Run from source

Install Python 3.10 or newer with Tk. Run the commands below from this repository's directory.

#### Windows

If running from source instead of using the bundled executable, install Python with Tk support, then run `python dxspider.py`.

#### macOS

Use a current Python with its own Tk installation. Apple's system/Xcode Python can load deprecated Tk 8.5, which may show blank windows or invisible widgets on newer macOS versions, including Tahoe.

With [Homebrew](https://brew.sh/), install Python and its matching Tk package:

```sh
brew install python@3.14 python-tk@3.14
"$(brew --prefix python@3.14)/bin/python3.14" -m tkinter
```

The second command opens a small Tk test window. Check that its buttons are visible, close it, then launch the app:

```sh
"$(brew --prefix python@3.14)/bin/python3.14" dxspider.py
```

The explicit interpreter path avoids accidentally selecting Apple's Python. Alternatively, install a current macOS Python from [python.org](https://www.python.org/downloads/macos/), which includes its own Tk, and use that interpreter to run the app.

If you see `DEPRECATION WARNING: The system version of Tk is deprecated`, switch to one of these Python installations. Setting `TK_SILENCE_DEPRECATION=1` only hides the warning; it does not fix rendering. See [Python's macOS Tk guidance](https://www.python.org/download/mac/tcltk/). Changing Python installations does not require deleting your saved scripts or settings.

#### Linux

Install your distribution's Python and matching Tk package. For example, on Ubuntu or Debian:

```sh
sudo apt install python3 python3-tk
python3 -m tkinter
```

Use a distribution version that provides Python 3.10 or newer. Check that the Tk test window renders correctly, close it, then run:

```sh
python3 dxspider.py
```

Other distributions may use a different package name for Tk. Run the app in a graphical desktop session; Tk needs a display.

## Using the app

1. Open **Settings**, enter your login callsign, and save. The initial node address is `w3lpl.net:7373`. Enter a DNS name or IP address, optionally followed by a port. Omitting the port uses 23. For IPv6 with a port, use brackets, for example `[2001:db8::1]:7373`. Saving checks DNS names with your system resolver. The app remembers the host, port, callsign, macro values, and script library in your user configuration directory.
2. Choose a starter script or click **New** for an ad-hoc one. Type one node command per line. Blank lines are skipped. **Save** updates the library, while **Save as…** creates a named copy.
3. **Preview** displays expanded commands. **Copy expanded commands** puts them on the clipboard for use in N1MM or a terminal.
4. Click **Apply** to open a callsign-only Telnet session. The app sends the visible editor contents one command at a time, waiting for your callsign's DXSpider prompt between commands. It closes the socket after the final reply, an error, or a timeout.

**Capture from node** reads the current callsign’s outgoing spot and RBN filters and available skimmer and See Me settings in one short session. The app queries `show/filter spots rbn` and `stat/user`, follows English pagination prompts, and opens the captured commands as an unsaved script in the editor. You can edit, copy, save, or apply it. The transcript flags unavailable station settings. If you keep unsaved edits when prompted, the captured script appears in the transcript instead.

## Macros and presets

Type `$` in the script editor to list available macros. Keep typing to narrow the list, use **Up** or **Down** to select a name, and press **Tab** to insert it. **Esc** dismisses the suggestions.

Saved scripts live in the `scripts` section of `settings.json`, alongside node settings and macros. On Windows the file is in `%APPDATA%\DXSpider Filters`, on macOS in `~/Library/Application Support/DXSpider Filters`, and on Linux in `$XDG_CONFIG_HOME/DXSpider Filters` (normally `~/.config/DXSpider Filters`). To remove a saved script, select it, click **Delete…**, and confirm. Deletion affects the local library only.

Use `$OPERATOR` for the login callsign. Add an OPERATOR entry in the macro table to override it. The starter scripts use `$LOCALSTATES` and `$SSBSTATES` for their spotter regions. Macro names are case sensitive and values are literal text. Undefined macros stop Apply before login.

The starter library comes from `samplescripts.txt`. Each preset clears spot and RBN filters and explicitly enables `seeme`. WRT interprets the missing mode in the sample as CW. Saved scripts can change any of these settings.

## Session results

The results show each command and its reply. The app stops on recognized English rejection messages. DXSpider replies are free text, so review unfamiliar responses in the transcript. A lost reply leaves the in-flight command's outcome unknown. Earlier commands may already have changed filters. The app lists the remaining commands and leaves retrying to the operator.

Run the local tests with `python -m unittest -v`. The session tests use a loopback node.

## GitHub Actions

Branch pushes and pull requests run the tests on Windows, macOS, and Linux. To publish a Windows release, tag the desired commit and push the tag. For example:

```sh
git tag v1.0.0
git push origin v1.0.0
```

Tags starting with `v` run the same test matrix. After the tests pass, the release workflow builds the x64 executable on Windows, checks that it opens the editor with the bundled starter script, and attaches it to a GitHub Release.

## Acknowledgements

Alan H, WA3EKL, gave me this idea when he generously shared his scripts with the PVRC group. The bones of the sample scripts that ship with this come from his posts.
