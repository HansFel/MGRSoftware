#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prüft vorhandene Bank-Transaktionen und deren Zuordnung zu Mitgliedern
"""

import sqlite3
import sys

DB_PATH = 'maschinengemeinschaft.db'

def check_transaktionen():
    """Zeigt alle Bank-Transaktionen und deren Status"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Prüfe ob Tabelle existiert
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='bank_transaktionen'
        """)
        
        if not cursor.fetchone():
            print("❌ Tabelle 'bank_transaktionen' existiert nicht")
            return False
        
        print("=== Bank-Transaktionen Übersicht ===\n")
        
        # Alle Transaktionen mit Zuordnung
        cursor.execute("""
            SELECT 
                t.id,
                t.datum,
                t.betrag,
                t.verwendungszweck,
                t.auftraggeber,
                t.zugeordnet_mitglied_id,
                b.vorname || ' ' || b.name as mitglied_name,
                g.name as gemeinschaft_name,
                t.status
            FROM bank_transaktionen t
            LEFT JOIN benutzer b ON t.zugeordnet_mitglied_id = b.id
            LEFT JOIN gemeinschaften g ON t.gemeinschaft_id = g.id
            ORDER BY t.datum DESC
        """)
        
        transaktionen = cursor.fetchall()
        
        if not transaktionen:
            print("ℹ️  Keine Bank-Transaktionen gefunden\n")
            return True
        
        print(f"Gefunden: {len(transaktionen)} Transaktionen\n")
        
        zugeordnet = 0
        nicht_zugeordnet = 0
        
        for t in transaktionen:
            t_id, datum, betrag, verwendung, auftraggeber, mitglied_id, mitglied_name, gem_name, status = t
            
            print(f"ID {t_id}: {datum} | {betrag:,.2f} €")
            print(f"  Gemeinschaft: {gem_name}")
            print(f"  Auftraggeber: {auftraggeber}")
            print(f"  Verwendung: {verwendung[:50]}...")
            
            if mitglied_id:
                print(f"  ✅ Zugeordnet zu: {mitglied_name}")
                zugeordnet += 1
            else:
                print(f"  ⚠️  Nicht zugeordnet")
                nicht_zugeordnet += 1
            
            print(f"  Status: {status}")
            print()
        
        print("=" * 50)
        print(f"Zugeordnet: {zugeordnet}")
        print(f"Nicht zugeordnet: {nicht_zugeordnet}")
        print("=" * 50)
        
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
    success = check_transaktionen()
    sys.exit(0 if success else 1)
