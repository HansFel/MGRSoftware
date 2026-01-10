"""
GUI-Anwendung für Maschinengemeinschaft
Hauptanwendung mit Tkinter
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from database import MaschinenDBContext
import os


class MaschinenGUI:
    """Hauptfenster der Anwendung"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Maschinengemeinschaft - Verwaltungssoftware")
        self.root.geometry("1200x700")
        
        # Datenbank initialisieren
        self.db_path = os.path.join(os.path.dirname(__file__), 
                                     "maschinengemeinschaft.db")
        self.init_database()
        
        # GUI erstellen
        self.create_menu()
        self.create_widgets()
        
        # Daten laden
        self.refresh_all()
    
    def init_database(self):
        """Datenbank initialisieren falls nötig"""
        if not os.path.exists(self.db_path):
            with MaschinenDBContext(self.db_path) as db:
                db.init_database()
    
    def create_menu(self):
        """Menüleiste erstellen"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Datei-Menü
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Datei", menu=file_menu)
        file_menu.add_command(label="Datenbank initialisieren", 
                             command=self.init_database)
        file_menu.add_separator()
        file_menu.add_command(label="Beenden", command=self.root.quit)
        
        # Stammdaten-Menü
        stammdaten_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Stammdaten", menu=stammdaten_menu)
        stammdaten_menu.add_command(label="Benutzer verwalten", 
                                   command=self.open_benutzer_window)
        stammdaten_menu.add_command(label="Maschinen verwalten", 
                                   command=self.open_maschinen_window)
        stammdaten_menu.add_command(label="Einsatzzwecke verwalten", 
                                   command=self.open_einsatzzwecke_window)
        
        # Hilfe-Menü
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Hilfe", menu=help_menu)
        help_menu.add_command(label="Über", command=self.show_about)
    
    def create_widgets(self):
        """Hauptfenster-Widgets erstellen"""
        # Notebook für Tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Tab 1: Neuer Einsatz
        self.create_einsatz_tab()
        
        # Tab 2: Einsätze anzeigen
        self.create_uebersicht_tab()
        
        # Tab 3: Statistiken
        self.create_statistik_tab()
    
    def create_einsatz_tab(self):
        """Tab für neuen Einsatz erstellen"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Neuer Einsatz")
        
        # Formular
        form_frame = ttk.LabelFrame(frame, text="Einsatz erfassen", padding=20)
        form_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        row = 0
        
        # Datum
        ttk.Label(form_frame, text="Datum:").grid(row=row, column=0, sticky='w', pady=5)
        self.datum_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(form_frame, textvariable=self.datum_var, width=30).grid(
            row=row, column=1, sticky='w', pady=5)
        row += 1
        
        # Benutzer
        ttk.Label(form_frame, text="Benutzer:").grid(row=row, column=0, sticky='w', pady=5)
        self.benutzer_var = tk.StringVar()
        self.benutzer_combo = ttk.Combobox(form_frame, textvariable=self.benutzer_var,
                                           width=28, state='readonly')
        self.benutzer_combo.grid(row=row, column=1, sticky='w', pady=5)
        row += 1
        
        # Maschine
        ttk.Label(form_frame, text="Maschine:").grid(row=row, column=0, sticky='w', pady=5)
        self.maschine_var = tk.StringVar()
        self.maschine_combo = ttk.Combobox(form_frame, textvariable=self.maschine_var,
                                          width=28, state='readonly')
        self.maschine_combo.grid(row=row, column=1, sticky='w', pady=5)
        self.maschine_combo.bind('<<ComboboxSelected>>', self.on_maschine_selected)
        row += 1
        
        # Einsatzzweck
        ttk.Label(form_frame, text="Einsatzzweck:").grid(row=row, column=0, sticky='w', pady=5)
        self.zweck_var = tk.StringVar()
        self.zweck_combo = ttk.Combobox(form_frame, textvariable=self.zweck_var,
                                       width=28, state='readonly')
        self.zweck_combo.grid(row=row, column=1, sticky='w', pady=5)
        row += 1
        
        # Anfangstand
        ttk.Label(form_frame, text="Anfangstand (Std.):").grid(
            row=row, column=0, sticky='w', pady=5)
        self.anfangstand_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.anfangstand_var, width=30).grid(
            row=row, column=1, sticky='w', pady=5)
        row += 1
        
        # Endstand
        ttk.Label(form_frame, text="Endstand (Std.):").grid(
            row=row, column=0, sticky='w', pady=5)
        self.endstand_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.endstand_var, width=30).grid(
            row=row, column=1, sticky='w', pady=5)
        row += 1
        
        # Betriebsstunden (berechnet)
        ttk.Label(form_frame, text="Betriebsstunden:").grid(
            row=row, column=0, sticky='w', pady=5)
        self.betriebsstunden_label = ttk.Label(form_frame, text="0.0", 
                                               font=('Arial', 10, 'bold'))
        self.betriebsstunden_label.grid(row=row, column=1, sticky='w', pady=5)
        row += 1
        
        # Treibstoffverbrauch
        ttk.Label(form_frame, text="Treibstoffverbrauch (l):").grid(
            row=row, column=0, sticky='w', pady=5)
        self.treibstoff_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.treibstoff_var, width=30).grid(
            row=row, column=1, sticky='w', pady=5)
        row += 1
        
        # Treibstoffkosten
        ttk.Label(form_frame, text="Treibstoffkosten (€):").grid(
            row=row, column=0, sticky='w', pady=5)
        self.kosten_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.kosten_var, width=30).grid(
            row=row, column=1, sticky='w', pady=5)
        row += 1
        
        # Anmerkungen
        ttk.Label(form_frame, text="Anmerkungen:").grid(
            row=row, column=0, sticky='nw', pady=5)
        self.anmerkungen_text = tk.Text(form_frame, width=30, height=4)
        self.anmerkungen_text.grid(row=row, column=1, sticky='w', pady=5)
        row += 1
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Einsatz speichern", 
                  command=self.save_einsatz).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Formular leeren", 
                  command=self.clear_form).pack(side='left', padx=5)
        
        # Bindings für automatische Berechnung
        self.anfangstand_var.trace('w', self.calculate_betriebsstunden)
        self.endstand_var.trace('w', self.calculate_betriebsstunden)
    
    def create_uebersicht_tab(self):
        """Tab für Einsatzübersicht erstellen"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Einsatzübersicht")
        
        # Toolbar
        toolbar = ttk.Frame(frame)
        toolbar.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(toolbar, text="Aktualisieren", 
                  command=self.refresh_einsaetze).pack(side='left', padx=2)
        ttk.Button(toolbar, text="Filter zurücksetzen", 
                  command=self.reset_filter).pack(side='left', padx=2)
        
        # Treeview für Einsätze
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        # Treeview
        columns = ('datum', 'benutzer', 'maschine', 'zweck', 'anfang', 
                  'ende', 'stunden', 'treibstoff', 'kosten')
        self.einsaetze_tree = ttk.Treeview(tree_frame, columns=columns, 
                                          show='headings', 
                                          yscrollcommand=vsb.set,
                                          xscrollcommand=hsb.set)
        
        vsb.config(command=self.einsaetze_tree.yview)
        hsb.config(command=self.einsaetze_tree.xview)
        
        # Spalten konfigurieren
        self.einsaetze_tree.heading('datum', text='Datum')
        self.einsaetze_tree.heading('benutzer', text='Benutzer')
        self.einsaetze_tree.heading('maschine', text='Maschine')
        self.einsaetze_tree.heading('zweck', text='Einsatzzweck')
        self.einsaetze_tree.heading('anfang', text='Anfang')
        self.einsaetze_tree.heading('ende', text='Ende')
        self.einsaetze_tree.heading('stunden', text='Stunden')
        self.einsaetze_tree.heading('treibstoff', text='Treibstoff (l)')
        self.einsaetze_tree.heading('kosten', text='Kosten (€)')
        
        self.einsaetze_tree.column('datum', width=100)
        self.einsaetze_tree.column('benutzer', width=150)
        self.einsaetze_tree.column('maschine', width=150)
        self.einsaetze_tree.column('zweck', width=120)
        self.einsaetze_tree.column('anfang', width=80)
        self.einsaetze_tree.column('ende', width=80)
        self.einsaetze_tree.column('stunden', width=80)
        self.einsaetze_tree.column('treibstoff', width=100)
        self.einsaetze_tree.column('kosten', width=100)
        
        # Grid layout
        self.einsaetze_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
    
    def create_statistik_tab(self):
        """Tab für Statistiken erstellen"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Statistiken")
        
        # Info-Label
        info_label = ttk.Label(frame, 
                              text="Wählen Sie einen Benutzer oder eine Maschine aus:",
                              font=('Arial', 11))
        info_label.pack(pady=20)
        
        # Auswahl-Frame
        select_frame = ttk.Frame(frame)
        select_frame.pack(pady=10)
        
        ttk.Label(select_frame, text="Benutzer:").grid(row=0, column=0, padx=5)
        self.stat_benutzer_combo = ttk.Combobox(select_frame, width=25, state='readonly')
        self.stat_benutzer_combo.grid(row=0, column=1, padx=5)
        ttk.Button(select_frame, text="Statistik anzeigen",
                  command=lambda: self.show_statistik('benutzer')).grid(
                      row=0, column=2, padx=5)
        
        ttk.Label(select_frame, text="Maschine:").grid(row=1, column=0, padx=5, pady=5)
        self.stat_maschine_combo = ttk.Combobox(select_frame, width=25, state='readonly')
        self.stat_maschine_combo.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(select_frame, text="Statistik anzeigen",
                  command=lambda: self.show_statistik('maschine')).grid(
                      row=1, column=2, padx=5, pady=5)
        
        # Statistik-Anzeige
        self.statistik_text = tk.Text(frame, width=80, height=20, 
                                     font=('Courier', 10))
        self.statistik_text.pack(pady=20, padx=20)
    
    # ==================== EVENT HANDLER ====================
    
    def on_maschine_selected(self, event=None):
        """Wenn Maschine ausgewählt wird, Anfangstand vorschlagen"""
        maschine_name = self.maschine_var.get()
        if not maschine_name:
            return
        
        with MaschinenDBContext(self.db_path) as db:
            maschinen = db.get_all_maschinen()
            for m in maschinen:
                display_name = f"{m['bezeichnung']} ({m['hersteller'] or 'unbekannt'})"
                if display_name == maschine_name:
                    aktueller_stand = m['stundenzaehler_aktuell'] or 0
                    self.anfangstand_var.set(str(aktueller_stand))
                    break
    
    def calculate_betriebsstunden(self, *args):
        """Betriebsstunden automatisch berechnen"""
        try:
            anfang = float(self.anfangstand_var.get() or 0)
            ende = float(self.endstand_var.get() or 0)
            stunden = max(0, ende - anfang)
            self.betriebsstunden_label.config(text=f"{stunden:.1f}")
        except ValueError:
            self.betriebsstunden_label.config(text="0.0")
    
    def save_einsatz(self):
        """Neuen Einsatz speichern"""
        try:
            # Validierung
            if not all([self.benutzer_var.get(), self.maschine_var.get(),
                       self.zweck_var.get(), self.anfangstand_var.get(),
                       self.endstand_var.get()]):
                messagebox.showwarning("Unvollständig", 
                                      "Bitte füllen Sie alle Pflichtfelder aus!")
                return
            
            datum = self.datum_var.get()
            anfang = float(self.anfangstand_var.get())
            ende = float(self.endstand_var.get())
            
            if ende < anfang:
                messagebox.showerror("Fehler", 
                                    "Endstand muss größer als Anfangstand sein!")
                return
            
            # IDs ermitteln
            with MaschinenDBContext(self.db_path) as db:
                # Benutzer-ID
                benutzer_name = self.benutzer_var.get()
                benutzer = [b for b in db.get_all_benutzer() 
                           if f"{b['name']}, {b['vorname']}" == benutzer_name][0]
                
                # Maschinen-ID
                maschine_name = self.maschine_var.get().split(' (')[0]
                maschine = [m for m in db.get_all_maschinen() 
                           if m['bezeichnung'] == maschine_name][0]
                
                # Zweck-ID
                zweck_name = self.zweck_var.get()
                zweck = [z for z in db.get_all_einsatzzwecke() 
                        if z['bezeichnung'] == zweck_name][0]
                
                # Optionale Werte
                treibstoff = float(self.treibstoff_var.get()) if self.treibstoff_var.get() else None
                kosten = float(self.kosten_var.get()) if self.kosten_var.get() else None
                anmerkungen = self.anmerkungen_text.get('1.0', 'end-1c').strip() or None
                
                # Speichern
                db.add_einsatz(
                    datum=datum,
                    benutzer_id=benutzer['id'],
                    maschine_id=maschine['id'],
                    einsatzzweck_id=zweck['id'],
                    anfangstand=anfang,
                    endstand=ende,
                    treibstoffverbrauch=treibstoff,
                    treibstoffkosten=kosten,
                    anmerkungen=anmerkungen
                )
            
            messagebox.showinfo("Erfolg", "Einsatz wurde gespeichert!")
            self.clear_form()
            self.refresh_einsaetze()
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Speichern: {str(e)}")
    
    def clear_form(self):
        """Formular leeren"""
        self.datum_var.set(datetime.now().strftime("%Y-%m-%d"))
        self.benutzer_var.set('')
        self.maschine_var.set('')
        self.zweck_var.set('')
        self.anfangstand_var.set('')
        self.endstand_var.set('')
        self.treibstoff_var.set('')
        self.kosten_var.set('')
        self.anmerkungen_text.delete('1.0', 'end')
    
    # ==================== DATEN LADEN ====================
    
    def refresh_all(self):
        """Alle Daten neu laden"""
        self.refresh_combos()
        self.refresh_einsaetze()
    
    def refresh_combos(self):
        """Comboboxen aktualisieren"""
        with MaschinenDBContext(self.db_path) as db:
            # Benutzer
            benutzer = db.get_all_benutzer()
            benutzer_names = [f"{b['name']}, {b['vorname']}" for b in benutzer]
            self.benutzer_combo['values'] = benutzer_names
            self.stat_benutzer_combo['values'] = benutzer_names
            
            # Maschinen
            maschinen = db.get_all_maschinen()
            maschinen_names = [f"{m['bezeichnung']} ({m['hersteller'] or 'unbekannt'})" 
                              for m in maschinen]
            self.maschine_combo['values'] = maschinen_names
            self.stat_maschine_combo['values'] = maschinen_names
            
            # Einsatzzwecke
            zwecke = db.get_all_einsatzzwecke()
            zweck_names = [z['bezeichnung'] for z in zwecke]
            self.zweck_combo['values'] = zweck_names
    
    def refresh_einsaetze(self):
        """Einsatzliste aktualisieren"""
        # Liste leeren
        for item in self.einsaetze_tree.get_children():
            self.einsaetze_tree.delete(item)
        
        # Daten laden
        with MaschinenDBContext(self.db_path) as db:
            einsaetze = db.get_all_einsaetze(limit=100)
            
            for e in einsaetze:
                self.einsaetze_tree.insert('', 'end', values=(
                    e['datum'],
                    e['benutzer'],
                    e['maschine'],
                    e['einsatzzweck'],
                    f"{e['anfangstand']:.1f}",
                    f"{e['endstand']:.1f}",
                    f"{e['betriebsstunden']:.1f}",
                    f"{e['treibstoffverbrauch']:.1f}" if e['treibstoffverbrauch'] else '',
                    f"{e['treibstoffkosten']:.2f}" if e['treibstoffkosten'] else ''
                ))
    
    def reset_filter(self):
        """Filter zurücksetzen"""
        self.refresh_einsaetze()
    
    def show_statistik(self, typ):
        """Statistik anzeigen"""
        self.statistik_text.delete('1.0', 'end')
        
        try:
            with MaschinenDBContext(self.db_path) as db:
                if typ == 'benutzer':
                    name = self.stat_benutzer_combo.get()
                    if not name:
                        return
                    
                    benutzer = [b for b in db.get_all_benutzer() 
                               if f"{b['name']}, {b['vorname']}" == name][0]
                    stat = db.get_statistik_benutzer(benutzer['id'])
                    einsaetze = db.get_einsaetze_by_benutzer(benutzer['id'])
                    
                    text = f"STATISTIK FÜR BENUTZER: {name}\n"
                    text += "=" * 60 + "\n\n"
                    text += f"Anzahl Einsätze:        {stat['anzahl_einsaetze']}\n"
                    text += f"Gesamt Betriebsstunden: {stat['gesamt_stunden']:.1f} h\n"
                    text += f"Gesamt Treibstoff:      {stat['gesamt_treibstoff']:.1f} l\n"
                    text += f"Gesamt Kosten:          {stat['gesamt_kosten']:.2f} €\n"
                    
                else:  # maschine
                    name = self.stat_maschine_combo.get().split(' (')[0]
                    if not name:
                        return
                    
                    maschine = [m for m in db.get_all_maschinen() 
                               if m['bezeichnung'] == name][0]
                    stat = db.get_statistik_maschine(maschine['id'])
                    
                    text = f"STATISTIK FÜR MASCHINE: {name}\n"
                    text += "=" * 60 + "\n\n"
                    text += f"Aktueller Stundenzähler: {maschine['stundenzaehler_aktuell']:.1f} h\n"
                    text += f"Anzahl Einsätze:         {stat['anzahl_einsaetze']}\n"
                    text += f"Gesamt Betriebsstunden:  {stat['gesamt_stunden']:.1f} h\n"
                    text += f"Gesamt Treibstoff:       {stat['gesamt_treibstoff']:.1f} l\n"
                    text += f"Anzahl Benutzer:         {stat['anzahl_benutzer']}\n"
                
                self.statistik_text.insert('1.0', text)
                
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Laden der Statistik: {str(e)}")
    
    # ==================== STAMMDATEN ====================
    
    def open_benutzer_window(self):
        """Benutzer-Verwaltungsfenster öffnen"""
        BenutzerWindow(self.root, self.db_path, self)
    
    def open_maschinen_window(self):
        """Maschinen-Verwaltungsfenster öffnen"""
        MaschinenWindow(self.root, self.db_path, self)
    
    def open_einsatzzwecke_window(self):
        """Einsatzzwecke-Verwaltungsfenster öffnen"""
        EinsatzzweckeWindow(self.root, self.db_path, self)
    
    def show_about(self):
        """Info-Dialog anzeigen"""
        messagebox.showinfo("Über", 
            "Maschinengemeinschaft Verwaltungssoftware\n\n"
            "Version 1.0\n"
            "Erstellt: Januar 2026\n\n"
            "Verwaltung von Maschineneinsätzen für Ihre Gemeinschaft")


