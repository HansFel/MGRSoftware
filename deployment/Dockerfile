# Dockerfile für Maschinengemeinschaft Flask-App
FROM python:3.11-slim

# Systempakete installieren
RUN apt-get update && \
    apt-get install -y build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Arbeitsverzeichnis
WORKDIR /opt/maschinengemeinschaft

# Requirements kopieren und installieren
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Quellcode kopieren
COPY . .

# Virtuelle Umgebung (optional, für Kompatibilität mit bestehenden Skripten)
RUN python -m venv .venv && \
    . .venv/bin/activate && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

# Port
EXPOSE 5000

# Startbefehl (wird von docker-compose überschrieben)
CMD ["bash", "-c", ". .venv/bin/activate && gunicorn -w 4 -b 0.0.0.0:5000 web_app:app"]
