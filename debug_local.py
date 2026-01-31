#!/usr/bin/env python3
"""Debug-Skript für lokale Testversion"""
import os
import sys
import traceback

# Umgebungsvariablen setzen
os.environ['DB_TYPE'] = 'sqlite'
os.environ['DB_PATH'] = 'data/test_lokal.db'
os.environ['SECRET_KEY'] = 'debug-key-2026'

print("=" * 50)
print("DEBUG: Lokale Testversion")
print("=" * 50)
print(f"Python: {sys.version}")
print(f"DB_TYPE: {os.environ.get('DB_TYPE')}")
print(f"DB_PATH: {os.environ.get('DB_PATH')}")
print()

# Schritt 1: Prüfen ob schema.sql existiert
print("1. Prüfe schema.sql...")
if os.path.exists('schema.sql'):
    print("   OK: schema.sql gefunden")
else:
    print("   FEHLER: schema.sql nicht gefunden!")
    sys.exit(1)

# Schritt 2: Database importieren
print("2. Importiere database.py...")
try:
    from database import MaschinenDBContext
    print("   OK: database.py importiert")
except Exception as e:
    print(f"   FEHLER: {e}")
    traceback.print_exc()
    sys.exit(1)

# Schritt 3: Datenbank-Verbindung testen
print("3. Teste Datenbank-Verbindung...")
try:
    db_path = os.environ.get('DB_PATH', 'data/test_lokal.db')

    # Verzeichnis erstellen falls nötig
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    with MaschinenDBContext(db_path) as db:
        # Prüfen ob Tabellen existieren
        db.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in db.cursor.fetchall()]

        if tables:
            print(f"   OK: {len(tables)} Tabellen gefunden: {tables[:5]}...")
        else:
            print("   Keine Tabellen - initialisiere Datenbank...")
            db.init_database()
            print("   OK: Datenbank initialisiert")
except Exception as e:
    print(f"   FEHLER: {e}")
    traceback.print_exc()
    sys.exit(1)

# Schritt 4: Web-App importieren
print("4. Importiere web_app.py...")
try:
    from web_app import app
    print("   OK: web_app.py importiert")
except Exception as e:
    print(f"   FEHLER: {e}")
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 50)
print("ALLE TESTS BESTANDEN!")
print("=" * 50)
print()
print("Starte Server auf http://localhost:5000 ...")
print("Beenden mit Strg+C")
print()

app.run(host='0.0.0.0', port=5000, debug=True)
