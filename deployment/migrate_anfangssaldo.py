#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration: Anfangssaldo für Gemeinschaften
Erstellt: 14. Januar 2026
"""

import sqlite3
import os

DB_PATH = 'maschinengemeinschaft.db'

def migrate():
    """Fügt Anfangssaldo-Feld zu Gemeinschaften hinzu"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Datenbank {DB_PATH} nicht gefunden!")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("📝 Erweitere Gemeinschaften-Tabelle...")
        
        # Prüfe ob Spalte bereits existiert
        cursor.execute("PRAGMA table_info(gemeinschaften)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'anfangssaldo_bank' not in columns:
            cursor.execute("""
                ALTER TABLE gemeinschaften
                ADD COLUMN anfangssaldo_bank REAL DEFAULT 0.0
            """)
            print("✅ Spalte 'anfangssaldo_bank' hinzugefügt")
        else:
            print("ℹ️ Spalte 'anfangssaldo_bank' existiert bereits")
        
        if 'anfangssaldo_datum' not in columns:
            cursor.execute("""
                ALTER TABLE gemeinschaften
                ADD COLUMN anfangssaldo_datum DATE DEFAULT NULL
            """)
            print("✅ Spalte 'anfangssaldo_datum' hinzugefügt")
        else:
            print("ℹ️ Spalte 'anfangssaldo_datum' existiert bereits")
        
        conn.commit()
        print("\n✅ Migration erfolgreich abgeschlossen!")
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei Migration: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("Migration: Anfangssaldo für Gemeinschaften")
    print("=" * 60)
    
    success = migrate()
    
    if not success:
        exit(1)
