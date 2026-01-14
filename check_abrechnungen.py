#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prüfe bestehende Abrechnungen auf Fehler"""

import sqlite3

conn = sqlite3.connect('maschinengemeinschaft.db')
cursor = conn.cursor()

print("=" * 70)
print("ANALYSE: Bestehende Abrechnungen")
print("=" * 70)

# Hole alle Abrechnungen
cursor.execute("""
    SELECT 
        ma.id,
        ma.gemeinschaft_id,
        g.name as gemeinschaft_name,
        ma.benutzer_id,
        b.name || ' ' || COALESCE(b.vorname, '') as mitglied_name,
        ma.zeitraum_von,
        ma.zeitraum_bis,
        ma.betrag_maschinen,
        ma.betrag_treibstoff,
        ma.betrag_gesamt
    FROM mitglieder_abrechnungen ma
    JOIN gemeinschaften g ON ma.gemeinschaft_id = g.id
    JOIN benutzer b ON ma.benutzer_id = b.id
    ORDER BY ma.gemeinschaft_id, ma.benutzer_id
""")

print("\nAlle Abrechnungen:")
print("-" * 70)

for row in cursor.fetchall():
    abr_id = row[0]
    gem_id = row[1]
    gem_name = row[2]
    benutzer_id = row[3]
    mitglied_name = row[4]
    zeitraum_von = row[5]
    zeitraum_bis = row[6]
    betrag_maschinen = row[7]
    betrag_treibstoff = row[8]
    betrag_gesamt = row[9]
    
    print(f"\nAbrechnung #{abr_id}")
    print(f"  Gemeinschaft: {gem_name} (ID: {gem_id})")
    print(f"  Mitglied: {mitglied_name} (ID: {benutzer_id})")
    print(f"  Zeitraum: {zeitraum_von} bis {zeitraum_bis}")
    print(f"  Maschinen: {betrag_maschinen:.2f} €")
    print(f"  Treibstoff: {betrag_treibstoff:.2f} €")
    print(f"  GESAMT: {betrag_gesamt:.2f} €")
    
    # Prüfe: Gibt es tatsächlich Einsätze dieser Gemeinschaft?
    cursor.execute("""
        SELECT COUNT(*), COALESCE(SUM(me.kosten_berechnet), 0)
        FROM maschineneinsaetze me
        JOIN maschinen m ON me.maschine_id = m.id
        WHERE me.benutzer_id = ?
        AND me.datum BETWEEN ? AND ?
        AND m.gemeinschaft_id = ?
    """, (benutzer_id, zeitraum_von, zeitraum_bis, gem_id))
    
    einsaetze_count, einsaetze_kosten = cursor.fetchone()
    
    cursor.execute("""
        SELECT COALESCE(SUM(me.treibstoffkosten), 0)
        FROM maschineneinsaetze me
        JOIN maschinen m ON me.maschine_id = m.id
        WHERE me.benutzer_id = ?
        AND me.datum BETWEEN ? AND ?
        AND m.gemeinschaft_id = ?
        AND m.treibstoff_berechnen = 1
    """, (benutzer_id, zeitraum_von, zeitraum_bis, gem_id))
    
    treibstoff_kosten = cursor.fetchone()[0]
    
    soll_gesamt = einsaetze_kosten + treibstoff_kosten
    
    print(f"  SOLL (neu berechnet):")
    print(f"    Einsätze: {einsaetze_count}")
    print(f"    Maschinen: {einsaetze_kosten:.2f} €")
    print(f"    Treibstoff: {treibstoff_kosten:.2f} €")
    print(f"    GESAMT: {soll_gesamt:.2f} €")
    
    if abs(betrag_gesamt - soll_gesamt) > 0.01:
        print(f"  ❌ FEHLER: Differenz von {betrag_gesamt - soll_gesamt:.2f} €")
    else:
        print(f"  ✅ OK")

# Statistiken pro Gemeinschaft
print("\n" + "=" * 70)
print("STATISTIK PRO GEMEINSCHAFT")
print("=" * 70)

cursor.execute("SELECT id, name FROM gemeinschaften ORDER BY name")
for gem_row in cursor.fetchall():
    gem_id = gem_row[0]
    gem_name = gem_row[1]
    
    cursor.execute("""
        SELECT COUNT(*), COALESCE(SUM(betrag_gesamt), 0)
        FROM mitglieder_abrechnungen
        WHERE gemeinschaft_id = ? AND status = 'offen'
    """, (gem_id,))
    
    anzahl, summe = cursor.fetchone()
    
    print(f"\n{gem_name} (ID: {gem_id})")
    print(f"  Offene Abrechnungen: {anzahl}")
    print(f"  Summe offen: {summe:.2f} €")

conn.close()
print("\n" + "=" * 70)
