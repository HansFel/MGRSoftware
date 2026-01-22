FROM python:3.11-slim

# Arbeitsverzeichnis erstellen
WORKDIR /app

# Abhängigkeiten installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Projektdateien kopieren
COPY . .

# Port freigeben
EXPOSE 5000

# Umgebungsvariablen (optional)
ENV FLASK_APP=web_app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Start mit Gunicorn (empfohlen für Produktion)
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "web_app:app"]
