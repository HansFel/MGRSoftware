#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration: CSV-Import-Konfiguration für Gemeinschaften
Erstellt: 14. Januar 2026
"""

import sqlite3
import os

DB_PATH = 'maschinengemeinschaft.db'

def migrate():
    """Erstellt Tabelle für CSV-Import-Konfigurationen"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Datenbank {DB_PATH} nicht gefunden!")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("📝 Erstelle CSV-Import-Konfigurationstabelle...")
        
        # Tabelle für CSV-Import-Konfigurationen
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS csv_import_konfiguration (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gemeinschaft_id INTEGER NOT NULL UNIQUE,
                trennzeichen TEXT DEFAULT ';',
                kodierung TEXT DEFAULT 'utf-8-sig',
                spalte_buchungsdatum TEXT DEFAULT 'Buchungstag',
                spalte_valutadatum TEXT DEFAULT 'Valutadatum',
                spalte_betrag TEXT DEFAULT 'Betrag',
                spalte_verwendungszweck TEXT DEFAULT 'Verwendungszweck',
                spalte_empfaenger TEXT DEFAULT 'Beguenstigter/Zahlungspflichtiger',
                spalte_kontonummer TEXT DEFAULT 'Kontonummer',
                spalte_bic TEXT DEFAULT 'BIC',
                dezimaltrennzeichen TEXT DEFAULT ',',
                tausendertrennzeichen TEXT DEFAULT '.',
                datumsformat TEXT DEFAULT '%d.%m.%Y',
                hat_kopfzeile BOOLEAN DEFAULT 1,
                zeilen_ueberspringen INTEGER DEFAULT 0,
                erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                geaendert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (gemeinschaft_id) REFERENCES gemeinschaften(id) ON DELETE CASCADE
            )
        """)
        print("✅ Tabelle 'csv_import_konfiguration' erstellt")
        
        # Trigger für Änderungsdatum
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS update_csv_config_timestamp 
            AFTER UPDATE ON csv_import_konfiguration
            BEGIN
                UPDATE csv_import_konfiguration 
                SET geaendert_am = CURRENT_TIMESTAMP 
                WHERE id = NEW.id;
            END
        """)
        print("✅ Trigger erstellt")
        
        # Standard-Konfigurationen für bestehende Gemeinschaften
        cursor.execute("SELECT id, name FROM gemeinschaften WHERE aktiv = 1")
        gemeinschaften = cursor.fetchall()
        
        for gem_id, gem_name in gemeinschaften:
            try:
                cursor.execute("""
                    INSERT INTO csv_import_konfiguration (gemeinschaft_id)
                    VALUES (?)
                """, (gem_id,))
                print(f"✅ Standard-Konfiguration für '{gem_name}' erstellt")
            except sqlite3.IntegrityError:
                # Konfiguration existiert bereits
                pass
        
        conn.commit()
        print("\n✅ CSV-Import-Konfiguration erfolgreich erstellt!")
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei Migration: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("Migration: CSV-Import-Konfiguration")
    print("=" * 60)
    
    success = migrate()
    
    if not success:
        exit(1)
