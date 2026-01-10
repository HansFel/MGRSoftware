#!/bin/bash
# Admin-Benutzer direkt in Docker erstellen

echo "🔐 Erstelle Admin-Benutzer im Docker-Container"
echo ""

cd ~/maschinengemeinschaft

docker exec maschinengemeinschaft python -c "
from database import MaschinenDBContext
import sys

try:
    with MaschinenDBContext('/data/maschinengemeinschaft.db') as db:
        # Neuen Admin-Benutzer erstellen
        db.add_benutzer(
            name='Admin',
            vorname='System',
            username='admin',
            password='Rattenberg@57',
            is_admin=True
        )
        print('✅ Neuer Admin-Benutzer erstellt!')
        print('')
        print('🔐 Login-Daten:')
        print('   URL: http://192.168.178.36:5000')
        print('   Username: admin')
        print('   Passwort: Rattenberg@57')
        print('')
        print('Nach dem Login sehen Sie das Admin-Menü ⚙️')
        
except Exception as e:
    if 'UNIQUE constraint failed' in str(e):
        print('ℹ️  Benutzer \"admin\" existiert bereits')
        print('')
        print('Setze Passwort neu...')
        
        import hashlib
        import sqlite3
        conn = sqlite3.connect('/data/maschinengemeinschaft.db')
        cursor = conn.cursor()
        
        password_hash = hashlib.sha256('Rattenberg@57'.encode()).hexdigest()
        cursor.execute('UPDATE benutzer SET password_hash = ?, is_admin = 1 WHERE username = ?', 
                      (password_hash, 'admin'))
        conn.commit()
        conn.close()
        
        print('✅ Passwort für \"admin\" neu gesetzt!')
        print('')
        print('🔐 Login: admin / Rattenberg@57')
    else:
        print(f'❌ Fehler: {e}')
        sys.exit(1)
"

echo ""
echo "Versuchen Sie jetzt den Login unter http://192.168.178.36:5000"
