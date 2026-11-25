# DXSpider Filters

A desktop script library for configuring a DXSpider node from Windows, macOS, or Linux.

## Run

On 64-bit Windows, download **DXSpider-Filters-Windows-x64.exe** from the repository’s **Releases** page and double-click it. The executable includes Python, Tk, and the starter scripts.

### Run from source

Install Python 3.10 or newer with Tk. Run `python dxspider.py` from this directory (on macOS or Linux, use `python3 dxspider.py`). Linux distributions may package Tk separately, for example as `python3-tk`.

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
