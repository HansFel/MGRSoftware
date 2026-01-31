@echo off
chcp 65001 >nul
echo ========================================
echo   Maschinengemeinschaft - Lokaler Test
echo ========================================
echo.

:: Prüfen ob Python installiert ist
python --version >nul 2>&1
if errorlevel 1 (
    echo FEHLER: Python ist nicht installiert!
    echo Bitte Python von https://python.org installieren.
    pause
    exit /b 1
)

:: Virtuelle Umgebung prüfen/erstellen
if not exist ".venv" (
    echo Erstelle virtuelle Umgebung...
    python -m venv .venv
)

:: Virtuelle Umgebung aktivieren
call .venv\Scripts\activate.bat

:: Dependencies installieren (falls nötig)
pip show flask >nul 2>&1
if errorlevel 1 (
    echo Installiere Abhängigkeiten...
    pip install -r requirements.txt
)

:: Umgebungsvariablen für lokalen SQLite-Modus
set DB_TYPE=sqlite
set DB_PATH=data/test_lokal.db
set SECRET_KEY=lokaler-test-key-2026
set FLASK_ENV=development

echo.
echo Starte lokalen Server mit SQLite...
echo Datenbank: %DB_PATH%
echo.
echo Oeffne im Browser: http://localhost:5000
echo.
echo Zum Beenden: Strg+C druecken
echo ========================================
echo.

:: Server starten
python web_app.py
