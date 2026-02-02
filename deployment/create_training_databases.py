#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Erstellt die SQLite-Übungsdatenbanken für Trainings- und Testzwecke
"""

import os
import sqlite3
import hashlib
from datetime import datetime, timedelta
import random

# Pfade
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRAINING_DIR = os.path.join(os.path.dirname(BASE_DIR), 'data', 'training')
SCHEMA_FILE = os.path.join(BASE_DIR, 'schema.sql')

# Sicherstellen dass Verzeichnis existiert
os.makedirs(TRAINING_DIR, exist_ok=True)


def hash_password(password):
    """Passwort hashen mit SHA-256"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def create_database(db_path):
    """Erstellt eine leere Datenbank mit Schema"""
    # Alte löschen falls vorhanden
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)

    # Schema laden und ausführen
    if os.path.exists(SCHEMA_FILE):
        with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
            schema = f.read()
        conn.executescript(schema)
    else:
        # Minimales Schema falls keine Datei vorhanden
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS benutzer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                vorname TEXT,
                username TEXT UNIQUE,
                password_hash TEXT,
                is_admin BOOLEAN DEFAULT 0,
                admin_level INTEGER DEFAULT 0,
                aktiv BOOLEAN DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS gemeinschaften (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                beschreibung TEXT,
                aktiv BOOLEAN DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS maschinen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bezeichnung TEXT NOT NULL,
                gemeinschaft_id INTEGER DEFAULT 1,
                aktiv BOOLEAN DEFAULT 1,
                stundenzaehler_aktuell REAL DEFAULT 0,
                abrechnungsart TEXT DEFAULT 'stunden',
                preis_pro_einheit REAL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS einsatzzwecke (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bezeichnung TEXT NOT NULL,
                aktiv BOOLEAN DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS maschineneinsaetze (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                datum DATE NOT NULL,
                benutzer_id INTEGER,
                maschine_id INTEGER,
                einsatzzweck_id INTEGER,
                anfangstand REAL,
                endstand REAL,
                betriebsstunden REAL,
                treibstoffverbrauch REAL,
                treibstoffkosten REAL,
                kosten_berechnet REAL
            );

            CREATE TABLE IF NOT EXISTS mitglied_gemeinschaft (
                mitglied_id INTEGER,
                gemeinschaft_id INTEGER,
                PRIMARY KEY (mitglied_id, gemeinschaft_id)
            );

            INSERT OR IGNORE INTO gemeinschaften (id, name) VALUES (1, 'Hauptgemeinschaft');
            INSERT OR IGNORE INTO einsatzzwecke (bezeichnung) VALUES ('Mähen'), ('Pflügen'), ('Transportfahrten');
        """)

    conn.commit()
    return conn


def add_admin_user(conn, name="Admin", username="admin", password="admin123"):
    """Fügt Admin-Benutzer hinzu"""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO benutzer (id, name, vorname, username, password_hash, is_admin, admin_level, aktiv)
        VALUES (1, ?, 'System', ?, ?, 1, 2, 1)
    """, (name, username, hash_password(password)))
    conn.commit()


def add_users(conn, count=5):
    """Fügt Testbenutzer hinzu"""
    cursor = conn.cursor()

    vornamen = ['Hans', 'Peter', 'Maria', 'Anna', 'Josef', 'Franz', 'Elisabeth', 'Johann', 'Theresia', 'Karl',
                'Martin', 'Stefan', 'Thomas', 'Michael', 'Andreas', 'Christian', 'Markus', 'Wolfgang', 'Gerhard', 'Herbert']
    nachnamen = ['Müller', 'Huber', 'Mair', 'Berger', 'Hofer', 'Gruber', 'Wagner', 'Moser', 'Bauer', 'Schmid',
                 'Winkler', 'Weber', 'Steiner', 'Maier', 'Eder', 'Schwarz', 'Fischer', 'Reiter', 'Brunner', 'Auer']

    for i in range(count):
        vorname = random.choice(vornamen)
        nachname = random.choice(nachnamen)
        username = f"{vorname.lower()}.{nachname.lower()}{i+1}"

        cursor.execute("""
            INSERT INTO benutzer (name, vorname, username, password_hash, is_admin, admin_level, aktiv)
            VALUES (?, ?, ?, ?, 0, 0, 1)
        """, (nachname, vorname, username, hash_password('test123')))

        # Zu Gemeinschaft hinzufügen
        user_id = cursor.lastrowid
        cursor.execute("""
            INSERT OR IGNORE INTO mitglied_gemeinschaft (mitglied_id, gemeinschaft_id)
            VALUES (?, 1)
        """, (user_id,))

    conn.commit()


def add_machines(conn, count=3):
    """Fügt Testmaschinen hinzu"""
    cursor = conn.cursor()

    maschinen = [
        ('Traktor Fendt 313', 'Fendt', '313 Vario', 35, 'stunden'),
        ('Traktor Steyr 4115', 'Steyr', '4115 Multi', 28, 'stunden'),
        ('Mähwerk Pöttinger', 'Pöttinger', 'Novacat 352', 15, 'hektar'),
        ('Ladewagen Strautmann', 'Strautmann', 'Super Vitesse', 12, 'stunden'),
        ('Güllefass Vakuumat', 'Vakuumat', '12000L', 8, 'stunden'),
        ('Kreisler Kuhn', 'Kuhn', 'GF 8501', 10, 'hektar'),
        ('Pflug Lemken', 'Lemken', 'Opal 110', 25, 'hektar'),
        ('Schneepflug', 'Hauer', 'HS 2800', 18, 'stunden'),
    ]

    for i in range(min(count, len(maschinen))):
        m = maschinen[i]
        cursor.execute("""
            INSERT INTO maschinen (bezeichnung, hersteller, modell, preis_pro_einheit, abrechnungsart,
                                   gemeinschaft_id, aktiv, stundenzaehler_aktuell)
            VALUES (?, ?, ?, ?, ?, 1, 1, ?)
        """, (m[0], m[1], m[2], m[3], m[4], random.randint(100, 2000)))

    conn.commit()


def add_einsaetze(conn, count=25):
    """Fügt Testeinsätze hinzu"""
    cursor = conn.cursor()

    # Benutzer und Maschinen abrufen
    cursor.execute("SELECT id FROM benutzer WHERE aktiv = 1 AND id > 1")
    benutzer_ids = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT id, stundenzaehler_aktuell, abrechnungsart, preis_pro_einheit FROM maschinen WHERE aktiv = 1")
    maschinen = cursor.fetchall()

    cursor.execute("SELECT id FROM einsatzzwecke WHERE aktiv = 1")
    zweck_ids = [row[0] for row in cursor.fetchall()]

    if not benutzer_ids or not maschinen or not zweck_ids:
        return

    # Stundenzähler pro Maschine tracken
    stundenzaehler = {m[0]: m[1] or 0 for m in maschinen}

    for i in range(count):
        benutzer_id = random.choice(benutzer_ids)
        maschine = random.choice(maschinen)
        maschine_id = maschine[0]
        abrechnungsart = maschine[2]
        preis = maschine[3] or 0

        zweck_id = random.choice(zweck_ids)

        # Datum in den letzten 180 Tagen
        datum = datetime.now() - timedelta(days=random.randint(1, 180))

        anfangstand = stundenzaehler[maschine_id]
        betriebsstunden = round(random.uniform(0.5, 8), 1)
        endstand = anfangstand + betriebsstunden
        stundenzaehler[maschine_id] = endstand

        treibstoffverbrauch = round(betriebsstunden * random.uniform(5, 15), 1)
        treibstoffkosten = round(treibstoffverbrauch * 1.5, 2)

        if abrechnungsart == 'stunden':
            kosten = betriebsstunden * preis
        else:
            flaeche = round(betriebsstunden * random.uniform(0.5, 2), 2)
            kosten = flaeche * preis

        cursor.execute("""
            INSERT INTO maschineneinsaetze (datum, benutzer_id, maschine_id, einsatzzweck_id,
                                            anfangstand, endstand, betriebsstunden,
                                            treibstoffverbrauch, treibstoffkosten, kosten_berechnet)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (datum.strftime('%Y-%m-%d'), benutzer_id, maschine_id, zweck_id,
              anfangstand, endstand, betriebsstunden, treibstoffverbrauch, treibstoffkosten, kosten))

    # Stundenzähler aktualisieren
    for maschine_id, stand in stundenzaehler.items():
        cursor.execute("UPDATE maschinen SET stundenzaehler_aktuell = ? WHERE id = ?", (stand, maschine_id))

    conn.commit()


def create_empty_db():
    """Erstellt leere Übungsdatenbank"""
    print("Erstelle: uebung_leer.db")
    db_path = os.path.join(TRAINING_DIR, 'uebung_leer.db')
    conn = create_database(db_path)
    add_admin_user(conn)
    conn.close()
    print(f"  -> {db_path}")


def create_anfaenger_db():
    """Erstellt Anfänger-Übungsdatenbank"""
    print("Erstelle: uebung_anfaenger.db")
    db_path = os.path.join(TRAINING_DIR, 'uebung_anfaenger.db')
    conn = create_database(db_path)
    add_admin_user(conn)
    add_users(conn, 5)
    add_machines(conn, 3)
    add_einsaetze(conn, 25)
    conn.close()
    print(f"  -> {db_path}")


def create_fortgeschritten_db():
    """Erstellt Fortgeschrittenen-Übungsdatenbank"""
    print("Erstelle: uebung_fortgeschritten.db")
    db_path = os.path.join(TRAINING_DIR, 'uebung_fortgeschritten.db')
    conn = create_database(db_path)
    add_admin_user(conn)
    add_users(conn, 15)
    add_machines(conn, 8)
    add_einsaetze(conn, 250)
    conn.close()
    print(f"  -> {db_path}")


def create_admin_db():
    """Erstellt Admin-Übungsdatenbank"""
    print("Erstelle: uebung_admin.db")
    db_path = os.path.join(TRAINING_DIR, 'uebung_admin.db')
    conn = create_database(db_path)
    add_admin_user(conn)
    add_users(conn, 25)
    add_machines(conn, 8)
    add_einsaetze(conn, 700)
    conn.close()
    print(f"  -> {db_path}")


if __name__ == '__main__':
    print("=" * 50)
    print("Erstelle Übungsdatenbanken...")
    print("=" * 50)

    create_empty_db()
    create_anfaenger_db()
    create_fortgeschritten_db()
    create_admin_db()

    print("=" * 50)
    print("Fertig!")
    print(f"Übungsdatenbanken erstellt in: {TRAINING_DIR}")
    print("Login: admin / admin123")
    print("Testbenutzer: [vorname].[nachname]X / test123")
    print("=" * 50)
