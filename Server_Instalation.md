# Server-Installation & Deployment der Web-Anwendung

Diese Anleitung beschreibt die Installation und den Betrieb der Maschinengemeinschaft-Webanwendung auf einem Linux-Server – klassisch und mit Docker.

---

## 1. Klassische Installation (ohne Docker)

### Voraussetzungen

- Linux-Server (z.B. Ubuntu)
- Python 3.8+ und pip
- Optional: Nginx als Reverse Proxy

### Schritte

#### 1.1. System vorbereiten

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

#### 1.2. Projekt kopieren

Kopiere den Projektordner auf den Server, z.B. nach `/opt/maschinengemeinschaft`.

#### 1.3. Virtuelle Umgebung & Abhängigkeiten

```bash
cd /opt/maschinengemeinschaft
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 1.4. Datenbank initialisieren

```bash
python database.py
```

#### 1.5. Benutzer anlegen

Starte die Desktop-App (optional, falls Benutzer fehlen):

```bash
python main.py
```
Benutzer mit Benutzername und Passwort anlegen.

#### 1.6. Webserver starten (Test)

```bash
python web_app.py
```
Zugriff: `http://<Server-IP>:5000`

#### 1.7. Produktionsbetrieb mit Gunicorn & Nginx

**Gunicorn installieren:**
```bash
pip install gunicorn
```
**Starten:**
```bash
gunicorn -w 4 -b 127.0.0.1:8000 web_app:app
```
**Systemd-Service und Nginx als Reverse Proxy einrichten** (siehe Web-Anleitung).

---

## 2. Docker-Installation

### Voraussetzungen

- Docker installiert ([Installationsanleitung](https://docs.docker.com/engine/install/))
- Optional: Docker Compose

### 2.1. Dockerfile erstellen

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
ENV FLASK_APP=web_app.py
ENV FLASK_RUN_HOST=0.0.0.0
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "web_app:app"]
```

### 2.2. Image bauen

```bash
docker build -t maschinengemeinschaft-web .
```

oder 

docker buildx create --use
docker buildx build -t maschinengemeinschaft-web .

### 2.3. Container starten

```bash
docker run -d \
  --name maschinengemeinschaft \
  -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  -e SECRET_KEY=dein_geheimer_schluessel \
  maschinengemeinschaft-web
```

### 2.4. Optional: Docker Compose

```yaml
version: "3.8"
services:
  web:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
    environment:
      - SECRET_KEY=dein_geheimer_schluessel
    restart: unless-stopped
```
Starten mit:
```bash
docker compose up -d
```

---

## 3. Reverse Proxy & HTTPS (empfohlen)

**Nginx-Konfiguration:**
```nginx
server {
    listen 80;
    server_name ihre-domain.de;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```
**HTTPS aktivieren:**
```bash
certbot --nginx -d ihre-domain.de
```

---

## 4. Sicherheit & Betrieb

- Starken `SECRET_KEY` setzen
- Debug-Modus deaktivieren
- Regelmäßige Backups von `./data`
- Firewall für Port 5000/80/443 konfigurieren

---

## 5. Support

Bei Problemen wenden Sie sich an den Administrator Ihrer Gemeinschaft.

---

**Stand:** Januar 2026