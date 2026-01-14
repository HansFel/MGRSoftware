@echo off
REM Build-Skript für Maschinengemeinschaft EXE
REM Einfach ausführen mit: build.bat

echo ============================================================
echo   Maschinengemeinschaft - EXE Build
echo ============================================================
echo.

REM Aktiviere virtuelle Umgebung falls vorhanden
if exist ".venv\Scripts\activate.bat" (
    echo Aktiviere virtuelle Umgebung...
    call .venv\Scripts\activate.bat
)

REM Prüfe ob PyInstaller installiert ist
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller nicht gefunden. Installiere...
    pip install pyinstaller
)

echo.
echo Starte Build-Prozess...
echo.

REM Erstelle EXE mit PyInstaller
pyinstaller --clean ^
    --name=Maschinengemeinschaft ^
    --onefile ^
    --windowed ^
    --add-data="templates;templates" ^
    --add-data="static;static" ^
    --add-data="schema.sql;." ^
    --add-data="web_app.py;." ^
    --add-data="database.py;." ^
    --hidden-import=flask ^
    --hidden-import=werkzeug ^
    --hidden-import=jinja2 ^
    --hidden-import=sqlite3 ^
    --collect-all=flask ^
    --collect-all=werkzeug ^
    launcher.py

if errorlevel 1 (
    echo.
    echo [FEHLER] Build fehlgeschlagen!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Build erfolgreich!
echo ============================================================
echo.
echo EXE-Datei: dist\Maschinengemeinschaft.exe
echo.

REM Erstelle Distribution-Ordner
echo Erstelle Distribution-Paket...
if not exist "distribution" mkdir distribution
copy dist\Maschinengemeinschaft.exe distribution\
copy ANLEITUNG_UEBUNGSMODUS.txt distribution\
copy schema.sql distribution\

if not exist "distribution\beispiel_datenbanken" mkdir distribution\beispiel_datenbanken

echo.
echo Distribution-Paket erstellt in: distribution\
echo.
echo Inhalt:
echo   - Maschinengemeinschaft.exe
echo   - ANLEITUNG_UEBUNGSMODUS.txt
echo   - schema.sql
echo   - beispiel_datenbanken\ (Ordner)
echo.
echo ============================================================
echo Fertig! Sie können jetzt den "distribution" Ordner
echo an Benutzer weitergeben.
echo ============================================================
echo.

pause
