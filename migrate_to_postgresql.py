#!/usr/bin/env python3
"""
Migrations-Script: SQLite -> PostgreSQL
Überträgt alle Daten von der SQLite-Datenbank nach PostgreSQL

Voraussetzungen:
1. PostgreSQL installiert und läuft
2. Datenbank 'maschinengemeinschaft' erstellt
3. Benutzer mit Schreibrechten vorhanden
4. psycopg2 installiert: pip install psycopg2-binary

Verwendung:
    python migrate_to_postgresql.py

Umgebungsvariablen:
    SQLITE_PATH - Pfad zur SQLite-Datenbank (Standard: ./data/maschinengemeinschaft.db)
    PG_HOST     - PostgreSQL Host (Standard: localhost)
    PG_PORT     - PostgreSQL Port (Standard: 5432)
    PG_DATABASE - PostgreSQL Datenbankname (Standard: maschinengemeinschaft)
    PG_USER     - PostgreSQL Benutzer (Standard: mgr_user)
    PG_PASSWORD - PostgreSQL Passwort
"""

import os
import sys
import sqlite3
from datetime import datetime

# Konfiguration
SQLITE_PATH = os.environ.get('SQLITE_PATH', './data/maschinengemeinschaft.db')
PG_HOST = os.environ.get('PG_HOST', 'localhost')
PG_PORT = os.environ.get('PG_PORT', '5432')
PG_DATABASE = os.environ.get('PG_DATABASE', 'maschinengemeinschaft')
PG_USER = os.environ.get('PG_USER', 'mgr_user')
PG_PASSWORD = os.environ.get('PG_PASSWORD', '')

# Tabellen in der richtigen Reihenfolge (wegen Foreign Keys)
TABLES_ORDER = [
    'gemeinschaften',
    'benutzer',
    'einsatzzwecke',
    'maschinen',
    'mitglied_gemeinschaft',
    'gemeinschafts_admin',
    'maschineneinsaetze',
    'maschineneinsaetze_storniert',
    'backup_bestaetigung',
    'backup_tracking',
    'gemeinschafts_nachrichten',
    'nachricht_gelesen',
    'maschinen_reservierungen',
    'maschinen_aufwendungen',
    'bank_transaktionen',
    'mitglieder_konten',
    'buchungen',
    'mitglieder_abrechnungen',
    'zahlungs_zuordnungen',
    'zahlungsreferenzen',
    'csv_import_konfiguration',
    'gemeinschafts_kosten',
    'jahresabschluesse',
]


def check_prerequisites():
    """Prüft Voraussetzungen"""
    print("Prüfe Voraussetzungen...")

    # SQLite-Datenbank vorhanden?
    if not os.path.exists(SQLITE_PATH):
        print(f"FEHLER: SQLite-Datenbank nicht gefunden: {SQLITE_PATH}")
        return False

    # psycopg2 installiert?
    try:
        import psycopg2
    except ImportError:
        print("FEHLER: psycopg2 nicht installiert!")
        print("Installieren Sie es mit: pip install psycopg2-binary")
        return False

    # PostgreSQL-Verbindung testen
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=PG_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD
        )
        conn.close()
        print(f"PostgreSQL-Verbindung OK: {PG_HOST}:{PG_PORT}/{PG_DATABASE}")
    except Exception as e:
        print(f"FEHLER: PostgreSQL-Verbindung fehlgeschlagen: {e}")
        return False

    print("Alle Voraussetzungen erfüllt.\n")
    return True


def get_table_columns(sqlite_cursor, table_name):
    """Holt Spaltennamen einer Tabelle"""
    sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in sqlite_cursor.fetchall()]


