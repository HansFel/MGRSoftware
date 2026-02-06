# Server-Installation (Docker)

Diese Anleitung beschreibt die Installation der Maschinengemeinschaft-Anwendung auf einem Ubuntu-Server mit Docker.

## Voraussetzungen

- Ubuntu Server 20.04 / 22.04 / 24.04
- SSH-Zugang zum Server
- Benutzer mit sudo-Rechten

## Server-Liste

| Server | Host | Benutzer | Zweck |
|--------|------|----------|-------|
| mgs1 | mgs1 | mgserver | Produktion |
| mgs2 | mgs2 | mgserver | Produktion |
| mgv1 | mgv1 | mgserver | Entwicklung |

## Installation

### 1. SSH-Key einrichten

```bash
ssh-copy-id mgserver@<servername>
```

### 2. Docker & Git installieren

```bash
ssh mgserver@<servername>

# Docker installieren
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER

# Abmelden und neu anmelden (damit Docker-Gruppe aktiv wird)
exit
ssh mgserver@<servername>

# Git installieren
sudo apt update && sudo apt install -y git
```

### 3. Repository klonen

```bash
sudo mkdir -p /opt/mgr
sudo chown $USER:$USER /opt/mgr
cd /opt/mgr
git clone https://github.com/HansFel/MGRSoftware.git .
```

### 4. Umgebungsvariablen konfigurieren

```bash
cd /opt/mgr/deployment

cat > .env << EOF
DB_PASSWORD=$(openssl rand -hex 16)
SECRET_KEY=$(openssl rand -hex 32)
DOMAIN=<servername>
EOF

# Überprüfen
cat .env
```

### 5. Container starten

```bash
cd /opt/mgr/deployment
docker compose up -d
```

### 6. Installation verifizieren

```bash
# Container-Status prüfen
docker ps

# Logs anzeigen
docker compose logs -f

# Web-App testen
curl -I http://localhost:5000/
```

## Container-Übersicht

| Container | Image | Port | Beschreibung |
|-----------|-------|------|--------------|
| maschinengemeinschaft-db | postgres:15 | 5432 | PostgreSQL Datenbank |
| maschinengemeinschaft-app | deployment-web | 5000 | Flask Web-Anwendung |
| maschinengemeinschaft-caddy | caddy:2 | 80, 443 | Reverse Proxy mit Auto-SSL |

## Befehle

### Container verwalten

```bash
cd /opt/mgr/deployment

# Status anzeigen
docker compose ps

# Container stoppen
docker compose stop

# Container starten
docker compose start

# Container neu starten
docker compose restart

# Container neu bauen und starten
docker compose up -d --build

# Logs anzeigen (live)
docker compose logs -f

# Logs eines Containers
docker compose logs -f web
```

### Updates einspielen

```bash
cd /opt/mgr
git pull origin main
cd deployment
docker compose restart web
```

### Datenbank-Backup

```bash
# Backup erstellen
docker exec maschinengemeinschaft-db pg_dump -U mgr_user maschinengemeinschaft > backup_$(date +%Y%m%d).sql

# Backup wiederherstellen
cat backup_20260206.sql | docker exec -i maschinengemeinschaft-db psql -U mgr_user maschinengemeinschaft
```

### Shell in Container

```bash
# Web-Container
docker exec -it maschinengemeinschaft-app bash

# Datenbank-Container
docker exec -it maschinengemeinschaft-db psql -U mgr_user maschinengemeinschaft
```

## GitHub Actions Deployment

Das automatische Deployment erfolgt über GitHub Actions. Bei jedem Push auf `main` werden die Änderungen automatisch auf die Server deployed.

### Workflow-Dateien

- `.github/workflows/deploy-mgs2.yml` - Deployment auf mgs2
- `.github/workflows/deploy-mgv1.yml` - Deployment auf mgv1

### GitHub Secrets einrichten

Unter Repository > Settings > Secrets and variables > Actions:

| Secret | Beschreibung | Beispiel |
|--------|--------------|----------|
| MGS2_HOST | IP-Adresse von mgs2 | 192.168.1.10 |
| MGS2_USER | SSH-Benutzer | mgserver |
| MGS2_SSH_KEY | Privater SSH-Key | -----BEGIN OPENSSH... |
| MGV1_HOST | IP-Adresse von mgv1 | 192.168.1.11 |
| MGV1_SSH_KEY | Privater SSH-Key | -----BEGIN OPENSSH... |

## Troubleshooting

### Container startet nicht

```bash
# Logs prüfen
docker compose logs web

# Container neu bauen
docker compose up -d --build web
```

### Datenbank-Verbindungsfehler

```bash
# Datenbank-Container prüfen
docker compose logs db

# Manuell verbinden
docker exec -it maschinengemeinschaft-db psql -U mgr_user maschinengemeinschaft
```

### Port bereits belegt

```bash
# Welcher Prozess nutzt Port 5000?
sudo lsof -i :5000

# Container stoppen und Port freigeben
docker compose down
```

### Speicherplatz prüfen

```bash
# Docker-Speicher anzeigen
docker system df

# Ungenutzte Images/Container entfernen
docker system prune -a
```
