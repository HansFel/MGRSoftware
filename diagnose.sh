#!/bin/bash
# Diagnose: Was ist in der Datenbank?

echo "🔍 DIAGNOSE - Datenbank prüfen"
echo ""

cd ~/maschinengemeinschaft

docker exec maschinengemeinschaft python -c "
import sqlite3

conn = sqlite3.connect('/data/maschinengemeinschaft.db')
cursor = conn.cursor()

# Spalten prüfen
print('📋 Spalten in benutzer-Tabelle:')
cursor.execute('PRAGMA table_info(benutzer)')
for col in cursor.fetchall():
    print(f'   - {col[1]} ({col[2]})')

print('')
print('👥 Alle Benutzer:')
cursor.execute('SELECT id, name, vorname, username, password_hash, is_admin FROM benutzer')
users = cursor.fetchall()

for u in users:
    print(f'   ID: {u[0]}')
    print(f'   Name: {u[1]} {u[2]}')
    print(f'   Username: {u[3] or \"(KEIN USERNAME!)\"}')
    print(f'   Passwort-Hash: {u[4][:20] if u[4] else \"(KEIN PASSWORT!)\"}...')
    print(f'   Admin: {\"Ja\" if u[5] else \"Nein\"}')
    print('')

conn.close()
"
