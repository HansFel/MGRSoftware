# Dockerfile für Maschinengemeinschaft Flask-App
FROM python:3.11-slim

# Systempakete installieren
RUN apt-get update && \
    apt-get install -y build-essential libpq-dev iputils-ping postgresql-client && \
    rm -rf /var/lib/apt/lists/*

# Arbeitsverzeichnis
WORKDIR /opt/maschinengemeinschaft

# Requirements kopieren und installieren
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Quellcode kopieren
COPY . .

# Port
EXPOSE 5000

# Startbefehl
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "web_app:app"]
