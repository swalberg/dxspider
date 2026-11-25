"""Brief callsign-only Telnet sessions with one command in flight at a time."""
import re
import socket
import time


LOGIN = re.compile(r"(?:^|\n)[ \t]*(?:\w+[ \t]+)?(?:login|callsign|call sign):[ \t]*", re.I)
PASSWORD = re.compile(r"(?:^|\n)[ \t]*password:[ \t]*", re.I)
PAGE = re.compile(r"(?:^|\n)Press Enter to continue, A to abort \(\d+ lines\) >", re.I)
ERROR = re.compile(
    r"^(?:sorry\b|error\b|syntax\b|usage\b|invalid\b|unknown\b|bad\b|"
    r"not allowed\b|permission denied\b|you must\b|you are not\b|"
    r"can't\b|cannot\b|not a valid\b|.*\b(?:is not a valid|not understood|"
    r"not recognised|not recognized|not found|syntax error)\b)", re.I)


class Reader:
    def __init__(self, sock, timeout):
        self.sock = sock
        self.timeout = timeout
        self.pending = ""
        self.state = "text"
        self.option = 0

    def decode(self, data):
        # Decline optional Telnet features. Negotiations can cross TCP reads.
        plain = bytearray()
        for byte in data:
            if self.state == "text":
                if byte == 255:
                    self.state = "iac"
                else:
                    plain.append(byte)
            elif self.state == "iac":
                self.state = "text"
                if byte in (251, 252, 253, 254):
                    self.option = byte
                    self.state = "option"
                elif byte == 250:
                    self.state = "sub"
                elif byte == 255:
                    plain.append(byte)
            elif self.state == "option":
                if self.option in (251, 253):
                    self.sock.sendall(bytes((255, 254 if self.option == 251 else 252, byte)))
                self.state = "text"
            elif self.state == "sub":
                if byte == 255:
                    self.state = "sub-iac"
            else:
                self.state = "text" if byte == 240 else "sub"
        return plain.decode("latin-1").replace("\r", "").replace("\x00", "")

    def until(self, pattern):
        return self.read_until(pattern)[0]

    def read_until(self, pattern):
        deadline = time.monotonic() + self.timeout
        while True:
            match = pattern.search(self.pending)
            if match:
                reply, self.pending = self.pending[:match.start()], self.pending[match.end():]
                return reply.strip(), match
            if PASSWORD.search(self.pending):
                raise OSError("The node requires a password.")
            remaining = deadline - time.monotonic()
            if remaining <= 0 or len(self.pending) > 512_000:
                raise OSError("Expected node prompt did not arrive.")
            self.sock.settimeout(remaining)
            data = self.sock.recv(8192)
            if not data:
                raise OSError("The node closed the connection.")
            self.pending += self.decode(data)

    def login(self, call):
        self.until(LOGIN)
        self.sock.sendall((call + "\r\n").encode("ascii"))
        self.prompt = re.compile(r"(?:^|\n)[ \t]*" + re.escape(call) +
                                 r"[ \t]+de[ \t]+[^\n>]+>", re.I)
        self.until(self.prompt)

    def query(self, command):
        self.sock.sendall((command + "\r\n").encode("ascii"))
        terminator = re.compile(f"(?:{self.prompt.pattern})|(?P<page>{PAGE.pattern})", re.I)
        pages = []
        for _ in range(100):
            reply, match = self.read_until(terminator)
            pages.append(reply)
            if not match["page"]:
                return "\n".join(pages)
            self.sock.sendall(b"\r\n")
        raise ValueError("Too many pages in configuration reply.")


def apply_commands(host, port, call, commands, report, timeout=10):
    next_index = 0
    active = None
    reader = None
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            reader = Reader(sock, timeout)
            reader.login(call)
            for index, command in enumerate(commands):
                active = command
                next_index = index + 1
                sock.sendall((command + "\r\n").encode("ascii"))
                reply = reader.until(reader.prompt)
                active = None
                lines = [line.strip() for line in reply.splitlines()
                         if line.strip() != command and not line.startswith("DX de ")]
                rejected = any(ERROR.match(line) for line in lines)
                report(f"{'Rejected' if rejected else 'Replied'} · {command}\n{reply or '(prompt only)'}")
                if rejected:
                    break
            else:
                return "Finished · connection closed"
    except OSError as exc:
        report(str(exc))
        if active is not None:
            report(f"Outcome unknown · {active}")
        if reader and reader.pending.strip():
            report(reader.pending.strip())
    if next_index < len(commands):
        report("Not sent\n" + "\n".join(commands[next_index:]))
    return "Stopped · disconnected"
