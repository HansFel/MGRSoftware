import tkinter as tk
from tkinter import filedialog, messagebox
import psycopg2
from psycopg2 import sql as psql
import os

class PostgresDBCreator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('PostgreSQL Datenbank anlegen und Schema importieren')
        self.geometry('500x350')
        self.create_widgets()

    def create_widgets(self):
        row = 0
        tk.Label(self, text='Server (Host/IP):').grid(row=row, column=0, sticky='e', padx=5, pady=5)
        self.host_entry = tk.Entry(self, width=30)
        self.host_entry.grid(row=row, column=1, padx=5, pady=5)
        row += 1

        tk.Label(self, text='Port:').grid(row=row, column=0, sticky='e', padx=5, pady=5)
        self.port_entry = tk.Entry(self, width=30)
        self.port_entry.insert(0, '5432')
        self.port_entry.grid(row=row, column=1, padx=5, pady=5)
        row += 1

        tk.Label(self, text='Admin-User:').grid(row=row, column=0, sticky='e', padx=5, pady=5)
        self.admin_user_entry = tk.Entry(self, width=30)
        self.admin_user_entry.insert(0, 'postgres')
        self.admin_user_entry.grid(row=row, column=1, padx=5, pady=5)
        row += 1

        tk.Label(self, text='Admin-Passwort:').grid(row=row, column=0, sticky='e', padx=5, pady=5)
        self.admin_pw_entry = tk.Entry(self, width=30, show='*')
        self.admin_pw_entry.grid(row=row, column=1, padx=5, pady=5)
        row += 1

        tk.Label(self, text='Neue Datenbank:').grid(row=row, column=0, sticky='e', padx=5, pady=5)
        self.db_name_entry = tk.Entry(self, width=30)
        self.db_name_entry.insert(0, 'maschinengemeinschaft')
        self.db_name_entry.grid(row=row, column=1, padx=5, pady=5)
        row += 1

        tk.Label(self, text='DB-User:').grid(row=row, column=0, sticky='e', padx=5, pady=5)
        self.db_user_entry = tk.Entry(self, width=30)
        self.db_user_entry.insert(0, 'mgr')
        self.db_user_entry.grid(row=row, column=1, padx=5, pady=5)
        row += 1

        tk.Label(self, text='DB-Passwort:').grid(row=row, column=0, sticky='e', padx=5, pady=5)
        self.db_pw_entry = tk.Entry(self, width=30, show='*')
        self.db_pw_entry.grid(row=row, column=1, padx=5, pady=5)
        row += 1

        tk.Label(self, text='Schema-SQL-Datei:').grid(row=row, column=0, sticky='e', padx=5, pady=5)
        self.schema_path = tk.StringVar()
        tk.Entry(self, textvariable=self.schema_path, width=30).grid(row=row, column=1, padx=5, pady=5)
        tk.Button(self, text='Durchsuchen...', command=self.browse_schema).grid(row=row, column=2, padx=5, pady=5)
        row += 1

        tk.Button(self, text='Datenbank anlegen & Schema importieren', command=self.create_db_and_import_schema).grid(row=row, column=0, columnspan=3, pady=15)

        tk.Label(self, text='Hinweis: Schema muss PostgreSQL-Syntax verwenden (SERIAL statt AUTOINCREMENT)', fg='gray').grid(row=row+1, column=0, columnspan=3, pady=5)

    def browse_schema(self):
        file_path = filedialog.askopenfilename(title='SQL-Schema auswählen', filetypes=[('SQL-Dateien', '*.sql')])
        if file_path:
            self.schema_path.set(file_path)


    def show_error_window(self, title, message):
        win = tk.Toplevel(self)
        win.title(title)
        win.geometry('600x300')
        tk.Label(win, text=title, fg='red', font=('Arial', 12, 'bold')).pack(pady=8)
        text = tk.Text(win, wrap='word', height=10)
        text.insert('1.0', message)
        text.config(state='normal')
        text.pack(expand=True, fill='both', padx=10, pady=5)
        text.focus_set()
        tk.Button(win, text='Schließen', command=win.destroy).pack(pady=8)

    def create_db_and_import_schema(self):
        host = self.host_entry.get().strip()
        port = self.port_entry.get().strip()
        admin_user = self.admin_user_entry.get().strip()
        admin_pw = self.admin_pw_entry.get().strip()
        db_name = self.db_name_entry.get().strip()
        db_user = self.db_user_entry.get().strip()
        db_pw = self.db_pw_entry.get().strip()
        schema_file = self.schema_path.get().strip()

        if not all([host, port, admin_user, admin_pw, db_name, db_user, db_pw, schema_file]):
            self.show_error_window('Fehler', 'Bitte alle Felder ausfüllen!')
            return
        if not os.path.isfile(schema_file):
            self.show_error_window('Fehler', 'Schema-Datei nicht gefunden!')
            return
        try:
            # 1. Datenbank anlegen
            conn = psycopg2.connect(host=host, port=port, user=admin_user, password=admin_pw, dbname='postgres')
            conn.autocommit = True
            cur = conn.cursor()
            try:
                cur.execute(psql.SQL("CREATE DATABASE {}").format(psql.Identifier(db_name)))
            except Exception as e:
                if 'already exists' in str(e):
                    if not messagebox.askyesno('Warnung', f'Datenbank {db_name} existiert bereits. Fortfahren und Schema importieren?'):
                        cur.close()
                        conn.close()
                        return
                else:
                    raise
            cur.close()
            conn.close()

            # 2. Mit neuer DB verbinden und Schema importieren
            conn = psycopg2.connect(host=host, port=port, user=db_user, password=db_pw, dbname=db_name)
            cur = conn.cursor()
            with open(schema_file, 'r', encoding='utf-8') as f:
                sql = f.read()
                cur.execute(sql)
            conn.commit()
            cur.close()
            conn.close()
            messagebox.showinfo('Erfolg', 'Datenbank und Schema erfolgreich erstellt!')
        except Exception as e:
            self.show_error_window('Fehler', str(e))

if __name__ == '__main__':
    app = PostgresDBCreator()
    app.mainloop()
