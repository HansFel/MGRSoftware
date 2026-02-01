# -*- coding: utf-8 -*-
"""
Schema-Migration für Maschinengemeinschaft
Prüft beim App-Start ob alle Spalten existieren und fügt fehlende hinzu.
"""

import os

# Datenbank-Typ aus Umgebungsvariable
DB_TYPE = os.environ.get('DB_TYPE', 'sqlite')
USING_POSTGRESQL = DB_TYPE == 'postgresql'

if USING_POSTGRESQL:
    import psycopg2
    PG_HOST = os.environ.get('PG_HOST', 'localhost')
    PG_PORT = os.environ.get('PG_PORT', '5432')
    PG_DATABASE = os.environ.get('PG_DATABASE', 'maschinengemeinschaft')
    PG_USER = os.environ.get('PG_USER', 'mgr_user')
    PG_PASSWORD = os.environ.get('PG_PASSWORD', '')


# Liste aller erforderlichen Spalten
# Format: (tabelle, spalte, datentyp_postgresql, datentyp_sqlite, default_wert)
REQUIRED_COLUMNS = [
    # maschinen_reservierungen
    ("maschinen_reservierungen", "status", "TEXT", "TEXT", "'aktiv'"),
    ("maschinen_reservierungen", "geaendert_am", "TIMESTAMP", "DATETIME", None),
    ("maschinen_reservierungen", "uhrzeit_von", "TEXT", "TEXT", None),
    ("maschinen_reservierungen", "uhrzeit_bis", "TEXT", "TEXT", None),

    # maschinen
    ("maschinen", "treibstoff_berechnen", "BOOLEAN", "BOOLEAN", "FALSE"),
    ("maschinen", "gemeinschaft_id", "INTEGER", "INTEGER", "1"),
    ("maschinen", "aktiv", "BOOLEAN", "BOOLEAN", "TRUE"),

    # benutzer
    ("benutzer", "letzter_treibstoffpreis", "REAL", "REAL", None),
    ("benutzer", "aktiv", "BOOLEAN", "BOOLEAN", "TRUE"),

    # mitglieder_abrechnungen
    ("mitglieder_abrechnungen", "betrag_gesamt", "REAL", "REAL", "0.0"),
    ("mitglieder_abrechnungen", "status", "TEXT", "TEXT", "'offen'"),

    # mitglieder_konten
    ("mitglieder_konten", "saldo", "REAL", "REAL", "0.0"),

    # zahlungsreferenzen
    ("zahlungsreferenzen", "gemeinschaft_id", "INTEGER", "INTEGER", None),
    ("zahlungsreferenzen", "aktiv", "BOOLEAN", "BOOLEAN", "TRUE"),
]

# Liste aller erforderlichen Tabellen
# Format: (tabelle, create_statement_postgresql, create_statement_sqlite)
REQUIRED_TABLES = [
    (
        "reservierungen_abgelaufen",
        """CREATE TABLE IF NOT EXISTS reservierungen_abgelaufen (
            id SERIAL PRIMARY KEY,
            reservierung_id INTEGER NOT NULL,
            maschine_id INTEGER NOT NULL,
            maschine_bezeichnung TEXT,
            benutzer_id INTEGER NOT NULL,
            benutzer_name TEXT,
            datum DATE NOT NULL,
            uhrzeit_von TEXT,
            uhrzeit_bis TEXT,
            nutzungsdauer_stunden REAL,
            zweck TEXT,
            bemerkung TEXT,
            erstellt_am TIMESTAMP,
            archiviert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS reservierungen_abgelaufen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reservierung_id INTEGER NOT NULL,
            maschine_id INTEGER NOT NULL,
            maschine_bezeichnung TEXT,
            benutzer_id INTEGER NOT NULL,
            benutzer_name TEXT,
            datum DATE NOT NULL,
            uhrzeit_von TEXT,
            uhrzeit_bis TEXT,
            nutzungsdauer_stunden REAL,
            zweck TEXT,
            bemerkung TEXT,
            erstellt_am DATETIME,
            archiviert_am DATETIME DEFAULT CURRENT_TIMESTAMP
        )"""
    ),
]


def get_connection():
    """Erstellt eine Datenbankverbindung"""
    if USING_POSTGRESQL:
        return psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=PG_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD
        )
    else:
        import sqlite3
        db_path = os.environ.get('SQLITE_PATH', 'maschinengemeinschaft.db')
        return sqlite3.connect(db_path)


def column_exists(cursor, table: str, column: str) -> bool:
    """Prüft ob eine Spalte in einer Tabelle existiert"""
    if USING_POSTGRESQL:
        cursor.execute("""
            SELECT 1 FROM information_schema.columns
            WHERE table_name = %s AND column_name = %s
        """, (table, column))
    else:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        return column in columns

    return cursor.fetchone() is not None


def table_exists(cursor, table: str) -> bool:
    """Prüft ob eine Tabelle existiert"""
    if USING_POSTGRESQL:
        cursor.execute("""
            SELECT 1 FROM information_schema.tables
            WHERE table_name = %s
        """, (table,))
    else:
        cursor.execute("""
            SELECT 1 FROM sqlite_master
            WHERE type='table' AND name=?
        """, (table,))

    return cursor.fetchone() is not None


def add_column(cursor, table: str, column: str, datatype: str, default: str = None):
    """Fügt eine Spalte zu einer Tabelle hinzu"""
    try:
        if default:
            if USING_POSTGRESQL:
                sql = f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {datatype} DEFAULT {default}"
            else:
                sql = f"ALTER TABLE {table} ADD COLUMN {column} {datatype} DEFAULT {default}"
        else:
            if USING_POSTGRESQL:
                sql = f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {datatype}"
            else:
                sql = f"ALTER TABLE {table} ADD COLUMN {column} {datatype}"

        cursor.execute(sql)
        print(f"  + Spalte hinzugefügt: {table}.{column}")
    except Exception as e:
        if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
            pass  # Spalte existiert bereits - OK
        else:
            raise


def create_table(cursor, table: str, create_sql: str):
    """Erstellt eine Tabelle"""
    cursor.execute(create_sql)
    print(f"  + Tabelle erstellt: {table}")


def run_migrations():
    """Führt alle notwendigen Migrationen durch"""
    print("Schema-Migration: Prüfe Datenbankstruktur...")

    try:
        conn = get_connection()
        cursor = conn.cursor()
        changes_made = 0

        # Tabellen prüfen und erstellen
        for table, pg_sql, sqlite_sql in REQUIRED_TABLES:
            if not table_exists(cursor, table):
                create_sql = pg_sql if USING_POSTGRESQL else sqlite_sql
                create_table(cursor, table, create_sql)
                changes_made += 1

        # Spalten prüfen und hinzufügen
        for table, column, pg_type, sqlite_type, default in REQUIRED_COLUMNS:
            if table_exists(cursor, table):
                if not column_exists(cursor, table, column):
                    datatype = pg_type if USING_POSTGRESQL else sqlite_type
                    add_column(cursor, table, column, datatype, default)
                    changes_made += 1

        conn.commit()

        if changes_made > 0:
            print(f"Schema-Migration: {changes_made} Änderungen durchgeführt.")
        else:
            print("Schema-Migration: Keine Änderungen notwendig.")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"Schema-Migration FEHLER: {e}")
        return False


if __name__ == "__main__":
    run_migrations()
