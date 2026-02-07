@echo off
REM MGR Software - Deployment auf alle Server
REM Einheitliche Struktur: /opt/mgr auf allen Servern

echo.
echo ========================================
echo   MGR Software Deployment
echo ========================================
echo.

REM Git Push
echo [1/4] Git Push...
git add -A
git commit -m "Deploy %date% %time%" 2>nul
git push
if errorlevel 1 (
    echo FEHLER: Git push fehlgeschlagen!
    pause
    exit /b 1
)

REM mgv1 (Entwicklung) - immer zuerst
echo.
echo [2/4] MGV1 (Entwicklung)...
ssh mgserver@mgv1 "cd /opt/mgr && git pull && cd deployment && sudo docker rm -f maschinengemeinschaft-app 2>/dev/null; sudo docker compose up -d --build web caddy"

echo.
echo ============================================
echo   MGV1 aktualisiert! Testen: http://mgv1:5000
echo ============================================
echo.

set /p confirm2="MGS2 (REPLIKATION) aktualisieren? (j/n): "
if /i not "%confirm2%"=="j" goto skip_mgs2

echo.
echo [3/4] MGS2 (Replikation)...
ssh mgserver@mgs2 "cd /opt/mgr && git pull && cd deployment && docker rm -f maschinengemeinschaft-app 2>/dev/null; docker-compose up -d --build web caddy"
echo   MGS2 aktualisiert!

:skip_mgs2
set /p confirm1="MGS1 (PRODUKTION) aktualisieren? (j/n): "
if /i not "%confirm1%"=="j" goto status

echo.
echo [4/4] MGS1 (PRODUKTION)...
ssh mgserver@mgs1 "cd /opt/mgr && git pull && cd deployment && docker rm -f maschinengemeinschaft-app 2>/dev/null; docker-compose up -d --build web caddy"
echo   MGS1 aktualisiert!

:status
echo.
echo ========================================
echo   Server Status
echo ========================================
echo.
echo MGV1:
ssh mgserver@mgv1 "sudo docker ps --format '  {{.Names}}: {{.Status}}' | grep maschinengemeinschaft"
echo.
echo MGS2:
ssh mgserver@mgs2 "docker ps --format '  {{.Names}}: {{.Status}}' | grep maschinengemeinschaft"
echo.
echo MGS1:
ssh mgserver@mgs1 "docker ps --format '  {{.Names}}: {{.Status}}' | grep maschinengemeinschaft"
echo.
echo ========================================
pause
