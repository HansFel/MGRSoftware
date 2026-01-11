#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Migration: Rentabilitätsrechnung für Maschinen
Fügt Felder für Anschaffungspreis und Abschreibungsdauer hinzu
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "maschinengemeinschaft.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("Migration: Rentabilitäts-Felder hinzufügen...")
        
        # Prüfe ob Spalten bereits existieren
        cursor.execute("PRAGMA table_info(maschinen)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'anschaffungspreis' not in columns:
            cursor.execute("""
                ALTER TABLE maschinen 
                ADD COLUMN anschaffungspreis REAL DEFAULT 0.0
            """)
            print("✓ Spalte 'anschaffungspreis' hinzugefügt")
        else:
            print("⚠ Spalte 'anschaffungspreis' existiert bereits")
        
        if 'abschreibungsdauer_jahre' not in columns:
            cursor.execute("""
                ALTER TABLE maschinen 
                ADD COLUMN abschreibungsdauer_jahre INTEGER DEFAULT 10
            """)
            print("✓ Spalte 'abschreibungsdauer_jahre' hinzugefügt")
        else:
            print("⚠ Spalte 'abschreibungsdauer_jahre' existiert bereits")
        
        conn.commit()
        print("✓ Migration erfolgreich abgeschlossen")
        
        # Zeige Maschinen
        cursor.execute("""
            SELECT id, bezeichnung, anschaffungspreis, abschreibungsdauer_jahre
            FROM maschinen 
            ORDER BY bezeichnung
        """)
        maschinen = cursor.fetchall()
        print(f"\n{len(maschinen)} Maschinen mit Rentabilitäts-Feldern:")
        for m in maschinen:
            print(f"  {m[1]}: Anschaffungspreis={m[2]:.2f}€, Abschreibung={m[3]} Jahre")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Fehler bei Migration: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
