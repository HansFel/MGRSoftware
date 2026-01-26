# PostgreSQL Streaming Replication - Setup-Anleitung

Diese Anleitung beschreibt die Einrichtung der Echtzeit-Replikation zwischen dem Primary-Server (Produktionsserver) und einem Standby-Server (Backup-Server).

## Übersicht

```
┌─────────────────┐         ┌─────────────────┐
│  PRIMARY (mgs2) │ ──WAL──>│  STANDBY        │
│  (Produktion)   │         │  (Backup)       │
│                 │         │                 │
│  PostgreSQL     │         │  PostgreSQL     │
│  maschinengemeinschaft-db │         │  (Hot Standby)  │
└─────────────────┘         └─────────────────┘
```

## Voraussetzungen

- **Primary-Server**: Der aktuelle Produktionsserver (mgs2)
- **Standby-Server**: Ein zweiter Server mit gleicher Hardware/OS
- Beide Server müssen sich im gleichen Netzwerk befinden
- SSH-Zugang zu beiden Servern

---

## Teil 1: Standby-Server vorbereiten

### 1.1 Ubuntu Server installieren

Falls noch nicht geschehen, installieren Sie Ubuntu Server (gleiche Version wie Primary).

### 1.2 Docker installieren

```bash
# Docker installieren
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Docker Compose installieren
sudo apt install docker-compose-plugin
```

### 1.3 Verzeichnisstruktur erstellen

```bash
# Benutzer und Verzeichnisse erstellen
sudo useradd -m -s /bin/bash mgserver
sudo mkdir -p /home/mgserver/mgserver
sudo chown -R mgserver:mgserver /home/mgserver/mgserver
```

---

## Teil 2: Primary-Server konfigurieren (mgs2)

### 2.1 PostgreSQL für Replication konfigurieren

Verbinden Sie sich mit dem PostgreSQL-Container:

```bash
docker exec -it maschinengemeinschaft-db bash
```

Oder direkt SQL ausführen:

```bash
docker exec -it maschinengemeinschaft-db psql -U mgr_user -d maschinengemeinschaft
```

### 2.2 Replication-User erstellen

```sql
-- Im PostgreSQL-Container ausführen
CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'ReplicatorPasswort123!';
```

### 2.3 PostgreSQL-Konfiguration anpassen

Die Konfiguration muss im Docker-Container angepasst werden. Erstellen Sie eine angepasste `postgresql.conf`:

```bash
# Auf dem Primary-Server
cd /home/mgserver/mgserver

# PostgreSQL-Konfiguration für Replication erstellen
cat > postgres-replication.conf << 'EOF'
# Replication Settings
wal_level = replica
max_wal_senders = 5
max_replication_slots = 5
hot_standby = on
wal_keep_size = 1GB

# Netzwerk
listen_addresses = '*'
EOF
```

### 2.4 pg_hba.conf für Replication anpassen

```bash
cat > pg_hba_replication.conf << 'EOF'
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             all                                     trust
host    all             all             127.0.0.1/32            scram-sha-256
host    all             all             ::1/128                 scram-sha-256
host    all             all             0.0.0.0/0               scram-sha-256

# Replication
host    replication     replicator      0.0.0.0/0               scram-sha-256
EOF
```

### 2.5 Docker Compose für Primary anpassen

Erstellen Sie eine neue `docker-compose-primary.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    container_name: maschinengemeinschaft-db
    restart: always
    environment:
      POSTGRES_DB: maschinengemeinschaft
      POSTGRES_USER: mgr_user
      POSTGRES_PASSWORD: ${DB_PASSWORD:-SicheresPasswort123!}
    volumes:
      - db_data:/var/lib/postgresql/data
      - ./postgres-replication.conf:/etc/postgresql/conf.d/replication.conf:ro
      - ./pg_hba_replication.conf:/etc/postgresql/pg_hba.conf:ro
    ports:
      - "5432:5432"
    command: >
      postgres
      -c config_file=/etc/postgresql/postgresql.conf
      -c hba_file=/etc/postgresql/pg_hba.conf
      -c wal_level=replica
      -c max_wal_senders=5
      -c max_replication_slots=5
      -c hot_standby=on

volumes:
  db_data:
```

