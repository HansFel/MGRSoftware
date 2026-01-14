#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test-Script für Reservierungen"""

import sqlite3
from datetime import datetime, timedelta

DB_PATH = 'maschinengemeinschaft.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=" * 60)
print("RESERVIERUNGEN IN DER DATENBANK")
print("=" * 60)

# Alle Reservierungen
cursor.execute("""
    SELECT COUNT(*) FROM maschinen_reservierungen
""")
gesamt = cursor.fetchone()[0]
print(f"\nGesamt Reservierungen: {gesamt}")

# Aktive Reservierungen
cursor.execute("""
    SELECT COUNT(*) FROM maschinen_reservierungen WHERE status = 'aktiv'
""")
aktiv = cursor.fetchone()[0]
print(f"Aktive Reservierungen: {aktiv}")

# Die letzten 5 Reservierungen
print("\n" + "=" * 60)
print("DIE LETZTEN 5 RESERVIERUNGEN:")
print("=" * 60)
cursor.execute("""
    SELECT r.id, r.maschine_id, r.benutzer_id, r.datum, r.uhrzeit_von, r.uhrzeit_bis, 
           r.status, m.bezeichnung as maschine, b.name as benutzer
    FROM maschinen_reservierungen r
    LEFT JOIN maschinen m ON r.maschine_id = m.id
    LEFT JOIN benutzer b ON r.benutzer_id = b.id
    ORDER BY r.erstellt_am DESC
    LIMIT 5
""")

for row in cursor.fetchall():
    print(f"\nID: {row[0]}")
    print(f"  Maschine: {row[7]} (ID: {row[1]})")
    print(f"  Benutzer: {row[8]} (ID: {row[2]})")
    print(f"  Datum: {row[3]}")
    print(f"  Zeit: {row[4]} - {row[5]}")
    print(f"  Status: {row[6]}")

# Zukünftige Reservierungen
heute = datetime.now().strftime('%Y-%m-%d')
in_10_tagen = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')

print("\n" + "=" * 60)
print(f"AKTIVE RESERVIERUNGEN VON HEUTE BIS +10 TAGE:")
print(f"Zeitraum: {heute} bis {in_10_tagen}")
print("=" * 60)

cursor.execute("""
    SELECT r.id, r.datum, r.uhrzeit_von, r.uhrzeit_bis, 
           m.bezeichnung as maschine, b.name as benutzer
    FROM maschinen_reservierungen r
    LEFT JOIN maschinen m ON r.maschine_id = m.id
    LEFT JOIN benutzer b ON r.benutzer_id = b.id
    WHERE r.status = 'aktiv'
      AND r.datum >= ?
      AND r.datum < ?
    ORDER BY r.datum, r.uhrzeit_von
""", (heute, in_10_tagen))

reservierungen = cursor.fetchall()
if reservierungen:
    for row in reservierungen:
        print(f"\n{row[1]} {row[2]}-{row[3]}: {row[4]} - {row[5]}")
else:
    print("\nKeine aktiven Reservierungen im Zeitraum!")

conn.close()