def migrate_table(sqlite_conn, pg_conn, table_name):
    """Migriert eine einzelne Tabelle"""
    import psycopg2

    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()

    # Prüfe ob Tabelle in SQLite existiert
    sqlite_cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    if not sqlite_cursor.fetchone():
        print(f"  Übersprungen: {table_name} (nicht in SQLite vorhanden)")
        return 0

    # Hole Spalten
    columns = get_table_columns(sqlite_cursor, table_name)

    # Filtere generierte Spalten (wie 'betriebsstunden')
    if table_name == 'maschineneinsaetze':
        columns = [c for c in columns if c != 'betriebsstunden']

    if not columns:
        print(f"  Übersprungen: {table_name} (keine Spalten)")
        return 0

    # Lösche existierende Daten in PostgreSQL
    pg_cursor.execute(f"DELETE FROM {table_name}")

    # Hole Daten aus SQLite
    columns_str = ', '.join(columns)
    sqlite_cursor.execute(f"SELECT {columns_str} FROM {table_name}")
    rows = sqlite_cursor.fetchall()

    if not rows:
        print(f"  Übersprungen: {table_name} (keine Daten)")
        return 0

    # Füge in PostgreSQL ein
    placeholders = ', '.join(['%s'] * len(columns))
    insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"

    count = 0
    for row in rows:
        # Konvertiere Boolean-Werte
        converted_row = []
        for val in row:
            if val == 1 and isinstance(val, int):
                # Könnte Boolean sein - prüfen wir später genauer
                converted_row.append(val)
            elif val == 0 and isinstance(val, int):
                converted_row.append(val)
            else:
                converted_row.append(val)

        try:
            pg_cursor.execute(insert_sql, converted_row)
            count += 1
        except Exception as e:
            print(f"    Fehler bei Zeile: {e}")
            print(f"    Daten: {converted_row[:3]}...")

    # Aktualisiere Sequenz für SERIAL-Spalten
    if 'id' in columns:
        pg_cursor.execute(f"""
            SELECT setval(pg_get_serial_sequence('{table_name}', 'id'),
                          COALESCE((SELECT MAX(id) FROM {table_name}), 1))
        """)

    pg_conn.commit()
    print(f"  Migriert: {table_name} ({count} Zeilen)")
    return count


def run_migration():
    """Führt die Migration durch"""
    import psycopg2

    print("=" * 60)
    print("SQLite -> PostgreSQL Migration")
    print("=" * 60)
    print(f"Quelle:  {SQLITE_PATH}")
    print(f"Ziel:    postgresql://{PG_USER}@{PG_HOST}:{PG_PORT}/{PG_DATABASE}")
    print("=" * 60 + "\n")

    if not check_prerequisites():
        return False

    # Verbindungen öffnen
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    pg_conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        database=PG_DATABASE,
        user=PG_USER,
        password=PG_PASSWORD
    )

    try:
        # Schema in PostgreSQL erstellen
        print("Erstelle PostgreSQL-Schema...")
        schema_file = os.path.join(os.path.dirname(__file__), 'schema_postgresql.sql')
        if os.path.exists(schema_file):
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            pg_cursor = pg_conn.cursor()
            pg_cursor.execute(schema_sql)
            pg_conn.commit()
            print("Schema erstellt.\n")
        else:
            print(f"WARNUNG: Schema-Datei nicht gefunden: {schema_file}")
            print("Stellen Sie sicher, dass das Schema bereits existiert.\n")

        # Tabellen migrieren
        print("Migriere Tabellen...")
        total_rows = 0
        for table in TABLES_ORDER:
            rows = migrate_table(sqlite_conn, pg_conn, table)
            total_rows += rows

        print("\n" + "=" * 60)
        print(f"Migration abgeschlossen!")
        print(f"Insgesamt {total_rows} Zeilen migriert.")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\nFEHLER bei Migration: {e}")
        pg_conn.rollback()
        return False

    finally:
        sqlite_conn.close()
        pg_conn.close()


def verify_migration():
    """Verifiziert die Migration"""
    import psycopg2

    print("\nVerifiziere Migration...")

    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    pg_conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        database=PG_DATABASE,
        user=PG_USER,
        password=PG_PASSWORD
    )

    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()

    errors = []

    for table in TABLES_ORDER:
        # Prüfe ob Tabelle existiert
        sqlite_cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,)
        )
        if not sqlite_cursor.fetchone():
            continue

        # Zähle Zeilen
        sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
        sqlite_count = sqlite_cursor.fetchone()[0]

        pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
        pg_count = pg_cursor.fetchone()[0]

        if sqlite_count != pg_count:
            errors.append(f"{table}: SQLite={sqlite_count}, PostgreSQL={pg_count}")
            print(f"  WARNUNG: {table} - Unterschied: SQLite={sqlite_count}, PostgreSQL={pg_count}")
        else:
            print(f"  OK: {table} ({pg_count} Zeilen)")

    sqlite_conn.close()
    pg_conn.close()

    if errors:
        print("\nWARNUNG: Es gibt Unterschiede bei der Zeilenanzahl!")
        return False
    else:
        print("\nVerifizierung erfolgreich!")
        return True


if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════╗
║     MASCHINENGEMEINSCHAFT - DATENBANK-MIGRATION              ║
║              SQLite -> PostgreSQL                            ║
╚══════════════════════════════════════════════════════════════╝
""")

    if len(sys.argv) > 1 and sys.argv[1] == '--verify':
        verify_migration()
    else:
        if run_migration():
            verify_migration()
            print("""
Nächste Schritte:
1. Setzen Sie die Umgebungsvariable: export DB_TYPE=postgresql
2. Starten Sie die Anwendung neu
3. Testen Sie alle Funktionen
""")
