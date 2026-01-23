# PostgreSQL Installation auf Ubuntu-Server

## Voraussetzungen

- Ubuntu Server 20.04, 22.04 oder 24.04
- Root- oder sudo-Zugang
- SSH-Zugang zum Server

---

## Schritt 1: PostgreSQL installieren

```bash
# System aktualisieren
sudo apt update && sudo apt upgrade -y

# PostgreSQL installieren
sudo apt install postgresql postgresql-contrib -y

# Prüfen ob PostgreSQL läuft
sudo systemctl status postgresql
```

**Erwartete Ausgabe:**
```
● postgresql.service - PostgreSQL RDBMS
     Active: active (exited)
```

---

## Schritt 2: Datenbank und Benutzer erstellen

```bash
# Als postgres-Benutzer anmelden und Datenbank erstellen
sudo -u postgres psql << 'EOF'
-- Datenbank erstellen
CREATE DATABASE maschinengemeinschaft;

-- Benutzer erstellen (PASSWORT ÄNDERN!)
CREATE USER mgr_user WITH ENCRYPTED PASSWORD 'IhrSicheresPasswort123!';

-- Berechtigungen vergeben
GRANT ALL PRIVILEGES ON DATABASE maschinengemeinschaft TO mgr_user;
ALTER DATABASE maschinengemeinschaft OWNER TO mgr_user;

-- Auf neue Datenbank wechseln und Schema-Rechte vergeben
\c maschinengemeinschaft
GRANT ALL ON SCHEMA public TO mgr_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mgr_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mgr_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO mgr_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO mgr_user;

\q
EOF
```

**Verbindung testen:**
```bash
psql -U mgr_user -d maschinengemeinschaft -h localhost -c "SELECT version();"
# Passwort eingeben wenn gefragt
```

---

## Schritt 3: Fernzugriff konfigurieren (Optional)

> **Nur nötig wenn die App auf einem anderen Server läuft!**

### 3.1 PostgreSQL auf alle Adressen lauschen lassen

```bash
# PostgreSQL-Version herausfinden
ls /etc/postgresql/

# Config bearbeiten (Version anpassen!)
sudo nano /etc/postgresql/16/main/postgresql.conf
```

**Ändern Sie:**
```
#listen_addresses = 'localhost'
```
**zu:**
```
listen_addresses = '*'
```

### 3.2 Authentifizierung für Remote-Zugriff erlauben

```bash
sudo nano /etc/postgresql/16/main/pg_hba.conf
```

**Am Ende hinzufügen:**
```
# Remote-Zugriff für mgr_user
host    maschinengemeinschaft    mgr_user    0.0.0.0/0    md5
```

**Oder für ein bestimmtes Netzwerk (sicherer):**
```
# Nur lokales Netzwerk
host    maschinengemeinschaft    mgr_user    192.168.178.0/24    md5
```

### 3.3 PostgreSQL neu starten

```bash
sudo systemctl restart postgresql
```

### 3.4 Firewall öffnen (falls aktiv)

```bash
sudo ufw allow 5432/tcp
```

---

## Schritt 4: Python-Umgebung vorbereiten

```bash
# Python und pip installieren (falls nicht vorhanden)
sudo apt install python3 python3-pip python3-venv -y

# In das Projektverzeichnis wechseln
cd /pfad/zur/MGRSoftware

# Virtuelle Umgebung erstellen (empfohlen)
python3 -m venv .venv
source .venv/bin/activate

# PostgreSQL-Treiber installieren
pip install psycopg2-binary

# Weitere Abhängigkeiten installieren
pip install flask reportlab
```

---

## Schritt 5: Daten von SQLite migrieren

### Option A: Migration vom Server (SQLite-Datei hochladen)

```bash
# SQLite-Datenbank auf Server kopieren (vom lokalen PC)
scp data/maschinengemeinschaft.db benutzer@server:/pfad/zur/MGRSoftware/data/

# Auf dem Server: Migration durchführen
cd /pfad/zur/MGRSoftware
source .venv/bin/activate

export PG_HOST=localhost
export PG_DATABASE=maschinengemeinschaft
export PG_USER=mgr_user
export PG_PASSWORD='IhrSicheresPasswort123!'

python migrate_to_postgresql.py
```

### Option B: Migration vom lokalen PC (Remote-Zugriff)

```bash
# Auf dem lokalen PC (Windows PowerShell)
$env:PG_HOST="server-ip-adresse"
$env:PG_DATABASE="maschinengemeinschaft"
$env:PG_USER="mgr_user"
$env:PG_PASSWORD="IhrSicheresPasswort123!"

python migrate_to_postgresql.py
```

**Erwartete Ausgabe:**
```
============================================================
SQLite -> PostgreSQL Migration
============================================================
Quelle:  ./data/maschinengemeinschaft.db
Ziel:    postgresql://mgr_user@localhost:5432/maschinengemeinschaft
============================================================

Prüfe Voraussetzungen...
PostgreSQL-Verbindung OK: localhost:5432/maschinengemeinschaft
Alle Voraussetzungen erfüllt.

Erstelle PostgreSQL-Schema...
Schema erstellt.

Migriere Tabellen...
  Migriert: gemeinschaften (1 Zeilen)
  Migriert: benutzer (19 Zeilen)
  Migriert: einsatzzwecke (10 Zeilen)
  ...

============================================================
Migration abgeschlossen!
Insgesamt XXX Zeilen migriert.
============================================================

Verifiziere Migration...
  OK: gemeinschaften (1 Zeilen)
  OK: benutzer (19 Zeilen)
  ...

Verifizierung erfolgreich!
```

