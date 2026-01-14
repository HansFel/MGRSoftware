#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Migration: Treibstoffkosten pro Benutzer
Fügt eine Spalte für individuelle Treibstoffkosten zur benutzer-Tabelle hinzu
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "maschinengemeinschaft.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("Migration: Treibstoffkosten-Spalte hinzufügen...")
        
        # Prüfe ob Spalte bereits existiert
        cursor.execute("PRAGMA table_info(benutzer)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'treibstoffkosten_preis' not in columns:
            # Füge treibstoffkosten_preis Spalte hinzu (Standard: 1.50 EUR/L)
            cursor.execute("""
                ALTER TABLE benutzer 
                ADD COLUMN treibstoffkosten_preis REAL DEFAULT 1.50
            """)
            print("✓ Spalte 'treibstoffkosten_preis' hinzugefügt")
            
            # Setze für alle existierenden Benutzer einen Standardwert
            cursor.execute("""
                UPDATE benutzer 
                SET treibstoffkosten_preis = 1.50 
                WHERE treibstoffkosten_preis IS NULL
            """)
            print("✓ Standardwert 1.50 EUR/L für alle Benutzer gesetzt")
        else:
            print("⚠ Spalte 'treibstoffkosten_preis' existiert bereits")
        
        conn.commit()
        print("✓ Migration erfolgreich abgeschlossen")
        
        # Zeige Benutzer mit ihren Treibstoffkosten
        cursor.execute("""
            SELECT id, name, vorname, treibstoffkosten_preis 
            FROM benutzer 
            ORDER BY name, vorname
        """)
        benutzer = cursor.fetchall()
        print(f"\n{len(benutzer)} Benutzer mit Treibstoffkosten:")
        for b in benutzer:
            print(f"  {b[1]}, {b[2]}: {b[3]:.2f} EUR/L")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Fehler bei Migration: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
