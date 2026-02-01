#!/usr/bin/env python3
"""Schneller DB-Check"""
import os
import sqlite3

os.environ['DB_TYPE'] = 'sqlite'
db_path = '../data/test_lokal.db'

print(f"Prüfe: {db_path}")
print(f"Existiert: {os.path.exists(db_path)}")

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cursor.fetchall()]
    print(f"Tabellen: {len(tables)}")

    if 'maschineneinsaetze' in tables:
        cursor.execute("PRAGMA table_info(maschineneinsaetze)")
        cols = [r[1] for r in cursor.fetchall()]
        print(f"Spalten in maschineneinsaetze: {cols}")

        cursor.execute("SELECT COUNT(*) FROM maschineneinsaetze")
        print(f"Anzahl Einsätze: {cursor.fetchone()[0]}")
    else:
        print("FEHLER: Tabelle maschineneinsaetze fehlt!")

    conn.close()
else:
    print("Datenbank existiert nicht - wird beim Start erstellt")