# ==================== STAMMDATEN-FENSTER ====================

class BenutzerWindow:
    """Fenster zur Benutzerverwaltung"""
    
    def __init__(self, parent, db_path, main_gui):
        self.db_path = db_path
        self.main_gui = main_gui
        
        self.window = tk.Toplevel(parent)
        self.window.title("Benutzerverwaltung")
        self.window.geometry("800x600")
        
        self.create_widgets()
        self.load_data()
    
    def create_widgets(self):
        # Toolbar
        toolbar = ttk.Frame(self.window)
        toolbar.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(toolbar, text="Neuer Benutzer", 
                  command=self.add_benutzer).pack(side='left', padx=2)
        ttk.Button(toolbar, text="Bearbeiten", 
                  command=self.edit_benutzer).pack(side='left', padx=2)
        ttk.Button(toolbar, text="Löschen", 
                  command=self.delete_benutzer).pack(side='left', padx=2)
        ttk.Button(toolbar, text="Aktualisieren", 
                  command=self.load_data).pack(side='left', padx=2)
        
        # Treeview
        columns = ('name', 'vorname', 'telefon', 'email', 'mitglied_seit')
        self.tree = ttk.Treeview(self.window, columns=columns, show='headings')
        
        self.tree.heading('name', text='Name')
        self.tree.heading('vorname', text='Vorname')
        self.tree.heading('telefon', text='Telefon')
        self.tree.heading('email', text='E-Mail')
        self.tree.heading('mitglied_seit', text='Mitglied seit')
        
        self.tree.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Doppelklick zum Bearbeiten
        self.tree.bind('<Double-1>', lambda e: self.edit_benutzer())
    
    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        with MaschinenDBContext(self.db_path) as db:
            self.benutzer_liste = db.get_all_benutzer()
            for b in self.benutzer_liste:
                self.tree.insert('', 'end', values=(
                    b['name'], b['vorname'], b['telefon'], 
                    b['email'], b['mitglied_seit']
                ), iid=str(b['id']))
    
    def add_benutzer(self):
        AddBenutzerDialog(self.window, self.db_path, self)
    
    def edit_benutzer(self):
        """Ausgewählten Benutzer bearbeiten"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Keine Auswahl", "Bitte wählen Sie einen Benutzer aus!")
            return
        
        benutzer_id = int(selection[0])
        benutzer = next((b for b in self.benutzer_liste if b['id'] == benutzer_id), None)
        if benutzer:
            EditBenutzerDialog(self.window, self.db_path, self, benutzer)
    
    def delete_benutzer(self):
        """Ausgewählten Benutzer deaktivieren"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Keine Auswahl", "Bitte wählen Sie einen Benutzer aus!")
            return
        
        benutzer_id = int(selection[0])
        benutzer = next((b for b in self.benutzer_liste if b['id'] == benutzer_id), None)
        if not benutzer:
            return
        
        antwort = messagebox.askyesno(
            "Benutzer deaktivieren",
            f"Möchten Sie {benutzer['name']}, {benutzer['vorname']} wirklich deaktivieren?\n\n"
            "Der Benutzer wird nicht gelöscht, sondern nur deaktiviert."
        )
        
        if antwort:
            try:
                with MaschinenDBContext(self.db_path) as db:
                    db.delete_benutzer(benutzer_id, soft_delete=True)
                messagebox.showinfo("Erfolg", "Benutzer wurde deaktiviert!")
                self.load_data()
                self.main_gui.refresh_combos()
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler: {str(e)}")


