#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration: Tabelle für Maschinenreservierungen
Erstellt: 11. Januar 2026
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = 'maschinengemeinschaft.db'

def migrate():
    """Erstellt Tabelle für Maschinenreservierungen"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Datenbank {DB_PATH} nicht gefunden!")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Prüfen ob Tabelle bereits existiert
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='maschinen_reservierungen'
        """)
        
        if cursor.fetchone():
            print("ℹ️  Tabelle 'maschinen_reservierungen' existiert bereits")
            conn.close()
            return True
        
        # Tabelle erstellen
        print("📝 Erstelle Tabelle 'maschinen_reservierungen'...")
        cursor.execute("""
            CREATE TABLE maschinen_reservierungen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                maschine_id INTEGER NOT NULL,
                benutzer_id INTEGER NOT NULL,
                datum DATE NOT NULL,
                uhrzeit_von TIME NOT NULL,
                uhrzeit_bis TIME NOT NULL,
                nutzungsdauer_stunden REAL NOT NULL,
                zweck TEXT,
                bemerkung TEXT,
                status TEXT DEFAULT 'aktiv',
                erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                geaendert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (maschine_id) REFERENCES maschinen(id) ON DELETE CASCADE,
                FOREIGN KEY (benutzer_id) REFERENCES benutzer(id) ON DELETE CASCADE
            )
        """)
        
        # Index für schnellere Abfragen
        cursor.execute("""
            CREATE INDEX idx_reservierungen_maschine_datum 
            ON maschinen_reservierungen(maschine_id, datum, status)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_reservierungen_benutzer 
            ON maschinen_reservierungen(benutzer_id, status)
        """)
        
        conn.commit()
        print("✅ Tabelle 'maschinen_reservierungen' erfolgreich erstellt")
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
    print("Migration: Maschinenreservierungen")
    print("=" * 60)
    
    success = migrate()
    
    if success:
        print("\n✅ Migration erfolgreich abgeschlossen!")
    else:
        print("\n❌ Migration fehlgeschlagen!")
        exit(1)
