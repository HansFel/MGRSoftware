#!/bin/bash
#===============================================================================
#
#   MASCHINENGEMEINSCHAFT - SERVER SETUP SCRIPT
#   Für Ubuntu Server 20.04 / 22.04 / 24.04
#
#   Verwendung:
#     chmod +x setup_server.sh
#     sudo ./setup_server.sh
#
#===============================================================================

set -e  # Bei Fehler abbrechen

# Farben für Ausgabe
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Konfiguration - BITTE ANPASSEN!
#===============================================================================
APP_NAME="maschinengemeinschaft"
APP_DIR="/opt/maschinengemeinschaft"
APP_USER="mgr"
APP_PORT="5000"

# PostgreSQL
DB_NAME="maschinengemeinschaft"
DB_USER="mgr_user"
DB_PASSWORD=""  # Wird generiert wenn leer

# Nginx (optional)
SETUP_NGINX="true"
DOMAIN=""  # Leer = nur IP-Zugriff

#===============================================================================

print_header() {
    echo ""
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}================================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}! $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Root-Check
if [ "$EUID" -ne 0 ]; then
    print_error "Bitte als root ausführen: sudo ./setup_server.sh"
    exit 1
fi

print_header "MASCHINENGEMEINSCHAFT - SERVER SETUP"

echo "Dieses Script installiert:"
echo "  - PostgreSQL Datenbank"
echo "  - Python 3 + virtuelle Umgebung"
echo "  - Systemd Service (Autostart)"
echo "  - Automatisches Backup (täglich)"
if [ "$SETUP_NGINX" = "true" ]; then
    echo "  - Nginx Reverse Proxy"
fi
echo ""

# Passwort generieren wenn nicht gesetzt
if [ -z "$DB_PASSWORD" ]; then
    DB_PASSWORD=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 20)
    print_warning "Generiertes Datenbank-Passwort: $DB_PASSWORD"
fi

read -p "Installation starten? (j/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Jj]$ ]]; then
    echo "Abgebrochen."
    exit 0
fi

#===============================================================================
print_header "SCHRITT 1: System aktualisieren"
#===============================================================================

apt update
apt upgrade -y
print_success "System aktualisiert"

#===============================================================================
print_header "SCHRITT 2: Benötigte Pakete installieren"
#===============================================================================

apt install -y \
    postgresql \
    postgresql-contrib \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    ufw

print_success "Pakete installiert"

#===============================================================================
print_header "SCHRITT 3: PostgreSQL konfigurieren"
#===============================================================================

# PostgreSQL starten
systemctl start postgresql
systemctl enable postgresql

# Datenbank und Benutzer erstellen
sudo -u postgres psql << EOF
-- Lösche falls existiert (für Neuinstallation)
DROP DATABASE IF EXISTS $DB_NAME;
DROP USER IF EXISTS $DB_USER;

-- Neu erstellen
CREATE DATABASE $DB_NAME;
CREATE USER $DB_USER WITH ENCRYPTED PASSWORD '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
ALTER DATABASE $DB_NAME OWNER TO $DB_USER;
EOF

# Schema-Rechte vergeben
sudo -u postgres psql -d $DB_NAME << EOF
GRANT ALL ON SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;
EOF

print_success "PostgreSQL Datenbank '$DB_NAME' erstellt"
print_success "PostgreSQL Benutzer '$DB_USER' erstellt"

#===============================================================================
print_header "SCHRITT 4: App-Benutzer und Verzeichnis erstellen"
#===============================================================================

# Benutzer erstellen (falls nicht existiert)
if ! id "$APP_USER" &>/dev/null; then
    useradd -r -m -s /bin/bash $APP_USER
    print_success "Benutzer '$APP_USER' erstellt"
else
    print_warning "Benutzer '$APP_USER' existiert bereits"
fi

# Verzeichnis erstellen
mkdir -p $APP_DIR
chown $APP_USER:$APP_USER $APP_DIR

print_success "Verzeichnis $APP_DIR erstellt"

#===============================================================================
print_header "SCHRITT 5: Python-Umgebung einrichten"
#===============================================================================

# Als App-Benutzer ausführen
sudo -u $APP_USER bash << EOF
cd $APP_DIR

# Virtuelle Umgebung erstellen
python3 -m venv .venv

# Aktivieren und Pakete installieren
source .venv/bin/activate
pip install --upgrade pip
pip install flask psycopg2-binary reportlab gunicorn
EOF

print_success "Python-Umgebung eingerichtet"

#===============================================================================
print_header "SCHRITT 6: Umgebungsvariablen konfigurieren"
#===============================================================================

# .env Datei erstellen
cat > $APP_DIR/.env << EOF
# Maschinengemeinschaft Konfiguration
# Erstellt: $(date)

# Datenbank
DB_TYPE=postgresql
PG_HOST=localhost
PG_PORT=5432
PG_DATABASE=$DB_NAME
PG_USER=$DB_USER
PG_PASSWORD=$DB_PASSWORD

# Flask
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 32)
EOF

chown $APP_USER:$APP_USER $APP_DIR/.env
chmod 600 $APP_DIR/.env

print_success "Umgebungsvariablen in $APP_DIR/.env gespeichert"

#===============================================================================
print_header "SCHRITT 7: Systemd Service einrichten"
#===============================================================================

