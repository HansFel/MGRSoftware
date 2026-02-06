@echo off
echo === Deployment ===

echo.
echo --- MGV1 (Entwicklung) ---
ssh mgserver@mgv1 "cd /opt/mgr && git pull origin main && cd deployment && docker compose restart web"

echo.
echo ============================================
echo   Entwicklungs-Server aktualisiert!
echo   Bitte testen: http://mgv1:5000
echo ============================================
echo.

set /p confirm2="MGS2 (REPLIKATION) aktualisieren? (j/n): "
if /i "%confirm2%"=="j" goto deploy_mgs2
goto skip_mgs2

:deploy_mgs2
echo.
echo --- MGS2 (Replikation) ---
ssh mgserver@mgs2 "cd /home/mgserver/mgserver && git pull origin main && cd deployment && docker-compose restart web"
echo.
echo   MGS2 aktualisiert! Testen: http://mgs2:5000
echo.

:skip_mgs2
set /p confirm1="MGS1 (PRODUKTION) aktualisieren? (j/n): "
if /i "%confirm1%"=="j" goto deploy_mgs1
goto ende

:deploy_mgs1
echo.
echo --- MGS1 (PRODUKTION) ---
ssh mgserver@mgs1 "cd /home/mgserver/mgserver && git pull origin main && cd deployment && docker-compose restart web"
echo.
echo === Produktion aktualisiert! ===
goto ende

:ende
echo.
pause
