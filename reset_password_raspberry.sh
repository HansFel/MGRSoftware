#!/bin/bash
# Passwort auf Raspberry Pi neu setzen

echo "🔐 Passwort zurücksetzen für Benutzer Felfer"
echo ""

cd ~/maschinengemeinschaft

docker exec -it maschinengemeinschaft python -c "
from database import MaschinenDBContext

# Neues Passwort hier eingeben:
new_password = 'Rattenberg@57'  # Ändern Sie dies bei Bedarf

with MaschinenDBContext('/data/maschinengemeinschaft.db') as db:
    db.update_password(1, new_password)
    print('✅ Passwort für Benutzer ID 1 (Felfer) wurde neu gesetzt!')
    print('')
    print('🔐 Neue Login-Daten:')
    print('   Username: Felfer')
    print('   Passwort: ' + new_password)
"

echo ""
echo "Sie können sich jetzt unter http://192.168.178.36:5000 anmelden."
