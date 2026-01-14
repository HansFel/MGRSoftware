import sqlite3
import hashlib
import os

# Test wie der Launcher eine DB erstellt
test_db = 'test_manual.db'

# Alte DB löschen falls vorhanden
if os.path.exists(test_db):
    os.remove(test_db)

# Schema einlesen
with open('schema.sql', 'r', encoding='utf-8') as f:
    schema = f.read()

# DB erstellen
conn = sqlite3.connect(test_db)
cursor = conn.cursor()
cursor.executescript(schema)

# Admin-User wie im Launcher
password_hash = hashlib.sha256("admin123".encode('utf-8')).hexdigest()
print(f"Erstelle Admin mit Hash: {password_hash}")

cursor.execute("""
    INSERT INTO benutzer (name, vorname, username, password_hash, is_admin, admin_level, aktiv)
    VALUES ('Admin', 'System', 'admin', ?, 1, 2, 1)
""", (password_hash,))

conn.commit()
conn.close()

print(f"\nDatenbank '{test_db}' erstellt")

# Jetzt versuchen einzuloggen mit database.py
from database import MaschinenDB

db = MaschinenDB(test_db)
db.connect()

print("\nVersuche Login mit 'admin' / 'admin123'...")
benutzer = db.verify_login('admin', 'admin123')

if benutzer:
    print(f"✓ LOGIN ERFOLGREICH!")
    print(f"  ID: {benutzer['id']}")
    print(f"  Benutzer: {benutzer['username']}")
    print(f"  Name: {benutzer['name']} {benutzer['vorname']}")
    print(f"  Admin: {benutzer['is_admin']}")
    print(f"  Admin-Level: {benutzer['admin_level']}")
else:
    print(f"✗ LOGIN FEHLGESCHLAGEN!")
    
    # Debug: Was steht in der DB?
    print("\n=== DEBUG: Benutzer in DB ===")
    cursor = db.cursor
    cursor.execute("SELECT id, username, password_hash, is_admin, admin_level, aktiv FROM benutzer WHERE username='admin'")
    row = cursor.fetchone()
    if row:
        print(f"Gefundener Admin-User:")
        print(f"  ID: {row[0]}")
        print(f"  Username: {row[1]}")
        print(f"  Password-Hash in DB: {row[2]}")
        print(f"  Is_Admin: {row[3]}")
        print(f"  Admin_Level: {row[4]}")
        print(f"  Aktiv: {row[5]}")
        
        # Teste Hash
        test_hash = hashlib.sha256("admin123".encode('utf-8')).hexdigest()
        print(f"\n  Erwarteter Hash: {test_hash}")
        print(f"  Hashes identisch: {row[2] == test_hash}")
    else:
        print("KEIN Admin-User gefunden!")

db.close()