class AddBenutzerDialog:
    """Dialog zum Hinzufügen eines Benutzers"""
    
    def __init__(self, parent, db_path, benutzer_window, benutzer=None):
        self.db_path = db_path
        self.benutzer_window = benutzer_window
        self.benutzer = benutzer
        self.edit_mode = benutzer is not None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Benutzer bearbeiten" if self.edit_mode else "Neuer Benutzer")
        self.dialog.geometry("400x400")
        
        # Formular
        frame = ttk.Frame(self.dialog, padding=20)
        frame.pack(fill='both', expand=True)
        
        ttk.Label(frame, text="Name:*").grid(row=0, column=0, sticky='w', pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.name_var, width=30).grid(
            row=0, column=1, pady=5)
        
        ttk.Label(frame, text="Vorname:").grid(row=1, column=0, sticky='w', pady=5)
        self.vorname_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.vorname_var, width=30).grid(
            row=1, column=1, pady=5)
        
        ttk.Label(frame, text="Benutzername:").grid(row=2, column=0, sticky='w', pady=5)
        self.username_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.username_var, width=30).grid(
            row=2, column=1, pady=5)
        
        ttk.Label(frame, text="Passwort:").grid(row=3, column=0, sticky='w', pady=5)
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(frame, textvariable=self.password_var, width=30, show='*')
        password_entry.grid(row=3, column=1, pady=5)
        
        ttk.Label(frame, text="Administrator:").grid(row=4, column=0, sticky='w', pady=5)
        self.admin_var = tk.BooleanVar()
        ttk.Checkbutton(frame, text="Admin-Rechte", variable=self.admin_var).grid(
            row=4, column=1, sticky='w', pady=5)
        
        ttk.Label(frame, text="Telefon:").grid(row=5, column=0, sticky='w', pady=5)
        self.telefon_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.telefon_var, width=30).grid(
            row=5, column=1, pady=5)
        
        ttk.Label(frame, text="E-Mail:").grid(row=6, column=0, sticky='w', pady=5)
        self.email_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.email_var, width=30).grid(
            row=6, column=1, pady=5)
        
        ttk.Label(frame, text="Mitglied seit:").grid(row=7, column=0, sticky='w', pady=5)
        self.datum_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(frame, textvariable=self.datum_var, width=30).grid(
            row=7, column=1, pady=5)
        
        # Felder mit vorhandenen Daten füllen (Edit-Modus)
        if self.edit_mode:
            self.name_var.set(benutzer['name'])
            self.vorname_var.set(benutzer['vorname'] or '')
            self.username_var.set(benutzer['username'] or '')
            self.admin_var.set(bool(benutzer.get('is_admin', False)))
            # Passwort nicht anzeigen im Edit-Modus
            self.telefon_var.set(benutzer['telefon'] or '')
            self.email_var.set(benutzer['email'] or '')
            self.datum_var.set(benutzer['mitglied_seit'] or '')
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=8, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Speichern", 
                  command=self.save).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Abbrechen", 
                  command=self.dialog.destroy).pack(side='left', padx=5)
    
    def save(self):
        if not self.name_var.get():
            messagebox.showwarning("Fehler", "Name ist erforderlich!")
            return
        
        try:
            with MaschinenDBContext(self.db_path) as db:
                if self.edit_mode:
                    # Benutzer aktualisieren
                    update_data = {
                        'name': self.name_var.get(),
                        'vorname': self.vorname_var.get() or None,
                        'username': self.username_var.get() or None,
                        'is_admin': self.admin_var.get(),
                        'telefon': self.telefon_var.get() or None,
                        'email': self.email_var.get() or None,
                        'mitglied_seit': self.datum_var.get() or None
                    }
                    db.update_benutzer(self.benutzer['id'], **update_data)
                    
                    # Passwort nur aktualisieren wenn eingegeben
                    if self.password_var.get():
                        db.update_password(self.benutzer['id'], self.password_var.get())
                    
                    messagebox.showinfo("Erfolg", "Benutzer wurde aktualisiert!")
                else:
                    # Neuen Benutzer hinzufügen
                    db.add_benutzer(
                        name=self.name_var.get(),
                        vorname=self.vorname_var.get() or None,
                        username=self.username_var.get() or None,
                        password=self.password_var.get() or None,
                        is_admin=self.admin_var.get(),
                        telefon=self.telefon_var.get() or None,
                        email=self.email_var.get() or None,
                        mitglied_seit=self.datum_var.get() or None
                    )
                    messagebox.showinfo("Erfolg", "Benutzer wurde hinzugefügt!")
            
            self.benutzer_window.load_data()
            self.benutzer_window.main_gui.refresh_combos()
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler: {str(e)}")


