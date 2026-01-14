"""
Migration: Fügt is_admin Spalte zur benutzer-Tabelle hinzu
"""

import sqlite3
import os

DB_PATH = "maschinengemeinschaft.db"

def migrate_add_is_admin():
    """Fügt is_admin Spalte hinzu"""
    if not os.path.exists(DB_PATH):
        print("❌ Datenbank nicht gefunden.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Prüfen ob Spalte bereits existiert
        cursor.execute("PRAGMA table_info(benutzer)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'is_admin' not in columns:
            print("➕ Füge 'is_admin' Spalte hinzu...")
            cursor.execute("ALTER TABLE benutzer ADD COLUMN is_admin BOOLEAN DEFAULT 0")
            conn.commit()
            print("✅ 'is_admin' Spalte hinzugefügt")
        else:
            print("ℹ️  'is_admin' Spalte existiert bereits")
        
        print("\n📝 Sie können nun in der Desktop-App (main.py) Administratoren festlegen.")
        
    except Exception as e:
        print(f"❌ Fehler: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔄 Starte Migration für Admin-Funktion...\n")
    migrate_add_is_admin()
