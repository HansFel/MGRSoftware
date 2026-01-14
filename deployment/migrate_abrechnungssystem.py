#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration: Abrechnungssystem für Gemeinschaftsadministratoren
Erstellt: 14. Januar 2026
"""

import sqlite3
import os
import hashlib
from datetime import datetime

DB_PATH = 'maschinengemeinschaft.db'

def generate_payment_reference(benutzer_id, gemeinschaft_id):
    """Generiert eine eindeutige Zahlungsreferenz"""
    # Format: MGR-{Gemeinschaft}-{Benutzer}-{Checksum}
    base = f"{gemeinschaft_id:03d}{benutzer_id:04d}"
    checksum = sum(int(d) for d in base) % 97
    return f"MGR-{gemeinschaft_id}-{benutzer_id}-{checksum:02d}"

def migrate():
    """Erstellt Tabellen für das Abrechnungssystem"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Datenbank {DB_PATH} nicht gefunden!")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("📝 Erstelle Abrechnungssystem-Tabellen...")
        
        # Tabelle für Zahlungsreferenzen der Mitglieder
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS zahlungsreferenzen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                benutzer_id INTEGER NOT NULL,
                gemeinschaft_id INTEGER NOT NULL,
                referenznummer TEXT UNIQUE NOT NULL,
                erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                aktiv BOOLEAN DEFAULT 1,
                FOREIGN KEY (benutzer_id) REFERENCES benutzer(id) ON DELETE CASCADE,
                FOREIGN KEY (gemeinschaft_id) REFERENCES gemeinschaften(id) ON DELETE CASCADE,
                UNIQUE(benutzer_id, gemeinschaft_id)
            )
        """)
        print("✅ Tabelle 'zahlungsreferenzen' erstellt")
        
        # Tabelle für Banktransaktionen (CSV-Import)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bank_transaktionen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gemeinschaft_id INTEGER NOT NULL,
                buchungsdatum DATE NOT NULL,
                valutadatum DATE,
                verwendungszweck TEXT,
                empfaenger TEXT,
                kontonummer TEXT,
                bic TEXT,
                betrag REAL NOT NULL,
                waehrung TEXT DEFAULT 'EUR',
                transaktions_hash TEXT UNIQUE NOT NULL,
                benutzer_id INTEGER,
                zugeordnet BOOLEAN DEFAULT 0,
                importiert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                importiert_von INTEGER,
                bemerkung TEXT,
                FOREIGN KEY (gemeinschaft_id) REFERENCES gemeinschaften(id),
                FOREIGN KEY (benutzer_id) REFERENCES benutzer(id),
                FOREIGN KEY (importiert_von) REFERENCES benutzer(id)
            )
        """)
        print("✅ Tabelle 'bank_transaktionen' erstellt")
        
        # Tabelle für Abrechnungen (Soll-Beträge)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mitglieder_abrechnungen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gemeinschaft_id INTEGER NOT NULL,
                benutzer_id INTEGER NOT NULL,
                abrechnungszeitraum TEXT NOT NULL,
                zeitraum_von DATE NOT NULL,
                zeitraum_bis DATE NOT NULL,
                betrag_gesamt REAL NOT NULL,
                betrag_treibstoff REAL DEFAULT 0,
                betrag_maschinen REAL DEFAULT 0,
                betrag_sonstiges REAL DEFAULT 0,
                status TEXT DEFAULT 'offen',
                erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                erstellt_von INTEGER,
                bezahlt_am TIMESTAMP,
                bemerkung TEXT,
                FOREIGN KEY (gemeinschaft_id) REFERENCES gemeinschaften(id),
                FOREIGN KEY (benutzer_id) REFERENCES benutzer(id),
                FOREIGN KEY (erstellt_von) REFERENCES benutzer(id)
            )
        """)
        print("✅ Tabelle 'mitglieder_abrechnungen' erstellt")
        
        # Tabelle für Zahlungszuordnungen
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS zahlungs_zuordnungen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaktion_id INTEGER NOT NULL,
                abrechnung_id INTEGER NOT NULL,
                betrag REAL NOT NULL,
                zugeordnet_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                zugeordnet_von INTEGER,
                FOREIGN KEY (transaktion_id) REFERENCES bank_transaktionen(id) ON DELETE CASCADE,
                FOREIGN KEY (abrechnung_id) REFERENCES mitglieder_abrechnungen(id) ON DELETE CASCADE,
                FOREIGN KEY (zugeordnet_von) REFERENCES benutzer(id)
            )
        """)
        print("✅ Tabelle 'zahlungs_zuordnungen' erstellt")
        
        # Indizes für Performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_zahlungsref_benutzer 
            ON zahlungsreferenzen(benutzer_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bank_trans_gemeinschaft 
            ON bank_transaktionen(gemeinschaft_id, buchungsdatum)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bank_trans_benutzer 
            ON bank_transaktionen(benutzer_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_abrechnungen_benutzer 
            ON mitglieder_abrechnungen(benutzer_id, status)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_abrechnungen_zeitraum 
            ON mitglieder_abrechnungen(gemeinschaft_id, zeitraum_von, zeitraum_bis)
        """)
        
        print("✅ Indizes erstellt")
        
        # Zahlungsreferenzen für bestehende Mitglieder generieren
        cursor.execute("""
            SELECT b.id, mg.gemeinschaft_id 
            FROM benutzer b
            JOIN mitglied_gemeinschaft mg ON b.id = mg.mitglied_id
            WHERE b.aktiv = 1
        """)
        
        mitglieder = cursor.fetchall()
        referenzen_erstellt = 0
        
        for benutzer_id, gemeinschaft_id in mitglieder:
            referenz = generate_payment_reference(benutzer_id, gemeinschaft_id)
            try:
                cursor.execute("""
                    INSERT INTO zahlungsreferenzen (benutzer_id, gemeinschaft_id, referenznummer)
                    VALUES (?, ?, ?)
                """, (benutzer_id, gemeinschaft_id, referenz))
                referenzen_erstellt += 1
            except sqlite3.IntegrityError:
                # Referenz existiert bereits
                pass
        
        print(f"✅ {referenzen_erstellt} Zahlungsreferenzen generiert")
        
        conn.commit()
        print("\n✅ Abrechnungssystem erfolgreich erstellt!")
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei Migration: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("Migration: Abrechnungssystem für Gemeinschaftsadministratoren")
    print("=" * 60)
    
    success = migrate()
    
    if not success:
        exit(1)
