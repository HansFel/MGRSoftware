# HTTPS Setup mit bestehendem nginx Container

Da du bereits nginx als Container laufen hast, musst du nur die nginx Konfiguration hinzufügen.

## Schritt 1: nginx Konfiguration hinzufügen

Kopiere die `nginx.conf` in dein nginx Container-Volume. Je nach Setup:

**Option A: Volume-Mount**
```bash
# Finde heraus, wo dein nginx die Configs liest
docker inspect <dein-nginx-container> | grep -A 5 Mounts

# Kopiere nginx.conf dorthin, z.B.:
cp nginx.conf /pfad/zu/nginx/conf.d/maschinengemeinschaft.conf
```

**Option B: Direkt in Container kopieren**
```bash
docker cp nginx.conf <dein-nginx-container>:/etc/nginx/conf.d/maschinengemeinschaft.conf
```

## Schritt 2: Domain anpassen

In `nginx.conf` ersetze `deine-domain.de` mit deiner echten Domain.

## Schritt 3: SSL-Zertifikat anfordern

Falls noch kein Zertifikat vorhanden:

```bash
# Certbot im nginx Container ausführen oder separater Container:
docker run --rm \
  -v /etc/letsencrypt:/etc/letsencrypt \
  -v /var/www/certbot:/var/www/certbot \
  -p 80:80 \
  certbot/certbot certonly \
  --standalone \
  --email deine@email.de \
  --agree-tos \
  -d deine-domain.de
```

## Schritt 4: Maschinengemeinschaft Container starten

```bash
cd ~/maschinengemeinschaft
docker compose up -d
```

Die App läuft jetzt auf `127.0.0.1:5000` und nginx leitet HTTPS-Traffic dorthin weiter.

## Schritt 5: nginx neu laden

```bash
docker exec <dein-nginx-container> nginx -s reload
```

## Prüfen

```bash
# nginx Konfiguration testen
docker exec <dein-nginx-container> nginx -t

# Logs prüfen
docker logs <dein-nginx-container>
docker logs maschinengemeinschaft
```

## Troubleshooting

### "502 Bad Gateway"

Falls nginx den App-Container nicht erreicht, ändere in nginx.conf:
```nginx
proxy_pass http://172.17.0.1:5000;
```

Die IP `172.17.0.1` ist die Docker-Bridge Gateway-Adresse.

### IP des Host finden

```bash
# Auf dem Raspberry Pi:
ip addr show docker0
```

Nutze die dort angezeigte IP in der nginx.conf.

### Alternative: Gleiches Docker-Netzwerk

Falls dein nginx und die App im gleichen Docker-Netzwerk sind:

```bash
# Netzwerk herausfinden
docker network ls
docker inspect <dein-nginx-container> | grep NetworkMode

# In docker-compose.yml hinzufügen:
# networks:
#   default:
#     external:
#       name: <dein-nginx-netzwerk>

# Dann in nginx.conf:
# proxy_pass http://maschinengemeinschaft:5000;
```
