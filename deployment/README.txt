================================================================================
   MASCHINENGEMEINSCHAFT - SERVER DEPLOYMENT
================================================================================

Dieses Verzeichnis enthält alle Dateien für das Server-Deployment.


SCHNELLSTART
============

1. Diesen Ordner auf den Ubuntu-Server kopieren:

   scp -r deployment/* benutzer@server-ip:/tmp/mgr-setup/


2. Auf dem Server einloggen:

   ssh benutzer@server-ip


3. Setup-Script ausführen:

   cd /tmp/mgr-setup
   chmod +x setup_server.sh
   sudo ./setup_server.sh


4. Nach dem Setup - Dateien in App-Verzeichnis verschieben:

   sudo cp -r templates static web_app.py database.py schema*.sql migrate_to_postgresql.py /opt/maschinengemeinschaft/
   sudo chown -R mgr:mgr /opt/maschinengemeinschaft/


5. Datenbank migrieren (optional, wenn SQLite-Daten vorhanden):

   cd /opt/maschinengemeinschaft
   sudo -u mgr bash
   source .venv/bin/activate
   source .env
   python migrate_to_postgresql.py


6. Service starten:

   sudo systemctl start maschinengemeinschaft
   sudo systemctl status maschinengemeinschaft


DATEIEN
=======

setup_server.sh          - Automatisches Server-Setup (PostgreSQL, Nginx, etc.)
upload_to_server.bat     - Windows-Script zum Hochladen
migrate_to_postgresql.py - Migration SQLite -> PostgreSQL
schema.sql               - SQLite Datenbank-Schema
schema_postgresql.sql    - PostgreSQL Datenbank-Schema
web_app.py               - Flask Webanwendung
database.py              - Datenbank-Modul
templates/               - HTML-Templates
static/                  - CSS, JavaScript, Bilder


VORAUSSETZUNGEN
===============

- Ubuntu Server 20.04, 22.04 oder 24.04
- Root-Zugang (sudo)
- Internetverbindung (für Paket-Installation)


NACH DER INSTALLATION
=====================

Zugriff:        http://SERVER-IP
Admin-Login:    admin / admin123  (PASSWORT ÄNDERN!)

Befehle:
  Status:       sudo systemctl status maschinengemeinschaft
  Neustart:     sudo systemctl restart maschinengemeinschaft
  Logs:         sudo journalctl -u maschinengemeinschaft -f
  Backup:       sudo /usr/local/bin/backup-maschinengemeinschaft.sh

Zugangsdaten:   /root/maschinengemeinschaft-credentials.txt


SUPPORT
=======

Bei Fragen: Dokumentation in docs/system/POSTGRESQL_INSTALLATION.md

================================================================================
