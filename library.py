"""Local settings, starter scripts, and offline command expansion."""
import json
import os
import re
import sys
import tempfile
from pathlib import Path


LOCAL = "PA,MD,VA,NC,SC,GA,OH,WV,KY,TN"
NAME = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")
TOKEN = re.compile(r"\$(" + NAME.pattern + ")")


def defaults():
    samples = Path(__file__).with_name("samplescripts.txt").read_text(encoding="utf-8-sig")
    scripts = {}
    for block in re.split(r"\n\s*\n(?=[^\n]+\nclear/spots)", samples.strip()):
        title, commands = block.split("\n", 1)
        commands = commands.strip().replace("N3RTW", "$OPERATOR")
        commands = commands.replace("ME,MA,NH,VT,RI,CT,NJ,DE," + LOCAL, "$SSBSTATES")
        commands = commands.replace(LOCAL, "$LOCALSTATES").replace("or info or", "or info cw or")
        if "set/seeme" not in commands:
            lines = commands.splitlines()
            lines.insert(3, "set/seeme")
            commands = "\n".join(lines)
        scripts[title.strip()] = commands
    return dict(host="w3lpl.net", port=7373, call="", scripts=scripts,
                macros={"LOCALSTATES": LOCAL, "SSBSTATES": "ME,MA,NH,VT,RI,CT,NJ,DE," + LOCAL})


def settings_file():
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    elif sys.platform == "darwin":
        base = Path.home() / "Library/Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "DXSpider Filters" / "settings.json"


def save(config, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False, mode="w", encoding="utf-8") as f:
        temp = Path(f.name)
        try:
            json.dump(config, f, indent=2)
            f.close()
            temp.replace(path)
        finally:
            temp.unlink(missing_ok=True)


def expand(script, config):
    values = {"OPERATOR": config["call"], **config["macros"]}
    commands = []
    for number, line in enumerate(script.splitlines(), 1):
        def substitute(match):
            name = match[1]
            if not values.get(name):
                raise ValueError(f"Line {number}: set ${name} before continuing.")
            return values[name]
        command = TOKEN.sub(substitute, line).strip()
        if command:
            if not command.isascii() or not command.isprintable():
                raise ValueError(f"Line {number}: commands must contain printable ASCII text.")
            commands.append(command)
    if not commands:
        raise ValueError("Enter at least one command.")
    return commands
