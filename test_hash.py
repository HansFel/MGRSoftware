import hashlib
import sys
import os

# Test Hash-Übereinstimmung
password = "admin123"

# Launcher-Methode
launcher_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
print(f"Launcher Hash: {launcher_hash}")

# Database-Methode importieren
sys.path.insert(0, os.path.dirname(__file__))
from database import MaschinenDB

db = MaschinenDB('test_hash.db')
db_hash = db._hash_password(password)
print(f"Database Hash: {db_hash}")

print(f"\nHashes stimmen überein: {launcher_hash == db_hash}")

# Test mit echter DB
import sqlite3
test_db = 'test_verify.db'

# Schema erstellen
with open('schema.sql', 'r', encoding='utf-8') as f:
    schema = f.read()
    
conn = sqlite3.connect(test_db)
cursor = conn.cursor()
cursor.executescript(schema)

# Admin mit Launcher-Methode erstellen
cursor.execute("""
    INSERT INTO benutzer (name, vorname, username, password_hash, is_admin, admin_level, aktiv)
    VALUES ('Admin', 'System', 'admin', ?, 1, 2, 1)
""", (launcher_hash,))
conn.commit()
conn.close()

# Mit Database-Klasse verifizieren
db = MaschinenDB(test_db)
db.connect()
benutzer = db.verify_login('admin', 'admin123')

if benutzer:
    print(f"\n✓ LOGIN ERFOLGREICH!")
    print(f"  Benutzer: {benutzer['username']}")
    print(f"  Admin-Level: {benutzer['admin_level']}")
else:
    print(f"\n✗ LOGIN FEHLGESCHLAGEN!")
    
# Aufräumen
os.remove(test_db)
if os.path.exists('test_hash.db'):
    os.remove('test_hash.db')
