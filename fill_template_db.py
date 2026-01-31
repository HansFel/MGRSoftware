"""
Füllt die Template-Datenbank mit Testdaten
"""

import sqlite3
import random
from datetime import datetime, timedelta
import hashlib
import os

# Pfad zur Template-Datenbank
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'DB_Templates', 'maschinengemeinschaft.db')

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def generate_data():
    print(f"Verbinde mit Datenbank: {DB_PATH}")

    if not os.path.exists(DB_PATH):
        print(f"FEHLER: Datenbank nicht gefunden: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH, timeout=30)
    cursor = conn.cursor()

    # Schema prüfen
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Gefundene Tabellen: {len(tables)}")

    # ==================== GEMEINSCHAFT ====================
    print("\nPrüfe Gemeinschaft...")
    cursor.execute("SELECT COUNT(*) FROM gemeinschaften")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO gemeinschaften (name, beschreibung, aktiv)
            VALUES ('Test-Gemeinschaft', 'Testdaten für Entwicklung', 1)
        """)
        conn.commit()
        print("  Gemeinschaft erstellt")
    else:
        print("  Gemeinschaft existiert bereits")

    cursor.execute("SELECT id FROM gemeinschaften LIMIT 1")
    gemeinschaft_id = cursor.fetchone()[0]

    # ==================== BENUTZER ====================
    print("\nErstelle Benutzer...")
    benutzer = [
        ('Admin', 'System', 'admin', 'admin123', 1, 2),
        ('Huber', 'Johann', 'jhuber', 'test123', 0, 0),
        ('Maier', 'Franz', 'fmaier', 'test123', 0, 0),
        ('Gruber', 'Maria', 'mgruber', 'test123', 0, 0),
        ('Hofer', 'Peter', 'phofer', 'test123', 0, 0),
        ('Steiner', 'Anna', 'asteiner', 'test123', 0, 0),
        ('Berger', 'Thomas', 'tberger', 'test123', 1, 1),
        ('Moser', 'Elisabeth', 'emoser', 'test123', 0, 0),
        ('Pichler', 'Michael', 'mpichler', 'test123', 0, 0),
        ('Egger', 'Sabine', 'segger', 'test123', 0, 0),
    ]

    for name, vorname, username, password, is_admin, admin_level in benutzer:
        cursor.execute("SELECT id FROM benutzer WHERE username = ?", (username,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO benutzer (name, vorname, username, password_hash, is_admin, admin_level, aktiv)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (name, vorname, username, hash_password(password), is_admin, admin_level))
            print(f"  + {username}")
    conn.commit()

    # Benutzer-IDs holen
    cursor.execute("SELECT id FROM benutzer WHERE aktiv = 1")
    benutzer_ids = [row[0] for row in cursor.fetchall()]
    print(f"  {len(benutzer_ids)} Benutzer vorhanden")

    # Mitgliedschaften erstellen
    print("\nErstelle Mitgliedschaften...")
    for bid in benutzer_ids:
        cursor.execute("""
            INSERT OR IGNORE INTO mitglied_gemeinschaft (mitglied_id, gemeinschaft_id, rolle)
            VALUES (?, ?, 'mitglied')
        """, (bid, gemeinschaft_id))
    conn.commit()

    # ==================== MASCHINEN ====================
    print("\nErstelle Maschinen...")
    maschinen = [
        ('Fendt 312 Vario', 'Fendt', '312 Vario', 2018, 'IL-123AB', 1250.5, 'stunden', 45.00),
        ('Steyr Multi 4120', 'Steyr', 'Multi 4120', 2020, 'IL-456CD', 850.0, 'stunden', 40.00),
        ('New Holland T5.120', 'New Holland', 'T5.120', 2019, 'IL-789EF', 1100.0, 'stunden', 42.00),
        ('Pöttinger Novacat 352', 'Pöttinger', 'Novacat 352', 2017, None, 200.0, 'stunden', 25.00),
        ('Krone EasyCut 320', 'Krone', 'EasyCut 320', 2021, None, 50.0, 'stunden', 22.00),
        ('Mengele Garant 540', 'Mengele', 'Garant 540', 2015, 'IL-111GH', 3500.0, 'stunden', 35.00),
        ('Steyr Kompakt 4075', 'Steyr', 'Kompakt 4075', 2022, 'IL-222IJ', 300.0, 'stunden', 38.00),
        ('Lindner Geotrac 84', 'Lindner', 'Geotrac 84', 2016, 'IL-333KL', 2200.0, 'stunden', 36.00),
    ]

    for bez, hersteller, modell, baujahr, kennz, stunden, abart, preis in maschinen:
        cursor.execute("SELECT id FROM maschinen WHERE bezeichnung = ?", (bez,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO maschinen (bezeichnung, hersteller, modell, baujahr, kennzeichen,
                                       stundenzaehler_aktuell, abrechnungsart, preis_pro_einheit,
                                       gemeinschaft_id, aktiv)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (bez, hersteller, modell, baujahr, kennz, stunden, abart, preis, gemeinschaft_id))
            print(f"  + {bez}")
    conn.commit()

    # Maschinen-IDs holen
    cursor.execute("SELECT id, stundenzaehler_aktuell FROM maschinen WHERE aktiv = 1")
    maschinen_data = cursor.fetchall()
    print(f"  {len(maschinen_data)} Maschinen vorhanden")

    # ==================== EINSATZZWECKE ====================
    cursor.execute("SELECT id FROM einsatzzwecke")
    zweck_ids = [row[0] for row in cursor.fetchall()]
    if not zweck_ids:
        print("\nErstelle Einsatzzwecke...")
        zwecke = ['Mähen', 'Pflügen', 'Säen', 'Ernten', 'Transport', 'Schneeräumung', 'Holzarbeiten', 'Sonstiges']
        for z in zwecke:
            cursor.execute("INSERT INTO einsatzzwecke (bezeichnung, aktiv) VALUES (?, 1)", (z,))
        conn.commit()
        cursor.execute("SELECT id FROM einsatzzwecke")
        zweck_ids = [row[0] for row in cursor.fetchall()]
    print(f"  {len(zweck_ids)} Einsatzzwecke vorhanden")

    # ==================== EINSÄTZE ====================
    print("\nErstelle Einsätze...")

    # Aktuelle Stundenzähler als dict
    stundenzaehler = {m[0]: m[1] for m in maschinen_data}
    maschinen_ids = list(stundenzaehler.keys())

    # Einsätze für die letzten 6 Monate
    heute = datetime.now()
    einsatz_count = 0

    for tage_zurueck in range(180, 0, -1):
        # 0-3 Einsätze pro Tag
        anzahl_einsaetze = random.choices([0, 1, 2, 3], weights=[30, 40, 20, 10])[0]

        for _ in range(anzahl_einsaetze):
            datum = (heute - timedelta(days=tage_zurueck)).strftime('%Y-%m-%d')
            benutzer_id = random.choice(benutzer_ids)
            maschine_id = random.choice(maschinen_ids)
            zweck_id = random.choice(zweck_ids)

            anfang = stundenzaehler[maschine_id]
            dauer = random.uniform(0.5, 8.0)
            ende = round(anfang + dauer, 1)
            stundenzaehler[maschine_id] = ende

            treibstoff = round(dauer * random.uniform(5, 15), 1) if random.random() > 0.3 else None
            kosten = round(dauer * random.uniform(30, 50), 2)

            try:
                cursor.execute("""
                    INSERT INTO maschineneinsaetze
                    (datum, benutzer_id, maschine_id, einsatzzweck_id, anfangstand, endstand,
                     betriebsstunden, treibstoffverbrauch, kosten_berechnet)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (datum, benutzer_id, maschine_id, zweck_id, anfang, ende,
                      round(dauer, 1), treibstoff, kosten))
                einsatz_count += 1
            except Exception as e:
                pass  # Duplikate ignorieren

    conn.commit()
    print(f"  {einsatz_count} Einsätze erstellt")

    # Stundenzähler aktualisieren
    for mid, stunden in stundenzaehler.items():
        cursor.execute("UPDATE maschinen SET stundenzaehler_aktuell = ? WHERE id = ?", (stunden, mid))
    conn.commit()

    # ==================== ZUSAMMENFASSUNG ====================
    print("\n" + "=" * 50)
    print("ZUSAMMENFASSUNG")
    print("=" * 50)

    cursor.execute("SELECT COUNT(*) FROM benutzer")
    print(f"Benutzer:     {cursor.fetchone()[0]}")

    cursor.execute("SELECT COUNT(*) FROM maschinen")
    print(f"Maschinen:    {cursor.fetchone()[0]}")

    cursor.execute("SELECT COUNT(*) FROM maschineneinsaetze")
    print(f"Einsätze:     {cursor.fetchone()[0]}")

    cursor.execute("SELECT COUNT(*) FROM einsatzzwecke")
    print(f"Zwecke:       {cursor.fetchone()[0]}")

    print("\nLogin-Daten:")
    print("  admin / admin123 (Administrator)")
    print("  jhuber / test123 (Benutzer)")

    conn.close()
    print("\nFertig!")

if __name__ == '__main__':
    generate_data()
