import tkinter as tk
import unittest

from macro_completion import MacroCompletion


class MacroCompletionTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Tk display unavailable: {exc}")
        self.addCleanup(self.root.destroy)
        self.editor = tk.Text(self.root, undo=True)
        self.editor.pack()
        self.names = ["OPERATOR", "LOCALSTATES", "LOCAL_ZONE", "OPERATOR"]
        self.popup = MacroCompletion(self.editor, lambda: self.names)
        self.root.update()
        self.editor.focus_force()
        self.root.update()

    def key(self, key):
        for action in ("KeyPress", "KeyRelease"):
            self.editor.event_generate(f"<{action}-{key}>")
        self.root.update()

    def test_filter_navigate_complete(self):
        self.key("dollar")
        self.assertEqual(self.popup.listbox.get(0, "end"), ("$LOCAL_ZONE", "$LOCALSTATES", "$OPERATOR"))
        self.key("l")
        self.assertEqual(self.popup.listbox.size(), 2)
        self.key("Down")
        self.key("Up")
        self.key("Down")
        self.key("Tab")
        self.assertEqual(self.editor.get("1.0", "end-1c"), "$LOCALSTATES")
        self.assertFalse(self.popup.listbox.winfo_manager())

    def test_escape_and_no_matches_restore_tab(self):
        self.key("dollar")
        self.key("Escape")
        self.assertFalse(self.popup.listbox.winfo_manager())
        self.key("z")
        self.assertFalse(self.popup.listbox.winfo_manager())
        self.key("Tab")
        self.assertEqual(self.editor.get("1.0", "end-1c"), "$z\t")

    def test_complete_in_middle_and_refresh_custom_names(self):
        self.names.append("Other_Mode")
        self.editor.insert("1.0", "set $otOLD next")
        self.editor.mark_set("insert", "1.6")
        self.key("Right")
        self.key("Tab")
        self.assertEqual(self.editor.get("1.0", "end-1c"), "set $Other_Mode next")
