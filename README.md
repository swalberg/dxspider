# DXSpider Filters

A desktop script library for configuring a DXSpider node from Windows, macOS, or Linux.

## Run

Install Python 3.10 or newer with Tk. Run `python dxspider.py` from this directory (on macOS or Linux, use `python3 dxspider.py`). Linux distributions may package Tk separately, for example as `python3-tk`.

1. Open **Settings**, enter your login callsign, and save. The default node is `w3lpl.net:7373`. The app remembers the host, port, callsign, macro values, and script library in your user configuration directory.
2. Choose a starter script or click **New** for an ad-hoc one. Type one node command per line. Blank lines are skipped. **Save** updates the library, while **Save as…** creates a named copy.
3. **Preview** displays expanded commands. **Copy expanded commands** puts them on the clipboard for use in N1MM or a terminal.
4. Click **Apply** to open a callsign-only Telnet session. The app sends the visible editor contents one command at a time, waiting for your callsign's DXSpider prompt between commands. It closes the socket after the final reply, an error, or a timeout.

## Macros and presets

Use `$OPERATOR` for the login callsign. Add an OPERATOR entry in the macro table to override it. The starter scripts use `$LOCALSTATES` and `$SSBSTATES` for their spotter regions. Macro names are case sensitive and values are literal text. Undefined macros stop Apply before login.

The starter library comes from `samplescripts.txt`. Each preset clears spot and RBN filters and explicitly enables `seeme`. WRT interprets the missing mode in the sample as CW. Saved scripts can change any of these settings.

## Session results

The results show each command and its reply. The app stops on recognized English rejection messages. DXSpider replies are free text, so review unfamiliar responses in the transcript. A lost reply leaves the in-flight command's outcome unknown. Earlier commands may already have changed filters. The app lists the remaining commands and leaves retrying to the operator.

Run the local tests with `python -m unittest -v`. The session tests use a loopback node.