cat > /etc/systemd/system/$APP_NAME.service << EOF
[Unit]
Description=Maschinengemeinschaft Web-Anwendung
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/.venv/bin/gunicorn -w 4 -b 127.0.0.1:$APP_PORT web_app:app
Restart=always
RestartSec=5

# Sicherheit
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable $APP_NAME

print_success "Systemd Service '$APP_NAME' eingerichtet"

#===============================================================================
print_header "SCHRITT 8: Backup-System einrichten"
#===============================================================================

# Backup-Verzeichnis
mkdir -p /var/backups/$APP_NAME
chown postgres:postgres /var/backups/$APP_NAME

# Backup-Script
cat > /usr/local/bin/backup-$APP_NAME.sh << 'BACKUP_SCRIPT'
#!/bin/bash
BACKUP_DIR="/var/backups/maschinengemeinschaft"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.sql.gz"

# Backup erstellen
pg_dump -U mgr_user maschinengemeinschaft | gzip > "$BACKUP_FILE"

# Alte Backups löschen (älter als 30 Tage)
find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +30 -delete

# Log
echo "$(date): Backup erstellt: $BACKUP_FILE" >> /var/log/maschinengemeinschaft-backup.log
BACKUP_SCRIPT

chmod +x /usr/local/bin/backup-$APP_NAME.sh

# Cron-Job für tägliches Backup um 2:00 Uhr
echo "0 2 * * * postgres /usr/local/bin/backup-$APP_NAME.sh" > /etc/cron.d/$APP_NAME-backup

print_success "Automatisches Backup eingerichtet (täglich 2:00 Uhr)"

#===============================================================================
if [ "$SETUP_NGINX" = "true" ]; then
print_header "SCHRITT 9: Nginx Reverse Proxy einrichten"
#===============================================================================

apt install -y nginx

# Nginx-Konfiguration
cat > /etc/nginx/sites-available/$APP_NAME << EOF
server {
    listen 80;
    server_name ${DOMAIN:-_};

    # Sicherheits-Header
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/${APP_NAME}_access.log;
    error_log /var/log/nginx/${APP_NAME}_error.log;

    # Proxy zur Flask-App
    location / {
        proxy_pass http://127.0.0.1:$APP_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Statische Dateien direkt ausliefern
    location /static {
        alias $APP_DIR/static;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    # Uploads begrenzen
    client_max_body_size 10M;
}
EOF

# Aktivieren
ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Testen und starten
nginx -t
systemctl restart nginx
systemctl enable nginx

print_success "Nginx eingerichtet"
fi

#===============================================================================
print_header "SCHRITT 10: Firewall konfigurieren"
#===============================================================================

ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

print_success "Firewall konfiguriert (SSH, HTTP, HTTPS erlaubt)"

#===============================================================================
print_header "SETUP ABGESCHLOSSEN!"
#===============================================================================

# Server-IP ermitteln
SERVER_IP=$(hostname -I | awk '{print $1}')

echo ""
echo -e "${GREEN}================================================================${NC}"
echo -e "${GREEN}  Installation erfolgreich!${NC}"
echo -e "${GREEN}================================================================${NC}"
echo ""
echo "Nächste Schritte:"
echo ""
echo "1. App-Dateien hochladen:"
echo "   scp -r * ${APP_USER}@${SERVER_IP}:${APP_DIR}/"
echo ""
echo "2. Datenbank-Schema erstellen und migrieren:"
echo "   ssh ${APP_USER}@${SERVER_IP}"
echo "   cd ${APP_DIR}"
echo "   source .venv/bin/activate"
echo "   source .env"
echo "   python migrate_to_postgresql.py"
echo ""
echo "3. Service starten:"
echo "   sudo systemctl start ${APP_NAME}"
echo ""
echo "4. Zugriff:"
echo "   http://${SERVER_IP}"
echo ""
echo -e "${YELLOW}================================================================${NC}"
echo -e "${YELLOW}  WICHTIG - ZUGANGSDATEN NOTIEREN!${NC}"
echo -e "${YELLOW}================================================================${NC}"
echo ""
echo "  Datenbank:     $DB_NAME"
echo "  DB-Benutzer:   $DB_USER"
echo "  DB-Passwort:   $DB_PASSWORD"
echo ""
echo "  App-Verzeichnis: $APP_DIR"
echo "  App-Benutzer:    $APP_USER"
echo ""
echo "  Config-Datei:    $APP_DIR/.env"
echo ""
echo -e "${YELLOW}================================================================${NC}"
echo ""

# Zugangsdaten in Datei speichern
cat > /root/maschinengemeinschaft-credentials.txt << EOF
MASCHINENGEMEINSCHAFT - ZUGANGSDATEN
====================================
Erstellt: $(date)
Server: $SERVER_IP

Datenbank:
  Name:     $DB_NAME
  Benutzer: $DB_USER
  Passwort: $DB_PASSWORD
  Host:     localhost
  Port:     5432

App:
  Verzeichnis: $APP_DIR
  Benutzer:    $APP_USER
  Port:        $APP_PORT

Befehle:
  Status:   sudo systemctl status $APP_NAME
  Start:    sudo systemctl start $APP_NAME
  Stop:     sudo systemctl stop $APP_NAME
  Logs:     sudo journalctl -u $APP_NAME -f
  Backup:   sudo /usr/local/bin/backup-$APP_NAME.sh
EOF

chmod 600 /root/maschinengemeinschaft-credentials.txt
echo "Zugangsdaten gespeichert in: /root/maschinengemeinschaft-credentials.txt"
echo ""
