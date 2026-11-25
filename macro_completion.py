"""Keyboard completion for macro references in a Tk text editor."""
import re
import tkinter as tk

from library import NAME


PREFIX = re.compile(r"\$(?:" + NAME.pattern + r")?$")


class MacroCompletion:
    def __init__(self, editor, macro_names):
        self.editor = editor
        self.macro_names = macro_names
        self.root = editor.winfo_toplevel()
        self.listbox = tk.Listbox(self.root, height=6, takefocus=False, exportselection=False)
        editor.bind("<KeyRelease>", self.on_release, add=True)
        editor.bind("<Down>", lambda _: self.move(1), add=True)
        editor.bind("<Up>", lambda _: self.move(-1), add=True)
        editor.bind("<Tab>", self.complete, add=True)
        editor.bind("<Escape>", self.dismiss, add=True)
        for event in ("<FocusOut>", "<ButtonPress>", "<MouseWheel>", "<Configure>"):
            editor.bind(event, self.hide, add=True)
        self.listbox.bind("<ButtonPress-1>", self.click)

    def hide(self, event=None):
        self.listbox.place_forget()

    def dismiss(self, event):
        if self.listbox.winfo_manager():
            self.hide()
            return "break"

    def prefix(self):
        before = self.editor.get("insert linestart", "insert")
        match = PREFIX.search(before)
        return match[0] if match else None

    def on_release(self, event):
        if event.keysym in ("Up", "Down", "Escape", "Tab", "ISO_Left_Tab"):
            return
        if event.keysym.startswith(("Shift_", "Control_", "Alt_", "Meta_", "Super_")):
            return
        if event.keysym in ("Return", "KP_Enter", "Home", "End", "Prior", "Next"):
            self.hide()
        else:
            self.refresh()

    def refresh(self):
        prefix = self.prefix()
        bounds = self.editor.bbox("insert")
        if not prefix or not bounds or self.editor.tag_ranges("sel"):
            self.hide()
            return
        names = sorted(set(self.macro_names()), key=lambda name: (name.casefold(), name))
        matches = ["$" + name for name in names if name.casefold().startswith(prefix[1:].casefold())]
        if not matches:
            self.hide()
            return
        box = self.listbox
        box.delete(0, "end")
        box.insert("end", *matches)
        box.selection_set(0)
        box.configure(height=min(7, len(matches)), width=max(12, max(map(len, matches))))
        x, y, _, height = bounds
        x += self.editor.winfo_rootx() - self.root.winfo_rootx()
        y += self.editor.winfo_rooty() - self.root.winfo_rooty()
        if y + height + box.winfo_reqheight() > self.root.winfo_height():
            y -= box.winfo_reqheight()
        else:
            y += height
        x = max(0, min(x, self.root.winfo_width() - box.winfo_reqwidth()))
        box.place(x=x, y=max(0, y))
        box.lift()

    def move(self, step):
        box = self.listbox
        if box.winfo_manager():
            index = (box.curselection()[0] + step) % box.size()
            box.selection_clear(0, "end")
            box.selection_set(index)
            box.see(index)
            return "break"

    def click(self, event):
        index = self.listbox.nearest(event.y)
        self.listbox.selection_clear(0, "end")
        self.listbox.selection_set(index)
        return self.complete(event)

    def complete(self, event):
        if not self.listbox.winfo_manager():
            return
        prefix = self.prefix()
        choice = self.listbox.get(self.listbox.curselection()[0])
        self.hide()
        if prefix and choice.casefold().startswith(prefix.casefold()):
            # Replace the entire identifier even when editing its middle.
            suffix = re.match(r"[A-Za-z0-9_]*", self.editor.get("insert", "insert lineend"))[0]
            start = self.editor.index(f"insert - {len(prefix)} chars")
            self.editor.edit_separator()
            self.editor.replace(start, f"insert + {len(suffix)} chars", choice)
            self.editor.mark_set("insert", f"{start} + {len(choice)} chars")
            self.editor.edit_separator()
            return "break"
