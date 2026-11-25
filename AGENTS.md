# DXSpider Filters

This Python/Tk desktop app manages an amateur radio operator’s DXSpider filters on Windows, macOS, and Linux. The operator may already be connected through N1MM using the same callsign. Long overlapping sessions can disconnect the logger.

## Operating behavior

- Editing, previewing, and copying scripts happen locally. Apply and Capture from node each open a short callsign-only Telnet session to the saved destination and disconnect when finished.
- Apply expands macros before login and waits for a reply to each command. Preserve the distinction between a rejected command, a lost reply, and commands still waiting to be sent. An earlier command may already have cleared the operator’s filters.
- Capture uses read-only queries and brings the result into the editor as an unsaved script. Keep the operator’s ability to preserve an existing draft.
- The bundled scripts in `samplescripts.txt` seed a new library. Operators can edit or delete presets and define their own macros. Preserve saved libraries when changing defaults or settings.

## Development

Run the app with `python dxspider.py` and the suite with `python -m unittest discover -v`. The Telnet tests use a loopback node. The editor and Settings tests use Tk and need a display to run.

See `README.md` for operator instructions and the tagged Windows release process. The Windows download bundles Python, Tk, and the starter scripts.
