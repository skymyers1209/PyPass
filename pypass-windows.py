import os
import json
import base64
import hashlib
import random
import string
import uuid
import time
import shutil
import tkinter as tk
from tkinter import messagebox, filedialog

APP_NAME = "PyPass - Password Manager"
VAULT_FILE = "pypass_vault.json"
USERNAME = os.getlogin()

BG = "#070b16"
PANEL = "#111827"
HEADER = "#111827"
BLUE = "#60a5fa"
TEXT = "#ffffff"
MUTED = "#9ca3af"
DANGER = "#ef4444"

SECONDS_30_DAYS = 30 * 24 * 60 * 60


def hash_value(value, salt=None):
    if salt is None:
        salt = os.urandom(16)

    key = hashlib.pbkdf2_hmac("sha256", value.encode("utf-8"), salt, 250000)
    return base64.b64encode(salt).decode(), base64.b64encode(key).decode()


def verify_hash(value, salt_b64, stored_hash):
    salt = base64.b64decode(salt_b64)
    _, new_hash = hash_value(value, salt)
    return new_hash == stored_hash


def load_vault():
    with open(VAULT_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    data.setdefault("items", [])
    data.setdefault("deleted_items", [])
    data.setdefault("generator_history", [])
    return data


def save_vault(data):
    with open(VAULT_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def create_vault_file(master_password):
    salt, password_hash = hash_value(master_password)

    data = {
        "username": USERNAME,
        "salt": salt,
        "password_hash": password_hash,
        "pin_enabled": False,
        "pin_full_time": False,
        "pin_salt": "",
        "pin_hash": "",
        "items": [],
        "deleted_items": [],
        "generator_history": []
    }

    save_vault(data)


class PyPassApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("560x720")
        self.root.minsize(420, 560)
        self.root.resizable(True, True)
        self.root.configure(bg=BG)

        self.generator_mode = "Password"
        self.generated_value = tk.StringVar()
        self.search_var = tk.StringVar()

        if not os.path.exists(VAULT_FILE):
            self.show_create_vault()
        else:
            self.clean_old_deleted_items()
            data = load_vault()
            if data.get("pin_enabled") and data.get("pin_full_time"):
                self.show_pin_login()
            else:
                self.show_login()

    def clear(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def initials(self):
        parts = USERNAME.replace(".", " ").replace("_", " ").split()
        if len(parts) >= 2:
            return parts[0][0].upper() + parts[1][0].upper()
        return USERNAME[:2].upper()

    def avatar(self, parent):
        return tk.Label(parent, text=self.initials(), font=("Segoe UI", 11), fg="#111827", bg="#b9bdd8", width=3)

    def check_password(self, password):
        data = load_vault()
        return verify_hash(password, data["salt"], data["password_hash"])

    def check_pin(self, pin):
        data = load_vault()
        if not data.get("pin_enabled"):
            return False
        return verify_hash(pin, data["pin_salt"], data["pin_hash"])

    def clean_old_deleted_items(self):
        if not os.path.exists(VAULT_FILE):
            return

        data = load_vault()
        now = time.time()
        data["deleted_items"] = [
            item for item in data.get("deleted_items", [])
            if now - item.get("deleted_at", now) < SECONDS_30_DAYS
        ]
        save_vault(data)

    def show_create_vault(self):
        self.clear()

        frame = tk.Frame(self.root, bg=BG)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="🔐", font=("Segoe UI Emoji", 54), bg=BG, fg=BLUE).pack(pady=(55, 12))
        tk.Label(frame, text="Create your PyPass vault", font=("Segoe UI", 22, "bold"), bg=BG, fg=TEXT).pack()
        tk.Label(frame, text=f"Welcome, {USERNAME}", font=("Segoe UI", 13), bg=BG, fg="#cbd5e1").pack(pady=(8, 24))

        self.new_password = tk.Entry(
            frame, font=("Segoe UI", 14), bg=BG, fg=TEXT,
            insertbackground=TEXT, show="•", relief="solid", bd=2
        )
        self.new_password.pack(padx=35, fill="x", ipady=10)

        tk.Button(
            frame, text="Create Vault", font=("Segoe UI", 13),
            bg=BLUE, fg="#06111f", relief="flat", height=2,
            command=self.create_new_vault
        ).pack(padx=35, fill="x", pady=18)

        tk.Label(frame, text="Set a master password for your new vault.", font=("Segoe UI", 11), bg=BG, fg=MUTED).pack()

    def create_new_vault(self):
        password = self.new_password.get()

        if len(password) < 6:
            messagebox.showwarning("PyPass", "Use at least 6 characters.")
            return

        create_vault_file(password)
        messagebox.showinfo("PyPass", "Your new vault has been created.")
        self.show_login()

    def show_login(self):
        self.clear()

        frame = tk.Frame(self.root, bg=BG)
        frame.pack(fill="both", expand=True)

        header = tk.Frame(frame, bg=HEADER)
        header.pack(fill="x")

        tk.Label(header, text="🔐  PyPass", font=("Segoe UI", 20, "bold"), fg=TEXT, bg=HEADER).pack(side="left", padx=25, pady=20)
        self.avatar(header).pack(side="right", padx=25)

        tk.Label(frame, text="🔒", font=("Segoe UI Emoji", 54), fg=BLUE, bg=BG).pack(pady=(55, 8))
        tk.Label(frame, text="Your vault is locked", font=("Segoe UI", 22, "bold"), fg=TEXT, bg=BG).pack()
        tk.Label(frame, text=USERNAME, font=("Segoe UI", 13), fg="#e5e7eb", bg=BG).pack(pady=(10, 24))

        self.password_entry = tk.Entry(
            frame, font=("Segoe UI", 14), fg=TEXT, bg=BG,
            insertbackground=TEXT, relief="solid", bd=2, show="•"
        )
        self.password_entry.pack(padx=35, fill="x", ipady=10)

        tk.Button(
            frame, text="Unlock", font=("Segoe UI", 13), fg="#06111f",
            bg=BLUE, relief="flat", height=2,
            command=self.unlock_password
        ).pack(padx=35, fill="x", pady=(18, 10))

        tk.Button(
            frame, text="Unlock with PIN", font=("Segoe UI", 13),
            fg=BLUE, bg=BG, relief="solid", bd=2, height=2,
            command=self.pin_button_clicked
        ).pack(padx=35, fill="x", pady=10)

    def unlock_password(self):
        if self.check_password(self.password_entry.get()):
            self.show_vault()
        else:
            messagebox.showerror("PyPass", "Incorrect master password.")

    def pin_button_clicked(self):
        data = load_vault()
        if not data.get("pin_enabled"):
            messagebox.showinfo("PyPass", "No PIN has been created yet. Enter your vault password first, then you can create one.")
            self.show_setup_pin()
        else:
            self.show_pin_login()

    def show_pin_login(self):
        self.clear()

        frame = tk.Frame(self.root, bg=BG)
        frame.pack(fill="both", expand=True)

        header = tk.Frame(frame, bg=HEADER)
        header.pack(fill="x")

        tk.Label(header, text="🔐  PyPass", font=("Segoe UI", 20, "bold"), fg=TEXT, bg=HEADER).pack(side="left", padx=25, pady=20)
        self.avatar(header).pack(side="right", padx=25)

        tk.Label(frame, text="🔢", font=("Segoe UI Emoji", 54), fg=BLUE, bg=BG).pack(pady=(55, 8))
        tk.Label(frame, text="Unlock with PIN", font=("Segoe UI", 22, "bold"), fg=TEXT, bg=BG).pack()
        tk.Label(frame, text=USERNAME, font=("Segoe UI", 13), fg="#e5e7eb", bg=BG).pack(pady=(10, 24))

        self.pin_entry = tk.Entry(
            frame, font=("Segoe UI", 16), fg=TEXT, bg=BG,
            insertbackground=TEXT, relief="solid", bd=2,
            show="•", justify="center"
        )
        self.pin_entry.pack(padx=35, fill="x", ipady=10)

        tk.Button(
            frame, text="Unlock", font=("Segoe UI", 13),
            fg="#06111f", bg=BLUE, relief="flat", height=2,
            command=self.unlock_pin
        ).pack(padx=35, fill="x", pady=(18, 10))

        tk.Button(
            frame, text="Use master password instead", font=("Segoe UI", 13),
            fg=BLUE, bg=BG, relief="solid", bd=2, height=2,
            command=self.show_login
        ).pack(padx=35, fill="x", pady=10)

    def unlock_pin(self):
        if self.check_pin(self.pin_entry.get()):
            self.show_vault()
        else:
            messagebox.showerror("PyPass", "Incorrect PIN.")

    def show_setup_pin(self):
        self.clear()

        frame = tk.Frame(self.root, bg=BG)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="🔢", font=("Segoe UI Emoji", 48), fg=BLUE, bg=BG).pack(pady=(35, 10))
        tk.Label(frame, text="Create a PIN", font=("Segoe UI", 22, "bold"), fg=TEXT, bg=BG).pack()

        tk.Label(frame, text="Enter your vault password first, then choose a PIN.", font=("Segoe UI", 11), fg=MUTED, bg=BG).pack(pady=(8, 18))

        self.pin_setup_password = tk.Entry(
            frame, font=("Segoe UI", 13), fg=TEXT, bg=BG,
            insertbackground=TEXT, relief="solid", bd=2, show="•"
        )
        self.pin_setup_password.pack(padx=35, fill="x", ipady=9)

        tk.Label(frame, text="Vault password", font=("Segoe UI", 10), fg=MUTED, bg=BG).pack(anchor="w", padx=40, pady=(4, 10))

        self.new_pin_entry = tk.Entry(
            frame, font=("Segoe UI", 14), fg=TEXT, bg=BG,
            insertbackground=TEXT, relief="solid", bd=2, show="•", justify="center"
        )
        self.new_pin_entry.pack(padx=35, fill="x", ipady=9)

        tk.Label(frame, text="New PIN", font=("Segoe UI", 10), fg=MUTED, bg=BG).pack(anchor="w", padx=40, pady=(4, 10))

        self.confirm_pin_entry = tk.Entry(
            frame, font=("Segoe UI", 14), fg=TEXT, bg=BG,
            insertbackground=TEXT, relief="solid", bd=2, show="•", justify="center"
        )
        self.confirm_pin_entry.pack(padx=35, fill="x", ipady=9)

        tk.Label(frame, text="Confirm PIN", font=("Segoe UI", 10), fg=MUTED, bg=BG).pack(anchor="w", padx=40, pady=(4, 10))

        self.full_time_pin = tk.IntVar(value=1)

        tk.Checkbutton(
            frame, text="Use PIN full time instead of master password",
            variable=self.full_time_pin, font=("Segoe UI", 11),
            fg=TEXT, bg=BG, selectcolor=PANEL,
            activebackground=BG, activeforeground=TEXT
        ).pack(anchor="w", padx=35, pady=6)

        tk.Button(
            frame, text="Create PIN", font=("Segoe UI", 13),
            bg=BLUE, fg="#06111f", relief="flat", height=2,
            command=self.create_pin
        ).pack(padx=35, fill="x", pady=12)

        tk.Button(
            frame, text="Back", font=("Segoe UI", 12),
            fg=BLUE, bg=BG, relief="solid", bd=2, height=2,
            command=self.show_login
        ).pack(padx=35, fill="x")

    def create_pin(self):
        vault_password = self.pin_setup_password.get()
        pin = self.new_pin_entry.get()
        confirm_pin = self.confirm_pin_entry.get()

        if not self.check_password(vault_password):
            messagebox.showerror("PyPass", "Incorrect vault password.")
            return

        if not pin.isdigit():
            messagebox.showwarning("PyPass", "PIN must only contain numbers.")
            return

        if len(pin) < 4:
            messagebox.showwarning("PyPass", "PIN must be at least 4 digits.")
            return

        if pin != confirm_pin:
            messagebox.showwarning("PyPass", "PINs do not match.")
            return

        pin_salt, pin_hash = hash_value(pin)

        data = load_vault()
        data["pin_enabled"] = True
        data["pin_full_time"] = bool(self.full_time_pin.get())
        data["pin_salt"] = pin_salt
        data["pin_hash"] = pin_hash
        save_vault(data)

        messagebox.showinfo("PyPass", "Your PIN has been created.")
        self.show_vault()

    def bottom_nav(self, parent, active):
        nav = tk.Frame(parent, bg=HEADER)
        nav.pack(side="bottom", fill="x")

        buttons = [
            ("▣\nVault", self.show_vault),
            ("↻\nGenerator", self.show_generator),
            ("✈\nSend", lambda: messagebox.showinfo("PyPass", "Send is coming soon.")),
            ("⚙\nSettings", self.show_settings)
        ]

        for label, command in buttons:
            color = BLUE if active in label else "#9ca3af"

            tk.Button(
                nav, text=label, font=("Segoe UI", 10),
                fg=color, bg=HEADER, activebackground=HEADER,
                activeforeground=color, relief="flat", command=command
            ).pack(side="left", expand=True, fill="both", pady=4)

    def show_vault(self):
        self.clean_old_deleted_items()
        self.clear()

        frame = tk.Frame(self.root, bg=BG)
        frame.pack(fill="both", expand=True)

        top = tk.Frame(frame, bg=HEADER)
        top.pack(fill="x")

        tk.Label(top, text="Vault", font=("Segoe UI", 20, "bold"), fg=TEXT, bg=HEADER).pack(side="left", padx=22, pady=18)

        tk.Button(top, text="🗑", font=("Segoe UI Emoji", 13), fg=TEXT, bg=HEADER, relief="flat", command=self.show_trash).pack(side="right", padx=(0, 10), pady=15)

        tk.Button(
            top, text="+  New", font=("Segoe UI", 12, "bold"),
            fg="#06111f", bg=BLUE, relief="flat", width=9,
            height=1, command=self.show_new_login
        ).pack(side="right", padx=(0, 10), pady=15)

        self.avatar(top).pack(side="right", padx=10)

        content = tk.Frame(frame, bg=BG)
        content.pack(fill="both", expand=True)

        welcome = tk.Frame(content, bg="#1e3a8a", highlightbackground=BLUE, highlightthickness=1)
        welcome.pack(fill="x", padx=20, pady=14)

        tk.Label(welcome, text="Welcome to your vault!", font=("Segoe UI", 15, "bold"), fg=TEXT, bg="#1e3a8a").pack(anchor="w", padx=16, pady=(12, 4))
        tk.Label(
            welcome,
            text="• Add passwords for easy access\n• Search your vault\n• Manage your saved items safely",
            font=("Segoe UI", 11), fg=TEXT, bg="#1e3a8a", justify="left"
        ).pack(anchor="w", padx=20, pady=(0, 12))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh_items_list())

        search = tk.Entry(
            content, textvariable=self.search_var, font=("Segoe UI", 13),
            bg=BG, fg=TEXT, insertbackground=TEXT, relief="solid", bd=2
        )
        search.pack(padx=20, fill="x", ipady=8)

        tk.Label(content, text="Search vault", font=("Segoe UI", 9), fg=MUTED, bg=BG).pack(anchor="w", padx=24, pady=(2, 4))

        self.items_area = tk.Frame(content, bg=BG)
        self.items_area.pack(fill="both", expand=True)

        self.refresh_items_list()
        self.bottom_nav(frame, "Vault")

    def refresh_items_list(self):
        for widget in self.items_area.winfo_children():
            widget.destroy()

        data = load_vault()
        items = data.get("items", [])
        query = self.search_var.get().lower().strip()

        filtered = []
        for item in items:
            if (
                query in item.get("name", "").lower()
                or query in item.get("username", "").lower()
                or query in item.get("website", "").lower()
            ):
                filtered.append(item)

        tk.Label(
            self.items_area,
            text=f"All items                                                {len(filtered)}",
            font=("Segoe UI", 12, "bold"), fg=TEXT, bg=BG
        ).pack(anchor="w", padx=25, pady=(12, 8))

        if not filtered:
            empty = tk.Frame(self.items_area, bg=PANEL)
            empty.pack(fill="x", padx=20, pady=8)

            tk.Label(empty, text="No passwords found.", font=("Segoe UI", 14, "bold"), fg="#e5e7eb", bg=PANEL).pack(pady=(20, 4))
            tk.Label(empty, text="Click “New” to add a password.", font=("Segoe UI", 11), fg=MUTED, bg=PANEL).pack(pady=(0, 20))
            return

        for item in filtered:
            self.password_item_box(self.items_area, item)

    def password_item_box(self, parent, item):
        box = tk.Frame(parent, bg=PANEL)
        box.pack(fill="x", padx=20, pady=5)

        tk.Label(box, text="🌐", font=("Segoe UI Emoji", 17), fg=MUTED, bg=PANEL).pack(side="left", padx=(12, 10), pady=10)

        text_area = tk.Frame(box, bg=PANEL)
        text_area.pack(side="left", fill="x", expand=True, pady=8)

        tk.Label(text_area, text=item.get("name", "Untitled"), font=("Segoe UI", 12, "bold"), fg=TEXT, bg=PANEL).pack(anchor="w")
        tk.Label(text_area, text=item.get("username", ""), font=("Segoe UI", 10), fg="#93c5fd", bg=PANEL).pack(anchor="w")

        tk.Button(box, text="✎", font=("Segoe UI", 13, "bold"), fg=TEXT, bg=PANEL, relief="flat", command=lambda i=item: self.show_edit_login(i)).pack(side="right", padx=4)
        tk.Button(box, text="⧉", font=("Segoe UI", 13, "bold"), fg=TEXT, bg=PANEL, relief="flat", command=lambda i=item: self.copy_password(i)).pack(side="right", padx=4)
        tk.Button(box, text="⋮", font=("Segoe UI", 16, "bold"), fg=TEXT, bg=PANEL, relief="flat", command=lambda i=item: self.delete_item(i)).pack(side="right", padx=(4, 10))

    def copy_password(self, item):
        self.root.clipboard_clear()
        self.root.clipboard_append(item.get("password", ""))
        messagebox.showinfo("PyPass", "Password copied to clipboard.")

    def delete_item(self, item):
        confirm = messagebox.askyesno("PyPass", "Move this password to trash?\n\nIt will be kept for 30 days before permanent deletion.")
        if not confirm:
            return

        data = load_vault()
        item_id = item.get("id")

        data["items"] = [x for x in data.get("items", []) if x.get("id") != item_id]
        item["deleted_at"] = time.time()

        data.setdefault("deleted_items", [])
        data["deleted_items"].append(item)

        save_vault(data)
        self.refresh_items_list()

    def show_trash(self):
        self.clean_old_deleted_items()
        self.clear()

        frame = tk.Frame(self.root, bg=BG)
        frame.pack(fill="both", expand=True)

        header = tk.Frame(frame, bg=HEADER)
        header.pack(fill="x")

        tk.Button(header, text="‹", font=("Segoe UI", 22), fg=TEXT, bg=HEADER, relief="flat", command=self.show_vault).pack(side="left", padx=(12, 4), pady=10)
        tk.Label(header, text="Trash", font=("Segoe UI", 20, "bold"), fg=TEXT, bg=HEADER).pack(side="left", pady=18)

        content = tk.Frame(frame, bg=BG)
        content.pack(fill="both", expand=True)

        tk.Label(content, text="Deleted passwords are kept for 30 days.", font=("Segoe UI", 11), fg=MUTED, bg=BG).pack(anchor="w", padx=20, pady=16)

        data = load_vault()
        deleted = data.get("deleted_items", [])

        if not deleted:
            empty = tk.Frame(content, bg=PANEL)
            empty.pack(fill="x", padx=20, pady=8)

            tk.Label(empty, text="Trash is empty.", font=("Segoe UI", 14, "bold"), fg=TEXT, bg=PANEL).pack(pady=(20, 4))
            tk.Label(empty, text="Deleted passwords will appear here.", font=("Segoe UI", 11), fg=MUTED, bg=PANEL).pack(pady=(0, 20))
        else:
            for item in deleted:
                box = tk.Frame(content, bg=PANEL)
                box.pack(fill="x", padx=20, pady=5)

                left = tk.Frame(box, bg=PANEL)
                left.pack(side="left", fill="x", expand=True, padx=14, pady=10)

                days_left = 30 - int((time.time() - item.get("deleted_at", time.time())) // 86400)

                tk.Label(left, text=item.get("name", "Untitled"), font=("Segoe UI", 12, "bold"), fg=TEXT, bg=PANEL).pack(anchor="w")
                tk.Label(left, text=f"{item.get('username', '')} • {days_left} days left", font=("Segoe UI", 10), fg="#93c5fd", bg=PANEL).pack(anchor="w")

                tk.Button(box, text="Restore", font=("Segoe UI", 10, "bold"), fg="#06111f", bg=BLUE, relief="flat", command=lambda i=item: self.restore_item(i)).pack(side="right", padx=8)
                tk.Button(box, text="Delete", font=("Segoe UI", 10, "bold"), fg=TEXT, bg=DANGER, relief="flat", command=lambda i=item: self.permanent_delete_item(i)).pack(side="right", padx=8)

    def restore_item(self, item):
        data = load_vault()
        item_id = item.get("id")

        data["deleted_items"] = [x for x in data.get("deleted_items", []) if x.get("id") != item_id]
        item.pop("deleted_at", None)

        data.setdefault("items", [])
        data["items"].append(item)

        save_vault(data)
        self.show_trash()

    def permanent_delete_item(self, item):
        confirm = messagebox.askyesno("PyPass", "Permanently delete this password? This cannot be undone.")
        if not confirm:
            return

        data = load_vault()
        item_id = item.get("id")
        data["deleted_items"] = [x for x in data.get("deleted_items", []) if x.get("id") != item_id]
        save_vault(data)
        self.show_trash()

    def show_new_login(self):
        self.show_login_editor(mode="new")

    def show_edit_login(self, item):
        self.show_login_editor(mode="edit", item=item)

    def show_login_editor(self, mode="new", item=None):
        self.clear()

        is_edit = mode == "edit"
        item = item or {}

        frame = tk.Frame(self.root, bg=BG)
        frame.pack(fill="both", expand=True)

        header = tk.Frame(frame, bg=HEADER)
        header.pack(fill="x")

        tk.Button(header, text="‹", font=("Segoe UI", 22), fg=TEXT, bg=HEADER, activebackground=HEADER, activeforeground=TEXT, relief="flat", command=self.show_vault).pack(side="left", padx=(12, 4), pady=10)

        tk.Label(header, text="Edit Login" if is_edit else "New Login", font=("Segoe UI", 20, "bold"), fg=TEXT, bg=HEADER).pack(side="left", pady=18)

        content = tk.Frame(frame, bg=BG)
        content.pack(fill="both", expand=True, padx=20, pady=14)

        tk.Label(content, text="Item details", font=("Segoe UI", 11, "bold"), fg=TEXT, bg=BG).pack(anchor="w", pady=(0, 8))

        details = tk.Frame(content, bg=PANEL, highlightbackground="#334155", highlightthickness=1)
        details.pack(fill="x", pady=(0, 14))

        tk.Label(details, text="Item name", font=("Segoe UI", 10), fg=MUTED, bg=PANEL).pack(anchor="w", padx=16, pady=(12, 2))

        self.item_name_entry = tk.Entry(details, font=("Segoe UI", 12), bg=PANEL, fg=TEXT, insertbackground=TEXT, relief="solid", bd=1)
        self.item_name_entry.pack(fill="x", padx=16, pady=(0, 10), ipady=8)
        self.item_name_entry.insert(0, item.get("name", ""))

        tk.Label(details, text="Owner", font=("Segoe UI", 10), fg=MUTED, bg=PANEL).pack(anchor="w", padx=16, pady=(0, 2))

        owner = tk.Entry(details, font=("Segoe UI", 12), bg="#1f2937", fg="#9ca3af", relief="solid", bd=1)
        owner.pack(fill="x", padx=16, pady=(0, 10), ipady=8)
        owner.insert(0, "Coming soon")
        owner.config(state="disabled")

        tk.Label(details, text="Folder", font=("Segoe UI", 10), fg=MUTED, bg=PANEL).pack(anchor="w", padx=16, pady=(0, 2))

        folder = tk.Entry(details, font=("Segoe UI", 12), bg="#1f2937", fg="#9ca3af", relief="solid", bd=1)
        folder.pack(fill="x", padx=16, pady=(0, 16), ipady=8)
        folder.insert(0, "-- Select --")
        folder.config(state="disabled")

        tk.Label(content, text="Login credentials", font=("Segoe UI", 11, "bold"), fg=TEXT, bg=BG).pack(anchor="w", pady=(0, 8))

        creds = tk.Frame(content, bg=PANEL, highlightbackground="#334155", highlightthickness=1)
        creds.pack(fill="x", pady=(0, 14))

        tk.Label(creds, text="Username", font=("Segoe UI", 10), fg=MUTED, bg=PANEL).pack(anchor="w", padx=16, pady=(12, 2))

        self.login_username_entry = tk.Entry(creds, font=("Segoe UI", 12), bg=PANEL, fg=TEXT, insertbackground=TEXT, relief="solid", bd=1)
        self.login_username_entry.pack(fill="x", padx=16, pady=(0, 10), ipady=8)
        self.login_username_entry.insert(0, item.get("username", ""))

        tk.Label(creds, text="Password", font=("Segoe UI", 10), fg=MUTED, bg=PANEL).pack(anchor="w", padx=16, pady=(0, 2))

        self.login_password_entry = tk.Entry(creds, font=("Segoe UI", 12), bg=PANEL, fg=TEXT, insertbackground=TEXT, relief="solid", bd=1)
        self.login_password_entry.pack(fill="x", padx=16, pady=(0, 6), ipady=8)
        self.login_password_entry.insert(0, item.get("password", ""))

        tk.Button(creds, text="Generate strong password", font=("Segoe UI", 10), fg=BLUE, bg=PANEL, relief="flat", command=self.fill_generated_password).pack(anchor="w", padx=12, pady=(0, 12))

        tk.Label(content, text="Autofill options", font=("Segoe UI", 11, "bold"), fg=TEXT, bg=BG).pack(anchor="w", pady=(0, 8))

        autofill = tk.Frame(content, bg=PANEL, highlightbackground="#334155", highlightthickness=1)
        autofill.pack(fill="x", pady=(0, 14))

        tk.Label(autofill, text="Website URI", font=("Segoe UI", 10), fg=MUTED, bg=PANEL).pack(anchor="w", padx=16, pady=(12, 2))

        self.website_entry = tk.Entry(autofill, font=("Segoe UI", 12), bg=PANEL, fg=TEXT, insertbackground=TEXT, relief="solid", bd=1)
        self.website_entry.pack(fill="x", padx=16, pady=(0, 16), ipady=8)
        self.website_entry.insert(0, item.get("website", ""))

        buttons = tk.Frame(frame, bg=HEADER)
        buttons.pack(side="bottom", fill="x")

        save_command = self.save_new_login if not is_edit else lambda: self.save_edited_login(item.get("id"))

        tk.Button(buttons, text="Save", font=("Segoe UI", 12, "bold"), fg="#06111f", bg=BLUE, relief="flat", width=8, command=save_command).pack(side="left", padx=(20, 8), pady=12)
        tk.Button(buttons, text="Cancel", font=("Segoe UI", 12, "bold"), fg=BLUE, bg=HEADER, relief="solid", bd=2, width=8, command=self.show_vault).pack(side="left", padx=8, pady=12)

    def fill_generated_password(self):
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        generated = "".join(random.choice(chars) for _ in range(25))
        self.login_password_entry.delete(0, "end")
        self.login_password_entry.insert(0, generated)

    def save_new_login(self):
        item_name = self.item_name_entry.get().strip()
        login_username = self.login_username_entry.get().strip()
        login_password = self.login_password_entry.get().strip()
        website = self.website_entry.get().strip()

        if not item_name:
            messagebox.showwarning("PyPass", "Item name is required.")
            return
        if not login_username:
            messagebox.showwarning("PyPass", "Username is required.")
            return
        if not login_password:
            messagebox.showwarning("PyPass", "Password is required.")
            return

        data = load_vault()

        new_item = {
            "id": str(uuid.uuid4()),
            "name": item_name,
            "username": login_username,
            "password": login_password,
            "website": website,
            "owner": "Coming soon",
            "folder": "",
            "type": "login",
            "created_at": time.time(),
            "updated_at": time.time()
        }

        data.setdefault("items", [])
        data["items"].append(new_item)
        save_vault(data)

        messagebox.showinfo("PyPass", "New login saved.")
        self.show_vault()

    def save_edited_login(self, item_id):
        item_name = self.item_name_entry.get().strip()
        login_username = self.login_username_entry.get().strip()
        login_password = self.login_password_entry.get().strip()
        website = self.website_entry.get().strip()

        if not item_name:
            messagebox.showwarning("PyPass", "Item name is required.")
            return
        if not login_username:
            messagebox.showwarning("PyPass", "Username is required.")
            return
        if not login_password:
            messagebox.showwarning("PyPass", "Password is required.")
            return

        data = load_vault()

        for item in data.get("items", []):
            if item.get("id") == item_id:
                item["name"] = item_name
                item["username"] = login_username
                item["password"] = login_password
                item["website"] = website
                item["updated_at"] = time.time()
                break

        save_vault(data)
        messagebox.showinfo("PyPass", "Login updated.")
        self.show_vault()

    def make_header(self, parent, title):
        header = tk.Frame(parent, bg=HEADER)
        header.pack(fill="x")

        tk.Label(header, text=title, font=("Segoe UI", 20, "bold"), fg=TEXT, bg=HEADER).pack(side="left", padx=22, pady=18)
        self.avatar(header).pack(side="right", padx=22)

    def show_generator(self):
        self.clear()

        frame = tk.Frame(self.root, bg=BG)
        frame.pack(fill="both", expand=True)

        self.make_header(frame, "Generator")

        content = tk.Frame(frame, bg=BG)
        content.pack(fill="both", expand=True)

        tabs = tk.Frame(content, bg=BG, highlightbackground=BLUE, highlightthickness=1)
        tabs.pack(fill="x", padx=20, pady=(14, 14))

        for mode in ["Password", "Passphrase", "Username"]:
            selected = self.generator_mode == mode
            tk.Button(
                tabs, text=mode, font=("Segoe UI", 11, "bold"),
                fg="#06111f" if selected else BLUE,
                bg=BLUE if selected else BG,
                activebackground=BLUE, relief="flat", height=2,
                command=lambda m=mode: self.switch_generator(m)
            ).pack(side="left", expand=True, fill="x")

        self.generate_value()

        output = tk.Frame(content, bg=PANEL, highlightbackground="#334155", highlightthickness=1)
        output.pack(fill="x", padx=20, pady=(0, 14))

        tk.Label(output, textvariable=self.generated_value, font=("Consolas", 12, "bold"), fg=TEXT, bg=PANEL, wraplength=320, justify="left").pack(side="left", padx=15, pady=20, fill="x", expand=True)

        tk.Button(output, text="↻", font=("Segoe UI", 15, "bold"), fg=TEXT, bg=PANEL, relief="flat", command=self.refresh_generator).pack(side="right", padx=8)
        tk.Button(output, text="📋", font=("Segoe UI Emoji", 13), fg=TEXT, bg=PANEL, relief="flat", command=self.copy_generated).pack(side="right")

        tk.Label(content, text="Options", font=("Segoe UI", 12, "bold"), fg=TEXT, bg=BG).pack(anchor="w", padx=20)

        if self.generator_mode == "Password":
            self.password_options(content)
        elif self.generator_mode == "Passphrase":
            self.passphrase_options(content)
        else:
            self.username_options(content)

        history = tk.Frame(content, bg=PANEL)
        history.pack(fill="x", padx=20, pady=14)

        tk.Label(history, text="Generator history                                      ❯", font=("Segoe UI", 11), fg=TEXT, bg=PANEL).pack(anchor="w", padx=16, pady=12)

        self.bottom_nav(frame, "Generator")

    def switch_generator(self, mode):
        self.generator_mode = mode
        self.show_generator()

    def generate_value(self):
        if self.generator_mode == "Password":
            chars = string.ascii_letters + string.digits + "!@#$%^&*"
            value = "".join(random.choice(chars) for _ in range(25))
        elif self.generator_mode == "Passphrase":
            words = ["showplace", "unpaid", "penalize", "pandemic", "flounder", "hemlock", "silver", "rocket", "orange", "window", "forest", "laptop"]
            value = "-".join(random.choice(words) for _ in range(6))
        else:
            words = ["luncheon", "skylark", "pixel", "vault", "python", "river", "nova", "cloud"]
            value = random.choice(words)

        self.generated_value.set(value)

    def refresh_generator(self):
        self.generate_value()

    def copy_generated(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.generated_value.get())
        messagebox.showinfo("PyPass", "Copied to clipboard.")

    def password_options(self, parent):
        box = tk.Frame(parent, bg=PANEL, highlightbackground="#334155", highlightthickness=1)
        box.pack(fill="x", padx=20, pady=8)

        tk.Label(box, text="Length", font=("Segoe UI", 11), fg="#93c5fd", bg=PANEL).pack(anchor="w", padx=16, pady=(14, 0))

        spin = tk.Spinbox(box, from_=5, to=128, font=("Segoe UI", 12), bg=PANEL, fg=TEXT, insertbackground=TEXT, relief="solid", bd=1)
        spin.delete(0, "end")
        spin.insert(0, "25")
        spin.pack(fill="x", padx=16, pady=5)

        tk.Label(box, text="Value must be between 5 and 128.", font=("Segoe UI", 10), fg="#93c5fd", bg=PANEL).pack(anchor="w", padx=16, pady=(0, 14))

        include = tk.Frame(parent, bg=PANEL, highlightbackground="#334155", highlightthickness=1)
        include.pack(fill="x", padx=20, pady=8)

        tk.Label(include, text="Include", font=("Segoe UI", 12, "bold"), fg=TEXT, bg=PANEL).pack(anchor="w", padx=16, pady=(14, 8))

        row = tk.Frame(include, bg=PANEL)
        row.pack(anchor="w", padx=12)

        for text in ["A-Z", "a-z", "0-9", "!@#$%^&*"]:
            var = tk.IntVar(value=1)
            tk.Checkbutton(row, text=text, variable=var, font=("Segoe UI", 10), fg=TEXT, bg=PANEL, selectcolor=BLUE, activebackground=PANEL, activeforeground=TEXT).pack(side="left", padx=4)

        tk.Checkbutton(include, text="Avoid ambiguous characters", font=("Segoe UI", 10), fg=TEXT, bg=PANEL, selectcolor=BG, activebackground=PANEL, activeforeground=TEXT).pack(anchor="w", padx=16, pady=(8, 14))

    def passphrase_options(self, parent):
        box = tk.Frame(parent, bg=PANEL, highlightbackground="#334155", highlightthickness=1)
        box.pack(fill="x", padx=20, pady=8)

        tk.Label(box, text="Number of words", font=("Segoe UI", 11), fg="#93c5fd", bg=PANEL).pack(anchor="w", padx=16, pady=(14, 0))

        spin = tk.Spinbox(box, from_=3, to=20, font=("Segoe UI", 12), bg=PANEL, fg=TEXT, relief="solid", bd=1)
        spin.delete(0, "end")
        spin.insert(0, "6")
        spin.pack(fill="x", padx=16, pady=5)

        tk.Label(box, text="Value must be between 3 and 20. Use 6 words or more to generate a strong passphrase.", font=("Segoe UI", 10), fg="#93c5fd", bg=PANEL, wraplength=430, justify="left").pack(anchor="w", padx=16, pady=(0, 14))

    def username_options(self, parent):
        box = tk.Frame(parent, bg=PANEL, highlightbackground="#334155", highlightthickness=1)
        box.pack(fill="x", padx=20, pady=8)

        tk.Label(box, text="Type", font=("Segoe UI", 11), fg="#93c5fd", bg=PANEL).pack(anchor="w", padx=16, pady=(14, 0))

        tk.Label(box, text="Random word                                      ⌄", font=("Segoe UI", 12), fg=TEXT, bg=PANEL, highlightbackground=MUTED, highlightthickness=1).pack(fill="x", padx=16, pady=6, ipady=8)

    def show_settings(self):
        self.clear()

        frame = tk.Frame(self.root, bg=BG)
        frame.pack(fill="both", expand=True)

        header = tk.Frame(frame, bg=HEADER)
        header.pack(fill="x")

        tk.Label(header, text="Settings", font=("Segoe UI", 20, "bold"), fg=TEXT, bg=HEADER).pack(side="left", padx=22, pady=18)
        self.avatar(header).pack(side="right", padx=22)

        content = tk.Frame(frame, bg=BG)
        content.pack(fill="both", expand=True, padx=20, pady=14)

        self.settings_row(content, "🔒  Vault options", self.show_vault_options)
        self.settings_row(content, "ⓘ  About", self.show_about)

        self.bottom_nav(frame, "Settings")

    def settings_row(self, parent, text, command):
        row = tk.Button(
            parent,
            text=f"{text}                                                        ❯",
            font=("Segoe UI", 12, "bold"),
            fg=TEXT,
            bg=PANEL,
            activebackground="#1f2937",
            activeforeground=TEXT,
            relief="flat",
            anchor="w",
            command=command
        )
        row.pack(fill="x", pady=5, ipady=12)

    def show_vault_options(self):
        self.clear()

        frame = tk.Frame(self.root, bg=BG)
        frame.pack(fill="both", expand=True)

        header = tk.Frame(frame, bg=HEADER)
        header.pack(fill="x")

        tk.Button(header, text="‹", font=("Segoe UI", 22), fg=TEXT, bg=HEADER, relief="flat", command=self.show_settings).pack(side="left", padx=(12, 4), pady=10)
        tk.Label(header, text="Vault options", font=("Segoe UI", 20, "bold"), fg=TEXT, bg=HEADER).pack(side="left", pady=18)

        content = tk.Frame(frame, bg=BG)
        content.pack(fill="both", expand=True, padx=20, pady=18)

        tk.Button(
            content,
            text="Export vault",
            font=("Segoe UI", 12, "bold"),
            fg=TEXT,
            bg=PANEL,
            activebackground="#1f2937",
            relief="flat",
            anchor="w",
            command=self.export_vault
        ).pack(fill="x", pady=6, ipady=12)

        tk.Button(
            content,
            text="Purge vault",
            font=("Segoe UI", 12, "bold"),
            fg=TEXT,
            bg=DANGER,
            activebackground="#b91c1c",
            relief="flat",
            anchor="w",
            command=self.purge_vault
        ).pack(fill="x", pady=6, ipady=12)

    def export_vault(self):
        if not os.path.exists(VAULT_FILE):
            messagebox.showerror("PyPass", "No vault file found.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            initialfile="pypass_vault_export.json"
        )

        if not path:
            return

        shutil.copyfile(VAULT_FILE, path)
        messagebox.showinfo("PyPass", "Vault exported successfully.")

    def purge_vault(self):
        confirm = messagebox.askyesno(
            "PyPass",
            "This will permanently delete all saved and deleted passwords from your vault.\n\nYour master password and PIN settings will stay.\n\nContinue?"
        )

        if not confirm:
            return

        data = load_vault()
        data["items"] = []
        data["deleted_items"] = []
        data["generator_history"] = []
        save_vault(data)

        messagebox.showinfo("PyPass", "Vault purged.")
        self.show_vault_options()

    def show_about(self):
        self.clear()

        frame = tk.Frame(self.root, bg=BG)
        frame.pack(fill="both", expand=True)

        header = tk.Frame(frame, bg=HEADER)
        header.pack(fill="x")

        tk.Button(header, text="‹", font=("Segoe UI", 22), fg=TEXT, bg=HEADER, relief="flat", command=self.show_settings).pack(side="left", padx=(12, 4), pady=10)
        tk.Label(header, text="About", font=("Segoe UI", 20, "bold"), fg=TEXT, bg=HEADER).pack(side="left", pady=18)

        content = tk.Frame(frame, bg=BG)
        content.pack(fill="both", expand=True, padx=20, pady=30)

        tk.Label(content, text="🔐", font=("Segoe UI Emoji", 64), fg=BLUE, bg=BG).pack(pady=(10, 8))
        tk.Label(content, text="PyPass v1.0", font=("Segoe UI", 22, "bold"), fg=TEXT, bg=BG).pack()
        tk.Label(content, text="Author: Skylar Myers", font=("Segoe UI", 13), fg=MUTED, bg=BG).pack(pady=(8, 22))

        tk.Button(
            content,
            text="Licenses",
            font=("Segoe UI", 12, "bold"),
            fg="#06111f",
            bg=BLUE,
            relief="flat",
            width=14,
            command=self.show_licenses
        ).pack(pady=10, ipady=8)

        tk.Label(frame, text="2026 ® Skylar Myers", font=("Segoe UI", 9), fg=MUTED, bg=BG).pack(side="bottom", anchor="e", padx=12, pady=10)

    def show_licenses(self):
        messagebox.showinfo(
            "PyPass Licenses",
            "PyPass Community Edition is open source and free to use, study, and modify.\n\n"
            "PyPass Business Edition is not open source. It may not be edited, modified, redistributed, or reverse engineered without written permission.\n\n"
            "© 2026 Skylar Myers"
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = PyPassApp(root)
    root.mainloop()