"""
Datenbankmodul für Maschinengemeinschaft
Verwaltet alle Datenbankoperationen
Unterstützt PostgreSQL und SQLite (Fallback)
"""

import os
import hashlib
import secrets
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# Datenbank-Konfiguration aus Umgebungsvariablen
DB_TYPE = os.environ.get('DB_TYPE', 'sqlite')  # 'postgresql' oder 'sqlite'

# PostgreSQL-Konfiguration
PG_HOST = os.environ.get('PG_HOST', 'localhost')
PG_PORT = os.environ.get('PG_PORT', '5432')
PG_DATABASE = os.environ.get('PG_DATABASE', 'maschinengemeinschaft')
PG_USER = os.environ.get('PG_USER', 'mgr_user')
PG_PASSWORD = os.environ.get('PG_PASSWORD', '')

# SQLite-Fallback
SQLITE_PATH = os.environ.get('SQLITE_PATH', 'maschinengemeinschaft.db')

# Import basierend auf DB-Typ
if DB_TYPE == 'postgresql':
    try:
        import psycopg2
        from psycopg2.extras import DictCursor
        USING_POSTGRESQL = True
    except ImportError:
        print("WARNUNG: psycopg2 nicht installiert, verwende SQLite")
        import sqlite3
        USING_POSTGRESQL = False
else:
    import sqlite3
    USING_POSTGRESQL = False


def convert_placeholders(sql: str) -> str:
    """Konvertiert ? Platzhalter zu %s für PostgreSQL"""
    if USING_POSTGRESQL:
        return sql.replace('?', '%s')
    return sql


def convert_sql_syntax(sql: str) -> str:
    """Konvertiert SQLite-spezifische Syntax zu PostgreSQL"""
    if not USING_POSTGRESQL:
        return sql

    import re

    # INSERT OR IGNORE -> INSERT ... ON CONFLICT DO NOTHING
    if 'INSERT OR IGNORE' in sql.upper():
        sql = sql.replace('INSERT OR IGNORE', 'INSERT')
        sql = sql.replace('insert or ignore', 'INSERT')
        # Füge ON CONFLICT DO NOTHING am Ende hinzu (vor dem letzten Semikolon)
        if sql.strip().endswith(')'):
            sql = sql.rstrip() + ' ON CONFLICT DO NOTHING'

    # datetime(zeitpunkt, '+24 hours') -> zeitpunkt + INTERVAL '24 hours'
    # Unterstützt auch Tabellen-Aliase wie b.zeitpunkt
    sql = re.sub(
        r"datetime\(([\w.]+),\s*'\+(\d+)\s*hours?'\)",
        r"\1 + INTERVAL '\2 hours'",
        sql,
        flags=re.IGNORECASE
    )

    # datetime('now') -> NOW()
    sql = re.sub(r"datetime\('now'\)", "NOW()", sql, flags=re.IGNORECASE)

    # datetime('now', 'localtime') -> NOW()
    sql = re.sub(r"datetime\('now',\s*'localtime'\)", "NOW()", sql, flags=re.IGNORECASE)

    # datetime(datum || ' ' || zeit) -> (datum || ' ' || zeit)::timestamp
    sql = re.sub(
        r"datetime\(([^)]+\|\|[^)]+)\)",
        r"(\1)::timestamp",
        sql,
        flags=re.IGNORECASE
    )

    # AUTOINCREMENT -> SERIAL (wird im Schema behandelt)

    # PRAGMA table_info(table) -> SELECT ordinal_position, column_name, data_type FROM information_schema.columns
    # PRAGMA returns: cid, name, type, notnull, dflt_value, pk - code uses col[1] for name
    pragma_match = re.match(r"PRAGMA\s+table_info\((\w+)\)", sql, flags=re.IGNORECASE)
    if pragma_match:
        table_name = pragma_match.group(1)
        sql = f"SELECT ordinal_position - 1, column_name, data_type, is_nullable, column_default, 0 FROM information_schema.columns WHERE table_name = '{table_name}' ORDER BY ordinal_position"

    # Boolean-Spalten: 1/0 -> true/false
    boolean_columns = ['aktiv', 'is_admin', 'nur_training', 'zugeordnet', 'storniert', 'ganztags', 'hat_kopfzeile', 'treibstoff_berechnen']
    for col in boolean_columns:
        sql = re.sub(rf'\b{col}\s*=\s*1\b', f'{col} = true', sql)
        sql = re.sub(rf'\b{col}\s*=\s*0\b', f'{col} = false', sql)

    return convert_placeholders(sql)


