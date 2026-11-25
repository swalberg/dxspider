import json
import socket
import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from dxspider import App, Settings
from library import defaults
from node_address import format_address, validate_address


class AddressTests(unittest.TestCase):
    def test_ip_literals_skip_dns(self):
        with patch("node_address.socket.getaddrinfo") as resolve:
            for text, host, port in [
                (" 192.0.2.1 ", "192.0.2.1", 23),
                ("192.0.2.1:1", "192.0.2.1", 1),
                ("2001:db8::1", "2001:db8::1", 23),
                ("[::1]", "::1", 23), ("[::1]:65535", "::1", 65535),
            ]:
                with self.subTest(text=text):
                    self.assertEqual(validate_address(text), (host, port))
                    self.assertEqual(validate_address(format_address(host, port)), (host, port))
            resolve.assert_not_called()

    def test_dns_names_use_resolver_and_keep_hostname(self):
        for text, host, port, family in [
            ("node.example:7373", "node.example", 7373, socket.AF_INET),
            ("node.example.", "node.example.", 23, socket.AF_INET6),
            ("localhost:", "localhost", 23, socket.AF_INET),
        ]:
            with self.subTest(text=text), patch("node_address.socket.getaddrinfo",
                                                return_value=[(family, 0, 0, "", ())]) as resolve:
                self.assertEqual(validate_address(text), (host, port))
                resolve.assert_called_once_with(host, port, type=socket.SOCK_STREAM)

    def test_invalid_syntax(self):
        with patch("node_address.socket.getaddrinfo") as resolve:
            for text in ("", ":23", "node:0", "node:65536", "node:ssh", "node:-1", "node:２３",
                         "node name", "bad..host", "-bad.example", "bad_.example", "bad.example-",
                         "999.1.2.3", "127.1", "[::1", "[example.org]:23", "::xyz",
                         "https://node.example", "[::1]:80:90"):
                with self.subTest(text=text), self.assertRaises(ValueError):
                    validate_address(text)
            resolve.assert_not_called()

    def test_unresolved_host(self):
        with patch("node_address.socket.getaddrinfo", side_effect=socket.gaierror()):
            with self.assertRaisesRegex(ValueError, "Could not resolve"):
                validate_address("missing.example")
        with patch("node_address.socket.getaddrinfo", return_value=[]):
            with self.assertRaisesRegex(ValueError, "Could not resolve"):
                validate_address("empty.example")


class SettingsSaveTests(unittest.TestCase):
    def test_existing_address_invalid_save_and_successful_retry(self):
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Tk display unavailable: {exc}")
        self.addCleanup(root.destroy)
        root.withdraw()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "settings.json"
            config = defaults()
            config.update(host="cluster.example", port=9000, call="W1TEST")
            app = App(root, config, path)
            settings = Settings(app)
            entry = settings.fields["address"]
            self.assertEqual(entry.get(), "cluster.example:9000")
            entry.delete(0, "end")
            entry.insert(0, "missing.example")
            with patch("node_address.socket.getaddrinfo", side_effect=socket.gaierror()), \
                    patch("dxspider.messagebox.showerror") as error:
                settings.save_button.invoke()
                self.wait_for(root, lambda: error.called)
            self.assertEqual(app.config, config)
            self.assertFalse(path.exists())
            entry.delete(0, "end")
            entry.insert(0, "::1")
            settings.save_button.invoke()
            self.wait_for(root, lambda: not settings.window.winfo_exists())
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")),
                             {**config, "host": "::1", "port": 23})
            self.assertIn("[::1]:23", app.destination["text"])

    def wait_for(self, root, condition):
        deadline = time.monotonic() + 5
        while not condition() and time.monotonic() < deadline:
            root.update()
            time.sleep(.01)
        self.assertTrue(condition())
