#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Debug-Script für Abrechnungen"""

import sqlite3

conn = sqlite3.connect('maschinengemeinschaft.db')
cursor = conn.cursor()

print("=" * 70)
print("DEBUG: Abrechnungen erstellen")
print("=" * 70)

# 1. Prüfe Maschineneinsätze
cursor.execute('SELECT COUNT(*) FROM maschineneinsaetze')
print(f'\nAnzahl Maschineneinsätze gesamt: {cursor.fetchone()[0]}')

cursor.execute('''
    SELECT datum, benutzer_id, maschine_id, kosten_berechnet, treibstoffkosten 
    FROM maschineneinsaetze 
    ORDER BY datum DESC 
    LIMIT 5
''')
print('\nLetzte 5 Einsätze:')
for row in cursor.fetchall():
    print(f'  Datum: {row[0]}, Benutzer: {row[1]}, Maschine: {row[2]}, Kosten: {row[3]}, Treibstoff: {row[4]}')

# 2. Prüfe Zeitraum (letzter Monat)
from datetime import datetime
heute = datetime.now()
if heute.month == 1:
    letzter_monat = 12
    jahr = heute.year - 1
else:
    letzter_monat = heute.month - 1
    jahr = heute.year

if letzter_monat in [1, 3, 5, 7, 8, 10, 12]:
    letzter_tag = 31
elif letzter_monat in [4, 6, 9, 11]:
    letzter_tag = 30
else:
    letzter_tag = 28

zeitraum_von = f"{jahr}-{letzter_monat:02d}-01"
zeitraum_bis = f"{jahr}-{letzter_monat:02d}-{letzter_tag}"

print(f'\nVorgeschlagener Zeitraum: {zeitraum_von} bis {zeitraum_bis}')

# Teste auch mit Januar 2026 (wo die Einsätze tatsächlich sind)
print('\n' + '=' * 70)
print('TEST MIT JANUAR 2026 (wo die Einsätze sind)')
print('=' * 70)
zeitraum_von_test = '2026-01-01'
zeitraum_bis_test = '2026-01-31'
print(f'Testzeitraum: {zeitraum_von_test} bis {zeitraum_bis_test}')

# 3. Teste Abrechnung für Gemeinschaft 2
gemeinschaft_id = 2
print(f'\n--- Test für Gemeinschaft {gemeinschaft_id} ---')

cursor.execute("""
    SELECT DISTINCT b.id, b.name, b.vorname
    FROM benutzer b
    JOIN mitglied_gemeinschaft mg ON b.id = mg.mitglied_id
    WHERE mg.gemeinschaft_id = ?
    ORDER BY b.name
""", (gemeinschaft_id,))
mitglieder = cursor.fetchall()
print(f'Anzahl Mitglieder: {len(mitglieder)}')

for mitglied in mitglieder:
    benutzer_id = mitglied[0]
    name = f"{mitglied[1]} {mitglied[2] or ''}"
    
    # Berechne Maschineneinsätze im TESTZEITRAUM (Januar 2026)
    cursor.execute("""
        SELECT COALESCE(SUM(kosten_berechnet), 0)
        FROM maschineneinsaetze
        WHERE benutzer_id = ? 
        AND datum BETWEEN ? AND ?
    """, (benutzer_id, zeitraum_von_test, zeitraum_bis_test))
    betrag_maschinen = cursor.fetchone()[0]
    
    # Berechne Treibstoffkosten im TESTZEITRAUM
    cursor.execute("""
        SELECT COALESCE(SUM(me.treibstoffkosten), 0)
        FROM maschineneinsaetze me
        JOIN maschinen m ON me.maschine_id = m.id
        WHERE me.benutzer_id = ? 
        AND me.datum BETWEEN ? AND ?
        AND m.treibstoff_berechnen = 1
    """, (benutzer_id, zeitraum_von_test, zeitraum_bis_test))
    betrag_treibstoff = cursor.fetchone()[0]
    
    betrag_gesamt = betrag_maschinen + betrag_treibstoff
    
    print(f'\n  Mitglied: {name} (ID: {benutzer_id})')
    print(f'    Maschinen: {betrag_maschinen:.2f} €')
    print(f'    Treibstoff: {betrag_treibstoff:.2f} €')
    print(f'    GESAMT: {betrag_gesamt:.2f} €')
    
    if betrag_gesamt > 0:
        print(f'    ✅ Würde Abrechnung erstellen')
        
        # Zeige Einsätze
        cursor.execute("""
            SELECT m.bezeichnung, me.datum, me.kosten_berechnet, me.treibstoffkosten
            FROM maschineneinsaetze me
            JOIN maschinen m ON me.maschine_id = m.id
            WHERE me.benutzer_id = ?
            AND me.datum BETWEEN ? AND ?
        """, (benutzer_id, zeitraum_von_test, zeitraum_bis_test))
        for einsatz in cursor.fetchall():
            treibstoff = einsatz[3] if einsatz[3] is not None else 0
            print(f'        {einsatz[1]}: {einsatz[0]} - {einsatz[2]:.2f}€ Maschine, {treibstoff:.2f}€ Treibstoff')
    else:
        print(f'    ⏭️  Keine Einsätze im Zeitraum')

# 4. Prüfe Tabellen-Schema
print('\n--- Tabellen-Schema ---')
cursor.execute('PRAGMA table_info(mitglieder_abrechnungen)')
print('\nmitglieder_abrechnungen:')
for row in cursor.fetchall():
    print(f'  {row[1]:30s} {row[2]:15s} {"NOT NULL" if row[3] else ""}')

cursor.execute('PRAGMA table_info(maschinen)')
print('\nmaschinen (relevante Spalten):')
for row in cursor.fetchall():
    if 'treibstoff' in row[1]:
        print(f'  {row[1]:30s} {row[2]:15s} {"NOT NULL" if row[3] else ""} DEFAULT: {row[4]}')

conn.close()
print('\n' + '=' * 70)
