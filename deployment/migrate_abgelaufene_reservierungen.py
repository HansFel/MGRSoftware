#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration: Tabelle für abgelaufene Reservierungen
Erstellt: 14. Januar 2026
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = 'maschinengemeinschaft.db'

def migrate():
    """Erstellt Tabelle für abgelaufene Reservierungen"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Datenbank {DB_PATH} nicht gefunden!")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Prüfen ob Tabelle bereits existiert
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='reservierungen_abgelaufen'
        """)
        
        if cursor.fetchone():
            print("ℹ️  Tabelle 'reservierungen_abgelaufen' existiert bereits")
            conn.close()
            return True
        
        # Tabelle erstellen
        print("📝 Erstelle Tabelle 'reservierungen_abgelaufen'...")
        cursor.execute("""
            CREATE TABLE reservierungen_abgelaufen (
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
                abgelaufen_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Index für schnellere Abfragen
        cursor.execute("""
            CREATE INDEX idx_abgelaufen_maschine 
            ON reservierungen_abgelaufen(maschine_id, datum)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_abgelaufen_benutzer 
            ON reservierungen_abgelaufen(benutzer_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_abgelaufen_datum 
            ON reservierungen_abgelaufen(abgelaufen_am)
        """)
        
        conn.commit()
        print("✅ Tabelle 'reservierungen_abgelaufen' erfolgreich erstellt")
        print("✅ Indizes erstellt")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei Migration: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("Migration: Abgelaufene Reservierungen")
    print("=" * 60)
    
    success = migrate()
    
    if success:
        print("\n✅ Migration erfolgreich abgeschlossen!")
    else:
        print("\n❌ Migration fehlgeschlagen!")
        exit(1)
