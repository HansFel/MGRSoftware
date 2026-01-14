# Installationsanleitung - Maschinengemeinschaft Software

## Inhaltsverzeichnis
1. [Übersicht](#übersicht)
2. [Systemanforderungen](#systemanforderungen)
3. [Installation mit Docker (empfohlen)](#installation-mit-docker-empfohlen)
4. [Installation auf Raspberry Pi](#installation-auf-raspberry-pi)
5. [Manuelle Installation ohne Docker](#manuelle-installation-ohne-docker)
6. [HTTPS-Konfiguration](#https-konfiguration)
7. [Datenbankmigration](#datenbankmigration)
8. [Erste Schritte](#erste-schritte)
9. [Updates und Wartung](#updates-und-wartung)
10. [Problembehandlung](#problembehandlung)

---

## Übersicht

Die Maschinengemeinschaft-Software ist eine Flask-basierte Webanwendung zur Verwaltung von:
- Maschineneinsätzen
- Maschinenreservierungen
- Rentabilitätsrechnungen
- Gemeinschaftsabrechnungen

**Empfohlene Installation:** Docker-Container für einfache Verwaltung und Updates

---

## Systemanforderungen

### Minimum

**Hardware:**
- CPU: 1 Core (Raspberry Pi 3 oder höher)
- RAM: 512 MB
- Speicher: 2 GB frei

**Software:**
- Linux (Debian, Ubuntu, Raspberry Pi OS)
- Docker 20.10+ und Docker Compose 2.0+
- Nginx (als Reverse Proxy)

### Empfohlen

**Hardware:**
- CPU: 2+ Cores (Raspberry Pi 4)
- RAM: 2 GB
- Speicher: 8 GB frei (für Logs und Backups)

**Software:**
- Debian 11/12 oder Ubuntu 22.04+
- Docker 24.0+
- Nginx mit SSL/TLS

**Netzwerk:**
- Statische IP-Adresse
- Port 80 (HTTP) oder 443 (HTTPS)
- Zugriff aus lokalem Netzwerk

---

## Installation mit Docker (empfohlen)

### Schritt 1: Vorbereitung

```bash
# System aktualisieren
sudo apt update
sudo apt upgrade -y

# Docker installieren (falls noch nicht vorhanden)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Docker Compose installieren
sudo apt install docker-compose -y

# Neuanmeldung erforderlich für Docker-Gruppe
# Alternativ: newgrp docker
```

### Schritt 2: Dateien übertragen

```bash
# Arbeitsverzeichnis erstellen
sudo mkdir -p /opt/maschinengemeinschaft
cd /opt/maschinengemeinschaft

# Dateien aus deployment-Verzeichnis hierhin kopieren
# Möglichkeit A: Per SCP von lokalem Rechner
scp -r /pfad/zu/deployment/* benutzer@server:/opt/maschinengemeinschaft/

# Möglichkeit B: Git Repository klonen (falls vorhanden)
git clone <repository-url> .

# Berechtigung setzen
sudo chown -R $USER:$USER /opt/maschinengemeinschaft
```

### Schritt 3: Konfiguration anpassen

```bash
# docker-compose.yml prüfen und bei Bedarf anpassen
nano docker-compose.yml
```

**Wichtige Einstellungen in `docker-compose.yml`:**

```yaml
services:
  web:
    build: .
    ports:
      - "5000:5000"  # Ändern falls Port 5000 belegt
    volumes:
      - ./data:/app/data  # Datenbank-Persistenz
      - ./static:/app/static  # Statische Dateien
    environment:
      - FLASK_ENV=production
    restart: unless-stopped
```

### Schritt 4: Container starten

```bash
# Container bauen und starten
docker-compose up -d --build

# Status prüfen
docker-compose ps

# Logs anzeigen
docker-compose logs -f web
```

### Schritt 5: Datenbank initialisieren

```bash
# In den Container wechseln
docker-compose exec web bash

# Datenbank-Schema erstellen
python3 -c "from database import init_db; init_db()"

# Migrationen ausführen
python3 migrate_db.py
python3 migrate_abrechnung.py
python3 migrate_admin.py
python3 migrate_maschinen_columns.py
python3 migrate_aufwendungen.py
python3 migrate_reservierungen.py

# Container verlassen
exit
```

### Schritt 6: Admin-Benutzer anlegen

```bash
# Admin erstellen
docker-compose exec web python3 create_admin.py

# Eingaben (Beispiel):
# Benutzername: admin
# Passwort: [Ihr sicheres Passwort]
# Name: Administrator
# Vorname: System
```

### Schritt 7: Nginx als Reverse Proxy

```bash
# Nginx installieren
sudo apt install nginx -y

# Nginx-Konfiguration erstellen
sudo nano /etc/nginx/sites-available/maschinengemeinschaft
```

**Inhalt (HTTP-only):**

```nginx
server {
    listen 80;
    server_name maschinengemeinschaft.local;  # Anpassen!

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /opt/maschinengemeinschaft/static/;
        expires 30d;
    }
}
```

```bash
# Konfiguration aktivieren
sudo ln -s /etc/nginx/sites-available/maschinengemeinschaft /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Optional: Default-Site entfernen

# Nginx-Konfiguration testen
sudo nginx -t

# Nginx neu starten
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### Schritt 8: Testen

```bash
# Browser öffnen und aufrufen:
http://[server-ip]

# Oder mit Hostname (falls DNS/Hosts konfiguriert):
http://maschinengemeinschaft.local

# Login mit Admin-Zugangsdaten
```

---

## Installation auf Raspberry Pi

### Besonderheiten

Raspberry Pi hat ARM-Architektur → Docker-Images werden beim Build automatisch angepasst

### Schnellinstallation

```bash
# 1. Raspberry Pi OS aktualisieren
sudo apt update && sudo apt upgrade -y

# 2. Docker installieren
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker pi

# 3. Neustart
sudo reboot

# 4. Nach Neustart: Dateien übertragen
cd /home/pi
mkdir maschinengemeinschaft
cd maschinengemeinschaft

# Von lokalem Rechner aus:
scp -r deployment/* pi@raspberrypi.local:/home/pi/maschinengemeinschaft/

# 5. Container starten
docker-compose up -d --build

# 6. Datenbank initialisieren (siehe Schritt 5 oben)

# 7. Admin anlegen (siehe Schritt 6 oben)

# 8. Nginx installieren und konfigurieren (siehe Schritt 7 oben)
```

### Raspberry Pi-spezifische Skripte

Das Projekt enthält fertige Skripte für Raspberry Pi:

```bash
# Setup-Skript ausführen
chmod +x setup_admin_raspberry.sh
./setup_admin_raspberry.sh

# Oder: Docker-spezifisches Setup
chmod +x start.sh
./start.sh
```

### Performance-Optimierung

```bash
# Docker-Logs begrenzen (verhindert Speicherprobleme)
sudo nano /etc/docker/daemon.json
```

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

```bash
sudo systemctl restart docker
```

---

## Manuelle Installation ohne Docker

### Schritt 1: Python installieren

```bash
# Python 3.9+ und pip
sudo apt install python3 python3-pip python3-venv -y

# Systemabhängigkeiten für ReportLab (PDF-Export)
sudo apt install gcc libjpeg-dev zlib1g-dev libfreetype6-dev -y
```

### Schritt 2: Anwendung einrichten

```bash
# Arbeitsverzeichnis erstellen
sudo mkdir -p /opt/maschinengemeinschaft
cd /opt/maschinengemeinschaft

# Dateien übertragen (wie oben beschrieben)

# Virtuelle Umgebung erstellen
python3 -m venv venv
source venv/bin/activate

# Abhängigkeiten installieren
pip install -r requirements.txt
```

### Schritt 3: Datenbank initialisieren

```bash
# Datenverzeichnis erstellen
mkdir -p data

# Schema erstellen
python3 -c "from database import init_db; init_db()"

# Migrationen ausführen
python3 migrate_db.py
python3 migrate_abrechnung.py
python3 migrate_admin.py
python3 migrate_maschinen_columns.py
python3 migrate_aufwendungen.py
python3 migrate_reservierungen.py
```

### Schritt 4: Admin anlegen

```bash
python3 create_admin.py
```

### Schritt 5: Systemd-Service erstellen

```bash
sudo nano /etc/systemd/system/maschinengemeinschaft.service
```

**Inhalt:**

```ini
[Unit]
Description=Maschinengemeinschaft Web Application
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/maschinengemeinschaft
Environment="PATH=/opt/maschinengemeinschaft/venv/bin"
ExecStart=/opt/maschinengemeinschaft/venv/bin/python3 web_app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Service aktivieren und starten
sudo systemctl daemon-reload
sudo systemctl enable maschinengemeinschaft
sudo systemctl start maschinengemeinschaft

# Status prüfen
sudo systemctl status maschinengemeinschaft
```

### Schritt 6: Nginx konfigurieren

Siehe Schritt 7 der Docker-Installation (identisch)

---

## HTTPS-Konfiguration

### Variante A: Let's Encrypt (Certbot)

**Voraussetzungen:**
- Öffentlich erreichbarer Server mit Domainnamen
- Port 80 und 443 offen

```bash
# Certbot installieren
sudo apt install certbot python3-certbot-nginx -y

# SSL-Zertifikat erstellen
sudo certbot --nginx -d ihre-domain.de

# Automatische Erneuerung testen
sudo certbot renew --dry-run
```

### Variante B: Selbstsigniertes Zertifikat (lokales Netzwerk)

```bash
# Zertifikat erstellen
sudo mkdir -p /etc/nginx/ssl
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/maschinengemeinschaft.key \
  -out /etc/nginx/ssl/maschinengemeinschaft.crt

# Nginx-Konfiguration anpassen
sudo nano /etc/nginx/sites-available/maschinengemeinschaft
```

**HTTPS-Konfiguration:**

```nginx
server {
    listen 80;
    server_name maschinengemeinschaft.local;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name maschinengemeinschaft.local;

    ssl_certificate /etc/nginx/ssl/maschinengemeinschaft.crt;
    ssl_certificate_key /etc/nginx/ssl/maschinengemeinschaft.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }

    location /static/ {
        alias /opt/maschinengemeinschaft/static/;
        expires 30d;
    }
}
```

```bash
sudo nginx -t
sudo systemctl reload nginx
```

**Hinweis:** Selbstsignierte Zertifikate erzeugen Browser-Warnungen, sind aber für lokale Netzwerke ausreichend.

### Variante C: Bestehendes HTTPS mit Nginx

Falls bereits ein Nginx mit SSL läuft:

```bash
# Neue Location hinzufügen
sudo nano /etc/nginx/sites-available/default  # Oder Ihre SSL-Config
```

**Location-Block hinzufügen:**

```nginx
location /maschinen/ {
    proxy_pass http://localhost:5000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto https;
}
```

Siehe auch: `HTTPS_MIT_BESTEHENDEM_NGINX.md` im deployment-Verzeichnis

---

## Datenbankmigration

### Neue Migrationen ausführen

Nach Updates müssen möglicherweise neue Migrationsskripte ausgeführt werden:

```bash
# Mit Docker:
docker-compose exec web python3 migrate_neue_funktion.py

# Ohne Docker:
cd /opt/maschinengemeinschaft
source venv/bin/activate
python3 migrate_neue_funktion.py
```

### Vorhandene Migrationen

Folgende Migrationen sollten in dieser Reihenfolge ausgeführt werden:

1. `migrate_db.py` - Basis-Schema
2. `migrate_abrechnung.py` - Abrechnungsfunktionen
3. `migrate_admin.py` - Admin-Funktionen
4. `migrate_maschinen_columns.py` - Erweiterte Maschinenfelder
5. `migrate_aufwendungen.py` - Aufwendungstabelle
6. `migrate_reservierungen.py` - Reservierungssystem

### Migrationsstatus prüfen

```bash
# Tabellen anzeigen
sqlite3 data/maschinengemeinschaft.db ".tables"

# Schema einer Tabelle anzeigen
sqlite3 data/maschinengemeinschaft.db ".schema maschineneinsaetze"
```

---

## Erste Schritte

### 1. Admin-Benutzer anlegen

```bash
docker-compose exec web python3 create_admin.py
# ODER
python3 create_admin.py
```

### 2. Anmelden

- Browser öffnen: `http://[server-ip]`
- Mit Admin-Zugangsdaten anmelden

### 3. Gemeinschaft anlegen

- Admin → Gemeinschaften → Neue Gemeinschaft
- Name eingeben (z.B. "Maschinenring Musterdorf")

### 4. Benutzer anlegen

- Admin → Benutzer → Neuer Benutzer
- Benutzerdaten eingeben
- Benutzer der Gemeinschaft zuweisen

### 5. Maschine anlegen

- Admin → Maschinen → Neue Maschine
- Maschinendetails eingeben
- Gemeinschaft zuordnen

### 6. Einsatzzwecke anlegen

- Admin → Einsatzzwecke → Neuer Einsatzzweck
- Zweck eingeben (z.B. "Pflügen", "Mähen")

### 7. Testen

- Als normaler Benutzer anmelden
- Maschine im Dashboard sichtbar?
- Einsatz erfassen testen
- Reservierung erstellen testen

---

## Updates und Wartung

### Anwendung aktualisieren

**Mit Docker:**

```bash
cd /opt/maschinengemeinschaft

# Dateien aktualisieren (Git oder manuell)
git pull  # Oder neue Dateien kopieren

# Container neu bauen und starten
docker-compose down
docker-compose up -d --build

# Neue Migrationen ausführen
docker-compose exec web python3 migrate_neue_funktion.py
```

**Ohne Docker:**

```bash
cd /opt/maschinengemeinschaft
source venv/bin/activate

# Dateien aktualisieren
git pull  # Oder neue Dateien kopieren

# Abhängigkeiten aktualisieren
pip install -r requirements.txt --upgrade

# Neue Migrationen ausführen
python3 migrate_neue_funktion.py

# Service neu starten
sudo systemctl restart maschinengemeinschaft
```

### Datensicherung

**Datenbank sichern:**

```bash
# Mit Docker:
docker-compose exec web sqlite3 /app/data/maschinengemeinschaft.db ".backup '/app/data/backup.db'"
docker cp maschinengemeinschaft_web_1:/app/data/backup.db ./backup_$(date +%Y%m%d).db

# Ohne Docker:
sqlite3 /opt/maschinengemeinschaft/data/maschinengemeinschaft.db ".backup '/opt/maschinengemeinschaft/data/backup.db'"
cp /opt/maschinengemeinschaft/data/backup.db ~/backups/backup_$(date +%Y%m%d).db
```

**Automatisches Backup mit Cronjob:**

```bash
crontab -e
```

```cron
# Tägliches Backup um 2 Uhr nachts
0 2 * * * /home/pi/maschinengemeinschaft/backup.sh
```

**backup.sh erstellen:**

```bash
#!/bin/bash
BACKUP_DIR="/home/pi/backups"
mkdir -p $BACKUP_DIR
docker-compose -f /home/pi/maschinengemeinschaft/docker-compose.yml exec -T web \
  sqlite3 /app/data/maschinengemeinschaft.db ".backup '/app/data/backup.db'"
docker cp maschinengemeinschaft_web_1:/app/data/backup.db \
  $BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).db

# Alte Backups löschen (älter als 30 Tage)
find $BACKUP_DIR -name "backup_*.db" -mtime +30 -delete
```

```bash
chmod +x backup.sh
```

### Datenbank wiederherstellen

```bash
# Mit Docker:
docker-compose down
docker cp backup_20250115.db maschinengemeinschaft_web_1:/app/data/maschinengemeinschaft.db
docker-compose up -d

# Ohne Docker:
sudo systemctl stop maschinengemeinschaft
cp backup_20250115.db /opt/maschinengemeinschaft/data/maschinengemeinschaft.db
sudo systemctl start maschinengemeinschaft
```

### Log-Dateien

**Docker-Logs:**

```bash
# Logs anzeigen
docker-compose logs -f web

# Logs der letzten 100 Zeilen
docker-compose logs --tail=100 web

# Logs speichern
docker-compose logs web > logs_$(date +%Y%m%d).txt
```

**Systemd-Logs (ohne Docker):**

```bash
sudo journalctl -u maschinengemeinschaft -f
sudo journalctl -u maschinengemeinschaft --since "1 hour ago"
```

---

## Problembehandlung

### Anwendung startet nicht

**Docker:**

```bash
# Container-Status prüfen
docker-compose ps

# Logs prüfen
docker-compose logs web

# Container neu starten
docker-compose restart web

# Container komplett neu bauen
docker-compose down
docker-compose up -d --build
```

**Ohne Docker:**

```bash
# Service-Status prüfen
sudo systemctl status maschinengemeinschaft

# Logs prüfen
sudo journalctl -u maschinengemeinschaft -n 50

# Service neu starten
sudo systemctl restart maschinengemeinschaft

# Manuelle Ausführung zum Debuggen
cd /opt/maschinengemeinschaft
source venv/bin/activate
python3 web_app.py
```

### Port bereits belegt

```bash
# Port 5000 prüfen
sudo lsof -i :5000

# Prozess beenden
sudo kill -9 [PID]

# Oder: Port in docker-compose.yml ändern
nano docker-compose.yml
# Zeile ändern: "5001:5000"
docker-compose up -d
```

### Datenbank-Fehler

```bash
# Datenbankintegrität prüfen
sqlite3 data/maschinengemeinschaft.db "PRAGMA integrity_check;"

# Datenbank reparieren (falls beschädigt)
sqlite3 data/maschinengemeinschaft.db ".recover" | sqlite3 data/maschinengemeinschaft_recovered.db

# Backup wiederherstellen
cp data/backup.db data/maschinengemeinschaft.db
```

### Nginx-Fehler

```bash
# Nginx-Konfiguration testen
sudo nginx -t

# Nginx-Fehlerlog prüfen
sudo tail -f /var/log/nginx/error.log

# Nginx neu starten
sudo systemctl restart nginx
```

### Berechtigungsprobleme

```bash
# Docker: Datenverzeichnis-Berechtigung
sudo chown -R 1000:1000 /opt/maschinengemeinschaft/data

# Ohne Docker: www-data Berechtigung
sudo chown -R www-data:www-data /opt/maschinengemeinschaft/data
```

### Python-Modul fehlt

```bash
# Docker: Container neu bauen
docker-compose down
docker-compose up -d --build

# Ohne Docker: Abhängigkeiten neu installieren
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

### Speicherplatz voll (Raspberry Pi)

```bash
# Speicherplatz prüfen
df -h

# Docker-Logs begrenzen (siehe Performance-Optimierung)

# Alte Logs löschen
docker-compose down
sudo rm -rf /var/lib/docker/containers/*/*-json.log
docker-compose up -d

# Nicht verwendete Docker-Ressourcen löschen
docker system prune -a
```

### Anwendung läuft langsam

**Ursachen:**
- Raspberry Pi überlastet
- Zu viele Docker-Container
- Datenbank zu groß

**Lösungen:**

```bash
# Datenbank optimieren
sqlite3 data/maschinengemeinschaft.db "VACUUM;"

# Alte Einsätze archivieren (manuell, falls gewünscht)

# Swap-Speicher erhöhen (Raspberry Pi)
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

---

## Netzwerkkonfiguration

### Statische IP-Adresse (Raspberry Pi)

```bash
sudo nano /etc/dhcpcd.conf
```

```conf
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8
```

```bash
sudo reboot
```

### Hostname ändern

```bash
sudo nano /etc/hostname
# Hostname eingeben: maschinengemeinschaft

sudo nano /etc/hosts
# 127.0.1.1 maschinengemeinschaft

sudo reboot
```

### Firewall konfigurieren (UFW)

```bash
sudo apt install ufw -y

# Port 80 (HTTP) öffnen
sudo ufw allow 80/tcp

# Port 443 (HTTPS) öffnen
sudo ufw allow 443/tcp

# SSH offen lassen
sudo ufw allow 22/tcp

# Firewall aktivieren
sudo ufw enable
sudo ufw status
```

---

## Diagnose-Skripte

Das Projekt enthält Diagnose-Skripte:

```bash
# Raspberry Pi Diagnose
chmod +x diagnose_raspi.sh
./diagnose_raspi.sh

# Allgemeine Diagnose
chmod +x diagnose.sh
./diagnose.sh
```

Diese Skripte prüfen:
- Docker-Installation
- Container-Status
- Datenbank-Status
- Netzwerk-Konfiguration
- Speicherplatz
- Logs

---

## Checkliste nach Installation

- [ ] Anwendung erreichbar über Browser
- [ ] Admin-Benutzer kann sich anmelden
- [ ] Gemeinschaft angelegt
- [ ] Normaler Benutzer angelegt
- [ ] Maschine angelegt und sichtbar
- [ ] Einsatz kann erfasst werden
- [ ] Reservierung kann erstellt werden
- [ ] PDF-Export funktioniert
- [ ] Nginx läuft und leitet weiter
- [ ] HTTPS funktioniert (optional)
- [ ] Backup-Strategie eingerichtet
- [ ] Firewall konfiguriert
- [ ] Dokumentation für Benutzer bereitgestellt

---

## Support und Weiterentwicklung

Bei Problemen oder Fragen:
1. Prüfen Sie die Logs
2. Konsultieren Sie diese Anleitung
3. Nutzen Sie die Diagnose-Skripte
4. Dokumentieren Sie das Problem genau

**Version:** 2.0 (Januar 2026)

---

## Weitere Dokumentation

- `BENUTZERANLEITUNG.md` - Anleitung für Endbenutzer
- `ADMIN_HANDBUCH.md` - Administratorenhandbuch
- `README.md` - Projektübersicht
- `SCHNELLSTART.md` - Schnellstart-Anleitung
- `HTTPS_ANLEITUNG.md` - HTTPS-Konfiguration
- `RASPBERRY_DOCKER.md` - Raspberry Pi Docker-Setup
