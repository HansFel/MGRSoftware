# 🐳 Docker Installation auf Raspberry Pi

## Schritt-für-Schritt Anleitung

### 1. Raspberry Pi vorbereiten

Aktualisieren Sie Ihr System:
```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### 2. Docker installieren

```bash
# Docker installieren (offizielles Installations-Skript)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker ohne sudo ausführen können
sudo usermod -aG docker $USER

# Docker Compose installieren
sudo apt-get install -y docker-compose

# Neustart (damit Gruppenmitgliedschaft wirksam wird)
sudo reboot
```

Nach dem Neustart:
```bash
# Docker-Installation prüfen
docker --version
docker-compose --version
```

### 3. Projektdateien auf Raspberry Pi übertragen

**Option A: Mit Git**
```bash
# Ihr Projekt auf GitHub/GitLab hochladen, dann:
git clone https://ihre-repo-url.git
cd MGRSoftware
```

**Option B: Mit SCP (von Ihrem Windows-PC)**
```powershell
# Im Projektverzeichnis auf Windows
scp -r * pi@raspberry-ip:/home/pi/maschinengemeinschaft/
```

**Option C: USB-Stick**
- Dateien auf USB-Stick kopieren
- USB-Stick am Raspberry Pi einstecken
- Dateien kopieren

### 4. Datenverzeichnis erstellen

```bash
cd /home/pi/maschinengemeinschaft
mkdir -p data
chmod 777 data
```

### 5. Docker Container starten

```bash
# Container bauen und starten
docker-compose up -d

# Logs ansehen
docker-compose logs -f
```

Die Anwendung ist jetzt erreichbar unter:
- **Im lokalen Netzwerk**: `http://raspberry-ip:5000`
- **Vom Raspberry selbst**: `http://localhost:5000`

### 6. Datenbank initialisieren und Benutzer anlegen

Da die Desktop-App (Tkinter) nicht im Docker Container läuft, nutzen Sie ein Python-Skript:

```bash
# Interaktive Python-Shell im Container
docker exec -it maschinengemeinschaft python

# Dann im Python-Interpreter:
```

```python
from database import MaschinenDBContext

# Datenbank-Pfad
db_path = "/data/maschinengemeinschaft.db"

with MaschinenDBContext(db_path) as db:
    # Datenbank initialisieren (falls noch nicht geschehen)
    db.init_database()
    
    # Ersten Benutzer anlegen
    benutzer_id = db.add_benutzer(
        name="Mustermann",
        vorname="Max",
        username="max",
        password="test123",  # ÄNDERN SIE DIES!
        email="max@example.com",
        mitglied_seit="2026-01-07"
    )
    print(f"✅ Benutzer erstellt mit ID: {benutzer_id}")
    
    # Maschine anlegen
    maschine_id = db.add_maschine(
        bezeichnung="Traktor Fendt",
        hersteller="Fendt",
        modell="Vario 724",
        baujahr=2020,
        stundenzaehler_aktuell=1234.5
    )
    print(f"✅ Maschine erstellt mit ID: {maschine_id}")

# Mit Strg+D oder exit() beenden
```

Oder mit einem Skript:

```bash
# Skript erstellen
cat > init_data.py << 'EOF'
from database import MaschinenDBContext

db_path = "/data/maschinengemeinschaft.db"

with MaschinenDBContext(db_path) as db:
    db.init_database()
    
    # Benutzer anlegen
    db.add_benutzer(
        name="Mustermann", vorname="Max",
        username="max", password="sichere123"
    )
    db.add_benutzer(
        name="Schmidt", vorname="Anna",
        username="anna", password="sichere456"
    )
    
    # Maschinen anlegen
    db.add_maschine(
        bezeichnung="Traktor 1", hersteller="Fendt",
        stundenzaehler_aktuell=1000.0
    )
    db.add_maschine(
        bezeichnung="Traktor 2", hersteller="John Deere",
        stundenzaehler_aktuell=2500.0
    )
    
    print("✅ Daten initialisiert!")
EOF

# Skript im Container ausführen
docker cp init_data.py maschinengemeinschaft:/tmp/
docker exec maschinengemeinschaft python /tmp/init_data.py
```

### 7. Container-Verwaltung

