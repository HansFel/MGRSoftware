#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Löscht ALLE bestehenden Abrechnungen, damit neue korrekte erstellt werden können
"""

import sqlite3

DB_PATH = 'maschinengemeinschaft.db'

def delete_all_abrechnungen():
    """Löscht alle Abrechnungen aus der Datenbank"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("=" * 70)
        print("LÖSCHE ALLE BESTEHENDEN ABRECHNUNGEN")
        print("=" * 70)
        
        # Zähle bestehende Abrechnungen
        cursor.execute("SELECT COUNT(*) FROM mitglieder_abrechnungen")
        anzahl = cursor.fetchone()[0]
        
        if anzahl == 0:
            print("\n✅ Keine Abrechnungen vorhanden. Nichts zu löschen.")
            return True
        
        print(f"\n⚠️  Es werden {anzahl} Abrechnung(en) gelöscht!")
        print("\nGrund: Die bestehenden Abrechnungen enthalten Maschinen-Kosten")
        print("       aus verschiedenen Gemeinschaften (Fehler vor der Korrektur).")
        print("\nNach dem Löschen können Sie neue, korrekte Abrechnungen erstellen,")
        print("die nur die Maschinen der jeweiligen Gemeinschaft berücksichtigen.")
        
        antwort = input("\nMöchten Sie fortfahren? (ja/nein): ").strip().lower()
        
        if antwort != 'ja':
            print("\n❌ Abgebrochen. Keine Abrechnungen wurden gelöscht.")
            return False
        
        # Lösche alle Abrechnungen
        cursor.execute("DELETE FROM mitglieder_abrechnungen")
        conn.commit()
        
        print(f"\n✅ {anzahl} Abrechnung(en) erfolgreich gelöscht!")
        print("\nSie können jetzt neue Abrechnungen erstellen über:")
        print("  Admin → Abrechnungen → [Gemeinschaft] → Abrechnungen erstellen")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    delete_all_abrechnungen()
