#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration: Bankverbindung für Gemeinschaften
Fügt Felder für Bankverbindung zur gemeinschaften Tabelle hinzu
Erstellt: 14. Januar 2026
"""

import sqlite3
import os

DB_PATH = 'maschinengemeinschaft.db'

def migrate():
    """Fügt Bankverbindungsfelder zur gemeinschaften Tabelle hinzu"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Datenbank {DB_PATH} nicht gefunden!")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("📝 Füge Bankverbindungsfelder zur gemeinschaften Tabelle hinzu...")
        
        # Prüfe ob Spalten bereits existieren
        cursor.execute("PRAGMA table_info(gemeinschaften)")
        columns = [col[1] for col in cursor.fetchall()]
        
        felder_hinzugefuegt = []
        
        if 'bank_name' not in columns:
            cursor.execute("ALTER TABLE gemeinschaften ADD COLUMN bank_name TEXT")
            felder_hinzugefuegt.append('bank_name')
        
        if 'bank_iban' not in columns:
            cursor.execute("ALTER TABLE gemeinschaften ADD COLUMN bank_iban TEXT")
            felder_hinzugefuegt.append('bank_iban')
        
        if 'bank_bic' not in columns:
            cursor.execute("ALTER TABLE gemeinschaften ADD COLUMN bank_bic TEXT")
            felder_hinzugefuegt.append('bank_bic')
        
        if 'bank_kontoinhaber' not in columns:
            cursor.execute("ALTER TABLE gemeinschaften ADD COLUMN bank_kontoinhaber TEXT")
            felder_hinzugefuegt.append('bank_kontoinhaber')
        
        if felder_hinzugefuegt:
            conn.commit()
            print(f"✅ Folgende Felder hinzugefügt: {', '.join(felder_hinzugefuegt)}")
        else:
            print("ℹ️  Alle Felder existieren bereits")
        
        print("\n✅ Migration erfolgreich abgeschlossen!")
        print("\nHinweis:")
        print("- Bankverbindung kann jetzt pro Gemeinschaft hinterlegt werden")
        print("- Wird in Abrechnungs-PDFs für Mitglieder angezeigt")
        print("- Einstellung unter: Admin → Gemeinschaften → [Gemeinschaft bearbeiten]")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Fehler bei der Migration: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 70)
    print("Migration: Bankverbindung für Gemeinschaften")
    print("=" * 70)
    migrate()
