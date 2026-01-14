# Deployment-Verzeichnis für Maschinengemeinschaft
# Alle Dateien für Docker/Raspberry Pi Installation

## Inhalt

### Hauptanwendung
- `web_app.py` - Flask Web-Anwendung
- `database.py` - Datenbankzugriff
- `schema.sql` - Datenbankschema
- `requirements.txt` - Python-Abhängigkeiten

### Docker
- `Dockerfile` - Docker Image Definition
- `docker-compose.yml` - Docker Compose Konfiguration
- `nginx.conf` - Nginx Reverse Proxy Konfiguration
- `nginx_http_only.conf` - Nginx ohne HTTPS

### Migrationen
- `migrate_treibstoffkosten.py` - Treibstoffkosten pro Benutzer
- `migrate_abrechnung.py` - Abrechnungssystem
- `migrate_maschinen_columns.py` - Neue Maschinenspalten
- `migrate_admin.py` - Admin-System
- `migrate_db.py` - Allgemeine DB-Migrationen
- `migrate_rentabilitaet.py` - Rentabilitätsrechnung
- `migrate_aufwendungen.py` - Maschinenaufwendungen
- `migrate_reservierungen.py` - Reservierungssystem
- `migrate_gemeinschaften.py` - Gemeinschaftsverwaltung

### Setup/Update Scripts
- `update_raspberry.sh` - Standard Update-Script
- `update_raspberry_vollstaendig.sh` - Vollständiges Update mit allen Migrationen
- `setup_admin_raspberry.sh` - Admin-Setup
- `setup_https.sh` - HTTPS Konfiguration

### Web-Interface
- `templates/` - HTML Templates (Jinja2)
- `static/` - CSS, JavaScript, Bilder

## Installation auf Raspberry Pi

### Alle Dateien übertragen:
```bash
scp -r deployment/* heizpi@192.168.x.x:~/maschinengemeinschaft/
```

### Auf Raspberry Pi:
```bash
ssh heizpi@192.168.x.x
cd ~/maschinengemeinschaft
chmod +x *.sh
./update_raspberry_vollstaendig.sh
```

## Neue Features in diesem Release

- ✅ Treibstoffpreis-Eingabe pro Benutzer
- ✅ Maschinenreservierungen (Datum/Uhrzeit)
- ✅ Reservierungsübersicht im Dashboard
- ✅ Stornierungsfunktion für Reservierungen
- ✅ Jährliche Aufwendungen (Wartung, Reparatur, Versicherung)
- ✅ Erweiterte Rentabilitätsrechnung mit Aufwendungen
- ✅ PDF-Export für Rentabilitätsberichte
- ✅ "Forderungen" statt "Schulden" Terminologie

## Voraussetzungen

- Docker & Docker Compose
- Python 3.11+
- SQLite3

## Port

Die Anwendung läuft auf Port 5000 (intern) und kann über Nginx auf Port 80/443 bereitgestellt werden.
