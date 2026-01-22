import sqlite3
import os

db_path = "test_maschinengemeinschaft.db"

# Lösche alte Test-DB falls vorhanden
if os.path.exists(db_path):
    os.remove(db_path)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()


with open('schema.sql', 'r', encoding='utf-8') as f:
    schema = f.read()
    cursor.executescript(schema)


# Admin-Benutzer anlegen
import hashlib
def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

admin_username = "admin"
admin_password = "admin123"
admin_hash = hash_password(admin_password)

# Vorherigen Admin löschen, falls vorhanden
cursor.execute("DELETE FROM benutzer WHERE username = ?", (admin_username,))

cursor.execute("""
    INSERT INTO benutzer (name, vorname, username, password_hash, is_admin, admin_level, aktiv)
    VALUES (?, ?, ?, ?, 1, 2, 1)
""", ("Administrator", "", admin_username, admin_hash))

conn.commit()
conn.close()

print(f"✓ Test-Datenbank erstellt: {db_path}")
print("Ein Start-Administrator wurde angelegt:")
print(f"Benutzername: {admin_username}")
print(f"Passwort: {admin_password}")