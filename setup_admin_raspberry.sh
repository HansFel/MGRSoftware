#!/bin/bash
# Admin-Setup für Raspberry Pi

echo "🔄 Schritt 1: Datenbank migrieren..."
cd ~/maschinengemeinschaft
docker exec -it maschinengemeinschaft python migrate_admin.py

echo ""
echo "🔄 Schritt 2: Container neu bauen..."
docker compose down
docker compose build --no-cache
docker compose up -d

echo ""
echo "⏳ Warte 5 Sekunden bis Container gestartet ist..."
sleep 5

echo ""
echo "🔄 Schritt 3: Admin-Benutzer erstellen..."
docker exec -it maschinengemeinschaft python -c "
from database import MaschinenDBContext
with MaschinenDBContext('/data/maschinengemeinschaft.db') as db:
    db.update_benutzer(1, is_admin=True)
    print('✅ Benutzer ID 1 ist jetzt Administrator')
"

echo ""
echo "✅ Setup abgeschlossen!"
echo ""
echo "🔐 Admin-Zugang:"
echo "   URL: http://192.168.178.36:5000"
echo "   Username: Felfer"
echo "   Passwort: Ihr gesetztes Passwort"
echo ""
echo "Nach dem Login sehen Sie das Admin-Menü oben rechts."
