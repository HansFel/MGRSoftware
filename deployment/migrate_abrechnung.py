"""
Migrations-Skript: Fügt Abrechnungs-Spalten zur maschinen-Tabelle hinzu
"""

import sqlite3
import os

DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.dirname(__file__), "maschinengemeinschaft.db"))

def migrate():
    """Fügt abrechnungsart und preis_pro_einheit Spalten hinzu"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Prüfen, ob Spalten existieren
        cursor.execute("PRAGMA table_info(maschinen)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # abrechnungsart hinzufügen (stunden, hektar, kilometer, etc.)
        if 'abrechnungsart' not in columns:
            print("Füge Spalte 'abrechnungsart' hinzu...")
            cursor.execute("ALTER TABLE maschinen ADD COLUMN abrechnungsart TEXT DEFAULT 'stunden'")
            print("✓ Spalte 'abrechnungsart' hinzugefügt")
        else:
            print("✓ Spalte 'abrechnungsart' existiert bereits")
        
        # preis_pro_einheit hinzufügen
        if 'preis_pro_einheit' not in columns:
            print("Füge Spalte 'preis_pro_einheit' hinzu...")
            cursor.execute("ALTER TABLE maschinen ADD COLUMN preis_pro_einheit REAL DEFAULT 0.0")
            print("✓ Spalte 'preis_pro_einheit' hinzugefügt")
        else:
            print("✓ Spalte 'preis_pro_einheit' existiert bereits")
        
        # Spalte in maschineneinsaetze für Fläche/Menge
        cursor.execute("PRAGMA table_info(maschineneinsaetze)")
        einsatz_columns = [row[1] for row in cursor.fetchall()]
        
        if 'flaeche_menge' not in einsatz_columns:
            print("Füge Spalte 'flaeche_menge' zu maschineneinsaetze hinzu...")
            cursor.execute("ALTER TABLE maschineneinsaetze ADD COLUMN flaeche_menge REAL")
            print("✓ Spalte 'flaeche_menge' hinzugefügt")
        else:
            print("✓ Spalte 'flaeche_menge' existiert bereits")
        
        if 'kosten_berechnet' not in einsatz_columns:
            print("Füge Spalte 'kosten_berechnet' zu maschineneinsaetze hinzu...")
            cursor.execute("ALTER TABLE maschineneinsaetze ADD COLUMN kosten_berechnet REAL")
            print("✓ Spalte 'kosten_berechnet' hinzugefügt")
        else:
            print("✓ Spalte 'kosten_berechnet' existiert bereits")
        
        conn.commit()
        print("\n✓ Migration erfolgreich abgeschlossen!")
        
    except Exception as e:
        print(f"✗ Fehler bei der Migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    print("Starte Datenbank-Migration für Abrechnung...")
    print(f"Datenbank: {DB_PATH}\n")
    migrate()
