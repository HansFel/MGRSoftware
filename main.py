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
        
        # Treibstoffpreis des aktuellen Benutzers
        self.aktueller_treibstoffpreis = 1.50  # Default
        
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
        
        # Admin-Menü
        admin_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Admin", menu=admin_menu)
        admin_menu.add_command(label="Einsätze nach Zeitraum löschen", 
                              command=self.open_delete_einsaetze_window)
        admin_menu.add_separator()
        admin_menu.add_command(label="Datenbank-Backup erstellen", 
                              command=self.create_database_backup)
        
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
        self.benutzer_combo.bind('<<ComboboxSelected>>', self.on_benutzer_selected)
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
        treibstoff_entry = ttk.Entry(form_frame, textvariable=self.treibstoff_var, width=30)
        treibstoff_entry.grid(row=row, column=1, sticky='w', pady=5)
        # Bei Änderung des Verbrauchs, Kosten automatisch berechnen
        self.treibstoff_var.trace('w', self.berechne_treibstoffkosten)
        row += 1
        
        # Treibstoffkosten
        ttk.Label(form_frame, text="Treibstoffkosten (€):").grid(
            row=row, column=0, sticky='w', pady=5)
        self.kosten_var = tk.StringVar()
        kosten_frame = ttk.Frame(form_frame)
        kosten_frame.grid(row=row, column=1, sticky='w', pady=5)
        ttk.Entry(kosten_frame, textvariable=self.kosten_var, width=20).pack(side='left')
        self.treibstoff_preis_label = ttk.Label(kosten_frame, text="", 
                                                 foreground='gray')
        self.treibstoff_preis_label.pack(side='left', padx=(5, 0))
        row += 1
        
        # Fläche/Menge
        ttk.Label(form_frame, text="Fläche/Menge:").grid(
            row=row, column=0, sticky='w', pady=5)
        self.flaeche_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.flaeche_var, width=30).grid(
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
        ttk.Button(toolbar, text="Als CSV exportieren", 
                  command=self.export_einsaetze_csv).pack(side='left', padx=2)
        
        # Treeview für Einsätze
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        # Treeview
        columns = ('datum', 'benutzer', 'maschine', 'zweck', 'preis',
                  'anfang', 'ende', 'menge', 'treibstoff', 'kosten_treibstoff', 'kosten_maschine')
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
        self.einsaetze_tree.heading('preis', text='Preis/Einh.')
        self.einsaetze_tree.heading('anfang', text='Anfang')
        self.einsaetze_tree.heading('ende', text='Ende')
        self.einsaetze_tree.heading('menge', text='Menge')
        self.einsaetze_tree.heading('treibstoff', text='Treibstoff (l)')
        self.einsaetze_tree.heading('kosten_treibstoff', text='Treibstoff€')
        self.einsaetze_tree.heading('kosten_maschine', text='Maschine€')
        
        self.einsaetze_tree.column('datum', width=100)
        self.einsaetze_tree.column('benutzer', width=120)
        self.einsaetze_tree.column('maschine', width=120)
        self.einsaetze_tree.column('zweck', width=100)
        self.einsaetze_tree.column('preis', width=80)
        self.einsaetze_tree.column('anfang', width=70)
        self.einsaetze_tree.column('ende', width=70)
        self.einsaetze_tree.column('menge', width=90)
        self.einsaetze_tree.column('treibstoff', width=90)
        self.einsaetze_tree.column('kosten_treibstoff', width=90)
        self.einsaetze_tree.column('kosten_maschine', width=90)
        
        # Grid layout
        self.einsaetze_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Summenzeile
        summen_frame = ttk.Frame(frame, padding=5)
        summen_frame.pack(fill='x', padx=5, pady=5)
        
        self.summen_label = ttk.Label(summen_frame, 
                                     text="Summen: Treibstoffkosten: 0,00 € | Maschinenkosten: 0,00 € | Gesamt: 0,00 €",
                                     font=('Arial', 10, 'bold'))
        self.summen_label.pack(side='right')
    
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
    
    def on_benutzer_selected(self, event=None):
        """Wenn Benutzer ausgewählt wird, nur dessen Gemeinschafts-Maschinen anzeigen"""
        benutzer_name = self.benutzer_var.get()
        if not benutzer_name:
            return
        
        with MaschinenDBContext(self.db_path) as db:
            # Finde Benutzer-ID
            benutzer = db.get_all_benutzer()
            benutzer_id = None
            for b in benutzer:
                display_name = f"{b['name']}, {b['vorname']}"
                if display_name == benutzer_name:
                    benutzer_id = b['id']
                    break
            
            if benutzer_id:
                # Hole Treibstoffkosten des Benutzers
                benutzer_data = db.get_benutzer(benutzer_id)
                self.aktueller_treibstoffpreis = benutzer_data.get('treibstoffkosten_preis', 1.50)
                self.treibstoff_preis_label.config(text=f"({self.aktueller_treibstoffpreis:.2f} EUR/L)")
                
                # Hole nur Maschinen aus Gemeinschaften des Benutzers
                cursor = db.connection.cursor()
                cursor.execute("""
                    SELECT DISTINCT m.* 
                    FROM maschinen m
                    JOIN gemeinschaften g ON m.gemeinschaft_id = g.id
                    JOIN mitglied_gemeinschaft mg ON g.id = mg.gemeinschaft_id
                    WHERE mg.mitglied_id = ? 
                      AND m.aktiv = 1 
                      AND g.aktiv = 1
                    ORDER BY m.bezeichnung
                """, (benutzer_id,))
                
                columns = [desc[0] for desc in cursor.description]
                maschinen = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                maschinen_names = [f"{m['bezeichnung']} ({m['hersteller'] or 'unbekannt'})" 
                                  for m in maschinen]
                self.maschine_combo['values'] = maschinen_names
                
                # Leere Auswahl
                self.maschine_var.set('')
    
    def berechne_treibstoffkosten(self, *args):
        """Berechne Treibstoffkosten basierend auf Verbrauch"""
        try:
            verbrauch = float(self.treibstoff_var.get())
            if verbrauch > 0:
                kosten = verbrauch * self.aktueller_treibstoffpreis
                self.kosten_var.set(f"{kosten:.2f}")
            else:
                self.kosten_var.set('')
        except (ValueError, AttributeError):
            pass
    
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
                flaeche = float(self.flaeche_var.get()) if self.flaeche_var.get() else None
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
                    anmerkungen=anmerkungen,
                    flaeche_menge=flaeche
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
        self.flaeche_var.set('')
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
            
            # Summen initialisieren
            summe_treibstoff = 0.0
            summe_maschine = 0.0
            
            for e in einsaetze:
                treibstoff_kosten = e.get('treibstoffkosten') or 0
                maschinen_kosten = e.get('kosten_berechnet') or 0
                preis = e.get('preis_pro_einheit') or 0
                abrechnungsart = e.get('abrechnungsart', 'stunden')
                flaeche_menge = e.get('flaeche_menge')
                
                # Preis mit Einheit formatieren
                preis_text = f"{preis:.2f}€"
                if abrechnungsart == 'hektar':
                    preis_text += "/ha"
                elif abrechnungsart == 'kilometer':
                    preis_text += "/km"
                elif abrechnungsart == 'stueck':
                    preis_text += "/St"
                else:
                    preis_text += "/h"
                
                # Menge mit richtiger Einheit formatieren
                if abrechnungsart == 'hektar' and flaeche_menge:
                    menge_text = f"{flaeche_menge:.2f} ha"
                elif abrechnungsart == 'kilometer' and flaeche_menge:
                    menge_text = f"{flaeche_menge:.2f} km"
                elif abrechnungsart == 'stueck' and flaeche_menge:
                    menge_text = f"{flaeche_menge:.0f} St"
                else:
                    menge_text = f"{e['betriebsstunden']:.1f} h"
                
                summe_treibstoff += treibstoff_kosten
                summe_maschine += maschinen_kosten
                
                self.einsaetze_tree.insert('', 'end', values=(
                    e['datum'],
                    e['benutzer'],
                    e['maschine'],
                    e['einsatzzweck'],
                    preis_text,
                    f"{e['anfangstand']:.1f}",
                    f"{e['endstand']:.1f}",
                    menge_text,
                    f"{e['treibstoffverbrauch']:.1f}" if e['treibstoffverbrauch'] else '',
                    f"{treibstoff_kosten:.2f}" if treibstoff_kosten > 0 else '',
                    f"{maschinen_kosten:.2f}" if maschinen_kosten > 0 else ''
                ))
            
            # Summenzeile aktualisieren
            gesamt = summe_treibstoff + summe_maschine
            self.summen_label.config(
                text=f"Summen: Treibstoffkosten: {summe_treibstoff:.2f} € | "
                     f"Maschinenkosten: {summe_maschine:.2f} € | "
                     f"Gesamt: {gesamt:.2f} €"
            )
    
    def reset_filter(self):
        """Filter zurücksetzen"""
        self.refresh_einsaetze()
    
    def export_einsaetze_csv(self):
        """Einsätze als CSV exportieren"""
        import csv
        from tkinter import filedialog
        from datetime import datetime
        
        # Dateiname vorschlagen
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dateiname = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV-Dateien", "*.csv"), ("Alle Dateien", "*.*")],
            initialfile=f"einsaetze_{timestamp}.csv"
        )
        
        if not dateiname:
            return
        
        try:
            with MaschinenDBContext(self.db_path) as db:
                einsaetze = db.get_all_einsaetze()
                
                with open(dateiname, 'w', newline='', encoding='utf-8-sig') as csvfile:
                    writer = csv.writer(csvfile, delimiter=';')
                    
                    # Header
                    writer.writerow([
                        'Datum', 'Benutzer', 'Maschine', 'Einsatzzweck', 
                        'Abrechnungsart', 'Preis pro Einheit',
                        'Anfangstand', 'Endstand', 'Betriebsstunden',
                        'Treibstoffverbrauch (l)', 'Treibstoffkosten (€)',
                        'Fläche/Menge', 'Maschinenkosten (€)', 'Anmerkungen'
                    ])
                    
                    # Daten
                    for e in einsaetze:
                        writer.writerow([
                            e['datum'],
                            e['benutzer'],
                            e['maschine'],
                            e['einsatzzweck'],
                            e.get('abrechnungsart', 'stunden'),
                            f"{e.get('preis_pro_einheit', 0):.2f}",
                            f"{e['anfangstand']:.1f}",
                            f"{e['endstand']:.1f}",
                            f"{e['betriebsstunden']:.1f}",
                            f"{e['treibstoffverbrauch']:.1f}" if e['treibstoffverbrauch'] else '',
                            f"{e.get('treibstoffkosten', 0):.2f}" if e.get('treibstoffkosten') else '',
                            f"{e.get('flaeche_menge', 0):.1f}" if e.get('flaeche_menge') else '',
                            f"{e.get('kosten_berechnet', 0):.2f}" if e.get('kosten_berechnet') else '',
                            e.get('anmerkungen', '')
                        ])
            
            messagebox.showinfo("Erfolg", f"Einsätze wurden als CSV exportiert:\n{dateiname}")
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Exportieren: {str(e)}")
    
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
                    text += f"Treibstoffkosten:       {stat['gesamt_kosten']:.2f} €\n"
                    text += f"Maschinenkosten:        {stat['gesamt_maschinenkosten']:.2f} €\n"
                    text += f"GESAMTKOSTEN:           {(stat['gesamt_kosten'] or 0) + (stat['gesamt_maschinenkosten'] or 0):.2f} €\n"
                    
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
        ttk.Button(toolbar, text="Deaktivieren", 
                  command=self.delete_benutzer).pack(side='left', padx=2)
        ttk.Button(toolbar, text="Reaktivieren", 
                  command=self.activate_benutzer).pack(side='left', padx=2)
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
            self.benutzer_liste = db.get_all_benutzer(nur_aktive=False)
            for b in self.benutzer_liste:
                values = (
                    b['name'], b['vorname'], b['telefon'], 
                    b['email'], b['mitglied_seit']
                )
                # Deaktivierte Benutzer mit Tag markieren
                tags = () if b['aktiv'] else ('deaktiviert',)
                self.tree.insert('', 'end', values=values, iid=str(b['id']), tags=tags)
        
        # Style für deaktivierte Benutzer
        self.tree.tag_configure('deaktiviert', foreground='gray')
    
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
    
    def activate_benutzer(self):
        """Ausgewählten Benutzer reaktivieren"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Keine Auswahl", "Bitte wählen Sie einen Benutzer aus!")
            return
        
        benutzer_id = int(selection[0])
        benutzer = next((b for b in self.benutzer_liste if b['id'] == benutzer_id), None)
        if not benutzer:
            return
        
        if benutzer['aktiv']:
            messagebox.showinfo("Info", "Dieser Benutzer ist bereits aktiv.")
            return
        
        antwort = messagebox.askyesno(
            "Benutzer reaktivieren",
            f"Möchten Sie {benutzer['name']}, {benutzer['vorname']} wieder aktivieren?"
        )
        
        if antwort:
            try:
                with MaschinenDBContext(self.db_path) as db:
                    db.activate_benutzer(benutzer_id)
                messagebox.showinfo("Erfolg", "Benutzer wurde reaktiviert!")
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
        ttk.Button(toolbar, text="Bearbeiten", 
                  command=self.edit_maschine).pack(side='left', padx=2)
        ttk.Button(toolbar, text="Löschen", 
                  command=self.delete_maschine).pack(side='left', padx=2)
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
        self.tree.bind('<Double-1>', lambda e: self.edit_maschine())
    
    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        with MaschinenDBContext(self.db_path) as db:
            self.maschinen_liste = db.get_all_maschinen()
            for m in self.maschinen_liste:
                self.tree.insert('', 'end', values=(
                    m['bezeichnung'], m['hersteller'], m['modell'],
                    m['baujahr'], m['kennzeichen'], 
                    f"{m['stundenzaehler_aktuell']:.1f}"
                ), iid=str(m['id']))
    
    def add_maschine(self):
        AddMaschineDialog(self.window, self.db_path, self)
    
    def edit_maschine(self):
        """Ausgewählte Maschine bearbeiten"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Keine Auswahl", "Bitte wählen Sie eine Maschine aus!")
            return
        
        maschine_id = int(selection[0])
        maschine = next((m for m in self.maschinen_liste if m['id'] == maschine_id), None)
        if maschine:
            EditMaschineDialog(self.window, self.db_path, self, maschine)
    
    def delete_maschine(self):
        """Ausgewählte Maschine löschen"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Keine Auswahl", "Bitte wählen Sie eine Maschine aus!")
            return
        
        maschine_id = int(selection[0])
        maschine = next((m for m in self.maschinen_liste if m['id'] == maschine_id), None)
        if not maschine:
            return
        
        antwort = messagebox.askyesno(
            "Maschine löschen",
            f"Möchten Sie {maschine['bezeichnung']} wirklich löschen?"
        )
        
        if antwort:
            try:
                with MaschinenDBContext(self.db_path) as db:
                    db.delete_maschine(maschine_id, soft_delete=True)
                messagebox.showinfo("Erfolg", "Maschine wurde deaktiviert!")
                self.load_data()
                self.main_gui.refresh_combos()
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler: {str(e)}")


class AddMaschineDialog:
    """Dialog zum Hinzufügen einer Maschine"""
    
    def __init__(self, parent, db_path, maschinen_window, maschine=None):
        self.db_path = db_path
        self.maschinen_window = maschinen_window
        self.maschine = maschine
        self.edit_mode = maschine is not None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Maschine bearbeiten" if self.edit_mode else "Neue Maschine")
        self.dialog.geometry("400x600")
        
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
        
        ttk.Label(frame, text="Erfassungsmodus:").grid(row=6, column=0, sticky='w', pady=5)
        self.erfassungsmodus_var = tk.StringVar(value="fortlaufend")
        erfassungsmodus_combo = ttk.Combobox(frame, textvariable=self.erfassungsmodus_var,
                                             values=['fortlaufend', 'direkt'],
                                             width=28, state='readonly')
        erfassungsmodus_combo.grid(row=6, column=1, pady=5)
        
        ttk.Label(frame, text="Abrechnungsart:").grid(row=7, column=0, sticky='w', pady=5)
        self.abrechnungsart_var = tk.StringVar(value="stunden")
        abrechnungsart_combo = ttk.Combobox(frame, textvariable=self.abrechnungsart_var,
                                            values=['stunden', 'hektar', 'kilometer', 'stueck'],
                                            width=28, state='readonly')
        abrechnungsart_combo.grid(row=7, column=1, pady=5)
        
        ttk.Label(frame, text="Preis pro Einheit:").grid(row=8, column=0, sticky='w', pady=5)
        self.preis_var = tk.StringVar(value="0")
        ttk.Entry(frame, textvariable=self.preis_var, width=30).grid(
            row=8, column=1, pady=5)
        
        # Felder mit vorhandenen Daten füllen (Edit-Modus)
        if self.edit_mode:
            self.bezeichnung_var.set(maschine['bezeichnung'])
            self.hersteller_var.set(maschine['hersteller'] or '')
            self.modell_var.set(maschine['modell'] or '')
            self.baujahr_var.set(str(maschine['baujahr']) if maschine['baujahr'] else '')
            self.kennzeichen_var.set(maschine['kennzeichen'] or '')
            self.stundenzaehler_var.set(str(maschine['stundenzaehler_aktuell'] or 0))
            self.erfassungsmodus_var.set(maschine.get('erfassungsmodus', 'fortlaufend'))
            self.abrechnungsart_var.set(maschine.get('abrechnungsart', 'stunden'))
            self.preis_var.set(str(maschine.get('preis_pro_einheit', 0)))
        
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=9, column=0, columnspan=2, pady=20)
        
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
                if self.edit_mode:
                    # Maschine aktualisieren
                    update_data = {
                        'bezeichnung': self.bezeichnung_var.get(),
                        'hersteller': self.hersteller_var.get() or None,
                        'modell': self.modell_var.get() or None,
                        'baujahr': int(self.baujahr_var.get().strip()) if self.baujahr_var.get().strip() else None,
                        'kennzeichen': self.kennzeichen_var.get() or None,
                        'stundenzaehler_aktuell': float(self.stundenzaehler_var.get().strip() or '0'),
                        'erfassungsmodus': self.erfassungsmodus_var.get(),
                        'abrechnungsart': self.abrechnungsart_var.get(),
                        'preis_pro_einheit': float(self.preis_var.get().strip() or '0')
                    }
                    db.update_maschine(self.maschine['id'], **update_data)
                    messagebox.showinfo("Erfolg", "Maschine wurde aktualisiert!")
                else:
                    # Neue Maschine hinzufügen
                    db.add_maschine(
                        bezeichnung=self.bezeichnung_var.get(),
                        hersteller=self.hersteller_var.get() or None,
                        modell=self.modell_var.get() or None,
                        baujahr=int(self.baujahr_var.get().strip()) if self.baujahr_var.get().strip() else None,
                        kennzeichen=self.kennzeichen_var.get() or None,
                        stundenzaehler_aktuell=float(self.stundenzaehler_var.get().strip() or '0'),
                        erfassungsmodus=self.erfassungsmodus_var.get(),
                        abrechnungsart=self.abrechnungsart_var.get(),
                        preis_pro_einheit=float(self.preis_var.get().strip() or '0')
                    )
                    messagebox.showinfo("Erfolg", "Maschine wurde hinzugefügt!")
            
            self.maschinen_window.load_data()
            self.maschinen_window.main_gui.refresh_combos()
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler: {str(e)}")


class EditMaschineDialog(AddMaschineDialog):
    """Dialog zum Bearbeiten einer Maschine (erbt von AddMaschineDialog)"""
    pass


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
        ttk.Button(toolbar, text="Bearbeiten", 
                  command=self.edit_zweck).pack(side='left', padx=2)
        ttk.Button(toolbar, text="Löschen", 
                  command=self.delete_zweck).pack(side='left', padx=2)
        ttk.Button(toolbar, text="Aktualisieren", 
                  command=self.load_data).pack(side='left', padx=2)
        
        columns = ('bezeichnung', 'beschreibung')
        self.tree = ttk.Treeview(self.window, columns=columns, show='headings')
        
        self.tree.heading('bezeichnung', text='Bezeichnung')
        self.tree.heading('beschreibung', text='Beschreibung')
        
        self.tree.column('bezeichnung', width=200)
        self.tree.column('beschreibung', width=350)
        
        self.tree.pack(fill='both', expand=True, padx=5, pady=5)
        self.tree.bind('<Double-1>', lambda e: self.edit_zweck())
    
    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        with MaschinenDBContext(self.db_path) as db:
            self.zwecke_liste = db.get_all_einsatzzwecke(nur_aktive=False)
            for z in self.zwecke_liste:
                self.tree.insert('', 'end', values=(
                    z['bezeichnung'], z['beschreibung']
                ), iid=str(z['id']))
    
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
    
    def edit_zweck(self):
        """Ausgewählten Einsatzzweck bearbeiten"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Keine Auswahl", "Bitte wählen Sie einen Einsatzzweck aus!")
            return
        
        zweck_id = int(selection[0])
        zweck = next((z for z in self.zwecke_liste if z['id'] == zweck_id), None)
        if not zweck:
            return
        
        # Dialog für Bearbeitung
        edit_dialog = tk.Toplevel(self.window)
        edit_dialog.title("Einsatzzweck bearbeiten")
        edit_dialog.geometry("400x200")
        
        frame = ttk.Frame(edit_dialog, padding=20)
        frame.pack(fill='both', expand=True)
        
        ttk.Label(frame, text="Bezeichnung:").grid(row=0, column=0, sticky='w', pady=5)
        bezeichnung_var = tk.StringVar(value=zweck['bezeichnung'])
        ttk.Entry(frame, textvariable=bezeichnung_var, width=30).grid(row=0, column=1, pady=5)
        
        ttk.Label(frame, text="Beschreibung:").grid(row=1, column=0, sticky='w', pady=5)
        beschreibung_var = tk.StringVar(value=zweck['beschreibung'] or '')
        ttk.Entry(frame, textvariable=beschreibung_var, width=30).grid(row=1, column=1, pady=5)
        
        def save_edit():
            if not bezeichnung_var.get():
                messagebox.showwarning("Fehler", "Bezeichnung ist erforderlich!")
                return
            try:
                with MaschinenDBContext(self.db_path) as db:
                    db.update_einsatzzweck(zweck_id, 
                                         bezeichnung=bezeichnung_var.get(),
                                         beschreibung=beschreibung_var.get() or None)
                messagebox.showinfo("Erfolg", "Einsatzzweck wurde aktualisiert!")
                self.load_data()
                self.main_gui.refresh_combos()
                edit_dialog.destroy()
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler: {str(e)}")
        
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        ttk.Button(button_frame, text="Speichern", command=save_edit).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Abbrechen", command=edit_dialog.destroy).pack(side='left', padx=5)
    
    def delete_zweck(self):
        """Ausgewählten Einsatzzweck löschen"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Keine Auswahl", "Bitte wählen Sie einen Einsatzzweck aus!")
            return
        
        zweck_id = int(selection[0])
        zweck = next((z for z in self.zwecke_liste if z['id'] == zweck_id), None)
        if not zweck:
            return
        
        antwort = messagebox.askyesno(
            "Einsatzzweck löschen",
            f"Möchten Sie '{zweck['bezeichnung']}' wirklich löschen?"
        )
        
        if antwort:
            try:
                with MaschinenDBContext(self.db_path) as db:
                    db.delete_einsatzzweck(zweck_id, soft_delete=True)
                messagebox.showinfo("Erfolg", "Einsatzzweck wurde deaktiviert!")
                self.load_data()
                self.main_gui.refresh_combos()
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler: {str(e)}")
    
    def open_delete_einsaetze_window(self):
        """Öffnet Dialog zum Löschen von Einsätzen nach Zeitraum"""
        delete_window = tk.Toplevel(self.root)
        delete_window.title("Einsätze nach Zeitraum löschen")
        delete_window.geometry("600x400")
        
        # Warnung
        warning_frame = ttk.Frame(delete_window)
        warning_frame.pack(pady=10, padx=10, fill=tk.X)
        
        warning_label = ttk.Label(warning_frame, 
                                  text="⚠️ ACHTUNG: Diese Aktion kann nicht rückgängig gemacht werden!",
                                  foreground="red",
                                  font=("Arial", 12, "bold"))
        warning_label.pack()
        
        info_label = ttk.Label(warning_frame,
                              text="Erstellen Sie vorher ein Backup über 'Admin > Datenbank-Backup erstellen'",
                              foreground="orange")
        info_label.pack()
        
        # Datumswahl Frame
        date_frame = ttk.LabelFrame(delete_window, text="Zeitraum auswählen")
        date_frame.pack(pady=10, padx=10, fill=tk.X)
        
        ttk.Label(date_frame, text="Von Datum (YYYY-MM-DD):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        von_entry = ttk.Entry(date_frame, width=20)
        von_entry.grid(row=0, column=1, padx=5, pady=5)
        von_entry.insert(0, "2024-01-01")
        
        ttk.Label(date_frame, text="Bis Datum (YYYY-MM-DD):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        bis_entry = ttk.Entry(date_frame, width=20)
        bis_entry.grid(row=1, column=1, padx=5, pady=5)
        bis_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        # Vorschau Frame
        preview_frame = ttk.LabelFrame(delete_window, text="Vorschau")
        preview_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        preview_text = tk.Text(preview_frame, height=6, width=70)
        preview_text.pack(pady=5, padx=5, fill=tk.BOTH, expand=True)
        
        def update_preview():
            von_datum = von_entry.get()
            bis_datum = bis_entry.get()
            
            try:
                with MaschinenDBContext(self.db_path) as db:
                    cursor = db.connection.cursor()
                    cursor.execute("""
                        SELECT COUNT(*) as anzahl,
                               SUM(treibstoff_kosten) as gesamt_treibstoff,
                               SUM(kosten_berechnet) as gesamt_maschine
                        FROM einsaetze
                        WHERE datum BETWEEN ? AND ?
                    """, (von_datum, bis_datum))
                    
                    result = cursor.fetchone()
                    anzahl = result[0] or 0
                    treibstoff = result[1] or 0
                    maschine = result[2] or 0
                    
                    preview_text.delete(1.0, tk.END)
                    preview_text.insert(tk.END, f"Es werden {anzahl} Einsätze gelöscht.\n\n")
                    preview_text.insert(tk.END, f"Zeitraum: {von_datum} bis {bis_datum}\n")
                    preview_text.insert(tk.END, f"Treibstoffkosten: {treibstoff:.2f} €\n")
                    preview_text.insert(tk.END, f"Maschinenkosten: {maschine:.2f} €\n")
                    preview_text.insert(tk.END, f"Gesamtkosten: {treibstoff + maschine:.2f} €\n")
            except Exception as e:
                preview_text.delete(1.0, tk.END)
                preview_text.insert(tk.END, f"Fehler bei Vorschau: {str(e)}")
        
        ttk.Button(date_frame, text="Vorschau aktualisieren", command=update_preview).grid(row=2, column=0, columnspan=2, pady=10)
        
        # Bestätigungs-Frame
        confirm_frame = ttk.LabelFrame(delete_window, text="Bestätigung")
        confirm_frame.pack(pady=10, padx=10, fill=tk.X)
        
        ttk.Label(confirm_frame, text='Geben Sie "LOESCHEN" ein, um zu bestätigen:').grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        confirm_entry = ttk.Entry(confirm_frame, width=20)
        confirm_entry.grid(row=0, column=1, padx=5, pady=5)
        
        def delete_einsaetze():
            if confirm_entry.get() != "LOESCHEN":
                messagebox.showerror("Fehler", 'Bitte geben Sie "LOESCHEN" zur Bestätigung ein!')
                return
            
            von_datum = von_entry.get()
            bis_datum = bis_entry.get()
            
            try:
                with MaschinenDBContext(self.db_path) as db:
                    cursor = db.connection.cursor()
                    cursor.execute("""
                        DELETE FROM einsaetze
                        WHERE datum BETWEEN ? AND ?
                    """, (von_datum, bis_datum))
                    
                    geloescht = cursor.rowcount
                    db.connection.commit()
                    
                messagebox.showinfo("Erfolg", f"{geloescht} Einsätze wurden gelöscht!")
                delete_window.destroy()
                self.refresh_einsaetze()
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Löschen: {str(e)}")
        
        # Buttons
        button_frame = ttk.Frame(delete_window)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Löschen", command=delete_einsaetze, 
                  style="Danger.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Abbrechen", command=delete_window.destroy).pack(side=tk.LEFT, padx=5)
        
        # Erste Vorschau laden
        update_preview()
    
    def create_database_backup(self):
        """Erstellt ein Backup der Datenbank"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dateiname = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("SQLite Datenbank", "*.db"), ("Alle Dateien", "*.*")],
            initialfile=f"maschinengemeinschaft_backup_{timestamp}.db"
        )
        
        if not dateiname:
            return
        
        try:
            import shutil
            shutil.copy2(self.db_path, dateiname)
            messagebox.showinfo("Erfolg", f"Backup erstellt:\n{dateiname}")
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Erstellen des Backups: {str(e)}")


# ==================== MAIN ====================

def main():
    root = tk.Tk()
    app = MaschinenGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
