"""
Erstellt mehrere Übungsdatenbanken mit verschiedenen Szenarien
"""

import sqlite3
import random
import shutil
from datetime import datetime, timedelta
import hashlib
import os

BASE_DIR = os.path.dirname(__file__)
TRAINING_DIR = os.path.join(BASE_DIR, 'data', 'training')
SCHEMA_FILE = os.path.join(BASE_DIR, 'schema.sql')
PRODUCTION_DB = os.path.join(BASE_DIR, 'data', 'maschinengemeinschaft.db')

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def init_database(db_path):
    """Initialisiert eine neue Datenbank mit Schema aus Produktions-DB"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Schema aus Produktions-DB kopieren
    if os.path.exists(PRODUCTION_DB):
        prod_conn = sqlite3.connect(PRODUCTION_DB)
        prod_cursor = prod_conn.cursor()

        # Alle CREATE TABLE Statements holen
        prod_cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL")
        for (sql,) in prod_cursor.fetchall():
            if sql and not sql.startswith('CREATE TABLE sqlite_'):
                try:
                    cursor.execute(sql)
                except sqlite3.OperationalError:
                    pass  # Tabelle existiert bereits

        # Alle CREATE VIEW Statements holen
        prod_cursor.execute("SELECT sql FROM sqlite_master WHERE type='view' AND sql IS NOT NULL")
        for (sql,) in prod_cursor.fetchall():
            if sql:
                try:
                    cursor.execute(sql)
                except sqlite3.OperationalError:
                    pass  # View existiert bereits

        # Alle CREATE INDEX Statements holen
        prod_cursor.execute("SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")
        for (sql,) in prod_cursor.fetchall():
            if sql:
                try:
                    cursor.execute(sql)
                except sqlite3.OperationalError:
                    pass  # Index existiert bereits

        # Alle CREATE TRIGGER Statements holen
        prod_cursor.execute("SELECT sql FROM sqlite_master WHERE type='trigger' AND sql IS NOT NULL")
        for (sql,) in prod_cursor.fetchall():
            if sql:
                try:
                    cursor.execute(sql)
                except sqlite3.OperationalError:
                    pass  # Trigger existiert bereits

        prod_conn.close()

        # Standard-Einsatzzwecke hinzufügen
        einsatzzwecke = [
            ('Mähen', 'Wiesen und Felder mähen'),
            ('Pflügen', 'Feldbearbeitung - Pflügen'),
            ('Säen', 'Aussaat von Getreide oder Gras'),
            ('Ernten', 'Ernte von Getreide, Heu, etc.'),
            ('Transportfahrten', 'Material- und Gütertransport'),
            ('Schneeräumung', 'Winterdienst und Schneeräumung'),
            ('Holzarbeiten', 'Holzrücken und Forstarbeiten'),
            ('Grünlandpflege', 'Weidepflege und Grünlandarbeiten'),
            ('Wegeinstandhaltung', 'Pflege und Instandhaltung von Wegen'),
            ('Sonstiges', 'Andere Einsätze'),
        ]
        for bez, beschr in einsatzzwecke:
            cursor.execute("INSERT OR IGNORE INTO einsatzzwecke (bezeichnung, beschreibung) VALUES (?, ?)", (bez, beschr))

        # Standard-Gemeinschaft
        cursor.execute("INSERT OR IGNORE INTO gemeinschaften (id, name, beschreibung) VALUES (1, 'Hauptgemeinschaft', 'Standard-Gemeinschaft')")

        # Admin-Benutzer
        cursor.execute("""
            INSERT OR IGNORE INTO benutzer (id, name, vorname, username, password_hash, is_admin, admin_level, aktiv)
            VALUES (1, 'Admin', 'System', 'admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 1, 2, 1)
        """)

    else:
        # Fallback: Verwende schema.sql
        with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
            schema = f.read()
        cursor.executescript(schema)

    conn.commit()
    return conn, cursor

def add_base_data(cursor, conn):
    """Fügt Basis-Einsatzzwecke hinzu (falls nicht vorhanden)"""
    # Einsatzzwecke sind bereits im Schema definiert
    conn.commit()

def create_anfaenger_db():
    """
    Anfänger-Datenbank: Wenige Daten, einfache Struktur
    - 1 Gemeinschaft
    - 5 Benutzer
    - 3 Maschinen
    - 20 Einsätze
    """
    db_path = os.path.join(TRAINING_DIR, 'uebung_anfaenger.db')
    print(f"\nErstelle Anfänger-Datenbank: {db_path}")

    if os.path.exists(db_path):
        os.remove(db_path)

    conn, cursor = init_database(db_path)

    # Gemeinschaft existiert bereits (Standard im Schema)

    # Benutzer
    benutzer = [
        ('Mustermann', 'Max', 'mmustermann', 'test123', 0, 0),
        ('Musterfrau', 'Maria', 'mmusterfrau', 'test123', 0, 0),
        ('Testbenutzer', 'Tom', 'ttest', 'test123', 0, 0),
        ('Trainer', 'Tina', 'ttrainer', 'test123', 1, 1),
    ]

    for b in benutzer:
        cursor.execute("""
            INSERT INTO benutzer (name, vorname, username, password_hash, is_admin, admin_level, aktiv, mitglied_seit)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
        """, (b[0], b[1], b[2], hash_password(b[3]), b[4], b[5], '2024-01-01'))

    # Mitglieder der Gemeinschaft zuordnen
    cursor.execute("SELECT id FROM benutzer WHERE username != 'admin'")
    for (uid,) in cursor.fetchall():
        cursor.execute("INSERT OR IGNORE INTO mitglied_gemeinschaft (mitglied_id, gemeinschaft_id) VALUES (?, 1)", (uid,))

    # Maschinen
    maschinen = [
        ('Traktor Fendt 200', 'Fendt', '200 Vario', 2020, 150.0, 35.00, 'stunden'),
        ('Ladewagen', 'Pöttinger', 'Jumbo', 2019, 0, 20.00, 'stunden'),
        ('Mähwerk', 'Kuhn', 'FC 3100', 2021, 0, 15.00, 'hektar'),
    ]

    for m in maschinen:
        cursor.execute("""
            INSERT INTO maschinen (bezeichnung, hersteller, modell, baujahr, stundenzaehler_aktuell,
                                   preis_pro_einheit, abrechnungsart, gemeinschaft_id, aktiv)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, 1)
        """, m)

    conn.commit()

    # Einsätze generieren
    cursor.execute("SELECT id FROM benutzer WHERE username != 'admin'")
    benutzer_ids = [r[0] for r in cursor.fetchall()]

    cursor.execute("SELECT id, stundenzaehler_aktuell, abrechnungsart, preis_pro_einheit FROM maschinen")
    maschinen_data = cursor.fetchall()

    cursor.execute("SELECT id FROM einsatzzwecke")
    zweck_ids = [r[0] for r in cursor.fetchall()]

    for maschine in maschinen_data:
        mid, stand, abart, preis = maschine
        current = stand or 0

        for _ in range(random.randint(5, 10)):
            datum = datetime.now() - timedelta(days=random.randint(1, 180))
            bid = random.choice(benutzer_ids)
            zid = random.choice(zweck_ids)

            anfang = current
            stunden = random.uniform(1.0, 4.0)
            ende = anfang + stunden
            current = ende

            flaeche = random.uniform(2.0, 8.0) if abart == 'hektar' else None
            kosten = (flaeche * preis) if flaeche else (stunden * preis)

            cursor.execute("""
                INSERT INTO maschineneinsaetze
                (datum, benutzer_id, maschine_id, einsatzzweck_id, anfangstand, endstand, flaeche_menge, kosten_berechnet)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (datum.strftime('%Y-%m-%d'), bid, mid, zid, round(anfang, 1), round(ende, 1),
                  round(flaeche, 2) if flaeche else None, round(kosten, 2)))

        cursor.execute("UPDATE maschinen SET stundenzaehler_aktuell = ? WHERE id = ?", (round(current, 1), mid))

    conn.commit()
    conn.close()

    cursor_count = sqlite3.connect(db_path).cursor()
    cursor_count.execute("SELECT COUNT(*) FROM maschineneinsaetze")
    count = cursor_count.fetchone()[0]
    print(f"  -> {count} Einsätze erstellt")

