"""
Migrations-Skript: Fügt fehlende Spalten zur maschinen-Tabelle hinzu
"""

import sqlite3
import os

DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.dirname(__file__), "maschinengemeinschaft.db"))

def migrate():
    """Fügt wartungsintervall und naechste_wartung Spalten hinzu"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Prüfen, ob Spalten existieren
        cursor.execute("PRAGMA table_info(maschinen)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # wartungsintervall hinzufügen (in Betriebsstunden)
        if 'wartungsintervall' not in columns:
            print("Füge Spalte 'wartungsintervall' hinzu...")
            cursor.execute("ALTER TABLE maschinen ADD COLUMN wartungsintervall INTEGER DEFAULT 50")
            print("✓ Spalte 'wartungsintervall' hinzugefügt")
        else:
            print("✓ Spalte 'wartungsintervall' existiert bereits")
        
        # naechste_wartung hinzufügen (Stundenzählerstand bei nächster Wartung)
        if 'naechste_wartung' not in columns:
            print("Füge Spalte 'naechste_wartung' hinzu...")
            cursor.execute("ALTER TABLE maschinen ADD COLUMN naechste_wartung REAL")
            print("✓ Spalte 'naechste_wartung' hinzugefügt")
        else:
            print("✓ Spalte 'naechste_wartung' existiert bereits")
        
        # anmerkungen hinzufügen falls nicht vorhanden
        if 'anmerkungen' not in columns:
            print("Füge Spalte 'anmerkungen' hinzu...")
            cursor.execute("ALTER TABLE maschinen ADD COLUMN anmerkungen TEXT")
            print("✓ Spalte 'anmerkungen' hinzugefügt")
        else:
            print("✓ Spalte 'anmerkungen' existiert bereits")
        
        conn.commit()
        print("\n✓ Migration erfolgreich abgeschlossen!")
        
    except Exception as e:
        print(f"✗ Fehler bei der Migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    print("Starte Datenbank-Migration für maschinen-Tabelle...")
    print(f"Datenbank: {DB_PATH}\n")
    migrate()
