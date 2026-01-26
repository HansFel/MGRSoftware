# -*- coding: utf-8 -*-
"""
SQL-Hilfsfunktionen für PostgreSQL/SQLite-Kompatibilität
"""

import re
from database import USING_POSTGRESQL


def convert_sql(sql: str) -> str:
    """Konvertiert SQLite-SQL zu PostgreSQL wenn nötig"""
    if not USING_POSTGRESQL:
        return sql

    # INSERT OR IGNORE -> INSERT ... ON CONFLICT DO NOTHING
    if 'INSERT OR IGNORE' in sql.upper():
        sql = re.sub(r'INSERT OR IGNORE', 'INSERT', sql, flags=re.IGNORECASE)
        # Finde das Ende des VALUES-Teils und füge ON CONFLICT DO NOTHING hinzu
        if 'VALUES' in sql.upper() and 'ON CONFLICT' not in sql.upper():
            # Füge am Ende hinzu (vor eventuellem Semikolon)
            sql = sql.rstrip().rstrip(';') + ' ON CONFLICT DO NOTHING'

    # datetime(zeitpunkt, '+24 hours') -> zeitpunkt + INTERVAL '24 hours'
    sql = re.sub(
        r"datetime\((\w+),\s*'\+(\d+)\s*hours?'\)",
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

    # date('now') -> CURRENT_DATE
    sql = re.sub(r"date\('now'\)", "CURRENT_DATE", sql, flags=re.IGNORECASE)

    # strftime('%Y', datum) -> TO_CHAR(datum, 'YYYY')
    sql = re.sub(
        r"strftime\s*\(\s*'%Y'\s*,\s*(\w+\.?\w*)\s*\)",
        r"TO_CHAR(\1, 'YYYY')",
        sql,
        flags=re.IGNORECASE
    )

    # strftime('%m', datum) -> TO_CHAR(datum, 'MM')
    sql = re.sub(
        r"strftime\s*\(\s*'%m'\s*,\s*(\w+\.?\w*)\s*\)",
        r"TO_CHAR(\1, 'MM')",
        sql,
        flags=re.IGNORECASE
    )

    # strftime('%Y-%m-%d', datum) -> TO_CHAR(datum, 'YYYY-MM-DD')
    sql = re.sub(
        r"strftime\s*\(\s*'%Y-%m-%d'\s*,\s*(\w+\.?\w*)\s*\)",
        r"TO_CHAR(\1, 'YYYY-MM-DD')",
        sql,
        flags=re.IGNORECASE
    )

    # GROUP_CONCAT(col) -> STRING_AGG(col, ',')
    # GROUP_CONCAT(col, 'sep') -> STRING_AGG(col, 'sep')
    sql = re.sub(
        r"GROUP_CONCAT\(([^,)]+)\)",
        r"STRING_AGG(\1::text, ',')",
        sql,
        flags=re.IGNORECASE
    )
    sql = re.sub(
        r"GROUP_CONCAT\(([^,]+),\s*('[^']+')\)",
        r"STRING_AGG(\1::text, \2)",
        sql,
        flags=re.IGNORECASE
    )

    # ? -> %s für Parameterisierung
    sql = sql.replace('?', '%s')

    # Boolean-Spalten: 1/0 -> true/false
    boolean_columns = ['aktiv', 'is_admin', 'nur_training', 'zugeordnet', 'storniert',
                       'ganztags', 'hat_kopfzeile', 'treibstoff_berechnen']
    for col in boolean_columns:
        sql = re.sub(rf'\b{col}\s*=\s*1\b', f'{col} = true', sql)
        sql = re.sub(rf'\b{col}\s*=\s*0\b', f'{col} = false', sql)

    return sql


def db_execute(cursor, sql: str, params: tuple = None):
    """Führt SQL aus mit automatischer Konvertierung"""
    sql = convert_sql(sql)
    if params:
        cursor.execute(sql, params)
    else:
        cursor.execute(sql)
