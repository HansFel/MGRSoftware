#!/bin/bash

# HTTPS Setup für Maschinengemeinschaft
# Dieses Skript richtet SSL/TLS mit Let's Encrypt ein

set -e

DOMAIN="ml76y0cjb8gqzf3p.myfritz.net"
EMAIL="htfel@example.com"  # Bitte durch echte E-Mail ersetzen!

echo "=================================="
echo "HTTPS Setup für Maschinengemeinschaft"
echo "=================================="
echo ""
echo "Domain: $DOMAIN"
echo "E-Mail: $EMAIL"
echo ""

# Prüfe ob Docker läuft
if ! docker ps >/dev/null 2>&1; then
    echo "❌ Docker läuft nicht oder keine Berechtigung!"
    echo "Versuche: sudo ./setup_https.sh"
    exit 1
fi

# Erstelle Verzeichnisse
echo "📁 Erstelle Verzeichnisse..."
mkdir -p certbot/conf
mkdir -p certbot/www

# Stoppe laufende Container
echo "🛑 Stoppe laufende Container..."
docker compose down 2>/dev/null || true

# Temporärer HTTP-Server für ACME Challenge
echo "🌐 Starte temporären nginx für Let's Encrypt..."
cat > nginx_temp.conf << 'EOF'
server {
    listen 80;
    server_name ml76y0cjb8gqzf3p.myfritz.net;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 200 "ACME Challenge Server läuft\n";
        add_header Content-Type text/plain;
    }
}
EOF

docker run -d --name nginx_temp \
    -p 80:80 \
    -v $(pwd)/nginx_temp.conf:/etc/nginx/conf.d/default.conf:ro \
    -v $(pwd)/certbot/www:/var/www/certbot:ro \
    nginx:alpine

echo "⏳ Warte 5 Sekunden..."
sleep 5

# Zertifikat anfordern
echo "🔐 Fordere SSL-Zertifikat an..."
docker run --rm \
    -v $(pwd)/certbot/conf:/etc/letsencrypt \
    -v $(pwd)/certbot/www:/var/www/certbot \
    --network host \
    certbot/certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN

# Aufräumen
echo "🧹 Räume auf..."
docker stop nginx_temp >/dev/null 2>&1 || true
docker rm nginx_temp >/dev/null 2>&1 || true
rm -f nginx_temp.conf

# Starte Services
echo "🚀 Starte Services..."
docker compose up -d

echo ""
echo "✅ HTTPS Setup abgeschlossen!"
echo ""
echo "Deine Anwendung ist jetzt erreichbar unter:"
echo "  https://$DOMAIN"
echo ""
echo "Hinweis: Das Zertifikat wird automatisch erneuert."
echo ""