class EditBenutzerDialog(AddBenutzerDialog):
    """Dialog zum Bearbeiten eines Benutzers (erbt von AddBenutzerDialog)"""
    pass


class MaschinenWindow:
    """Fenster zur Maschinenverwaltung"""
    
    def __init__(self, parent, db_path, main_gui):
        self.db_path = db_path
        self.main_gui = main_gui
        
        self.window = tk.Toplevel(parent)
        self.window.title("Maschinenverwaltung")
        self.window.geometry("900x600")
        
        self.create_widgets()
        self.load_data()
    
    def create_widgets(self):
        toolbar = ttk.Frame(self.window)
        toolbar.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(toolbar, text="Neue Maschine", 
                  command=self.add_maschine).pack(side='left', padx=2)
        ttk.Button(toolbar, text="Aktualisieren", 
                  command=self.load_data).pack(side='left', padx=2)
        
        columns = ('bezeichnung', 'hersteller', 'modell', 'baujahr', 
                  'kennzeichen', 'stundenzaehler')
        self.tree = ttk.Treeview(self.window, columns=columns, show='headings')
        
        self.tree.heading('bezeichnung', text='Bezeichnung')
        self.tree.heading('hersteller', text='Hersteller')
        self.tree.heading('modell', text='Modell')
        self.tree.heading('baujahr', text='Baujahr')
        self.tree.heading('kennzeichen', text='Kennzeichen')
        self.tree.heading('stundenzaehler', text='Stundenzähler')
        
        self.tree.pack(fill='both', expand=True, padx=5, pady=5)
    
    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        with MaschinenDBContext(self.db_path) as db:
            maschinen = db.get_all_maschinen()
            for m in maschinen:
                self.tree.insert('', 'end', values=(
                    m['bezeichnung'], m['hersteller'], m['modell'],
                    m['baujahr'], m['kennzeichen'], 
                    f"{m['stundenzaehler_aktuell']:.1f}"
                ))
    
    def add_maschine(self):
        AddMaschineDialog(self.window, self.db_path, self)