def create_fortgeschritten_db():
    """
    Fortgeschrittenen-Datenbank: Mehr Daten, mehrere Gemeinschaften
    - 2 Gemeinschaften
    - 15 Benutzer
    - 8 Maschinen
    - 200+ Einsätze
    """
    db_path = os.path.join(TRAINING_DIR, 'uebung_fortgeschritten.db')
    print(f"\nErstelle Fortgeschrittenen-Datenbank: {db_path}")

    if os.path.exists(db_path):
        os.remove(db_path)

    conn, cursor = init_database(db_path)

    # Zweite Gemeinschaft
    cursor.execute("""
        INSERT INTO gemeinschaften (name, beschreibung)
        VALUES ('Bergbauern-Kooperative', 'Gemeinschaft der Bergbauern')
    """)

    # Benutzer
    namen = [
        ('Huber', 'Hans'), ('Maier', 'Maria'), ('Gruber', 'Georg'),
        ('Hofer', 'Helga'), ('Steiner', 'Stefan'), ('Berger', 'Brigitte'),
        ('Winkler', 'Wolfgang'), ('Pichler', 'Petra'), ('Reiter', 'Robert'),
        ('Eder', 'Eva'), ('Bauer', 'Bruno'), ('Fischer', 'Franziska'),
    ]

    for i, (name, vorname) in enumerate(namen):
        username = f"{vorname[0].lower()}{name.lower()}"
        is_admin = 1 if i == 0 else 0
        admin_level = 1 if i == 0 else 0
        cursor.execute("""
            INSERT INTO benutzer (name, vorname, username, password_hash, is_admin, admin_level, aktiv, mitglied_seit)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
        """, (name, vorname, username, hash_password('test123'), is_admin, admin_level,
              (datetime.now() - timedelta(days=random.randint(100, 1000))).strftime('%Y-%m-%d')))

    cursor.execute("SELECT id FROM benutzer WHERE username != 'admin'")
    benutzer_ids = [r[0] for r in cursor.fetchall()]

    # Mitglieder auf Gemeinschaften verteilen
    for i, bid in enumerate(benutzer_ids):
        gid = 1 if i < 8 else 2
        cursor.execute("INSERT INTO mitglied_gemeinschaft (mitglied_id, gemeinschaft_id) VALUES (?, ?)", (bid, gid))
        if random.random() < 0.3:  # 30% sind in beiden
            cursor.execute("INSERT OR IGNORE INTO mitglied_gemeinschaft (mitglied_id, gemeinschaft_id) VALUES (?, ?)",
                          (bid, 2 if gid == 1 else 1))

    # Maschinen
    maschinen = [
        ('Traktor Fendt 724', 'Fendt', '724 Vario', 2019, 800.0, 45.00, 'stunden', 1),
        ('Traktor John Deere', 'John Deere', '6130R', 2020, 450.0, 40.00, 'stunden', 1),
        ('Mähdrescher Claas', 'Claas', 'Lexion 770', 2018, 300.0, 150.00, 'stunden', 1),
        ('Ladewagen Pöttinger', 'Pöttinger', 'Jumbo 6010', 2021, 0, 25.00, 'stunden', 1),
        ('Kreiselmäher', 'Kuhn', 'FC 3160', 2020, 0, 18.00, 'hektar', 2),
        ('Traktor Steyr', 'Steyr', '4130 Profi', 2022, 200.0, 38.00, 'stunden', 2),
        ('Rundballenpresse', 'Krone', 'Comprima', 2020, 0, 8.00, 'stueck', 2),
        ('Güllefass', 'Zunhammer', 'SKE 15000', 2017, 0, 12.00, 'stunden', 2),
    ]

    for m in maschinen:
        cursor.execute("""
            INSERT INTO maschinen (bezeichnung, hersteller, modell, baujahr, stundenzaehler_aktuell,
                                   preis_pro_einheit, abrechnungsart, gemeinschaft_id, aktiv)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, m)

    conn.commit()

    # Einsätze generieren
    cursor.execute("SELECT id, stundenzaehler_aktuell, abrechnungsart, preis_pro_einheit, gemeinschaft_id FROM maschinen")
    maschinen_data = cursor.fetchall()

    cursor.execute("SELECT id FROM einsatzzwecke")
    zweck_ids = [r[0] for r in cursor.fetchall()]

    for maschine in maschinen_data:
        mid, stand, abart, preis, gid = maschine
        current = stand or 0

        # Benutzer dieser Gemeinschaft
        cursor.execute("SELECT mitglied_id FROM mitglied_gemeinschaft WHERE gemeinschaft_id = ?", (gid,))
        gem_benutzer = [r[0] for r in cursor.fetchall()]
        if not gem_benutzer:
            gem_benutzer = benutzer_ids[:5]

        for _ in range(random.randint(20, 40)):
            datum = datetime.now() - timedelta(days=random.randint(1, 365))
            bid = random.choice(gem_benutzer)
            zid = random.choice(zweck_ids)

            anfang = current
            stunden = random.uniform(0.5, 6.0)
            ende = anfang + stunden
            current = ende

            flaeche = None
            if abart == 'hektar':
                flaeche = random.uniform(2.0, 15.0)
            elif abart == 'stueck':
                flaeche = random.randint(10, 60)

            kosten = (flaeche * preis) if flaeche else (stunden * preis)

            treibstoff = random.uniform(8.0, 25.0) if random.random() < 0.2 else None
            treibstoff_kosten = treibstoff * 1.55 if treibstoff else None

            cursor.execute("""
                INSERT INTO maschineneinsaetze
                (datum, benutzer_id, maschine_id, einsatzzweck_id, anfangstand, endstand,
                 flaeche_menge, kosten_berechnet, treibstoffverbrauch, treibstoffkosten)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (datum.strftime('%Y-%m-%d'), bid, mid, zid, round(anfang, 1), round(ende, 1),
                  round(flaeche, 2) if flaeche else None, round(kosten, 2),
                  round(treibstoff, 1) if treibstoff else None,
                  round(treibstoff_kosten, 2) if treibstoff_kosten else None))

        cursor.execute("UPDATE maschinen SET stundenzaehler_aktuell = ? WHERE id = ?", (round(current, 1), mid))

    conn.commit()
    conn.close()

    cursor_count = sqlite3.connect(db_path).cursor()
    cursor_count.execute("SELECT COUNT(*) FROM maschineneinsaetze")
    count = cursor_count.fetchone()[0]
    print(f"  -> {count} Einsätze erstellt")

