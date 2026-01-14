#!/usr/bin/env python3
"""
Migration: Tabelle für stornierte Einsätze erstellen
"""

import sqlite3
import os

def migrate():
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'maschinengemeinschaft.db')
    if not os.path.exists(db_path):
        db_path = 'maschinengemeinschaft.db'
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tabelle für stornierte Einsätze erstellen
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS maschineneinsaetze_storniert (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_einsatz_id INTEGER NOT NULL,
            datum TEXT NOT NULL,
            benutzer_id INTEGER NOT NULL,
            maschine_id INTEGER NOT NULL,
            einsatzzweck_id INTEGER,
            stundenzaehler_anfang REAL,
            stundenzaehler_ende REAL,
            betriebsstunden REAL,
            hektar REAL,
            kilometer REAL,
            stueck INTEGER,
            treibstoffverbrauch REAL,
            treibstoffkosten REAL,
            maschinenkosten REAL,
            gesamtkosten REAL,
            bemerkung TEXT,
            storniert_am TEXT NOT NULL,
            storniert_von INTEGER NOT NULL,
            stornierungsgrund TEXT,
            FOREIGN KEY (benutzer_id) REFERENCES benutzer(id),
            FOREIGN KEY (maschine_id) REFERENCES maschinen(id),
            FOREIGN KEY (einsatzzweck_id) REFERENCES einsatzzwecke(id),
            FOREIGN KEY (storniert_von) REFERENCES benutzer(id)
        )
    ''')
    
    # Index für Performance
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_storniert_benutzer 
        ON maschineneinsaetze_storniert(benutzer_id)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_storniert_maschine 
        ON maschineneinsaetze_storniert(maschine_id)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_storniert_datum 
        ON maschineneinsaetze_storniert(datum)
    ''')
    
    conn.commit()
    conn.close()
    print("✓ Migration erfolgreich: Tabelle maschineneinsaetze_storniert erstellt")

if __name__ == '__main__':
    migrate()
