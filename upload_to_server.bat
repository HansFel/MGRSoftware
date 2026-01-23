@echo off
REM ============================================================================
REM   MASCHINENGEMEINSCHAFT - DATEIEN AUF SERVER HOCHLADEN
REM ============================================================================

echo.
echo ============================================
echo   Maschinengemeinschaft - Server Upload
echo ============================================
echo.

set /p SERVER_IP="Server IP-Adresse: "
set /p SERVER_USER="Server Benutzer (Standard: mgr): "
if "%SERVER_USER%"=="" set SERVER_USER=mgr

set APP_DIR=/opt/maschinengemeinschaft

echo.
echo Lade Dateien hoch nach %SERVER_USER%@%SERVER_IP%:%APP_DIR%
echo.

REM Dateien hochladen (ohne .venv, __pycache__, .git, data/*.db)
scp -r ^
    web_app.py ^
    database.py ^
    schema.sql ^
    schema_postgresql.sql ^
    migrate_to_postgresql.py ^
    templates ^
    static ^
    %SERVER_USER%@%SERVER_IP%:%APP_DIR%/

echo.
echo ============================================
echo   Upload abgeschlossen!
echo ============================================
echo.
echo Naechste Schritte auf dem Server:
echo.
echo   ssh %SERVER_USER%@%SERVER_IP%
echo   cd %APP_DIR%
echo   source .venv/bin/activate
echo   source .env
echo   python migrate_to_postgresql.py
echo   sudo systemctl start maschinengemeinschaft
echo.

pause
