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

conn.commit()
conn.close()

print(f"✓ Test-Datenbank erstellt: {db_path}")
print("Login: admin / admin123")