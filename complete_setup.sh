#!/bin/bash
# Komplettes Setup: Admin-Funktion + Passwort setzen

echo "🔄 SCHRITT 1: Migration und Container neu bauen"
cd ~/maschinengemeinschaft

# Container stoppen
docker compose down

# Container neu bauen
docker compose build --no-cache
docker compose up -d

echo "⏳ Warte 10 Sekunden bis Container läuft..."
sleep 10

echo ""
echo "🔄 SCHRITT 2: Datenbank migrieren (is_admin Spalte)"
docker exec maschinengemeinschaft python -c "
import sqlite3
conn = sqlite3.connect('/data/maschinengemeinschaft.db')
cursor = conn.cursor()
# Prüfe ob Spalte existiert
cursor.execute('PRAGMA table_info(benutzer)')
columns = [col[1] for col in cursor.fetchall()]
if 'is_admin' not in columns:
    cursor.execute('ALTER TABLE benutzer ADD COLUMN is_admin BOOLEAN DEFAULT 0')
    conn.commit()
    print('✅ is_admin Spalte hinzugefügt')
else:
    print('ℹ️  is_admin Spalte existiert bereits')
conn.close()
"

echo ""
echo "🔄 SCHRITT 3: Admin-Rechte setzen"
docker exec maschinengemeinschaft python -c "
import sqlite3
conn = sqlite3.connect('/data/maschinengemeinschaft.db')
cursor = conn.cursor()
cursor.execute('UPDATE benutzer SET is_admin = 1 WHERE id = 1')
conn.commit()
conn.close()
print('✅ Admin-Rechte gesetzt')
"

echo ""
echo "🔄 SCHRITT 4: Passwort setzen"
docker exec maschinengemeinschaft python -c "
from database import MaschinenDBContext
import hashlib

password = 'Rattenberg@57'
password_hash = hashlib.sha256(password.encode()).hexdigest()

with MaschinenDBContext('/data/maschinengemeinschaft.db') as db:
    db.cursor.execute('UPDATE benutzer SET password_hash = ? WHERE id = 1', (password_hash,))
    db.conn.commit()
    print('✅ Passwort gesetzt')
"

echo ""
echo "✅ SETUP ABGESCHLOSSEN!"
echo ""
echo "🔐 Login-Daten:"
echo "   URL: http://192.168.178.36:5000"
echo "   Username: Felfer"
echo "   Passwort: Rattenberg@57"
echo ""
echo "Nach dem Login sollten Sie das Admin-Menü sehen."
