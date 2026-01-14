"""
Migration: Fügt erfassungsmodus Spalte zur maschinen Tabelle hinzu
Datum: 11. Januar 2026

Erfassungsmodus:
- 'fortlaufend': Start/Ende Stundenzähler wird erfasst (bisheriges Verhalten)
- 'direkt': Direkte Eingabe von Stunden/Menge ohne Start/Ende
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "maschinengemeinschaft.db")

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Prüfe ob Spalte bereits existiert
        cursor.execute("PRAGMA table_info(maschinen)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'erfassungsmodus' in columns:
            print("Spalte 'erfassungsmodus' existiert bereits.")
            return
        
        # Füge Spalte hinzu
        print("Füge Spalte 'erfassungsmodus' zur Tabelle 'maschinen' hinzu...")
        cursor.execute("""
            ALTER TABLE maschinen 
            ADD COLUMN erfassungsmodus TEXT DEFAULT 'fortlaufend'
        """)
        
        conn.commit()
        print("✓ Migration erfolgreich abgeschlossen!")
        print("  Alle bestehenden Maschinen haben den Modus 'fortlaufend'")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Fehler bei der Migration: {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