### 2.6 Replication Slot erstellen

```bash
docker exec -it maschinengemeinschaft-db psql -U mgr_user -d maschinengemeinschaft -c \
  "SELECT pg_create_physical_replication_slot('mgr_standby_slot');"
```

---

## Teil 3: Standby-Server einrichten

### 3.1 Base Backup erstellen

Auf dem **Standby-Server** ausführen:

```bash
# PostgreSQL-Client installieren
sudo apt install postgresql-client-16

# Verzeichnis für Daten erstellen
sudo mkdir -p /var/lib/postgresql/data
sudo chown -R 999:999 /var/lib/postgresql/data

# Base Backup vom Primary holen
pg_basebackup -h PRIMARY_IP -p 5432 -U replicator -D /var/lib/postgresql/data \
  -Fp -Xs -P -R -S mgr_standby_slot

# Passwort eingeben wenn gefragt: ReplicatorPasswort123!
```

### 3.2 Docker Compose für Standby

Auf dem Standby-Server:

```yaml
# docker-compose-standby.yml
version: '3.8'

services:
  db:
    image: postgres:15
    container_name: maschinengemeinschaft-db-standby
    restart: always
    environment:
      POSTGRES_DB: maschinengemeinschaft
      POSTGRES_USER: mgr_user
      POSTGRES_PASSWORD: ${DB_PASSWORD:-SicheresPasswort123!}
    volumes:
      - /var/lib/postgresql/data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    command: postgres
```

### 3.3 Standby-Signal erstellen

```bash
# Auf dem Standby-Server
touch /var/lib/postgresql/data/standby.signal

# postgresql.auto.conf sollte bereits durch pg_basebackup erstellt sein
# Inhalt prüfen:
cat /var/lib/postgresql/data/postgresql.auto.conf
```

Die Datei sollte etwa so aussehen:
```
primary_conninfo = 'host=PRIMARY_IP port=5432 user=replicator password=ReplicatorPasswort123!'
primary_slot_name = 'mgr_standby_slot'
```

### 3.4 Standby starten

```bash
cd /home/mgserver/mgserver
docker-compose -f docker-compose-standby.yml up -d
```

---

## Teil 4: Replication überprüfen

### 4.1 Auf dem Primary-Server

```bash
# Aktive Replikationen anzeigen
docker exec -it maschinengemeinschaft-db psql -U mgr_user -d maschinengemeinschaft -c \
  "SELECT client_addr, state, sent_lsn, write_lsn, flush_lsn, replay_lsn FROM pg_stat_replication;"
```

Erwartete Ausgabe:
```
 client_addr  |   state   | sent_lsn  | write_lsn | flush_lsn | replay_lsn
--------------+-----------+-----------+-----------+-----------+------------
 192.168.x.x  | streaming | 0/3000148 | 0/3000148 | 0/3000148 | 0/3000148
```

### 4.2 Auf dem Standby-Server

```bash
# Prüfen ob Standby-Modus aktiv ist
docker exec -it maschinengemeinschaft-db-standby psql -U mgr_user -d maschinengemeinschaft -c \
  "SELECT pg_is_in_recovery();"
```

Erwartete Ausgabe:
```
 pg_is_in_recovery
-------------------
 t
```

### 4.3 Replication-Lag prüfen

```bash
# Auf dem Primary
docker exec -it maschinengemeinschaft-db psql -U mgr_user -d maschinengemeinschaft -c \
  "SELECT client_addr,
          pg_wal_lsn_diff(sent_lsn, replay_lsn) AS byte_lag,
          replay_lag
   FROM pg_stat_replication;"
```

---

## Teil 5: Failover (Umschalten auf Standby)

### 5.1 Geplantes Failover

Bei einem geplanten Wechsel:

1. **Anwendung stoppen**
   ```bash
   # Auf dem Primary
   docker stop maschinengemeinschaft-app
   ```

