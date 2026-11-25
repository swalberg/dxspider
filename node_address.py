"""Parse a user-entered Telnet address and validate it with the system resolver."""
import ipaddress
import re
import socket


def format_address(host, port):
    return f"[{host}]:{port}" if ":" in host else f"{host}:{port}"


def validate_address(value):
    address = value.strip()
    port_text = ""
    if not address or any(char.isspace() for char in address):
        raise ValueError("Enter a node address such as w3lpl.net:7373.")
    if address.startswith("["):
        match = re.fullmatch(r"\[([^\]]+)\](?::([^:]*))?", address)
        if not match:
            raise ValueError("Use [IPv6 address]:port.")
        host, port_text = match.groups()
        ipaddress.IPv6Address(host)
    elif address.count(":") > 1:
        ipaddress.IPv6Address(address)
        host = address
    else:
        host, _, port_text = address.partition(":")

    port = 23
    if port_text:
        if not re.fullmatch(r"[0-9]{1,5}", port_text) or not 1 <= int(port_text) <= 65535:
            raise ValueError("The port must be a number from 1 to 65535.")
        port = int(port_text)
    try:
        ipaddress.ip_address(host)
    except ValueError:
        try:
            dns_name = host.encode("idna").decode("ascii").removesuffix(".")
        except UnicodeError as exc:
            raise ValueError("Enter a valid DNS name or IP address.") from exc
        labels = dns_name.split(".")
        label = r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
        if (len(dns_name) > 253 or any(not re.fullmatch(label, part, re.I) for part in labels)
                or all(re.fullmatch(r"(?:[0-9]+|0x[0-9a-f]+)", part, re.I) for part in labels)):
            raise ValueError("Enter a valid DNS name or IP address.")
        try:
            results = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        except OSError as exc:
            raise ValueError(f"Could not resolve {host} to an IP address.") from exc
        if not any(row[0] in (socket.AF_INET, socket.AF_INET6) for row in results):
            raise ValueError(f"Could not resolve {host} to an IP address.")
    return host, port
