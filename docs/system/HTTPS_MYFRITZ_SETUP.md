# HTTPS Setup für MyFritz Domain

## Problem
Die Webseite war unter HTTPS nicht erreichbar, weil:
1. Port 443 war auf 8443 gemappt (falsch)
2. Kein SSL-Zertifikat vorhanden
3. nginx.conf hatte keine HTTPS-Konfiguration

## Lösung

### Was wurde geändert:

1. **docker-compose.yml**: Port 443 richtig gemappt (nicht 8443)
2. **nginx.conf**: HTTPS-Block mit SSL-Konfiguration hinzugefügt
3. **setup_https_myfritz.sh**: Automatisches Setup-Skript erstellt

### Schritte auf dem Raspberry Pi:

#### Option 1: Mit SSL-Zertifikat (empfohlen)

**Voraussetzungen:**
- Port 80 und 443 müssen im Router auf den Raspberry Pi weitergeleitet sein
- Domain muss auf deine öffentliche IP zeigen

```bash
cd ~/maschinengemeinschaft

# E-Mail in setup_https_myfritz.sh anpassen
nano setup_https_myfritz.sh
# Zeile 10: EMAIL="deine@email.de"

# Ausführbar machen und starten
chmod +x setup_https_myfritz.sh
sudo ./setup_https_myfritz.sh
```

Das Skript:
- Erstellt notwendige Verzeichnisse
- Fordert SSL-Zertifikat von Let's Encrypt an
- Startet nginx mit HTTPS

#### Option 2: Ohne SSL (nur HTTP)

Falls SSL nicht funktioniert, nutze die HTTP-only Konfiguration:

```bash
cd ~/maschinengemeinschaft

# Verwende HTTP-only nginx.conf
cp nginx_http_only.conf nginx.conf

# Ändere Port in docker-compose.yml zurück
nano docker-compose.yml
# Zeile 24: "80:80" statt "443:443"

# Starte Services
docker compose down
docker compose up -d
```

### Zugriff:

- **Mit SSL**: https://ml76y0cjb8gqzf3p.myfritz.net
- **Ohne SSL**: http://ml76y0cjb8gqzf3p.myfritz.net

### Portweiterleitung im Router prüfen:

Für HTTPS brauchst du:
- Port 80 → Raspberry Pi IP:80 (für Let's Encrypt)
- Port 443 → Raspberry Pi IP:443 (für HTTPS)

Nur für HTTP:
- Port 80 → Raspberry Pi IP:80

### Fehlersuche:

```bash
# Logs anschauen
docker compose logs nginx
docker compose logs maschinengemeinschaft

# Status prüfen
docker compose ps

# Container neu starten
docker compose restart
```

### Zertifikat erneuern:

Das Zertifikat wird automatisch erneuert. Manuell:

```bash
docker compose run --rm certbot renew
docker compose restart nginx
```
