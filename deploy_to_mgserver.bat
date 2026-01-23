REM Datei: deploy_to_mgserver.bat

set LOCAL_DIR=C:\Users\HTFel\OneDrive\Gemeinschaften\Traktor\MGRSoftware
set REMOTE_USER=mgserver
set REMOTE_HOST=mgserver
set REMOTE_DIR=~/mgserver

REM Einzelne Dateien übertragen
echo Übertrage Hauptdateien...
scp %LOCAL_DIR%\web_app.py %REMOTE_USER%@%REMOTE_HOST%:%REMOTE_DIR%
scp %LOCAL_DIR%\database.py %REMOTE_USER%@%REMOTE_HOST%:%REMOTE_DIR%
scp %LOCAL_DIR%\schema.sql %REMOTE_USER%@%REMOTE_HOST%:%REMOTE_DIR%
scp %LOCAL_DIR%\requirements.txt %REMOTE_USER%@%REMOTE_HOST%:%REMOTE_DIR%
scp %LOCAL_DIR%\Dockerfile %REMOTE_USER%@%REMOTE_HOST%:%REMOTE_DIR%
scp %LOCAL_DIR%\docker-compose.yml %REMOTE_USER%@%REMOTE_HOST%:%REMOTE_DIR%
scp %LOCAL_DIR%\create_training_databases.py %REMOTE_USER%@%REMOTE_HOST%:%REMOTE_DIR%

REM Templates übertragen
echo Übertrage Templates...
scp -r %LOCAL_DIR%\templates %REMOTE_USER%@%REMOTE_HOST%:%REMOTE_DIR%

REM Training-Verzeichnis erstellen und Datenbanken übertragen
echo Übertrage Training-Datenbanken...
ssh %REMOTE_USER%@%REMOTE_HOST% "mkdir -p %REMOTE_DIR%/data/training"
scp -r %LOCAL_DIR%\data\training %REMOTE_USER%@%REMOTE_HOST%:%REMOTE_DIR%/data/

REM Docker Compose neu starten (als root)
echo Starte Docker Container neu...
ssh %REMOTE_USER%@%REMOTE_HOST% "cd ~/maschinengemeinschaft/deployment && sudo docker compose down && sudo docker compose up -d --build"

echo.
echo ========================================
echo Übertragung und Deployment abgeschlossen!
echo ========================================