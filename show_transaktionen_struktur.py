#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zeigt Struktur der bank_transaktionen Tabelle
"""

import sqlite3

DB_PATH = 'maschinengemeinschaft.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Prüfe ob Tabelle existiert
cursor.execute("""
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name='bank_transaktionen'
""")

if cursor.fetchone():
    print("Tabelle 'bank_transaktionen' gefunden\n")
    
    # Zeige Struktur
    cursor.execute("PRAGMA table_info(bank_transaktionen)")
    columns = cursor.fetchall()
    
    print("Spalten:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # Zeige Anzahl
    cursor.execute("SELECT COUNT(*) FROM bank_transaktionen")
    count = cursor.fetchone()[0]
    print(f"\nAnzahl Einträge: {count}")
    
    if count > 0:
        # Zeige erste 3 Einträge
        cursor.execute("SELECT * FROM bank_transaktionen LIMIT 3")
        print("\nErste Einträge:")
        for row in cursor.fetchall():
            print(row)
else:
    print("Tabelle 'bank_transaktionen' existiert nicht")

conn.close()