class CursorWrapper:
    """Wrapper für Cursor, der automatisch SQL konvertiert"""

    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, sql, params=None):
        sql = convert_sql_syntax(sql)
        if params:
            self._cursor.execute(sql, params)
        else:
            self._cursor.execute(sql)

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def fetchmany(self, size=None):
        if size:
            return self._cursor.fetchmany(size)
        return self._cursor.fetchmany()

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    @property
    def rowcount(self):
        return self._cursor.rowcount

    @property
    def description(self):
        return self._cursor.description

    def close(self):
        self._cursor.close()

    def __iter__(self):
        return iter(self._cursor)


class ConnectionWrapper:
    """Wrapper für Connection, der CursorWrapper zurückgibt"""

    def __init__(self, connection):
        self._connection = connection

    def cursor(self, *args, **kwargs):
        return CursorWrapper(self._connection.cursor(*args, **kwargs))

    def commit(self):
        self._connection.commit()

    def rollback(self):
        self._connection.rollback()

    def close(self):
        self._connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class MaschinenDB:
    """Hauptklasse für Datenbankverwaltung"""

    def __init__(self, db_path: str = None):
        """Initialisiere Datenbankverbindung"""
        self.db_path = db_path or SQLITE_PATH
        self.connection = None
        self.cursor = None
        self.using_postgresql = USING_POSTGRESQL

    def connect(self):
        """Verbindung zur Datenbank herstellen"""
        if self.using_postgresql:
            raw_connection = psycopg2.connect(
                host=PG_HOST,
                port=PG_PORT,
                database=PG_DATABASE,
                user=PG_USER,
                password=PG_PASSWORD
            )
            # Wrapper für automatische SQL-Konvertierung
            self.connection = ConnectionWrapper(raw_connection)
            self._raw_connection = raw_connection  # Für commit/rollback
            self.cursor = CursorWrapper(raw_connection.cursor(cursor_factory=DictCursor))
        else:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()
            self._raw_connection = self.connection

    def close(self):
        """Datenbankverbindung schließen"""
        if self.cursor:
            self.cursor.close()
        if hasattr(self, '_raw_connection') and self._raw_connection:
            self._raw_connection.close()
        elif self.connection:
            self.connection.close()

    def execute(self, sql: str, params: tuple = None):
        """SQL ausführen mit automatischer Syntax-Konvertierung"""
        sql = convert_sql_syntax(sql)
        if params:
            self.cursor.execute(sql, params)
        else:
            self.cursor.execute(sql)

    def fetchone(self) -> Optional[Dict]:
        """Eine Zeile abrufen als Dictionary"""
        row = self.cursor.fetchone()
        if row is None:
            return None
        if self.using_postgresql:
            return dict(row)
        return dict(row)

    def fetchall(self) -> List[Dict]:
        """Alle Zeilen abrufen als Liste von Dictionaries"""
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]

    @property
    def lastrowid(self) -> int:
        """Letzte eingefügte ID abrufen"""
        if self.using_postgresql:
            # Bei PostgreSQL muss RETURNING id verwendet werden
            # oder wir holen die ID separat
            self.cursor.execute("SELECT lastval()")
            return self.cursor.fetchone()[0]
        return self.cursor.lastrowid

    def init_database(self):
        """Datenbank mit Schema initialisieren"""
        if self.using_postgresql:
            schema_file = os.path.join(os.path.dirname(__file__), 'schema_postgresql.sql')
        else:
            schema_file = os.path.join(os.path.dirname(__file__), 'schema.sql')

        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        if self.using_postgresql:
            # PostgreSQL: Einzelne Statements ausführen
            self.cursor.execute(schema_sql)
        else:
            # SQLite: executescript verwenden
            self.cursor.executescript(schema_sql)
        self.connection.commit()

    # ==================== BENUTZER ====================

    def add_benutzer(self, name: str, vorname: str = None, username: str = None,
                     password: str = None, is_admin: bool = False, adresse: str = None,
                     telefon: str = None, email: str = None,
                     mitglied_seit: str = None, bemerkungen: str = None) -> int:
        """Neuen Benutzer hinzufügen"""
        password_hash = self._hash_password(password) if password else None

        if self.using_postgresql:
            sql = """INSERT INTO benutzer (name, vorname, username, password_hash,
                                           is_admin, adresse, telefon, email,
                                           mitglied_seit, bemerkungen)
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                     RETURNING id"""
            self.cursor.execute(sql, (name, vorname, username, password_hash,
                                      is_admin, adresse, telefon, email,
                                      mitglied_seit, bemerkungen))
            return self.cursor.fetchone()[0]
        else:
            sql = """INSERT INTO benutzer (name, vorname, username, password_hash,
                                           is_admin, adresse, telefon, email,
                                           mitglied_seit, bemerkungen)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            self.cursor.execute(sql, (name, vorname, username, password_hash,
                                      is_admin, adresse, telefon, email,
                                      mitglied_seit, bemerkungen))
            self.connection.commit()
            return self.cursor.lastrowid

    def get_all_benutzer(self, nur_aktive: bool = True) -> List[Dict]:
        """Alle Benutzer abrufen"""
        sql = "SELECT * FROM benutzer"
        if nur_aktive:
            sql += " WHERE aktiv = true" if self.using_postgresql else " WHERE aktiv = 1"
        sql += " ORDER BY name, vorname"

        self.execute(sql)
        return self.fetchall()

    def get_benutzer(self, benutzer_id: int) -> Optional[Dict]:
        """Einzelnen Benutzer abrufen"""
        self.execute("SELECT * FROM benutzer WHERE id = ?", (benutzer_id,))
        return self.fetchone()

    def get_benutzer_by_id(self, benutzer_id: int) -> Optional[Dict]:
        """Einzelnen Benutzer abrufen (Alias für get_benutzer)"""
        return self.get_benutzer(benutzer_id)

    def update_benutzer(self, benutzer_id: int, **kwargs):
        """Benutzer aktualisieren"""
        if self.using_postgresql:
            fields = ', '.join([f"{key} = %s" for key in kwargs.keys()])
            sql = f"UPDATE benutzer SET {fields} WHERE id = %s"
        else:
            fields = ', '.join([f"{key} = ?" for key in kwargs.keys()])
            sql = f"UPDATE benutzer SET {fields} WHERE id = ?"
        values = list(kwargs.values()) + [benutzer_id]
        self.cursor.execute(sql, values)
        self.connection.commit()

    def delete_benutzer(self, benutzer_id: int, soft_delete: bool = True):
        """Benutzer löschen (soft delete = nur deaktivieren)"""
        if soft_delete:
            if self.using_postgresql:
                self.cursor.execute("UPDATE benutzer SET aktiv = false WHERE id = %s",
                                  (benutzer_id,))
            else:
                self.cursor.execute("UPDATE benutzer SET aktiv = 0 WHERE id = ?",
                                  (benutzer_id,))
        else:
            self.execute("DELETE FROM benutzer WHERE id = ?", (benutzer_id,))
        self.connection.commit()

    def activate_benutzer(self, benutzer_id: int):
        """Benutzer reaktivieren"""
        if self.using_postgresql:
            self.cursor.execute("UPDATE benutzer SET aktiv = true WHERE id = %s",
                              (benutzer_id,))
        else:
            self.cursor.execute("UPDATE benutzer SET aktiv = 1 WHERE id = ?",
                              (benutzer_id,))
        self.connection.commit()

    def _hash_password(self, password: str) -> str:
        """Passwort hashen mit SHA-256"""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def verify_login(self, username: str, password: str) -> Optional[Dict]:
        """Benutzer-Login überprüfen"""
        password_hash = self._hash_password(password)
        if self.using_postgresql:
            sql = """SELECT * FROM benutzer
                     WHERE username = %s AND password_hash = %s AND aktiv = true"""
        else:
            sql = """SELECT * FROM benutzer
                     WHERE username = ? AND password_hash = ? AND aktiv = 1"""
        self.cursor.execute(sql, (username, password_hash))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def update_password(self, benutzer_id: int, new_password: str):
        """Passwort eines Benutzers ändern"""
        password_hash = self._hash_password(new_password)
        self.execute(
            "UPDATE benutzer SET password_hash = ? WHERE id = ?",
            (password_hash, benutzer_id)
        )
        self.connection.commit()

    def get_gemeinschafts_admin_ids(self, benutzer_id: int) -> List[int]:
        """Hole Gemeinschafts-IDs, für die ein Benutzer Admin ist"""
        self.execute("""
            SELECT gemeinschaft_id FROM gemeinschafts_admin
            WHERE benutzer_id = ?
        """, (benutzer_id,))
        return [row['gemeinschaft_id'] for row in self.fetchall()]

    def add_gemeinschafts_admin(self, benutzer_id: int, gemeinschaft_id: int):
        """Benutzer als Gemeinschafts-Admin hinzufügen"""
        if self.using_postgresql:
            self.cursor.execute("""
                INSERT INTO gemeinschafts_admin
                (benutzer_id, gemeinschaft_id, erstellt_am)
                VALUES (%s, %s, %s)
                ON CONFLICT (benutzer_id, gemeinschaft_id) DO NOTHING
            """, (benutzer_id, gemeinschaft_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        else:
            self.cursor.execute("""
                INSERT OR IGNORE INTO gemeinschafts_admin
                (benutzer_id, gemeinschaft_id, erstellt_am)
                VALUES (?, ?, ?)
            """, (benutzer_id, gemeinschaft_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        self.connection.commit()

    def remove_gemeinschafts_admin(self, benutzer_id: int, gemeinschaft_id: int):
        """Gemeinschafts-Admin-Rechte entfernen"""
        self.execute("""
            DELETE FROM gemeinschafts_admin
            WHERE benutzer_id = ? AND gemeinschaft_id = ?
        """, (benutzer_id, gemeinschaft_id))
        self.connection.commit()

    def is_gemeinschafts_admin(self, benutzer_id: int, gemeinschaft_id: int) -> bool:
        """Prüfen ob Benutzer Admin einer Gemeinschaft ist"""
        self.execute("""
            SELECT COUNT(*) as cnt FROM gemeinschafts_admin
            WHERE benutzer_id = ? AND gemeinschaft_id = ?
        """, (benutzer_id, gemeinschaft_id))
        result = self.fetchone()
        return result['cnt'] > 0 if result else False

    # ==================== MASCHINEN ====================

    def add_maschine(self, bezeichnung: str, hersteller: str = None,
                     modell: str = None, baujahr: int = None,
                     kennzeichen: str = None, anschaffungsdatum: str = None,
                     stundenzaehler_aktuell: float = 0,
                     wartungsintervall: int = 50,
                     naechste_wartung: float = None,
                     naechste_wartung_bei: float = None,
                     anmerkungen: str = None,
                     bemerkungen: str = None,
                     abrechnungsart: str = 'stunden',
                     preis_pro_einheit: float = 0.0,
                     erfassungsmodus: str = 'fortlaufend',
                     gemeinschaft_id: int = None,
                     anschaffungspreis: float = 0.0,
                     abschreibungsdauer_jahre: int = 10) -> int:
        """Neue Maschine hinzufügen"""
        # naechste_wartung hat Vorrang vor naechste_wartung_bei (Kompatibilität)
        wartung = naechste_wartung if naechste_wartung is not None else naechste_wartung_bei

        if self.using_postgresql:
            sql = """INSERT INTO maschinen (bezeichnung, hersteller, modell, baujahr,
                            kennzeichen, anschaffungsdatum,
                            stundenzaehler_aktuell, wartungsintervall,
                            naechste_wartung_bei, bemerkungen,
                            abrechnungsart, preis_pro_einheit,
                            erfassungsmodus, gemeinschaft_id,
                            anschaffungspreis, abschreibungsdauer_jahre)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                 RETURNING id"""
            self.cursor.execute(sql, (bezeichnung, hersteller, modell, baujahr,
                          kennzeichen, anschaffungsdatum,
                          stundenzaehler_aktuell, wartungsintervall,
                          wartung, anmerkungen or bemerkungen,
                          abrechnungsart, preis_pro_einheit,
                          erfassungsmodus, gemeinschaft_id,
                          anschaffungspreis, abschreibungsdauer_jahre))
            return self.cursor.fetchone()[0]
        else:
            sql = """INSERT INTO maschinen (bezeichnung, hersteller, modell, baujahr,
                            kennzeichen, anschaffungsdatum,
                            stundenzaehler_aktuell, wartungsintervall,
                            naechste_wartung_bei, bemerkungen,
                            abrechnungsart, preis_pro_einheit,
                            erfassungsmodus, gemeinschaft_id,
                            anschaffungspreis, abschreibungsdauer_jahre)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            self.cursor.execute(sql, (bezeichnung, hersteller, modell, baujahr,
                          kennzeichen, anschaffungsdatum,
                          stundenzaehler_aktuell, wartungsintervall,
                          wartung, anmerkungen or bemerkungen,
                          abrechnungsart, preis_pro_einheit,
                          erfassungsmodus, gemeinschaft_id,
                          anschaffungspreis, abschreibungsdauer_jahre))
            self.connection.commit()
            return self.cursor.lastrowid

    def get_all_maschinen(self, nur_aktive: bool = True) -> List[Dict]:
        """Alle Maschinen abrufen"""
        sql = "SELECT * FROM maschinen"
        if nur_aktive:
            sql += " WHERE aktiv = true" if self.using_postgresql else " WHERE aktiv = 1"
        sql += " ORDER BY bezeichnung"

        self.execute(sql)
        return self.fetchall()

    def get_maschine(self, maschine_id: int) -> Optional[Dict]:
        """Einzelne Maschine abrufen"""
        self.execute("SELECT * FROM maschinen WHERE id = ?", (maschine_id,))
        return self.fetchone()

    def get_maschine_by_id(self, maschine_id: int) -> Optional[Dict]:
        """Einzelne Maschine abrufen (Alias für get_maschine)"""
        return self.get_maschine(maschine_id)

    def update_maschine(self, maschine_id: int, **kwargs):
        """Maschine aktualisieren"""
        if self.using_postgresql:
            fields = ', '.join([f"{key} = %s" for key in kwargs.keys()])
            sql = f"UPDATE maschinen SET {fields} WHERE id = %s"
        else:
            fields = ', '.join([f"{key} = ?" for key in kwargs.keys()])
            sql = f"UPDATE maschinen SET {fields} WHERE id = ?"
        values = list(kwargs.values()) + [maschine_id]
        self.cursor.execute(sql, values)
        self.connection.commit()

    def update_stundenzaehler(self, maschine_id: int, neuer_stand: float):
        """Stundenzähler einer Maschine aktualisieren"""
        self.update_maschine(maschine_id, stundenzaehler_aktuell=neuer_stand)

    def delete_maschine(self, maschine_id: int, soft_delete: bool = True):
        """Maschine löschen (soft delete = nur deaktivieren)"""
        if soft_delete:
            if self.using_postgresql:
                self.cursor.execute("UPDATE maschinen SET aktiv = false WHERE id = %s",
                                  (maschine_id,))
            else:
                self.cursor.execute("UPDATE maschinen SET aktiv = 0 WHERE id = ?",
                                  (maschine_id,))
        else:
            self.execute("DELETE FROM maschinen WHERE id = ?", (maschine_id,))
        self.connection.commit()

    # ==================== EINSATZZWECKE ====================

    def add_einsatzzweck(self, bezeichnung: str, beschreibung: str = None) -> int:
        """Neuen Einsatzzweck hinzufügen"""
        if self.using_postgresql:
            sql = "INSERT INTO einsatzzwecke (bezeichnung, beschreibung) VALUES (%s, %s) RETURNING id"
            self.cursor.execute(sql, (bezeichnung, beschreibung))
            return self.cursor.fetchone()[0]
        else:
            sql = "INSERT INTO einsatzzwecke (bezeichnung, beschreibung) VALUES (?, ?)"
            self.cursor.execute(sql, (bezeichnung, beschreibung))
            self.connection.commit()
            return self.cursor.lastrowid

    def get_all_einsatzzwecke(self, nur_aktive: bool = True) -> List[Dict]:
        """Alle Einsatzzwecke abrufen"""
        sql = "SELECT * FROM einsatzzwecke"
        if nur_aktive:
            sql += " WHERE aktiv = true" if self.using_postgresql else " WHERE aktiv = 1"
        sql += " ORDER BY bezeichnung"

        self.execute(sql)
        return self.fetchall()

    def get_einsatzzweck_by_id(self, einsatzzweck_id: int) -> Optional[Dict]:
        """Einzelnen Einsatzzweck abrufen"""
        self.execute("SELECT * FROM einsatzzwecke WHERE id = ?", (einsatzzweck_id,))
        return self.fetchone()

    def update_einsatzzweck(self, einsatzzweck_id: int, **kwargs):
        """Einsatzzweck aktualisieren"""
        if self.using_postgresql:
            fields = ', '.join([f"{key} = %s" for key in kwargs.keys()])
            sql = f"UPDATE einsatzzwecke SET {fields} WHERE id = %s"
        else:
            fields = ', '.join([f"{key} = ?" for key in kwargs.keys()])
            sql = f"UPDATE einsatzzwecke SET {fields} WHERE id = ?"
        values = list(kwargs.values()) + [einsatzzweck_id]
        self.cursor.execute(sql, values)
        self.connection.commit()

    def delete_einsatzzweck(self, einsatzzweck_id: int, soft_delete: bool = True):
        """Einsatzzweck löschen (soft delete = nur deaktivieren)"""
        if soft_delete:
            if self.using_postgresql:
                self.cursor.execute("UPDATE einsatzzwecke SET aktiv = false WHERE id = %s",
                                  (einsatzzweck_id,))
            else:
                self.cursor.execute("UPDATE einsatzzwecke SET aktiv = 0 WHERE id = ?",
                                  (einsatzzweck_id,))
        else:
            self.execute("DELETE FROM einsatzzwecke WHERE id = ?", (einsatzzweck_id,))
        self.connection.commit()

    def activate_einsatzzweck(self, einsatzzweck_id: int):
        """Einsatzzweck reaktivieren"""
        if self.using_postgresql:
            self.cursor.execute("UPDATE einsatzzwecke SET aktiv = true WHERE id = %s",
                              (einsatzzweck_id,))
        else:
            self.cursor.execute("UPDATE einsatzzwecke SET aktiv = 1 WHERE id = ?",
                              (einsatzzweck_id,))
        self.connection.commit()

    # ==================== MASCHINENEINSÄTZE ====================

    def add_einsatz(self, datum: str, benutzer_id: int, maschine_id: int,
                    einsatzzweck_id: int, anfangstand: float, endstand: float,
                    treibstoffverbrauch: float = None, treibstoffkosten: float = None,
                    anmerkungen: str = None, flaeche_menge: float = None) -> int:
        """Neuen Maschineneinsatz hinzufügen"""
        if endstand < anfangstand:
            raise ValueError("Endstand muss größer oder gleich Anfangstand sein!")

        # Kosten berechnen basierend auf Maschinen-Abrechnungsart
        kosten_berechnet = None
        maschine = self.get_maschine_by_id(maschine_id)
        if maschine:
            abrechnungsart = maschine.get('abrechnungsart', 'stunden')
            preis = maschine.get('preis_pro_einheit', 0) or 0

            if abrechnungsart == 'stunden':
                # Berechne basierend auf Betriebsstunden
                kosten_berechnet = (endstand - anfangstand) * preis
            elif abrechnungsart in ['hektar', 'kilometer', 'stueck']:
                # Berechne basierend auf Fläche/Menge, falls vorhanden
                if flaeche_menge and flaeche_menge > 0:
                    kosten_berechnet = flaeche_menge * preis
                else:
                    # Fallback: 0 Euro wenn keine Menge angegeben
                    kosten_berechnet = 0.0

        if self.using_postgresql:
            sql = """INSERT INTO maschineneinsaetze (datum, benutzer_id, maschine_id,
                                                     einsatzzweck_id, anfangstand, endstand,
                                                     treibstoffverbrauch, treibstoffkosten,
                                                     anmerkungen, flaeche_menge, kosten_berechnet)
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                     RETURNING id"""
            self.cursor.execute(sql, (datum, benutzer_id, maschine_id, einsatzzweck_id,
                                      anfangstand, endstand, treibstoffverbrauch,
                                      treibstoffkosten, anmerkungen, flaeche_menge,
                                      kosten_berechnet))
            einsatz_id = self.cursor.fetchone()[0]
        else:
            sql = """INSERT INTO maschineneinsaetze (datum, benutzer_id, maschine_id,
                                                     einsatzzweck_id, anfangstand, endstand,
                                                     treibstoffverbrauch, treibstoffkosten,
                                                     anmerkungen, flaeche_menge, kosten_berechnet)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            self.cursor.execute(sql, (datum, benutzer_id, maschine_id, einsatzzweck_id,
                                      anfangstand, endstand, treibstoffverbrauch,
                                      treibstoffkosten, anmerkungen, flaeche_menge,
                                      kosten_berechnet))
            self.connection.commit()
            einsatz_id = self.cursor.lastrowid

        # Stundenzähler der Maschine automatisch aktualisieren
        self.update_stundenzaehler(maschine_id, endstand)

        return einsatz_id

    def get_all_einsaetze(self, limit: int = None) -> List[Dict]:
        """Alle Einsätze abrufen (übersichtlich formatiert)"""
        sql = "SELECT * FROM einsaetze_uebersicht"
        if limit:
            sql += f" LIMIT {limit}"

        self.execute(sql)
        return self.fetchall()

    def get_einsaetze_by_benutzer(self, benutzer_id: int) -> List[Dict]:
        """Einsätze eines bestimmten Benutzers abrufen"""
        benutzer = self.get_benutzer(benutzer_id)
        if not benutzer:
            return []

        search_pattern = f"%{benutzer['name']}%"
        self.execute("SELECT * FROM einsaetze_uebersicht WHERE benutzer LIKE ?", (search_pattern,))
        return self.fetchall()

    def get_einsaetze_by_maschine(self, maschine_id: int) -> List[Dict]:
        """Einsätze einer bestimmten Maschine abrufen"""
        maschine = self.get_maschine(maschine_id)
        if not maschine:
            return []

        self.execute("SELECT * FROM einsaetze_uebersicht WHERE maschine = ?", (maschine['bezeichnung'],))
        return self.fetchall()

    def get_einsaetze_by_zeitraum(self, von: str, bis: str) -> List[Dict]:
        """Einsätze in einem Zeitraum abrufen"""
        self.execute("""SELECT * FROM einsaetze_uebersicht
                 WHERE datum BETWEEN ? AND ?""", (von, bis))
        return self.fetchall()

    def get_statistik_benutzer(self, benutzer_id: int) -> Dict:
        """Statistik für einen Benutzer"""
        self.execute("""SELECT
                    COUNT(*) as anzahl_einsaetze,
                    SUM(betriebsstunden) as gesamt_stunden,
                    SUM(treibstoffverbrauch) as gesamt_treibstoff,
                    SUM(treibstoffkosten) as gesamt_kosten,
                    SUM(kosten_berechnet) as gesamt_maschinenkosten
                 FROM maschineneinsaetze
                 WHERE benutzer_id = ?""", (benutzer_id,))
        return self.fetchone() or {}

    def get_statistik_maschine(self, maschine_id: int) -> Dict:
        """Statistik für eine Maschine"""
        self.execute("""SELECT
                    COUNT(*) as anzahl_einsaetze,
                    SUM(betriebsstunden) as gesamt_stunden,
                    SUM(treibstoffverbrauch) as gesamt_treibstoff,
                    COUNT(DISTINCT benutzer_id) as anzahl_benutzer
                 FROM maschineneinsaetze
                 WHERE maschine_id = ?""", (maschine_id,))
        return self.fetchone() or {}


# Context Manager Support
class MaschinenDBContext(MaschinenDB):
    """Context Manager für automatische Verbindungsverwaltung"""

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.connection.commit()
        else:
            self.connection.rollback()
        self.close()
        return False


if __name__ == "__main__":
    # Testcode
    print(f"Datenbank-Typ: {'PostgreSQL' if USING_POSTGRESQL else 'SQLite'}")
    print("Initialisiere Datenbank...")
    with MaschinenDBContext() as db:
        db.init_database()
        print("Datenbank erfolgreich initialisiert!")

        # Zeige vorhandene Einsatzzwecke
        zwecke = db.get_all_einsatzzwecke()
        print(f"\n{len(zwecke)} Einsatzzwecke verfügbar")