def create_admin_training_db():
    """
    Admin-Training: Komplexe Daten für Administrator-Schulung
    - 3 Gemeinschaften
    - 25 Benutzer mit verschiedenen Rechten
    - 15 Maschinen
    - 500+ Einsätze
    - Verschiedene Szenarien (inaktive User, Wartungen, etc.)
    """
    db_path = os.path.join(TRAINING_DIR, 'uebung_admin.db')
    print(f"\nErstelle Admin-Training-Datenbank: {db_path}")

    if os.path.exists(db_path):
        os.remove(db_path)

    conn, cursor = init_database(db_path)

    # Gemeinschaften
    cursor.execute("INSERT INTO gemeinschaften (name, beschreibung) VALUES ('Talgemeinschaft', 'Bauern im Tal')")
    cursor.execute("INSERT INTO gemeinschaften (name, beschreibung) VALUES ('Alm-Kooperative', 'Almwirtschaft')")

    # Viele Benutzer mit verschiedenen Rechten
    namen = [
        ('Huber', 'Johann', 0, 0, 1), ('Maier', 'Franz', 0, 0, 1),
        ('Gruber', 'Maria', 0, 0, 1), ('Hofer', 'Peter', 0, 0, 1),
        ('Steiner', 'Anna', 0, 0, 1), ('Berger', 'Thomas', 1, 1, 1),  # Gemeinschafts-Admin
        ('Winkler', 'Elisabeth', 0, 0, 1), ('Pichler', 'Josef', 0, 0, 1),
        ('Reiter', 'Katharina', 0, 0, 1), ('Eder', 'Markus', 0, 0, 1),
        ('Bauer', 'Sabine', 0, 0, 1), ('Fischer', 'Hans', 0, 0, 1),
        ('Wagner', 'Christine', 0, 0, 0),  # Inaktiv
        ('Moser', 'Friedrich', 0, 0, 1), ('Schwarz', 'Gabriele', 0, 0, 1),
        ('Weber', 'Martin', 1, 1, 1),  # Gemeinschafts-Admin
        ('Schneider', 'Laura', 0, 0, 1), ('Fuchs', 'Andreas', 0, 0, 1),
        ('Braun', 'Sophia', 0, 0, 1), ('Zimmermann', 'David', 0, 0, 0),  # Inaktiv
        ('Hoffmann', 'Emma', 0, 0, 1), ('Schmidt', 'Lukas', 0, 0, 1),
    ]

    for n in namen:
        username = f"{n[1][0].lower()}{n[0].lower()}"
        cursor.execute("""
            INSERT INTO benutzer (name, vorname, username, password_hash, is_admin, admin_level, aktiv, mitglied_seit)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (n[0], n[1], username, hash_password('test123'), n[2], n[3], n[4],
              (datetime.now() - timedelta(days=random.randint(100, 1500))).strftime('%Y-%m-%d')))

    cursor.execute("SELECT id FROM benutzer WHERE aktiv = 1 AND username != 'admin'")
    aktive_benutzer = [r[0] for r in cursor.fetchall()]

    # Verteile auf Gemeinschaften
    for i, bid in enumerate(aktive_benutzer):
        gid = (i % 3) + 1
        cursor.execute("INSERT INTO mitglied_gemeinschaft (mitglied_id, gemeinschaft_id) VALUES (?, ?)", (bid, gid))

    # Maschinen für alle Gemeinschaften
    maschinen = [
        ('Fendt 724 Vario', 'Fendt', '724', 2019, 1500.0, 48.00, 'stunden', 1, 180000),
        ('John Deere 6130R', 'John Deere', '6130R', 2020, 850.0, 42.00, 'stunden', 1, 140000),
        ('Claas Lexion 770', 'Claas', 'Lexion', 2018, 600.0, 180.00, 'stunden', 1, 420000),
        ('Pöttinger Jumbo', 'Pöttinger', 'Jumbo 6010', 2021, 0, 25.00, 'stunden', 1, 75000),
        ('Kuhn Mäher', 'Kuhn', 'FC 3160', 2020, 0, 18.00, 'hektar', 1, 28000),
        ('Steyr 4130', 'Steyr', '4130 Profi', 2022, 400.0, 40.00, 'stunden', 2, 125000),
        ('Krone Presse', 'Krone', 'Comprima F125', 2020, 0, 8.50, 'stueck', 2, 48000),
        ('Zunhammer Gülle', 'Zunhammer', 'SKE 18500', 2017, 0, 12.00, 'stunden', 2, 65000),
        ('MF 5711 S', 'Massey Ferguson', '5711', 2021, 500.0, 38.00, 'stunden', 3, 115000),
        ('Amazone Streuer', 'Amazone', 'ZA-TS 3200', 2019, 0, 6.00, 'hektar', 3, 22000),
        ('Lemken Pflug', 'Lemken', 'Juwel 8', 2018, 0, 28.00, 'hektar', 3, 35000),
        ('Horsch Sämaschine', 'Horsch', 'Pronto 4 DC', 2020, 0, 22.00, 'hektar', 3, 85000),
        ('Stoll Frontlader', 'Stoll', 'FZ 50.1', 2021, 0, 15.00, 'stunden', 3, 18000),
        ('Hauer Schneepflug', 'Hauer', 'HSP 2800', 2018, 0, 35.00, 'stunden', 1, 12000),
        ('Reform Muli', 'Reform', 'Muli T10X', 2020, 350.0, 55.00, 'stunden', 2, 145000),
    ]

    for m in maschinen:
        cursor.execute("""
            INSERT INTO maschinen (bezeichnung, hersteller, modell, baujahr, stundenzaehler_aktuell,
                                   preis_pro_einheit, abrechnungsart, gemeinschaft_id, aktiv, anschaffungspreis)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
        """, m)

    conn.commit()

    # Viele Einsätze generieren
    cursor.execute("SELECT id, stundenzaehler_aktuell, abrechnungsart, preis_pro_einheit, gemeinschaft_id FROM maschinen")
    maschinen_data = cursor.fetchall()

    cursor.execute("SELECT id FROM einsatzzwecke")
    zweck_ids = [r[0] for r in cursor.fetchall()]

    total_einsaetze = 0

    for maschine in maschinen_data:
        mid, stand, abart, preis, gid = maschine
        current = stand or 0

        cursor.execute("SELECT mitglied_id FROM mitglied_gemeinschaft WHERE gemeinschaft_id = ?", (gid,))
        gem_benutzer = [r[0] for r in cursor.fetchall()]
        if not gem_benutzer:
            gem_benutzer = aktive_benutzer[:5]

        for _ in range(random.randint(30, 60)):
            datum = datetime.now() - timedelta(days=random.randint(1, 730))
            bid = random.choice(gem_benutzer)
            zid = random.choice(zweck_ids)

            anfang = current
            stunden = random.uniform(0.5, 8.0)
            ende = anfang + stunden
            current = ende

            flaeche = None
            if abart == 'hektar':
                flaeche = random.uniform(1.0, 20.0)
            elif abart == 'stueck':
                flaeche = random.randint(5, 80)

            kosten = (flaeche * preis) if flaeche else (stunden * preis)

            treibstoff = random.uniform(5.0, 40.0) if random.random() < 0.25 else None
            treibstoff_kosten = treibstoff * random.uniform(1.40, 1.70) if treibstoff else None

            anmerkungen = None
            if random.random() < 0.1:
                anmerkungen = random.choice([
                    'Gutes Wetter', 'Regen', 'Schwieriges Gelände', 'Wartung fällig',
                    'Ölstand geprüft', 'Steiles Gelände', 'Nasser Boden'
                ])

            cursor.execute("""
                INSERT INTO maschineneinsaetze
                (datum, benutzer_id, maschine_id, einsatzzweck_id, anfangstand, endstand,
                 flaeche_menge, kosten_berechnet, treibstoffverbrauch, treibstoffkosten, anmerkungen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (datum.strftime('%Y-%m-%d'), bid, mid, zid, round(anfang, 1), round(ende, 1),
                  round(flaeche, 2) if flaeche else None, round(kosten, 2),
                  round(treibstoff, 1) if treibstoff else None,
                  round(treibstoff_kosten, 2) if treibstoff_kosten else None, anmerkungen))
            total_einsaetze += 1

        cursor.execute("UPDATE maschinen SET stundenzaehler_aktuell = ? WHERE id = ?", (round(current, 1), mid))

    conn.commit()
    conn.close()
    print(f"  -> {total_einsaetze} Einsätze erstellt")

def create_leer_db():
    """Leere Datenbank zum freien Üben"""
    db_path = os.path.join(TRAINING_DIR, 'uebung_leer.db')
    print(f"\nErstelle leere Übungsdatenbank: {db_path}")

    if os.path.exists(db_path):
        os.remove(db_path)

    conn, cursor = init_database(db_path)
    conn.close()
    print("  -> Leere Datenbank erstellt (nur Schema + Admin-User)")

def main():
    # Stelle sicher, dass Training-Verzeichnis existiert
    os.makedirs(TRAINING_DIR, exist_ok=True)

    print("="*60)
    print("ERSTELLE ÜBUNGSDATENBANKEN")
    print("="*60)

    create_leer_db()
    create_anfaenger_db()
    create_fortgeschritten_db()
    create_admin_training_db()

    print("\n" + "="*60)
    print("FERTIG!")
    print("="*60)
    print(f"\nÜbungsdatenbanken erstellt in: {TRAINING_DIR}")
    print("\nVerfügbare Datenbanken:")
    for f in os.listdir(TRAINING_DIR):
        if f.endswith('.db'):
            size = os.path.getsize(os.path.join(TRAINING_DIR, f)) / 1024
            print(f"  - {f} ({size:.1f} KB)")

    print("\nLogin für alle Datenbanken:")
    print("  Admin:     admin / admin123")
    print("  Benutzer:  [vorname][nachname] / test123")
    print("             z.B. mmustermann / test123")

if __name__ == "__main__":
    main()