2. **Standby zum Primary promoten**
   ```bash
   # Auf dem Standby
   docker exec -it maschinengemeinschaft-db-standby psql -U mgr_user -d maschinengemeinschaft -c \
     "SELECT pg_promote();"
   ```

3. **Anwendung auf Standby starten**
   ```bash
   # Auf dem neuen Primary (ehemals Standby)
   docker-compose up -d
   ```

4. **DNS/IP umstellen** oder Clients auf neuen Server verweisen

### 5.2 Notfall-Failover

Bei Ausfall des Primary:

1. **Standby promoten**
   ```bash
   docker exec -it maschinengemeinschaft-db-standby psql -U mgr_user -d maschinengemeinschaft -c \
     "SELECT pg_promote();"
   ```

2. **Anwendung starten** (falls noch nicht)

3. **Clients umleiten**

---

## Teil 6: Nach dem Failover

### 6.1 Alten Primary als neuen Standby einrichten

Der alte Primary muss komplett neu als Standby eingerichtet werden:

```bash
# Auf dem alten Primary (jetzt neuer Standby)
docker stop maschinengemeinschaft-db
rm -rf /var/lib/postgresql/data/*

# Base Backup vom neuen Primary holen
pg_basebackup -h NEUER_PRIMARY_IP -p 5432 -U replicator -D /var/lib/postgresql/data \
  -Fp -Xs -P -R -S mgr_standby_slot

# Als Standby starten
docker-compose -f docker-compose-standby.yml up -d
```

---

## Monitoring & Wartung

### Replication Status in der Web-App

Die Maschinengemeinschaft-App enthält ein Web-Interface zur Überwachung:

**Admin > Datenexport > Replication**

Hier können Sie:
- Den Replication-Status sehen
- Standby-Server konfigurieren
- Verbindungstests durchführen
- Replication aktivieren/deaktivieren

### Logs überwachen

```bash
# Primary
docker logs -f maschinengemeinschaft-db

# Standby
docker logs -f maschinengemeinschaft-db-standby
```

### Replication Slots aufräumen

Ungenutzte Slots können WAL-Dateien ansammeln:

```bash
# Slots anzeigen
docker exec -it maschinengemeinschaft-db psql -U mgr_user -d maschinengemeinschaft -c \
  "SELECT * FROM pg_replication_slots;"

# Ungenutzten Slot löschen
docker exec -it maschinengemeinschaft-db psql -U mgr_user -d maschinengemeinschaft -c \
  "SELECT pg_drop_replication_slot('alter_slot_name');"
```

---

## Troubleshooting

### Problem: Standby verbindet nicht

1. Netzwerk prüfen:
   ```bash
   ping PRIMARY_IP
   telnet PRIMARY_IP 5432
   ```

2. Firewall prüfen:
   ```bash
   sudo ufw allow 5432/tcp
   ```

3. pg_hba.conf prüfen (Replication-Eintrag vorhanden?)

### Problem: Replication Lag wächst

1. Netzwerkbandbreite prüfen
2. Standby-Hardware prüfen (genug RAM/CPU?)
3. WAL-Größe erhöhen:
   ```sql
   ALTER SYSTEM SET wal_keep_size = '2GB';
   SELECT pg_reload_conf();
   ```

### Problem: Slot belegt zu viel Speicher

```bash
# Speicherverbrauch prüfen
docker exec -it maschinengemeinschaft-db psql -U mgr_user -d maschinengemeinschaft -c \
  "SELECT slot_name, pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS retained_wal
   FROM pg_replication_slots;"
```

---

## Sicherheitshinweise

1. **Passwörter**: Verwenden Sie sichere, einzigartige Passwörter für den Replicator-User
2. **Netzwerk**: Idealerweise Replication über privates Netzwerk/VPN
3. **Verschlüsselung**: Für Replication über Internet SSL/TLS aktivieren
4. **Backups**: Replication ersetzt KEINE Backups! Führen Sie weiterhin regelmäßige Backups durch

---

**Erstellt mit Unterstützung von Claude AI (Anthropic)**
**Stand: Januar 2026**
