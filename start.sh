#!/bin/bash

# Initialisierungsskript für Docker Container
# Wird beim ersten Start ausgeführt

DB_FILE="/data/maschinengemeinschaft.db"

# Prüfen ob Datenbank existiert
if [ ! -f "$DB_FILE" ]; then
    echo "📦 Datenbank nicht gefunden. Initialisiere neue Datenbank..."
    python -c "
from database import MaschinenDBContext
import os
db_path = os.environ.get('DB_PATH', '/data/maschinengemeinschaft.db')
with MaschinenDBContext(db_path) as db:
    db.init_database()
print('✅ Datenbank initialisiert!')
"
else
    echo "✅ Datenbank gefunden: $DB_FILE"
fi

# Webserver starten
echo "🚀 Starte Webserver..."
exec python web_app.py
