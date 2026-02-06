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
if /i "%confirm2%"=="j" (
    echo.
    echo --- MGS2 (Replikation) ---
    ssh mgserver@mgs2 "cd /home/mgserver/mgserver && git pull origin main && cd deployment && docker-compose restart web"
    echo.
    echo   MGS2 aktualisiert! Testen: http://mgs2:5000
    echo.
)

set /p confirm1="MGS1 (PRODUKTION) aktualisieren? (j/n): "
if /i "%confirm1%"=="j" (
    echo.
    echo --- MGS1 (PRODUKTION) ---
    ssh mgserver@mgs1 "cd /home/mgserver/mgserver && git pull origin main && cd deployment && docker-compose restart web"
    echo.
    echo === Produktion aktualisiert! ===
) else (
    echo.
    echo MGS1 wurde NICHT aktualisiert.
)

pause
