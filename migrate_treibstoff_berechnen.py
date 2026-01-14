#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration: Treibstoff-Berechnungseinstellung für Maschinen
Fügt Spalte hinzu, um zu steuern ob Treibstoff in Abrechnungen berücksichtigt wird
Erstellt: 14. Januar 2026
"""

import sqlite3
import os

DB_PATH = 'maschinengemeinschaft.db'

def migrate():
    """Fügt treibstoff_berechnen Spalte zur maschinen Tabelle hinzu"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Datenbank {DB_PATH} nicht gefunden!")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("📝 Füge Spalte 'treibstoff_berechnen' zur maschinen Tabelle hinzu...")
        
        # Prüfe ob Spalte bereits existiert
        cursor.execute("PRAGMA table_info(maschinen)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'treibstoff_berechnen' not in columns:
            # Füge Spalte hinzu (Standard: 0 = Treibstoff NICHT berechnen, da die meisten Mitglieder selbst tanken)
            cursor.execute("""
                ALTER TABLE maschinen 
                ADD COLUMN treibstoff_berechnen BOOLEAN DEFAULT 0
            """)
            print("✅ Spalte 'treibstoff_berechnen' hinzugefügt (Standard: NICHT berechnen)")
            
            # Setze bestehende Maschinen auf 0 (nicht berechnen)
            cursor.execute("UPDATE maschinen SET treibstoff_berechnen = 0")
            print(f"✅ Alle bestehenden Maschinen auf 'Treibstoff NICHT berechnen' gesetzt")
        else:
            print("ℹ️  Spalte 'treibstoff_berechnen' existiert bereits")
        
        conn.commit()
        print("\n✅ Migration erfolgreich abgeschlossen!")
        print("\nHinweis:")
        print("- Standard: Treibstoffkosten werden NICHT berechnet (da Mitglieder selbst tanken)")
        print("- In der Maschinenverwaltung kann dies pro Maschine eingestellt werden")
        print("- Nur wenn aktiviert, werden Treibstoffkosten in Abrechnungen aufgenommen")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Fehler bei der Migration: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 70)
    print("Migration: Treibstoff-Berechnungseinstellung für Maschinen")
    print("=" * 70)
    migrate()
