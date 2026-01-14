#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration: Tabelle für gelöschte/stornierte Reservierungen
Erstellt: 14. Januar 2026
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = 'maschinengemeinschaft.db'

def migrate():
    """Erstellt Tabelle für gelöschte/stornierte Reservierungen"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Datenbank {DB_PATH} nicht gefunden!")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Prüfen ob Tabelle bereits existiert
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='reservierungen_geloescht'
        """)
        
        if cursor.fetchone():
            print("ℹ️  Tabelle 'reservierungen_geloescht' existiert bereits")
            conn.close()
            return True
        
        # Tabelle erstellen
        print("📝 Erstelle Tabelle 'reservierungen_geloescht'...")
        cursor.execute("""
            CREATE TABLE reservierungen_geloescht (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reservierung_id INTEGER,
                maschine_id INTEGER NOT NULL,
                maschine_bezeichnung TEXT,
                benutzer_id INTEGER NOT NULL,
                benutzer_name TEXT,
                datum DATE NOT NULL,
                uhrzeit_von TIME NOT NULL,
                uhrzeit_bis TIME NOT NULL,
                nutzungsdauer_stunden REAL NOT NULL,
                zweck TEXT,
                bemerkung TEXT,
                erstellt_am TIMESTAMP,
                geloescht_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                geloescht_von INTEGER,
                grund TEXT
            )
        """)
        
        # Index für schnellere Abfragen
        cursor.execute("""
            CREATE INDEX idx_geloescht_maschine 
            ON reservierungen_geloescht(maschine_id, datum)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_geloescht_benutzer 
            ON reservierungen_geloescht(benutzer_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_geloescht_datum 
            ON reservierungen_geloescht(geloescht_am)
        """)
        
        conn.commit()
        print("✅ Tabelle 'reservierungen_geloescht' erfolgreich erstellt")
        print("✅ Indizes erstellt")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei Migration: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == '__main__':
    print("Migration: Gelöschte Reservierungen")
    print("=" * 50)
    if migrate():
        print("\n✅ Migration erfolgreich abgeschlossen")
    else:
        print("\n❌ Migration fehlgeschlagen")
