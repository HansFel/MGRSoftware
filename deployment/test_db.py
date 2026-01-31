#!/usr/bin/env python3
"""Test-Skript für Datenbank-Initialisierung"""
import os
import sys

# Umgebungsvariablen setzen
os.environ['DB_TYPE'] = 'sqlite'
os.environ['DB_PATH'] = '../data/test_lokal.db'

print("=" * 50)
print("Datenbank-Test")
print("=" * 50)
print(f"DB_TYPE: {os.environ.get('DB_TYPE')}")
print(f"DB_PATH: {os.environ.get('DB_PATH')}")
print()

# Verzeichnis erstellen
db_path = os.environ.get('DB_PATH')
db_dir = os.path.dirname(db_path)
if db_dir and not os.path.exists(db_dir):
    os.makedirs(db_dir, exist_ok=True)
    print(f"Verzeichnis erstellt: {db_dir}")

# Prüfen ob schema.sql existiert
if os.path.exists('schema.sql'):
    print("schema.sql gefunden")
else:
    print("FEHLER: schema.sql nicht gefunden!")
    sys.exit(1)

# Database importieren
print("\nImportiere database.py...")
from database import MaschinenDBContext, DB_TYPE, USING_POSTGRESQL

print(f"DB_TYPE aus database.py: {DB_TYPE}")
print(f"USING_POSTGRESQL: {USING_POSTGRESQL}")

# Datenbank initialisieren
print("\nInitialisiere Datenbank...")
try:
    with MaschinenDBContext(db_path) as db:
        # Prüfen ob Tabellen existieren
        db.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in db.cursor.fetchall()]

        if not tables:
            print("Keine Tabellen - initialisiere...")
            db.init_database()
            db.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in db.cursor.fetchall()]

        print(f"\nTabellen ({len(tables)}):")
        for t in sorted(tables):
            print(f"  - {t}")

        # Admin-Benutzer prüfen
        print("\nPrüfe Admin-Benutzer...")
        db.cursor.execute("SELECT id, username, is_admin FROM benutzer WHERE username = 'admin'")
        admin = db.cursor.fetchone()
        if admin:
            print(f"  Admin gefunden: ID={admin[0]}, username={admin[1]}, is_admin={admin[2]}")
        else:
            print("  FEHLER: Admin-Benutzer nicht gefunden!")

        # Login testen
        print("\nTeste Login...")
        result = db.verify_login('admin', 'admin123')
        if result:
            print(f"  Login erfolgreich: {result.get('username')}")
        else:
            print("  Login fehlgeschlagen!")
            # Passwort-Hash prüfen
            db.cursor.execute("SELECT password_hash FROM benutzer WHERE username = 'admin'")
            row = db.cursor.fetchone()
            if row:
                print(f"  Gespeicherter Hash: {row[0][:40]}...")
                # Erwarteter Hash für 'admin123'
                import hashlib
                expected = hashlib.sha256('admin123'.encode()).hexdigest()
                print(f"  Erwarteter Hash:    {expected[:40]}...")
                if row[0] == expected:
                    print("  Hashes stimmen überein!")
                else:
                    print("  HASHES UNTERSCHIEDLICH!")

except Exception as e:
    print(f"FEHLER: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 50)
print("Test abgeschlossen!")
print("=" * 50)
