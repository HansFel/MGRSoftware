@echo off
REM MGR Software - Datenbank Synchronisation
REM Kopiert DB von mgs2 (Master) auf mgs1 und mgv1

echo.
echo ========================================
echo   Datenbank Synchronisation
echo   Quelle: MGS2 (Master)
echo ========================================
echo.

echo [1/5] Backup von MGS2 erstellen...
ssh mgserver@mgs2 "docker exec maschinengemeinschaft-db pg_dump -U mgr_user -d maschinengemeinschaft > /tmp/db_master.sql && ls -lh /tmp/db_master.sql"

echo.
echo [2/5] Backup herunterladen...
scp mgserver@mgs2:/tmp/db_master.sql "%TEMP%\mgr_db_master.sql"
if errorlevel 1 (
    echo FEHLER: Download fehlgeschlagen!
    pause
    exit /b 1
)

echo.
set /p sync_mgv1="MGV1 synchronisieren? (j/n): "
if /i "%sync_mgv1%"=="j" (
    echo [3/5] Backup zu MGV1 hochladen...
    scp "%TEMP%\mgr_db_master.sql" mgserver@mgv1:/tmp/db_master.sql
    echo Restore auf MGV1...
    ssh mgserver@mgv1 "sudo docker exec -i maschinengemeinschaft-db psql -U mgr_user -d maschinengemeinschaft < /tmp/db_master.sql"
    ssh mgserver@mgv1 "sudo docker restart maschinengemeinschaft-app"
    echo   MGV1 synchronisiert!
)

echo.
set /p sync_mgs1="MGS1 (PRODUKTION) synchronisieren? (j/n): "
if /i "%sync_mgs1%"=="j" (
    echo [4/5] Backup zu MGS1 hochladen...
    scp "%TEMP%\mgr_db_master.sql" mgserver@mgs1:/tmp/db_master.sql
    echo Restore auf MGS1...
    ssh mgserver@mgs1 "docker exec -i maschinengemeinschaft-db psql -U mgr_user -d maschinengemeinschaft < /tmp/db_master.sql"
    ssh mgserver@mgs1 "docker restart maschinengemeinschaft-app"
    echo   MGS1 synchronisiert!
)

echo.
echo ========================================
echo   Synchronisation abgeschlossen!
echo ========================================
pause
