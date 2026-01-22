#!/bin/bash
# Installationsskript für Maschinengemeinschaft-Software
# Voraussetzungen: Python 3, git, pip

set -e

# 1. System-Updates und Abhängigkeiten installieren (Beispiel für Debian/Ubuntu)
echo "System-Updates und Python installieren..."
sudo apt-get update && sudo apt-get install -y python3 python3-venv python3-pip git

# 2. Projekt klonen (falls nicht lokal)
# git clone <REPO_URL> <ZIELORDNER>
# cd <ZIELORDNER>

# 3. Virtuelle Umgebung anlegen
echo "Virtuelle Umgebung wird erstellt..."
python3 -m venv .venv
source .venv/bin/activate

# 4. Abhängigkeiten installieren
echo "Python-Abhängigkeiten werden installiert..."
pip install --upgrade pip
pip install -r requirements.txt

# 5. Datenbank initialisieren (falls nötig)
# echo "Initialisiere Datenbank..."
# python3 database.py --init

# 6. Startbefehl anzeigen
echo "Installation abgeschlossen!"
echo "Starte die Anwendung mit:"
echo "source .venv/bin/activate && python3 web_app.py"
