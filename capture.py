"""Read the operator's spot and RBN configuration into a replayable script."""
import re
import socket

from session import Reader


FILTER_QUERY = "show/filter spots rbn"
MODES = {"cw": "cw", "ft4/8": "ft", "beacon": "beacon", "psk": "psk", "rtty": "rtty"}


def filter_commands(reply, call):
    section = None
    recognized = False
    commands = ["clear/spots all", "clear/rbn all"]
    for raw in reply.splitlines():
        line = raw.strip()
        if not line or line.lower() == FILTER_QUERY or line.lower().startswith("dx de "):
            continue
        if line.lower() == f"no filters defined for {call}".lower():
            recognized = True
            continue
        heading = re.fullmatch(re.escape(call) + r"\s*:\s*(spots|rbn)(\s+input)?", line, re.I)
        if heading:
            section = heading[1].lower() if not heading[2] else "input"
            recognized = recognized or section != "input"
            continue
        rule = re.fullmatch(r"filter([0-9])\s+(accept|reject)\s+(.+)", line, re.I)
        if rule and section:
            if section != "input":
                commands.append(f"{rule[2].lower()}/{section} {rule[1]} {rule[3]}")
            continue
        raise ValueError(f"Unrecognized filter reply: {line}")
    if not recognized:
        raise ValueError("No recognizable output filters in the node reply.")
    return commands


def station_commands(reply):
    flags = {}
    for line in reply.splitlines():
        label, _, value = line.strip().lower().partition(":")
        flags[label.strip()] = value.strip()
    commands, missing = [], []
    if flags.get("want rbn spots") == "no":
        commands.append("unset/skimmer")
    elif (flags.get("want rbn spots") == "yes" and
          all(flags.get(f"want rbn {key}") in ("yes", "no") for key in MODES)):
        modes = [mode for key, mode in MODES.items() if flags[f"want rbn {key}"] == "yes"]
        if modes:
            commands.append("set/skimmer " + " ".join(modes))
    if not commands:
        missing.append("skimmer modes")
    seeme = flags.get("rbn see me")
    if seeme in ("yes", "no"):
        commands.append("set/seeme" if seeme == "yes" else "unset/seeme")
    else:
        missing.append("See Me")
    return commands, missing


def capture_configuration(host, port, call, report, timeout=10):
    with socket.create_connection((host, port), timeout=timeout) as sock:
        reader = Reader(sock, timeout)
        reader.login(call)
        filters = reader.query(FILTER_QUERY)
        report(f"{FILTER_QUERY}\n{filters}")
        commands = filter_commands(filters, call)
        settings, missing = station_commands(reader.query("stat/user"))
    if missing:
        report("Omitted from capture (unavailable or incomplete): " + ", ".join(missing))
    return "\n".join(commands + settings)