class AddMaschineDialog:
    """Dialog zum Hinzufügen einer Maschine"""
    
    def __init__(self, parent, db_path, maschinen_window):
        self.db_path = db_path
        self.maschinen_window = maschinen_window
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Neue Maschine")
        self.dialog.geometry("400x500")
        
        frame = ttk.Frame(self.dialog, padding=20)
        frame.pack(fill='both', expand=True)
        
        ttk.Label(frame, text="Bezeichnung:*").grid(row=0, column=0, sticky='w', pady=5)
        self.bezeichnung_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.bezeichnung_var, width=30).grid(
            row=0, column=1, pady=5)
        
        ttk.Label(frame, text="Hersteller:").grid(row=1, column=0, sticky='w', pady=5)
        self.hersteller_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.hersteller_var, width=30).grid(
            row=1, column=1, pady=5)
        
        ttk.Label(frame, text="Modell:").grid(row=2, column=0, sticky='w', pady=5)
        self.modell_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.modell_var, width=30).grid(
            row=2, column=1, pady=5)
        
        ttk.Label(frame, text="Baujahr:").grid(row=3, column=0, sticky='w', pady=5)
        self.baujahr_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.baujahr_var, width=30).grid(
            row=3, column=1, pady=5)
        
        ttk.Label(frame, text="Kennzeichen:").grid(row=4, column=0, sticky='w', pady=5)
        self.kennzeichen_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.kennzeichen_var, width=30).grid(
            row=4, column=1, pady=5)
        
        ttk.Label(frame, text="Stundenzähler:").grid(row=5, column=0, sticky='w', pady=5)
        self.stundenzaehler_var = tk.StringVar(value="0")
        ttk.Entry(frame, textvariable=self.stundenzaehler_var, width=30).grid(
            row=5, column=1, pady=5)
        
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Speichern", 
                  command=self.save).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Abbrechen", 
                  command=self.dialog.destroy).pack(side='left', padx=5)
    
    def save(self):
        if not self.bezeichnung_var.get():
            messagebox.showwarning("Fehler", "Bezeichnung ist erforderlich!")
            return
        
        try:
            with MaschinenDBContext(self.db_path) as db:
                db.add_maschine(
                    bezeichnung=self.bezeichnung_var.get(),
                    hersteller=self.hersteller_var.get() or None,
                    modell=self.modell_var.get() or None,
                    baujahr=int(self.baujahr_var.get()) if self.baujahr_var.get() else None,
                    kennzeichen=self.kennzeichen_var.get() or None,
                    stundenzaehler_aktuell=float(self.stundenzaehler_var.get())
                )
            
            messagebox.showinfo("Erfolg", "Maschine wurde hinzugefügt!")
            self.maschinen_window.load_data()
            self.maschinen_window.main_gui.refresh_combos()
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler: {str(e)}")