```bash
# Status prüfen
docker-compose ps

# Logs ansehen
docker-compose logs -f

# Container stoppen
docker-compose stop

# Container starten
docker-compose start

# Container neustarten
docker-compose restart

# Container stoppen und entfernen
docker-compose down

# Container neu bauen (nach Code-Änderungen)
docker-compose up -d --build
```

### 8. Automatischer Start beim Booten

Docker Container starten automatisch dank `restart: unless-stopped` in der docker-compose.yml.

Um sicherzustellen, dass Docker beim Boot startet:
```bash
sudo systemctl enable docker
```

### 9. Netzwerkzugriff konfigurieren

**IP-Adresse des Raspberry Pi finden:**
```bash
hostname -I
```

**Von anderen Geräten zugreifen:**
- Browser öffnen
- Eingeben: `http://RASPBERRY-PI-IP:5000`
- Mit Benutzername und Passwort anmelden

### 10. Port-Weiterleitung (optional)

Falls Sie von außerhalb Ihres Netzwerks zugreifen möchten:

1. Router-Einstellungen öffnen
2. Port-Weiterleitung einrichten: Port 5000 → Raspberry Pi IP
3. **Wichtig**: Verwenden Sie HTTPS und starke Passwörter!

### 11. HTTPS einrichten (empfohlen für Produktion)

**Mit Nginx Reverse Proxy:**

```bash
# Nginx installieren
sudo apt-get install -y nginx

# Nginx-Konfiguration
sudo nano /etc/nginx/sites-available/maschinengemeinschaft
```

```nginx
server {
    listen 80;
    server_name ihre-domain.de;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Konfiguration aktivieren
sudo ln -s /etc/nginx/sites-available/maschinengemeinschaft /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# SSL mit Let's Encrypt (kostenlos)
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d ihre-domain.de
```

### 12. Backup der Datenbank

```bash
# Manuelles Backup
cp data/maschinengemeinschaft.db data/backup_$(date +%Y%m%d).db

# Automatisches tägliches Backup (Crontab)
crontab -e

# Folgende Zeile hinzufügen:
0 2 * * * cp /home/pi/maschinengemeinschaft/data/maschinengemeinschaft.db /home/pi/maschinengemeinschaft/data/backup_$(date +\%Y\%m\%d).db
```

### 13. Updates einspielen

```bash
# Code aktualisieren (z.B. mit Git)
git pull

# Container neu bauen und starten
docker-compose up -d --build
```

## 🔧 Troubleshooting

### Container startet nicht
```bash
docker-compose logs
```

### Port bereits belegt
```bash
# Anderen Port verwenden (z.B. 8080)
# In docker-compose.yml ändern:
ports:
  - "8080:5000"
```

### Datenbank-Fehler
```bash
# Datenbank-Berechtigungen prüfen
ls -la data/
chmod 666 data/maschinengemeinschaft.db
```

### Performance-Probleme
```bash
# Raspberry Pi Status prüfen
vcgencmd measure_temp
htop
```

## 📊 Monitoring

```bash
# Ressourcen-Nutzung
docker stats maschinengemeinschaft

# Container-Logs live
docker logs -f maschinengemeinschaft
```

## 🔐 Sicherheit (Wichtig!)

1. **Starke Passwörter** verwenden
2. **Firewall** konfigurieren:
   ```bash
   sudo apt-get install ufw
   sudo ufw allow 22/tcp   # SSH
   sudo ufw allow 80/tcp   # HTTP
   sudo ufw allow 443/tcp  # HTTPS
   sudo ufw enable
   ```
3. **Regelmäßige Updates**:
   ```bash
   sudo apt-get update && sudo apt-get upgrade -y
   ```
4. **HTTPS** in Produktion verwenden
5. **Backups** regelmäßig erstellen

## 📱 Zugriff von Mobilgeräten

1. Raspberry Pi IP-Adresse notieren
2. Auf Handy/Tablet Browser öffnen
3. Eingeben: `http://RASPBERRY-IP:5000`
4. Als Lesezeichen speichern
5. Optional: Zum Home-Screen hinzufügen

---

Bei Fragen oder Problemen: Logs mit `docker-compose logs -f` prüfen!
