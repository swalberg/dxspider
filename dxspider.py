"""DXSpider Filters desktop application. Run with python dxspider.py."""
import json
import queue
import re
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from tkinter.scrolledtext import ScrolledText

from library import NAME, defaults, expand, save, settings_file
from session import apply_commands


class App:
    def __init__(self, root, config, path):
        self.root, self.config, self.path = root, config, path
        self.current = None
        self.original = ""
        self.running = False
        self.events = queue.Queue()
        root.title("DXSpider Filters")
        root.geometry("840x650")
        root.minsize(620, 500)
        frame = ttk.Frame(root, padding=16)
        frame.pack(fill="both", expand=True)
        header = ttk.Frame(frame)
        header.pack(fill="x", pady=(0, 12))
        self.destination = ttk.Label(header)
        self.destination.pack(side="left")
        self.show_destination()
        ttk.Button(header, text="Settings", command=self.settings).pack(side="right")
        bar = ttk.Frame(frame)
        bar.pack(fill="x")
        ttk.Label(bar, text="Script").pack(side="left", padx=(0, 6))
        self.choice = ttk.Combobox(bar, state="readonly", width=22)
        self.choice.pack(side="left")
        self.choice.bind("<<ComboboxSelected>>", lambda _: self.select(self.choice.get()))
        for label, action in [("New", lambda: self.select(None)), ("Save", self.save_script),
                              ("Save as…", lambda: self.save_script(True))]:
            ttk.Button(bar, text=label, command=action).pack(side="left", padx=(5, 0))
        self.editor = ScrolledText(frame, wrap="none", height=12, undo=True)
        self.editor.pack(fill="both", expand=True, pady=8)
        actions = ttk.Frame(frame)
        actions.pack(fill="x")
        self.apply_button = ttk.Button(actions, text="Apply", command=self.apply)
        self.apply_button.pack(side="right")
        for label, action in [("Preview", self.preview), ("Copy expanded commands", self.copy)]:
            ttk.Button(actions, text=label, command=action).pack(side="left", padx=(0, 6))
        self.status = ttk.Label(frame, text="Offline")
        self.status.pack(anchor="w", pady=(12, 4))
        self.output = ScrolledText(frame, height=8, wrap="word", state="disabled")
        self.output.pack(fill="both", expand=True)
        self.select(next(iter(config["scripts"]), None))
        root.protocol("WM_DELETE_WINDOW", self.close)

    def show_destination(self):
        c = self.config
        self.destination.config(text=f"{c['call'] or 'Set callsign'}  @  {c['host']}:{c['port']}")

    def content(self):
        return self.editor.get("1.0", "end-1c")

    def can_discard(self):
        return self.content() == self.original or messagebox.askyesno(
            "Unsaved script", "Discard the edits to this script?", parent=self.root)

    def select(self, name):
        if not self.can_discard():
            self.choice.set(self.current or "")
            return
        self.current = name
        self.original = self.config["scripts"].get(name, "")
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", self.original)
        self.editor.edit_reset()
        self.choice.configure(values=list(self.config["scripts"]))
        self.choice.set(name or "")

    def persist(self, **changes):
        updated = {**self.config, **changes}
        try:
            save(updated, self.path)
        except OSError as exc:
            messagebox.showerror("Could not save settings", str(exc))
            return False
        self.config = updated
        return True

    def save_script(self, as_new=False):
        name = self.current
        if as_new or not name:
            name = simpledialog.askstring("Save script", "Script name", parent=self.root)
            if not name or not name.strip():
                return
            name = name.strip()
            if name in self.config["scripts"] and not messagebox.askyesno(
                    "Replace script", f"Replace {name} in the library?"):
                return
        body = self.content()
        if self.persist(scripts={**self.config["scripts"], name: body}):
            self.original = body
            self.select(name)

    def commands(self):
        try:
            return expand(self.content(), self.config)
        except ValueError as exc:
            messagebox.showerror("Script needs attention", str(exc))

    def log(self, text, clear=False):
        self.output.configure(state="normal")
        if clear:
            self.output.delete("1.0", "end")
        self.output.insert("end", text + "\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def preview(self):
        if self.running:
            return
        commands = self.commands()
        if commands:
            self.status.configure(text="Expanded commands")
            self.log("\n".join(commands), clear=True)

    def copy(self):
        commands = self.commands()
        if commands:
            self.root.clipboard_clear()
            self.root.clipboard_append("\n".join(commands))
            if not self.running:
                self.status.configure(text="Expanded commands copied")

    def apply(self):
        if self.running:
            return
        if not self.config["call"]:
            messagebox.showinfo("Callsign required", "Enter your login callsign in Settings.")
            self.settings()
            return
        commands = self.commands()
        if not commands:
            return
        c = self.config
        self.running = True
        self.apply_button.state(["disabled"])
        self.status.configure(text="Applying script…")
        self.log(f"{c['call']} @ {c['host']}:{c['port']}", clear=True)

        def work():
            try:
                result = apply_commands(c["host"], c["port"], c["call"], commands,
                                        lambda msg: self.events.put(("log", msg)))
            except Exception as exc:
                result = f"Stopped · {exc}"
            self.events.put(("done", result))

        threading.Thread(target=work, daemon=True).start()
        self.root.after(40, self.poll)

    def poll(self):
        while True:
            try:
                kind, value = self.events.get_nowait()
            except queue.Empty:
                self.root.after(40, self.poll)
                return
            if kind == "done":
                self.running = False
                self.apply_button.state(["!disabled"])
                self.status.configure(text=value)
                return
            self.log(value)

    def close(self):
        if self.running and not messagebox.askyesno("Apply in progress", "Exit during this session?"):
            return
        if self.can_discard():
            self.root.destroy()

    def settings(self):
        Settings(self)


class Settings:
    def __init__(self, app):
        self.app = app
        self.window = tk.Toplevel(app.root)
        self.window.title("Node and macros")
        self.window.transient(app.root)
        self.window.grab_set()
        panel = ttk.Frame(self.window, padding=16)
        panel.pack(fill="both", expand=True)
        self.fields = {}
        for row, (key, label) in enumerate([("host", "Node host"), ("port", "Port"),
                                            ("call", "Login callsign")]):
            ttk.Label(panel, text=label).grid(row=row, column=0, sticky="w")
            entry = ttk.Entry(panel, width=35)
            entry.grid(row=row, column=1, sticky="ew", pady=2)
            entry.insert(0, str(app.config[key]))
            self.fields[key] = entry
        ttk.Label(panel, text="Macros  ·  $OPERATOR defaults to the login callsign").grid(
            row=3, columnspan=2, sticky="w", pady=(12, 4))
        self.macros = dict(app.config["macros"])
        self.table = ttk.Treeview(panel, columns=("name", "value"), show="headings", height=6)
        for col, width in [("name", 125), ("value", 270)]:
            self.table.heading(col, text=col.title())
            self.table.column(col, width=width)
        self.table.grid(row=4, columnspan=2, sticky="nsew")
        self.table.bind("<Double-1>", lambda _: self.edit(False))
        self.refresh()
        actions = ttk.Frame(panel)
        actions.grid(row=5, columnspan=2, sticky="ew", pady=(8, 0))
        for label, action in [("Add", lambda: self.edit(True)), ("Edit", lambda: self.edit(False)),
                              ("Remove", self.remove)]:
            ttk.Button(actions, text=label, command=action).pack(side="left")
        ttk.Button(actions, text="Save settings", command=self.commit).pack(side="right")
        panel.columnconfigure(1, weight=1)
        panel.rowconfigure(4, weight=1)

    def refresh(self):
        self.table.delete(*self.table.get_children())
        for name, value in self.macros.items():
            self.table.insert("", "end", iid=name, values=(name, value))

    def remove(self):
        for name in self.table.selection():
            del self.macros[name]
        self.refresh()

    def edit(self, add):
        if add:
            name = simpledialog.askstring("New macro", "Macro name (without $)", parent=self.window)
            if name is None:
                return
            name = name.strip()
            if not NAME.fullmatch(name) or name in self.macros:
                messagebox.showerror("Macro name", "Use a unique name with letters, digits, or underscores, starting with a letter or underscore.", parent=self.window)
                return
        else:
            selected = self.table.selection()
            if not selected:
                return
            name = selected[0]
        value = simpledialog.askstring("Macro value", f"Literal text for ${name}",
                                       initialvalue=self.macros.get(name, ""), parent=self.window)
        if value is not None and value.strip():
            self.macros[name] = value.strip()
            self.refresh()

    def commit(self):
        host, port, call = (self.fields[k].get().strip() for k in ("host", "port", "call"))
        if (not host or any(ch.isspace() for ch in host) or not port.isascii() or
                not port.isdecimal() or len(port) > 5 or not 1 <= int(port) <= 65535 or
                not re.fullmatch(r"[A-Za-z0-9/\-]+", call)):
            messagebox.showerror("Node settings", "Enter a hostname, port (1–65535), and login callsign.", parent=self.window)
            return
        if self.app.persist(host=host, port=int(port), call=call.upper(), macros=self.macros):
            self.app.show_destination()
            self.window.destroy()


def main():
    root = tk.Tk()
    path = settings_file()
    try:
        config = json.loads(path.read_text(encoding="utf-8")) if path.exists() else defaults()
        App(root, config, path)
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        messagebox.showerror("Could not open DXSpider Filters", str(exc), parent=root)
        root.destroy()
        return
    root.mainloop()


if __name__ == "__main__":
    main()
