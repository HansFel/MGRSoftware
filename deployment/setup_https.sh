#!/bin/bash

# HTTPS Setup für Maschinengemeinschaft mit Let's Encrypt
# Dieses Skript auf dem Raspberry Pi ausführen

echo "=== HTTPS Setup für Maschinengemeinschaft ==="
echo ""
echo "WICHTIG: Bevor du dieses Skript ausführst:"
echo "1. Ersetze 'deine-domain.de' in nginx.conf mit deiner echten Domain"
echo "2. Stelle sicher, dass Port 80 und 443 in deinem Router weitergeleitet sind"
echo "3. Deine Domain muss auf die öffentliche IP zeigen"
echo ""
read -p "Hast du die Domain in nginx.conf angepasst? (ja/nein): " antwort

if [ "$antwort" != "ja" ]; then
    echo "Bitte passe zuerst nginx.conf an!"
    exit 1
fi

read -p "Deine Domain (z.B. maschinengemeinschaft.example.com): " DOMAIN
read -p "Deine E-Mail für Let's Encrypt: " EMAIL

echo ""
echo "Erstelle Verzeichnisse..."
mkdir -p certbot/conf
mkdir -p certbot/www

echo ""
echo "Starte nginx temporär für Zertifikat-Anfrage..."

# Temporäre nginx Konfiguration für Certbot Challenge
cat > nginx_temp.conf << EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 200 'OK';
        add_header Content-Type text/plain;
    }
}
EOF

# Nginx mit temporärer Config starten
docker run -d --name nginx_temp \
    -p 80:80 \
    -v $(pwd)/nginx_temp.conf:/etc/nginx/conf.d/default.conf \
    -v $(pwd)/certbot/www:/var/www/certbot \
    nginx:alpine

sleep 5

echo ""
echo "Fordere SSL-Zertifikat von Let's Encrypt an..."
docker run --rm \
    -v $(pwd)/certbot/conf:/etc/letsencrypt \
    -v $(pwd)/certbot/www:/var/www/certbot \
    certbot/certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN

# Temporären nginx stoppen
docker stop nginx_temp
docker rm nginx_temp
rm nginx_temp.conf

echo ""
echo "Aktualisiere nginx.conf mit deiner Domain..."
sed -i "s/deine-domain.de/$DOMAIN/g" nginx.conf

echo ""
echo "Starte alle Container..."
docker compose up -d

echo ""
echo "=== Setup abgeschlossen! ==="
echo ""
echo "Deine Anwendung ist jetzt erreichbar unter:"
echo "https://$DOMAIN"
echo ""
echo "Das Zertifikat wird automatisch alle 12 Stunden erneuert."
