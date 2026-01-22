import sqlite3
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import os

SCHEMA_FILE = "schema.sql"

# Hilfsfunktion: Lese alle Tabellennamen aus einer SQLite-DB
def get_table_names(db_path):
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        return [row[0] for row in cur.fetchall()]

# Hilfsfunktion: Führe schema.sql auf DB aus (nur fehlende Tabellen/Spalten werden ergänzt)
def apply_schema(db_path):
    with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
        schema = f.read()
    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema)
    return True

# Tabelle leeren
def clear_table(db_path, table):
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(f"DELETE FROM {table}")
        conn.commit()

# GUI
class DBRepairTool(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SQLite DB-Tool: Reparieren & Leeren")
        self.geometry("420x350")
        self.db_path = None
        self.tables = []

        self.label = tk.Label(self, text="Keine Datenbank ausgewählt.")
        self.label.pack(pady=10)

        self.btn_open = tk.Button(self, text="Datenbank auswählen", command=self.open_db)
        self.btn_open.pack(pady=5)

        self.btn_schema = tk.Button(self, text="Schema prüfen/reparieren", command=self.repair_schema, state=tk.DISABLED)
        self.btn_schema.pack(pady=5)

        self.listbox = tk.Listbox(self)
        self.listbox.pack(pady=10, fill=tk.BOTH, expand=True)

        self.btn_clear = tk.Button(self, text="Ausgewählte Tabelle leeren", command=self.clear_selected_table, state=tk.DISABLED)
        self.btn_clear.pack(pady=5)

    def open_db(self):
        path = filedialog.askopenfilename(title="SQLite-Datenbank auswählen", filetypes=[("SQLite DB", "*.db;*.sqlite;*.sqlite3"), ("Alle Dateien", "*.*")])
        if path:
            self.db_path = path
            self.label.config(text=f"Datenbank: {os.path.basename(path)}")
            self.refresh_tables()
            self.btn_schema.config(state=tk.NORMAL)
            self.btn_clear.config(state=tk.NORMAL)

    def refresh_tables(self):
        if not self.db_path:
            return
        self.tables = get_table_names(self.db_path)
        self.listbox.delete(0, tk.END)
        for t in self.tables:
            self.listbox.insert(tk.END, t)

    def repair_schema(self):
        if not self.db_path:
            return
        try:
            apply_schema(self.db_path)
            messagebox.showinfo("Fertig", "Schema wurde geprüft und ggf. repariert.")
            self.refresh_tables()
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Reparieren: {e}")

    def clear_selected_table(self):
        if not self.db_path:
            return
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Hinweis", "Bitte zuerst eine Tabelle auswählen.")
            return
        table = self.tables[sel[0]]
        if messagebox.askyesno("Tabelle leeren", f"Alle Daten aus '{table}' unwiderruflich löschen?"):
            try:
                clear_table(self.db_path, table)
                messagebox.showinfo("Erfolg", f"Tabelle '{table}' wurde geleert.")
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Leeren: {e}")

if __name__ == "__main__":
    app = DBRepairTool()
    app.mainloop()
