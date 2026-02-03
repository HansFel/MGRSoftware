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
    ("maschinen_reservierungen", "nutzungsdauer_stunden", "REAL", "REAL", None),
    ("maschinen_reservierungen", "zweck", "TEXT", "TEXT", None),
    ("maschinen_reservierungen", "bemerkung", "TEXT", "TEXT", None),

    # maschinen
    ("maschinen", "treibstoff_berechnen", "BOOLEAN", "BOOLEAN", "FALSE"),
    ("maschinen", "gemeinschaft_id", "INTEGER", "INTEGER", "1"),
    ("maschinen", "aktiv", "BOOLEAN", "BOOLEAN", "TRUE"),

    # benutzer
    ("benutzer", "letzter_treibstoffpreis", "REAL", "REAL", None),
    ("benutzer", "aktiv", "BOOLEAN", "BOOLEAN", "TRUE"),

    # mitglieder_abrechnungen
    ("mitglieder_abrechnungen", "gemeinschaft_id", "INTEGER", "INTEGER", None),
    ("mitglieder_abrechnungen", "benutzer_id", "INTEGER", "INTEGER", None),
    ("mitglieder_abrechnungen", "zeitraum_von", "DATE", "DATE", None),
    ("mitglieder_abrechnungen", "zeitraum_bis", "DATE", "DATE", None),
    ("mitglieder_abrechnungen", "betrag_maschinen", "REAL", "REAL", "0.0"),
    ("mitglieder_abrechnungen", "betrag_treibstoff", "REAL", "REAL", "0.0"),
    ("mitglieder_abrechnungen", "betrag_gesamt", "REAL", "REAL", "0.0"),
    ("mitglieder_abrechnungen", "status", "TEXT", "TEXT", "'offen'"),
    ("mitglieder_abrechnungen", "erstellt_am", "TIMESTAMP", "DATETIME", None),
    ("mitglieder_abrechnungen", "bezahlt_am", "TIMESTAMP", "DATETIME", None),

    # mitglieder_konten
    ("mitglieder_konten", "saldo", "REAL", "REAL", "0.0"),

    # zahlungsreferenzen
    ("zahlungsreferenzen", "gemeinschaft_id", "INTEGER", "INTEGER", None),
    ("zahlungsreferenzen", "aktiv", "BOOLEAN", "BOOLEAN", "TRUE"),

    # gemeinschaften - Finanzen
    ("gemeinschaften", "anfangssaldo_bank", "REAL", "REAL", "0.0"),
    ("gemeinschaften", "anfangssaldo_datum", "DATE", "DATE", None),
    ("gemeinschaften", "bank_name", "TEXT", "TEXT", None),
    ("gemeinschaften", "bank_iban", "TEXT", "TEXT", None),
    ("gemeinschaften", "bank_bic", "TEXT", "TEXT", None),
    ("gemeinschaften", "bank_kontoinhaber", "TEXT", "TEXT", None),

    # bank_transaktionen
    ("bank_transaktionen", "gemeinschaft_id", "INTEGER", "INTEGER", None),
    ("bank_transaktionen", "benutzer_id", "INTEGER", "INTEGER", None),
    ("bank_transaktionen", "zugeordnet", "BOOLEAN", "BOOLEAN", "FALSE"),
    ("bank_transaktionen", "zuordnung_typ", "TEXT", "TEXT", None),
    ("bank_transaktionen", "zuordnung_id", "INTEGER", "INTEGER", None),
    ("bank_transaktionen", "buchungsdatum", "DATE", "DATE", None),
    ("bank_transaktionen", "betrag", "REAL", "REAL", None),
    ("bank_transaktionen", "verwendungszweck", "TEXT", "TEXT", None),
    ("bank_transaktionen", "importiert_am", "TIMESTAMP", "DATETIME", None),
    ("bank_transaktionen", "importiert_von", "INTEGER", "INTEGER", None),

    # buchungen
    ("buchungen", "benutzer_id", "INTEGER", "INTEGER", None),
    ("buchungen", "gemeinschaft_id", "INTEGER", "INTEGER", None),
    ("buchungen", "typ", "TEXT", "TEXT", None),
    ("buchungen", "datum", "DATE", "DATE", None),
    ("buchungen", "betrag", "REAL", "REAL", None),
    ("buchungen", "beschreibung", "TEXT", "TEXT", None),
]

