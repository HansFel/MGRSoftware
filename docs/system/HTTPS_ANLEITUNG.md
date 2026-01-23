# HTTPS Setup für Maschinengemeinschaft

## Voraussetzungen

1. **Domain**: Du brauchst eine eigene Domain (z.B. `maschinengemeinschaft.meinedomain.de`)
2. **DNS konfiguriert**: Die Domain muss auf deine öffentliche IP-Adresse zeigen
3. **Portweiterleitung im Router**:
   - Port 80 (HTTP) → Raspberry Pi Port 80
   - Port 443 (HTTPS) → Raspberry Pi Port 443

## Schnell-Setup (empfohlen)

### Schritt 1: Domain in nginx.conf eintragen

Öffne `nginx.conf` und ersetze **alle** Vorkommen von `deine-domain.de` mit deiner echten Domain.

### Schritt 2: Setup-Skript ausführen

Auf dem Raspberry Pi:

```bash
cd ~/maschinengemeinschaft
chmod +x setup_https.sh
./setup_https.sh
```

Das Skript fragt nach:
- Deiner Domain
- Deiner E-Mail-Adresse (für Let's Encrypt Benachrichtigungen)

### Schritt 3: Fertig!

Deine Anwendung ist jetzt unter `https://deine-domain.de` erreichbar.

---

## Manuelles Setup

Falls das automatische Skript nicht funktioniert:

### 1. Verzeichnisse erstellen

```bash
mkdir -p certbot/conf
mkdir -p certbot/www
```

### 2. Erstes Zertifikat anfordern

```bash
# Domain und E-Mail anpassen!
docker run --rm \
  -v $(pwd)/certbot/conf:/etc/letsencrypt \
  -v $(pwd)/certbot/www:/var/www/certbot \
  -p 80:80 \
  certbot/certbot certonly \
  --standalone \
  --email deine@email.de \
  --agree-tos \
  --no-eff-email \
  -d deine-domain.de
```

### 3. nginx.conf anpassen

Ersetze in `nginx.conf` alle Vorkommen von `deine-domain.de` mit deiner Domain.

### 4. Container starten

```bash
docker compose up -d
```

---

## Zertifikat erneuern

Das Zertifikat wird automatisch alle 12 Stunden geprüft und bei Bedarf erneuert.

Manuelle Erneuerung:

```bash
docker compose run --rm certbot renew
docker compose restart nginx
```

---

## Troubleshooting

### "Connection refused" auf Port 80/443

- Prüfe Portweiterleitung im Router
- Prüfe Firewall auf Raspberry Pi: `sudo ufw status`

### "Domain nicht erreichbar"

- Prüfe DNS-Einstellungen mit: `nslookup deine-domain.de`
- Öffentliche IP prüfen: `curl ifconfig.me`

### "Zertifikat ungültig"

- Prüfe ob Domain in nginx.conf korrekt ist
- Zertifikat neu anfordern (siehe Manuelles Setup)

### Container-Logs prüfen

```bash
docker logs nginx
docker logs maschinengemeinschaft
docker logs certbot
```

---

## Alternative: Cloudflare Tunnel (ohne Portweiterleitung)

Falls du keine Portweiterleitung einrichten kannst, nutze Cloudflare Tunnel:

1. Kostenloser Cloudflare Account erstellen
2. Cloudflared auf Raspberry Pi installieren
3. Tunnel einrichten (automatisches HTTPS ohne Zertifikat)

Anleitung: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/
