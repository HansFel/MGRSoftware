@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo   Maschinengemeinschaft - Lokaler Test
echo ========================================
echo.

REM Pruefen ob Python installiert ist
python --version >nul 2>&1
if errorlevel 1 (
    echo FEHLER: Python ist nicht installiert!
    echo Bitte Python von https://python.org installieren.
    pause
    exit /b 1
)

REM Virtuelle Umgebung pruefen/erstellen
if not exist ".venv" (
    echo Erstelle virtuelle Umgebung...
    python -m venv .venv
)

REM Virtuelle Umgebung aktivieren
call .venv\Scripts\activate.bat

REM Dependencies installieren (falls noetig)
pip show flask >nul 2>&1
if errorlevel 1 (
    echo Installiere Abhaengigkeiten...
    pip install -r deployment\requirements.txt
)

REM Ins deployment Verzeichnis wechseln
cd deployment

REM Umgebungsvariablen fuer lokalen SQLite-Modus
set DB_TYPE=sqlite
set DB_PATH=../data/test_lokal.db
set SECRET_KEY=lokaler-test-key-2026
set FLASK_ENV=development

echo.
echo Starte lokalen Server (modulare Version)...
echo Datenbank: %DB_PATH%
echo.
echo Oeffne im Browser: http://localhost:5000
echo.
echo Zum Beenden: Strg+C druecken
echo ========================================
echo.

REM Server starten
python web_app.py