# Liste aller erforderlichen Tabellen
# Format: (tabelle, create_statement_postgresql, create_statement_sqlite)
REQUIRED_TABLES = [
    (
        "reservierungen_geloescht",
        """CREATE TABLE IF NOT EXISTS reservierungen_geloescht (
            id SERIAL PRIMARY KEY,
            reservierung_id INTEGER NOT NULL,
            maschine_id INTEGER NOT NULL,
            maschine_bezeichnung TEXT,
            benutzer_id INTEGER NOT NULL,
            benutzer_name TEXT,
            datum DATE NOT NULL,
            uhrzeit_von TEXT,
            uhrzeit_bis TEXT,
            zweck TEXT,
            grund TEXT,
            geloescht_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            geloescht_von INTEGER
        )""",
        """CREATE TABLE IF NOT EXISTS reservierungen_geloescht (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reservierung_id INTEGER NOT NULL,
            maschine_id INTEGER NOT NULL,
            maschine_bezeichnung TEXT,
            benutzer_id INTEGER NOT NULL,
            benutzer_name TEXT,
            datum DATE NOT NULL,
            uhrzeit_von TEXT,
            uhrzeit_bis TEXT,
            zweck TEXT,
            grund TEXT,
            geloescht_am DATETIME DEFAULT CURRENT_TIMESTAMP,
            geloescht_von INTEGER
        )"""
    ),
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
    (
        "bank_transaktionen",
        """CREATE TABLE IF NOT EXISTS bank_transaktionen (
            id SERIAL PRIMARY KEY,
            gemeinschaft_id INTEGER,
            buchungsdatum DATE NOT NULL,
            valutadatum DATE,
            betrag REAL NOT NULL,
            waehrung TEXT DEFAULT 'EUR',
            verwendungszweck TEXT,
            auftraggeber TEXT,
            iban TEXT,
            bic TEXT,
            importiert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            importiert_von INTEGER,
            zugeordnet BOOLEAN DEFAULT FALSE,
            benutzer_id INTEGER,
            zuordnung_typ TEXT,
            zuordnung_id INTEGER,
            import_hash TEXT UNIQUE
        )""",
        """CREATE TABLE IF NOT EXISTS bank_transaktionen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gemeinschaft_id INTEGER,
            buchungsdatum DATE NOT NULL,
            valutadatum DATE,
            betrag REAL NOT NULL,
            waehrung TEXT DEFAULT 'EUR',
            verwendungszweck TEXT,
            auftraggeber TEXT,
            iban TEXT,
            bic TEXT,
            importiert_am DATETIME DEFAULT CURRENT_TIMESTAMP,
            importiert_von INTEGER,
            zugeordnet BOOLEAN DEFAULT 0,
            benutzer_id INTEGER,
            zuordnung_typ TEXT,
            zuordnung_id INTEGER,
            import_hash TEXT UNIQUE
        )"""
    ),
    (
        "gemeinschafts_kosten",
        """CREATE TABLE IF NOT EXISTS gemeinschafts_kosten (
            id SERIAL PRIMARY KEY,
            gemeinschaft_id INTEGER NOT NULL,
            transaktion_id INTEGER,
            maschine_id INTEGER,
            kategorie TEXT NOT NULL,
            betrag REAL NOT NULL,
            datum DATE NOT NULL,
            beschreibung TEXT,
            erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            erstellt_von INTEGER
        )""",
        """CREATE TABLE IF NOT EXISTS gemeinschafts_kosten (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gemeinschaft_id INTEGER NOT NULL,
            transaktion_id INTEGER,
            maschine_id INTEGER,
            kategorie TEXT NOT NULL,
            betrag REAL NOT NULL,
            datum DATE NOT NULL,
            beschreibung TEXT,
            erstellt_am DATETIME DEFAULT CURRENT_TIMESTAMP,
            erstellt_von INTEGER
        )"""
    ),
    (
        "mitglieder_abrechnungen",
        """CREATE TABLE IF NOT EXISTS mitglieder_abrechnungen (
            id SERIAL PRIMARY KEY,
            gemeinschaft_id INTEGER NOT NULL,
            benutzer_id INTEGER NOT NULL,
            zeitraum_von DATE,
            zeitraum_bis DATE,
            betrag_maschinen REAL DEFAULT 0.0,
            betrag_treibstoff REAL DEFAULT 0.0,
            betrag_gesamt REAL DEFAULT 0.0,
            status TEXT DEFAULT 'offen',
            erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            bezahlt_am TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS mitglieder_abrechnungen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gemeinschaft_id INTEGER NOT NULL,
            benutzer_id INTEGER NOT NULL,
            zeitraum_von DATE,
            zeitraum_bis DATE,
            betrag_maschinen REAL DEFAULT 0.0,
            betrag_treibstoff REAL DEFAULT 0.0,
            betrag_gesamt REAL DEFAULT 0.0,
            status TEXT DEFAULT 'offen',
            erstellt_am DATETIME DEFAULT CURRENT_TIMESTAMP,
            bezahlt_am DATETIME
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


def check_missing_schema():
    """Prüft welche Tabellen und Spalten fehlen (ohne sie hinzuzufügen)"""
    missing = {'tables': [], 'columns': []}

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Tabellen prüfen
        for table, pg_sql, sqlite_sql in REQUIRED_TABLES:
            if not table_exists(cursor, table):
                missing['tables'].append(table)

        # Spalten prüfen
        for table, column, pg_type, sqlite_type, default in REQUIRED_COLUMNS:
            if table_exists(cursor, table):
                if not column_exists(cursor, table, column):
                    missing['columns'].append(f"{table}.{column}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Schema-Check Fehler: {e}")

    return missing


def run_migrations_with_report():
    """Führt Migrationen durch und gibt einen Bericht zurück"""
    report = {'tables_added': [], 'columns_added': [], 'errors': []}

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Tabellen prüfen und erstellen
        for table, pg_sql, sqlite_sql in REQUIRED_TABLES:
            if not table_exists(cursor, table):
                try:
                    create_sql = pg_sql if USING_POSTGRESQL else sqlite_sql
                    cursor.execute(create_sql)
                    report['tables_added'].append(table)
                except Exception as e:
                    report['errors'].append(f"Tabelle {table}: {e}")

        # Spalten prüfen und hinzufügen
        for table, column, pg_type, sqlite_type, default in REQUIRED_COLUMNS:
            if table_exists(cursor, table):
                if not column_exists(cursor, table, column):
                    try:
                        datatype = pg_type if USING_POSTGRESQL else sqlite_type
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
                        report['columns_added'].append(f"{table}.{column}")
                    except Exception as e:
                        if "already exists" not in str(e).lower():
                            report['errors'].append(f"Spalte {table}.{column}: {e}")

        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        report['errors'].append(f"Verbindungsfehler: {e}")

    return report


if __name__ == "__main__":
    run_migrations()
