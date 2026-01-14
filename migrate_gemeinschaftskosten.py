#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration: Gemeinschaftskosten und erweiterte Transaktionszuordnung
Erstellt: 14. Januar 2026
"""

import sqlite3
import os

DB_PATH = 'maschinengemeinschaft.db'

def migrate():
    """Erstellt Tabelle für Gemeinschaftskosten und erweitert Transaktionen"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Datenbank {DB_PATH} nicht gefunden!")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("📝 Erweitere Abrechnungssystem...")
        
        # Tabelle für Gemeinschaftskosten (Ausgaben)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gemeinschafts_kosten (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gemeinschaft_id INTEGER NOT NULL,
                transaktion_id INTEGER,
                maschine_id INTEGER,
                kategorie TEXT DEFAULT 'sonstiges',
                betrag REAL NOT NULL,
                datum DATE NOT NULL,
                beschreibung TEXT,
                bemerkung TEXT,
                erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                erstellt_von INTEGER,
                FOREIGN KEY (gemeinschaft_id) REFERENCES gemeinschaften(id),
                FOREIGN KEY (transaktion_id) REFERENCES bank_transaktionen(id) ON DELETE SET NULL,
                FOREIGN KEY (maschine_id) REFERENCES maschinen(id) ON DELETE SET NULL,
                FOREIGN KEY (erstellt_von) REFERENCES benutzer(id)
            )
        """)
        print("✅ Tabelle 'gemeinschafts_kosten' erstellt")
        
        # Spalten zu bank_transaktionen hinzufügen falls nicht vorhanden
        cursor.execute("PRAGMA table_info(bank_transaktionen)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'zuordnung_typ' not in columns:
            cursor.execute("""
                ALTER TABLE bank_transaktionen
                ADD COLUMN zuordnung_typ TEXT DEFAULT NULL
            """)
            print("✅ Spalte 'zuordnung_typ' hinzugefügt")
        
        if 'zuordnung_id' not in columns:
            cursor.execute("""
                ALTER TABLE bank_transaktionen
                ADD COLUMN zuordnung_id INTEGER DEFAULT NULL
            """)
            print("✅ Spalte 'zuordnung_id' hinzugefügt")
        
        # Indizes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_gemeinschafts_kosten_gemeinschaft 
            ON gemeinschafts_kosten(gemeinschaft_id, datum)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_gemeinschafts_kosten_maschine 
            ON gemeinschafts_kosten(maschine_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bank_trans_zuordnung 
            ON bank_transaktionen(zuordnung_typ, zuordnung_id)
        """)
        
        print("✅ Indizes erstellt")
        
        conn.commit()
        print("\n✅ Erweiterung erfolgreich abgeschlossen!")
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei Migration: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("Migration: Gemeinschaftskosten & Transaktionszuordnung")
    print("=" * 60)
    
    success = migrate()
    
    if not success:
        exit(1)
