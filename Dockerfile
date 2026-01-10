FROM python:3.11-slim

# Arbeitsverzeichnis erstellen
WORKDIR /app

# System-Abhängigkeiten installieren
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python-Abhängigkeiten kopieren und installieren
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Anwendungscode kopieren
COPY database.py .
COPY web_app.py .
COPY schema.sql .
COPY templates ./templates/

# Datenverzeichnis erstellen
RUN mkdir -p /data

# Umgebungsvariablen
ENV PYTHONUNBUFFERED=1
ENV DB_PATH=/data/maschinengemeinschaft.db

# Port exponieren
EXPOSE 5000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/login')" || exit 1

# Startskript
CMD ["python", "web_app.py"]
