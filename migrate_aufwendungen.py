#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration: Tabelle für jährliche Maschinenaufwendungen
Erstellt: 11. Januar 2026
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = 'maschinengemeinschaft.db'

def migrate():
    """Erstellt Tabelle für jährliche Maschinenaufwendungen"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Datenbank {DB_PATH} nicht gefunden!")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Prüfen ob Tabelle bereits existiert
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='maschinen_aufwendungen'
        """)
        
        if cursor.fetchone():
            print("ℹ️  Tabelle 'maschinen_aufwendungen' existiert bereits")
            conn.close()
            return True
        
        # Tabelle erstellen
        print("📝 Erstelle Tabelle 'maschinen_aufwendungen'...")
        cursor.execute("""
            CREATE TABLE maschinen_aufwendungen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                maschine_id INTEGER NOT NULL,
                jahr INTEGER NOT NULL,
                wartungskosten REAL DEFAULT 0.0,
                reparaturkosten REAL DEFAULT 0.0,
                versicherung REAL DEFAULT 0.0,
                steuern REAL DEFAULT 0.0,
                sonstige_kosten REAL DEFAULT 0.0,
                bemerkung TEXT,
                erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                geaendert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (maschine_id) REFERENCES maschinen(id) ON DELETE CASCADE,
                UNIQUE(maschine_id, jahr)
            )
        """)
        
        # Index für schnellere Abfragen
        cursor.execute("""
            CREATE INDEX idx_aufwendungen_maschine_jahr 
            ON maschinen_aufwendungen(maschine_id, jahr)
        """)
        
        conn.commit()
        print("✅ Tabelle 'maschinen_aufwendungen' erfolgreich erstellt")
        print("✅ Index 'idx_aufwendungen_maschine_jahr' erstellt")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei Migration: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("Migration: Maschinenaufwendungen")
    print("=" * 60)
    
    success = migrate()
    
    if success:
        print("\n✅ Migration erfolgreich abgeschlossen!")
    else:
        print("\n❌ Migration fehlgeschlagen!")
        exit(1)
