#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration: Buchungssystem für doppelte Buchführung

Erstellt Tabellen für:
- buchungen: Alle Transaktionen (Abrechnungen, Zahlungen, manuelle Buchungen)
- mitglieder_konten: Cache für Kontostände pro Mitglied und Gemeinschaft
"""

import sqlite3
import sys
from datetime import datetime

DB_PATH = 'maschinengemeinschaft.db'

def migrate():
    """Führt die Migration durch"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("=== Buchungssystem Migration ===\n")
        
        # 1. Tabelle: buchungen
        print("Erstelle Tabelle 'buchungen'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS buchungen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                benutzer_id INTEGER NOT NULL,
                gemeinschaft_id INTEGER NOT NULL,
                datum DATE NOT NULL,
                betrag REAL NOT NULL,
                typ TEXT NOT NULL CHECK(typ IN (
                    'abrechnung',      -- Automatisch aus Abrechnungserstellung
                    'einzahlung',      -- Zahlung des Mitglieds
                    'auszahlung',      -- Auszahlung an Mitglied (z.B. Rückerstattung)
                    'korrektur',       -- Manuelle Korrektur durch Admin
                    'jahresuebertrag'  -- Übertrag Vorjahressaldo
                )),
                beschreibung TEXT,
                referenz_typ TEXT,     -- 'abrechnung', 'manually', etc.
                referenz_id INTEGER,   -- ID der Abrechnung oder NULL
                erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                erstellt_von INTEGER NOT NULL, -- Admin der die Buchung erstellt hat
                
                FOREIGN KEY (benutzer_id) REFERENCES benutzer(id),
                FOREIGN KEY (gemeinschaft_id) REFERENCES gemeinschaften(id),
                FOREIGN KEY (erstellt_von) REFERENCES benutzer(id)
            )
        """)
        
        # Index für schnelle Abfragen
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_buchungen_benutzer_gemeinschaft 
            ON buchungen(benutzer_id, gemeinschaft_id, datum)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_buchungen_referenz 
            ON buchungen(referenz_typ, referenz_id)
        """)
        print("✓ Tabelle 'buchungen' erstellt")
        
        # 2. Tabelle: mitglieder_konten (Cache für Salden)
        print("\nErstelle Tabelle 'mitglieder_konten'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mitglieder_konten (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                benutzer_id INTEGER NOT NULL,
                gemeinschaft_id INTEGER NOT NULL,
                saldo REAL DEFAULT 0,           -- Aktueller Kontostand
                saldo_vorjahr REAL DEFAULT 0,   -- Saldo vom Jahresabschluss
                letzte_aktualisierung TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(benutzer_id, gemeinschaft_id),
                FOREIGN KEY (benutzer_id) REFERENCES benutzer(id),
                FOREIGN KEY (gemeinschaft_id) REFERENCES gemeinschaften(id)
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_mitglieder_konten_gemeinschaft 
            ON mitglieder_konten(gemeinschaft_id, saldo)
        """)
        print("✓ Tabelle 'mitglieder_konten' erstellt")
        
        # 3. Tabelle: jahresabschluesse (Historie der Jahresabschlüsse)
        print("\nErstelle Tabelle 'jahresabschluesse'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jahresabschluesse (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gemeinschaft_id INTEGER NOT NULL,
                jahr INTEGER NOT NULL,
                abschluss_datum DATE NOT NULL,
                erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                erstellt_von INTEGER NOT NULL,
                bemerkung TEXT,
                
                UNIQUE(gemeinschaft_id, jahr),
                FOREIGN KEY (gemeinschaft_id) REFERENCES gemeinschaften(id),
                FOREIGN KEY (erstellt_von) REFERENCES benutzer(id)
            )
        """)
        print("✓ Tabelle 'jahresabschluesse' erstellt")
        
        conn.commit()
        
        print("\n=== Migration erfolgreich abgeschlossen! ===")
        print("\nNächste Schritte:")
        print("1. Bestehende Abrechnungen in Buchungen umwandeln")
        print("2. Für jedes Mitglied ein Konto initialisieren")
        print("3. Web-Interface für Buchungen implementieren")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Datenbankfehler: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ Fehler: {e}", file=sys.stderr)
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
