REM Datei: deploy_to_raspberry.bat

set LOCAL_DIR=C:\Users\HTFel\OneDrive\Gemeinschaften\Traktor\MGRSoftware
set REMOTE_USER=heizpi
set REMOTE_HOST=heizpi
set REMOTE_DIR=~/maschinengemeinschaft/deployment

REM Einzelne Dateien übertragen
scp %LOCAL_DIR%\web_app.py %REMOTE_USER%@%REMOTE_HOST%:%REMOTE_DIR%
scp %LOCAL_DIR%\database.py %REMOTE_USER%@%REMOTE_HOST%:%REMOTE_DIR%
scp %LOCAL_DIR%\requirements.txt %REMOTE_USER%@%REMOTE_HOST%:%REMOTE_DIR%
scp %LOCAL_DIR%\Dockerfile %REMOTE_USER%@%REMOTE_HOST%:%REMOTE_DIR%
scp -r %LOCAL_DIR%\data %REMOTE_USER%@%REMOTE_HOST%:%REMOTE_DIR%
scp -r %LOCAL_DIR%\deployment %REMOTE_USER%@%REMOTE_HOST%:%REMOTE_DIR%

echo Übertragung abgeschlossen!