---

## Schritt 6: Anwendung mit PostgreSQL starten

### 6.1 Umgebungsvariablen setzen

**Temporär (für aktuelle Session):**
```bash
export DB_TYPE=postgresql
export PG_HOST=localhost
export PG_PORT=5432
export PG_DATABASE=maschinengemeinschaft
export PG_USER=mgr_user
export PG_PASSWORD='IhrSicheresPasswort123!'
```

**Permanent (empfohlen):**
```bash
# Datei erstellen
cat > /pfad/zur/MGRSoftware/.env << 'EOF'
DB_TYPE=postgresql
PG_HOST=localhost
PG_PORT=5432
PG_DATABASE=maschinengemeinschaft
PG_USER=mgr_user
PG_PASSWORD=IhrSicheresPasswort123!
EOF

# Vor dem Start laden
source /pfad/zur/MGRSoftware/.env
```

### 6.2 Anwendung starten

```bash
cd /pfad/zur/MGRSoftware
source .venv/bin/activate
source .env

python web_app.py
```

---

## Schritt 7: Systemd-Service einrichten (Optional)

Damit die Anwendung automatisch beim Serverstart läuft:

```bash
sudo nano /etc/systemd/system/maschinengemeinschaft.service
```

**Inhalt:**
```ini
[Unit]
Description=Maschinengemeinschaft Web-Anwendung
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/pfad/zur/MGRSoftware
Environment="DB_TYPE=postgresql"
Environment="PG_HOST=localhost"
Environment="PG_PORT=5432"
Environment="PG_DATABASE=maschinengemeinschaft"
Environment="PG_USER=mgr_user"
Environment="PG_PASSWORD=IhrSicheresPasswort123!"
ExecStart=/pfad/zur/MGRSoftware/.venv/bin/python web_app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Service aktivieren:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable maschinengemeinschaft
sudo systemctl start maschinengemeinschaft

# Status prüfen
sudo systemctl status maschinengemeinschaft
```

---

## Schritt 8: Backup einrichten

### Automatisches tägliches Backup

```bash
# Backup-Verzeichnis erstellen
sudo mkdir -p /var/backups/maschinengemeinschaft
sudo chown postgres:postgres /var/backups/maschinengemeinschaft

# Backup-Script erstellen
sudo nano /usr/local/bin/backup-maschinengemeinschaft.sh
```

**Script-Inhalt:**
```bash
#!/bin/bash
BACKUP_DIR="/var/backups/maschinengemeinschaft"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/maschinengemeinschaft_$DATE.sql.gz"

# Backup erstellen und komprimieren
pg_dump -U mgr_user maschinengemeinschaft | gzip > "$BACKUP_FILE"

# Alte Backups löschen (älter als 30 Tage)
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete

echo "Backup erstellt: $BACKUP_FILE"
```

```bash
# Ausführbar machen
sudo chmod +x /usr/local/bin/backup-maschinengemeinschaft.sh

# Cron-Job einrichten (täglich um 2:00 Uhr)
echo "0 2 * * * postgres /usr/local/bin/backup-maschinengemeinschaft.sh" | sudo tee /etc/cron.d/maschinengemeinschaft-backup
```

### Manuelles Backup

```bash
pg_dump -U mgr_user -h localhost maschinengemeinschaft > backup.sql
```

### Wiederherstellung

```bash
psql -U mgr_user -h localhost -d maschinengemeinschaft < backup.sql
```

---

## Fehlerbehebung

### Problem: "FATAL: password authentication failed"

```bash
# Passwort zurücksetzen
sudo -u postgres psql -c "ALTER USER mgr_user WITH PASSWORD 'NeuesPasswort';"
```

### Problem: "could not connect to server: Connection refused"

```bash
# Prüfen ob PostgreSQL läuft
sudo systemctl status postgresql

# Neu starten
sudo systemctl restart postgresql

# Logs prüfen
sudo tail -50 /var/log/postgresql/postgresql-*-main.log
```

### Problem: "no pg_hba.conf entry for host"

```bash
# pg_hba.conf prüfen und IP-Bereich hinzufügen
sudo nano /etc/postgresql/*/main/pg_hba.conf
sudo systemctl restart postgresql
```

### Problem: "psycopg2 not found"

```bash
# In virtueller Umgebung installieren
source .venv/bin/activate
pip install psycopg2-binary
```

---

## Sicherheitshinweise

1. **Starkes Passwort verwenden** - Mindestens 16 Zeichen mit Sonderzeichen
2. **Firewall konfigurieren** - Port 5432 nur für vertrauenswürdige IPs öffnen
3. **SSL aktivieren** - Für Verbindungen über das Internet
4. **Regelmäßige Backups** - Täglich automatisch + vor Updates
5. **Updates installieren** - `sudo apt update && sudo apt upgrade`

---

## Schnellreferenz

| Befehl | Beschreibung |
|--------|--------------|
| `sudo systemctl status postgresql` | Status prüfen |
| `sudo systemctl restart postgresql` | Neu starten |
| `sudo -u postgres psql` | Als Admin anmelden |
| `psql -U mgr_user -d maschinengemeinschaft` | Als App-User anmelden |
| `pg_dump -U mgr_user maschinengemeinschaft > backup.sql` | Backup erstellen |

---

*Erstellt: Januar 2026*
*Version: 1.0*
