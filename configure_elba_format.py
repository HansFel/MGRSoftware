#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Konfiguration für Raiffeisen Elba CSV-Format aktualisieren
Erstellt: 14. Januar 2026
"""

import sqlite3
import os

DB_PATH = 'maschinengemeinschaft.db'

def update_elba_config():
    """Aktualisiert CSV-Konfiguration für Raiffeisen Elba Format"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Datenbank {DB_PATH} nicht gefunden!")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Alle Gemeinschaften anzeigen
        cursor.execute("SELECT id, name FROM gemeinschaften WHERE aktiv = 1")
        gemeinschaften = cursor.fetchall()
        
        print("Verfügbare Gemeinschaften:")
        for gem_id, gem_name in gemeinschaften:
            print(f"  [{gem_id}] {gem_name}")
        
        print("\n" + "="*60)
        print("Raiffeisen Elba Format:")
        print("  - KEINE Kopfzeile")
        print("  - Spalten: Buchungsdatum; Beschreibung; Valutadatum; Betrag; Währung; Zeitstempel")
        print("  - Trennzeichen: ;")
        print("  - Dezimaltrennzeichen: ,")
        print("="*60)
        
        gemeinschaft_id = input("\nFür welche Gemeinschaft konfigurieren? (ID eingeben): ")
        gemeinschaft_id = int(gemeinschaft_id)
        
        # Prüfen ob Gemeinschaft existiert
        cursor.execute("SELECT name FROM gemeinschaften WHERE id = ?", (gemeinschaft_id,))
        result = cursor.fetchone()
        if not result:
            print(f"❌ Gemeinschaft mit ID {gemeinschaft_id} nicht gefunden!")
            return False
        
        gemeinschaft_name = result[0]
        
        print(f"\n📝 Konfiguriere Raiffeisen Elba-Format für: {gemeinschaft_name}")
        
        # WICHTIG: Da Elba KEINE Kopfzeile hat, verwenden wir die Spalten-Nummern
        # CSV.DictReader kann nicht mit nummerierten Spalten arbeiten ohne Header
        # Daher müssen wir künstliche Spaltennamen erstellen
        
        cursor.execute("""
            UPDATE csv_import_konfiguration
            SET trennzeichen = ';',
                kodierung = 'utf-8',
                spalte_buchungsdatum = 'Spalte1',
                spalte_valutadatum = 'Spalte3',
                spalte_betrag = 'Spalte4',
                spalte_verwendungszweck = 'Spalte2',
                spalte_empfaenger = 'Spalte2',
                spalte_kontonummer = '',
                spalte_bic = '',
                dezimaltrennzeichen = ',',
                tausendertrennzeichen = '',
                datumsformat = '%d.%m.%Y',
                hat_kopfzeile = 0,
                zeilen_ueberspringen = 0
            WHERE gemeinschaft_id = ?
        """, (gemeinschaft_id,))
        
        conn.commit()
        print(f"✅ Raiffeisen Elba-Format für '{gemeinschaft_name}' konfiguriert!")
        print("\n⚠️  WICHTIG: Das Elba-Format hat KEINE Kopfzeile.")
        print("   Die Spalten werden als Spalte1, Spalte2, etc. bezeichnet.")
        print("   Der Import wurde entsprechend angepasst.")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("Raiffeisen Elba CSV-Format Konfiguration")
    print("=" * 60 + "\n")
    
    update_elba_config()
