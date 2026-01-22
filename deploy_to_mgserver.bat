REM Datei: deploy_to_mgserver.bat

set LOCAL_DIR=C:\Users\HTFel\OneDrive\Gemeinschaften\Traktor\MGRSoftware
set REMOTE_USER=mgserver
set REMOTE_HOST=mgserver
set REMOTE_DIR=~/mgserver

REM Einzelne Dateien übertragen
scp %LOCAL_DIR%\web_app.py %REMOTE_USER%@%REMOTE_HOST%:%REMOTE_DIR%
scp %LOCAL_DIR%\database.py %REMOTE_USER%@%REMOTE_HOST%:%REMOTE_DIR%
scp %LOCAL_DIR%\requirements.txt %REMOTE_USER%@%REMOTE_HOST%:%REMOTE_DIR%
scp %LOCAL_DIR%\Dockerfile %REMOTE_USER%@%REMOTE_HOST%:%REMOTE_DIR%
scp %LOCAL_DIR%\docker-compose.yml %REMOTE_USER%@%REMOTE_HOST%:%REMOTE_DIR%
scp -r %LOCAL_DIR%\data %REMOTE_USER%@%REMOTE_HOST%:%REMOTE_DIR%

REM Docker Compose neu starten (als root)
ssh %REMOTE_USER%@%REMOTE_HOST% "cd ~/maschinengemeinschaft/deployment && sudo docker compose down && sudo docker compose up -d --build"

echo Übertragung und Deployment abgeschlossen!