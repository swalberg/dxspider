import json
import socket
import tempfile
import threading
import unittest
from pathlib import Path

from capture import capture_configuration, filter_commands, station_commands
from library import defaults, expand, save
from session import apply_commands


class LibraryTests(unittest.TestCase):
    def test_starters_and_storage(self):
        config = defaults()
        config["call"] = "W1TEST"
        self.assertEqual(list(config["scripts"]), [
            "CWT", "Normal DX", "WRT", "Sweepstakes SSB", "Sweepstakes CW",
            "WAE RTTY", "CQWW SSB", "California QSO Party", "Makrothen RTTY",
            "Pennsylvania QSO Party", "NAQP CW", "ARRL DX SSB",
        ])
        for script in config["scripts"].values():
            commands = expand(script, config)
            self.assertEqual(commands[:2], ["clear/spots all", "clear/rbn all"])
            self.assertIn("set/seeme", commands)
            self.assertEqual(commands.count("acc/spot 0 call W1TEST"), 1)
            self.assertEqual(commands.count("acc/rbn 0 call W1TEST"), 1)
            self.assertNotIn("$", "\n".join(commands))
        self.assertIn("acc/spot 0 call W1TEST", expand(config["scripts"]["CWT"], config))
        self.assertIn("info cw or info ssb", config["scripts"]["WRT"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            save(config, path)
            self.assertEqual(json.loads(path.read_text()), config)

    def test_undefined_macro_line(self):
        with self.assertRaisesRegex(ValueError, r"Line 3: set \$MISSING"):
            expand("clear/spots all\n\nacc/spot 0 call $MISSING", defaults())


class SessionTests(unittest.TestCase):
    def simulate(self, responses, capture=False):
        prompt = b"W1TEST de NODE-2 24-Nov-2026 1420Z dxspider >"
        received, log, errors = [], [], []
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        port = listener.getsockname()[1]

        def server():
            try:
                with listener, listener.accept()[0] as client, client.makefile("rb") as stream:
                    client.settimeout(3)
                    client.sendall(b"\xff\xfb")
                    client.sendall(b"\x01login: ")
                    self.assertEqual(stream.read(3), b"\xff\xfe\x01")
                    self.assertEqual(stream.readline(), b"W1TEST\r\n")
                    client.sendall(prompt)
                    for reply in responses:
                        received.append(stream.readline().decode().strip())
                        if reply is None:
                            return
                        pages = reply if isinstance(reply, tuple) else (reply,)
                        for page in pages[:-1]:
                            client.sendall(b"\r\n" + page + b"\r\nPress Enter to continue, A to abort (2 lines) >")
                            self.assertEqual(stream.readline(), b"\r\n")
                        client.sendall(b"\r\n" + pages[-1] + b"\r\n" + prompt)
                    self.assertEqual(stream.read(1), b"")
            except Exception as exc:
                errors.append(exc)

        worker = threading.Thread(target=server, daemon=True)
        worker.start()
        if capture:
            result = capture_configuration("127.0.0.1", port, "W1TEST", log.append, 2)
        else:
            result = apply_commands("127.0.0.1", port, "W1TEST", ["one", "two", "three"], log.append, 2)
        worker.join(4)
        self.assertFalse(worker.is_alive())
        if errors:
            raise errors[0]
        return received, "\n".join(log), result

    def test_success_and_close(self):
        received, _, result = self.simulate([b"OK", b"DX de W3ABC: 14000 A1B", b""])
        self.assertEqual(received, ["one", "two", "three"])
        self.assertIn("Finished", result)

    def test_rejection(self):
        received, log, _ = self.simulate([b"OK", b"Sorry, invalid filter"])
        self.assertEqual(received, ["one", "two"])
        self.assertIn("Rejected · two", log)
        self.assertIn("Not sent\nthree", log)

    def test_lost_reply(self):
        _, log, _ = self.simulate([None])
        self.assertIn("Outcome unknown · one", log)
        self.assertIn("Not sent\ntwo\nthree", log)

    def test_capture_and_close(self):
        received, log, script = self.simulate([
            (b"W1TEST : spots\r\n filter3 reject not by_state PA",
             b"DX de W9ABC: 14001 W2XYZ\r\nW1TEST : rbn\r\n filter0 accept call W1TEST"),
            b"Want RBN spots: Yes\r\nRBN See Me: No\r\nWant RBN CW: Yes\r\n"
            b"Want RBN Beacon: No\r\nWant RBN RTTY: Yes\r\nWant RBN FT4/8: No\r\nWant RBN PSK: No"
        ], capture=True)
        self.assertEqual(received, ["show/filter spots rbn", "stat/user"])
        self.assertEqual(script.splitlines(), ["clear/spots all", "clear/rbn all",
                         "reject/spots 3 not by_state PA", "accept/rbn 0 call W1TEST",
                         "set/skimmer cw rtty", "unset/seeme"])
        self.assertNotIn("Omitted", log)

    def test_capture_requires_recognizable_filters(self):
        with self.assertRaises(ValueError):
            filter_commands("Unknown command", "W1TEST")
        self.assertEqual(filter_commands("No filters defined for W1TEST", "W1TEST"),
                         ["clear/spots all", "clear/rbn all"])
        self.assertEqual(station_commands("Want RBN spots: Yes\nWant RBN CW: Yes"),
                         ([], ["skimmer modes", "See Me"]))