class EinsatzzweckeWindow:
    """Fenster zur Verwaltung von Einsatzzwecken"""
    
    def __init__(self, parent, db_path, main_gui):
        self.db_path = db_path
        self.main_gui = main_gui
        
        self.window = tk.Toplevel(parent)
        self.window.title("Einsatzzwecke verwalten")
        self.window.geometry("600x400")
        
        self.create_widgets()
        self.load_data()
    
    def create_widgets(self):
        toolbar = ttk.Frame(self.window)
        toolbar.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(toolbar, text="Neuer Einsatzzweck", 
                  command=self.add_zweck).pack(side='left', padx=2)
        ttk.Button(toolbar, text="Aktualisieren", 
                  command=self.load_data).pack(side='left', padx=2)
        
        columns = ('bezeichnung', 'beschreibung')
        self.tree = ttk.Treeview(self.window, columns=columns, show='headings')
        
        self.tree.heading('bezeichnung', text='Bezeichnung')
        self.tree.heading('beschreibung', text='Beschreibung')
        
        self.tree.column('bezeichnung', width=200)
        self.tree.column('beschreibung', width=350)
        
        self.tree.pack(fill='both', expand=True, padx=5, pady=5)
    
    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        with MaschinenDBContext(self.db_path) as db:
            zwecke = db.get_all_einsatzzwecke()
            for z in zwecke:
                self.tree.insert('', 'end', values=(
                    z['bezeichnung'], z['beschreibung']
                ))
    
    def add_zweck(self):
        bezeichnung = simpledialog.askstring("Neuer Einsatzzweck", 
                                            "Bezeichnung:", parent=self.window)
        if not bezeichnung:
            return
        
        beschreibung = simpledialog.askstring("Neuer Einsatzzweck", 
                                             "Beschreibung (optional):", 
                                             parent=self.window)
        
        try:
            with MaschinenDBContext(self.db_path) as db:
                db.add_einsatzzweck(bezeichnung, beschreibung)
            
            messagebox.showinfo("Erfolg", "Einsatzzweck wurde hinzugefügt!")
            self.load_data()
            self.main_gui.refresh_combos()
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler: {str(e)}")


# ==================== MAIN ====================

def main():
    root = tk.Tk()
    app = MaschinenGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
