#!/usr/bin/env python3
"""
Maschinengemeinschaft - Lokaler Launcher
Ermöglicht das einfache Starten der Anwendung mit Datenbankauswahl
"""

import sys
import os
import webbrowser
import time
import threading
import socket
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess

class LauncherGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Maschinengemeinschaft - Lokaler Server")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        self.db_path = None
        self.server_process = None
        self.port = 5000
        self._new_db_created = False
        
        self.setup_ui()
        
    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#2c3e50", height=80)
        header.pack(fill=tk.X)
        
        title = tk.Label(header, text="Maschinengemeinschaft", 
                        font=("Arial", 20, "bold"), fg="white", bg="#2c3e50")
        title.pack(pady=20)
        
        # Main Content
        content = tk.Frame(self.root, padx=20, pady=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Anleitung
        info_text = """Willkommen zum Übungsmodus!

So starten Sie:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Klicken Sie unten auf "Neue Datenbank erstellen"
2. Speichern Sie die Datei (z.B. Uebung.db)
3. Der Server startet automatisch
4. Ihr Browser öffnet sich automatisch

Die Anwendung läuft nur lokal auf diesem Computer."""
        
        info_label = tk.Label(content, text=info_text, justify=tk.LEFT, 
                             font=("Arial", 10))
        info_label.pack(pady=10, fill=tk.X)
        
        # Große Start-Buttons
        self.btn_container = tk.Frame(content)
        self.btn_container.pack(pady=20)
        
        # Neue Datenbank Button - größer und prominenter
        self.new_db_btn = tk.Button(self.btn_container, 
                 text="➕ Neue Datenbank erstellen\n(empfohlen für Übung)", 
                 command=self.create_and_start,
                 bg="#27ae60", fg="white", 
                 font=("Arial", 12, "bold"),
                 padx=30, pady=20,
                 relief=tk.RAISED,
                 bd=3)
        self.new_db_btn.pack(pady=10)
        
        # Bestehende Datenbank Button
        self.open_db_btn = tk.Button(self.btn_container, 
                 text="📂 Bestehende Datenbank öffnen", 
                 command=self.select_and_start,
                 bg="#3498db", fg="white", 
                 font=("Arial", 11),
                 padx=30, pady=15)
        self.open_db_btn.pack(pady=10)
        
        # Datenbank-Info
        self.db_label = tk.Label(content, text="", 
                                fg="gray", font=("Arial", 9))
        self.db_label.pack(pady=5)
        
        # Status und URL Display
        self.status_label = tk.Label(content, text="", font=("Arial", 10, "bold"), fg="blue")
        self.status_label.pack(pady=10)
        
        # Login-Info Label (für neue Datenbank)
        self.login_info_label = tk.Label(content, text="", font=("Arial", 9), 
                                         fg="#27ae60", bg="#ecf0f1", padx=10, pady=5,
                                         relief=tk.RIDGE, bd=2)
        
        self.url_frame = tk.Frame(content, bg="#ecf0f1", relief=tk.SUNKEN, bd=2)
        self.url_label = tk.Label(self.url_frame, text="", font=("Arial", 12, "bold"),
                                 fg="#2c3e50", bg="#ecf0f1", padx=20, pady=10)
        self.url_label.pack()
        
        # Stop Button (wird nur gezeigt wenn Server läuft)
        self.stop_btn = tk.Button(content, text="⏹ Server stoppen", 
                                   command=self.stop_server,
                                   bg="#e74c3c", fg="white", 
                                   font=("Arial", 11, "bold"),
                                   padx=30, pady=10)
        
    def select_and_start(self):
        """Datenbank wählen und direkt starten"""
        filepath = filedialog.askopenfilename(
            title="Datenbank wählen",
            filetypes=[("SQLite Datenbank", "*.db"), ("Alle Dateien", "*.*")],
            initialdir=os.path.join(os.path.dirname(__file__), "data"),
            parent=self.root
        )
        
        if filepath:
            self.db_path = filepath
            self.db_label.config(text=f"Datenbank: {os.path.basename(filepath)}", fg="blue")
            self.start_server()
            
    def create_and_start(self):
        """Neue Datenbank erstellen und direkt starten"""
        self.create_new_database()
        if self.db_path:  # Wenn Datenbank erfolgreich erstellt
            self.start_server()
            
    def create_new_database(self):
        filepath = filedialog.asksaveasfilename(
            title="Neue Datenbank erstellen",
            defaultextension=".db",
            filetypes=[("SQLite Datenbank", "*.db")],
            initialfile="maschinengemeinschaft_uebung.db",
            initialdir=os.path.join(os.path.dirname(__file__), "data"),
            parent=self.root
        )
        
        if filepath:
            # Stelle sicher, dass das Verzeichnis existiert
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Initialisiere leere Datenbank
            self.initialize_database(filepath)
            
            self.db_path = filepath
            self.db_label.config(text=f"Datenbank: {os.path.basename(filepath)}", fg="blue")
    
    def initialize_database(self, db_path):
        """Initialisiert eine neue Datenbank mit Schema"""
        import sqlite3
        
        schema_file = os.path.join(os.path.dirname(__file__), 'schema.sql')
        
        if not os.path.exists(schema_file):
            messagebox.showerror("Fehler", "schema.sql nicht gefunden!")
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema = f.read()
            cursor.executescript(schema)
        
        # Standard-Admin anlegen
        # Standard-Admin wird bereits durch schema.sql angelegt
        
        conn.commit()
        conn.close()
        
        # Merke dass neue DB erstellt wurde
        self._new_db_created = True
    
    def find_free_port(self):
        """Findet einen freien Port"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port
    
    def start_server(self):
        if self.server_process:
            messagebox.showwarning("Server läuft", "Der Server läuft bereits!")
            return
        
        if not self.db_path:
            messagebox.showerror("Fehler", "Bitte wählen Sie zuerst eine Datenbank!")
            return
        
        # Finde freien Port
        self.port = self.find_free_port()
        
        # Setze Umgebungsvariablen für Flask
        os.environ['DB_PATH'] = self.db_path
        os.environ['FLASK_PORT'] = str(self.port)
        
        # Starte Server in separatem Thread
        try:
            # Importiere Flask App
            from web_app import app
            
            # Starte Flask in einem Thread
            def run_flask():
                app.run(host='127.0.0.1', port=self.port, debug=False, use_reloader=False)
            
            self.server_thread = threading.Thread(target=run_flask, daemon=True)
            self.server_thread.start()
            
            # Merke dass Server läuft (wir verwenden einen Dummy-Prozess-Indikator)
            self.server_process = True
            
            # Warte kurz bis Server startet
            time.sleep(2)
            
            # Prüfe ob Server läuft (mehrere Versuche)
            server_ready = False
            for i in range(10):  # 10 Versuche à 1 Sekunde = max 10 Sekunden
                # Prüfe ob Port erreichbar ist
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex(('127.0.0.1', self.port))
                    sock.close()
                    if result == 0:
                        server_ready = True
                        break
                except:
                    pass
                time.sleep(1)
                self.status_label.config(text=f"Server startet... ({i+1}/10)")
                self.root.update()
            
            # Prüfe ob Server läuft
            if server_ready:
                url = f"http://127.0.0.1:{self.port}"
                
                # Update UI
                self.status_label.config(text="✅ Server erfolgreich gestartet!", fg="green", font=("Arial", 11, "bold"))
                
                # URL anzeigen mit Copy-Button
                url_display = tk.Frame(self.url_frame, bg="#ecf0f1")
                url_display.pack(fill=tk.X, padx=10, pady=5)
                
                url_text = tk.Entry(url_display, font=("Courier New", 12, "bold"), 
                                   fg="#2c3e50", bg="white", bd=2, relief=tk.SUNKEN,
                                   justify=tk.CENTER, width=30)
                url_text.insert(0, url)
                url_text.config(state='readonly')
                url_text.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
                
                def copy_url():
                    self.root.clipboard_clear()
                    self.root.clipboard_append(url)
                    copy_btn.config(text="✓ Kopiert!")
                    self.root.after(2000, lambda: copy_btn.config(text="📋 Kopieren"))
                
                copy_btn = tk.Button(url_display, text="📋 Kopieren", command=copy_url,
                                    bg="#3498db", fg="white", font=("Arial", 9, "bold"),
                                    padx=10, pady=5, cursor="hand2")
                copy_btn.pack(side=tk.LEFT, padx=5)
                
                hint_label = tk.Label(self.url_frame, 
                                     text="Browser öffnet sich automatisch oder URL manuell eingeben",
                                     font=("Arial", 9), fg="#7f8c8d", bg="#ecf0f1")
                hint_label.pack(pady=5)
                
                self.url_frame.pack(pady=10, fill=tk.X)
                
                self.stop_btn.pack(pady=10)
                
                # Verstecke die Start-Buttons
                self.btn_container.pack_forget()
                
                # Zeige Login-Info bei neuer Datenbank
                if self._new_db_created:
                    self.login_info_label.config(
                        text="🔑 Standard-Login:\nBenutzername: admin  |  Passwort: admin123")
                    self.login_info_label.pack(pady=5)
                    self._new_db_created = False
                
                # Browser öffnen
                threading.Thread(target=lambda: webbrowser.open(url), daemon=True).start()
            else:
                # Server konnte nicht gestartet werden
                self.server_process = None
                raise Exception(f"Server läuft, aber Port {self.port} ist nicht erreichbar.\n\nBitte warten Sie noch einen Moment und öffnen Sie dann\nhttp://127.0.0.1:{self.port} manuell im Browser.")
                
        except Exception as e:
            messagebox.showerror("Fehler", f"Server-Start fehlgeschlagen:\n{str(e)}")
            self.server_process = None
    
    def stop_server(self):
        if self.server_process:
            if messagebox.askyesno("Server stoppen", "Server wirklich stoppen?"):
                # Bei Thread-basiertem Server können wir den Thread nicht direkt stoppen
                # Wir markieren nur, dass der Server gestoppt wurde
                # Flask wird beim Schließen der Anwendung automatisch beendet (daemon thread)
                self.server_process = None
                
                self.status_label.config(text="Server gestoppt", fg="gray")
                self.url_frame.pack_forget()
                self.stop_btn.pack_forget()
                self.login_info_label.pack_forget()
                
                # Zeige Buttons wieder an
                self.btn_container.pack(pady=20)
                
                messagebox.showinfo("Server gestoppt", 
                    "Der Server wird beim Schließen der Anwendung automatisch beendet.\n\n"
                    "Sie können jetzt eine neue Datenbank starten.")
            
    def run(self):
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        if self.server_process:
            if messagebox.askokcancel("Beenden", 
                                     "Server läuft noch. Wirklich beenden?"):
                self.stop_server()
                self.root.destroy()
        else:
            self.root.destroy()

if __name__ == "__main__":
    app = LauncherGUI()
    app.run()
