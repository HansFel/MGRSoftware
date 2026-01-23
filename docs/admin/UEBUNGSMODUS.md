# Übungsmodus - Lokale Installation

## Übersicht

Der Übungsmodus ermöglicht es Benutzern, die Maschinengemeinschaft-Software auf ihrem eigenen Computer zu installieren und zu testen, ohne die Produktions-Datenbank zu beeinflussen.

## Installation

### Für Endbenutzer (EXE-Datei)

1. **Download**
   - Laden Sie `Maschinengemeinschaft.exe` herunter
   - Keine weitere Installation nötig!

2. **Starten**
   - Doppelklick auf `Maschinengemeinschaft.exe`
   - Das Launcher-Fenster öffnet sich

3. **Datenbank wählen**
   - **Neue Datenbank erstellen**: Erstellt eine leere Übungs-Datenbank
   - **Bestehende Datenbank**: Wählen Sie eine `.db` Datei zum Üben

4. **Server starten**
   - Klicken Sie auf "Server starten"
   - Der Browser öffnet sich automatisch
   - Die URL wird angezeigt (z.B. `http://127.0.0.1:5000`)

5. **Login**
   - Bei neuer Datenbank:
     - Benutzername: `admin`
     - Passwort: `admin123`

## EXE-Datei erstellen (für Entwickler)

### Voraussetzungen

```bash
pip install pyinstaller
```

### Build-Prozess

1. **Einfache Methode**:
   ```bash
   python build_exe.py
   ```

2. **Manuelle Methode**:
   ```bash
   pyinstaller --name=Maschinengemeinschaft ^
               --onefile ^
               --windowed ^
               --add-data="templates;templates" ^
               --add-data="static;static" ^
               --add-data="schema.sql;." ^
               --hidden-import=flask ^
               --hidden-import=sqlite3 ^
               launcher.py
   ```

3. **Ausgabe**:
   - Die EXE-Datei befindet sich in `dist/Maschinengemeinschaft.exe`

### Distribution Package erstellen

Erstellen Sie einen Ordner mit:
```
Maschinengemeinschaft/
├── Maschinengemeinschaft.exe
├── ANLEITUNG.txt
├── schema.sql (wird automatisch eingebettet)
└── beispiel_datenbanken/
    └── uebung.db (optional)
```

## Technische Details

### Launcher (launcher.py)

Der Launcher ist eine grafische Anwendung (Tkinter), die:
- Eine Datenbankauswahl-Dialog bietet
- Den Flask-Server im Hintergrund startet
- Einen freien Port automatisch findet
- Den Browser mit der richtigen URL öffnet
- Den Server-Status anzeigt
- Sauberes Herunterfahren ermöglicht

### Umgebungsvariablen

Der Launcher setzt folgende Variablen für web_app.py:
- `DB_PATH`: Pfad zur gewählten Datenbank
- `FLASK_PORT`: Verwendeter Port (automatisch gefunden)

### web_app.py Anpassungen

Fügen Sie am Anfang von web_app.py hinzu:

```python
# Übungsmodus: Datenbank-Pfad aus Umgebungsvariable
DB_PATH = os.environ.get('DB_PATH')
if DB_PATH:
    DATABASE = DB_PATH
else:
    DATABASE = os.path.join(os.path.dirname(__file__), 'data', 'maschinengemeinschaft.db')

# Port aus Umgebungsvariable
FLASK_PORT = int(os.environ.get('FLASK_PORT', 5000))
```

Und am Ende der Datei:

```python
if __name__ == '__main__':
    port = int(os.environ.get('FLASK_PORT', 5000))
    app.run(host='127.0.0.1', port=port, debug=False)
```

## Sicherheitshinweise

### Was ist sicher im Übungsmodus?

- ✓ Läuft nur lokal (127.0.0.1)
- ✓ Nicht vom Netzwerk aus erreichbar
- ✓ Eigene Datenbank pro Installation
- ✓ Keine Auswirkung auf Produktions-Server

### Was sollten Benutzer wissen?

- Dies ist nur zum Üben gedacht
- Änderungen wirken sich nicht auf die echte Datenbank aus
- Zum Üben sollte eine separate Datenbank verwendet werden
- Die Daten bleiben auf dem lokalen Computer

## Anwendungsfälle

1. **Schulung neuer Benutzer**
   - Benutzer können alle Funktionen testen
   - Keine Angst, etwas kaputt zu machen
   - Praktisches Lernen

2. **Admin-Training**
   - Admin-Funktionen ausprobieren
   - Berichte testen
   - Workflow verstehen

3. **Offline-Nutzung**
   - Funktioniert ohne Internetverbindung
   - Demonstration bei Besprechungen
   - Mobile Präsentationen

4. **Entwicklung/Testing**
   - Schnelles lokales Testen
   - Verschiedene Datenbank-Zustände ausprobieren
   - Feature-Entwicklung

## Fehlerbehebung

### "Server konnte nicht gestartet werden"

- Port bereits belegt → Launcher findet automatisch einen freien Port
- Python nicht gefunden → Prüfen Sie die EXE-Build-Einstellungen
- Firewall blockiert → Windows Firewall-Ausnahme hinzufügen

### "Datenbank kann nicht geöffnet werden"

- Datei-Berechtigung fehlt → Als Administrator ausführen
- Datei beschädigt → Neue Datenbank erstellen
- Falsches Format → Muss SQLite3 Datenbank sein

### Browser öffnet sich nicht

- URL manuell kopieren und in Browser einfügen
- Standard-Browser prüfen
- Firewall-Einstellungen prüfen

## Beispiel-Anleitung für Benutzer

### ANLEITUNG.txt (für Distribution)

```
=== MASCHINENGEMEINSCHAFT - ÜBUNGSMODUS ===

INSTALLATION:
Keine Installation nötig! Einfach Maschinengemeinschaft.exe starten.

ERSTE SCHRITTE:
1. Programm starten (Doppelklick auf Maschinengemeinschaft.exe)
2. "Neue Datenbank" klicken
3. Speicherort wählen (z.B. Dokumente\MGR_Uebung.db)
4. "Server starten" klicken
5. Browser öffnet sich automatisch

LOGIN:
Benutzername: admin
Passwort: admin123

WICHTIG:
- Dies ist ein Übungssystem
- Ihre Daten bleiben auf Ihrem Computer
- Die echte Datenbank wird nicht verändert

SUPPORT:
Bei Fragen: [Ihre Kontakt-Info]
```

## Automatisches Update-System (Optional)

Für zukünftige Versionen können Sie ein Update-Mechanismus hinzufügen:

```python
def check_for_updates():
    """Prüft auf neue Versionen"""
    import requests
    try:
        response = requests.get('https://ihr-server.de/version.txt')
        latest_version = response.text.strip()
        current_version = "1.0.0"
        
        if latest_version > current_version:
            if messagebox.askyesno("Update verfügbar", 
                                   f"Neue Version {latest_version} verfügbar!\n"
                                   f"Jetzt herunterladen?"):
                webbrowser.open('https://ihr-server.de/download')
    except:
        pass  # Offline-Modus, kein Update-Check möglich
```

## Lizenzierung

Wenn Sie die Software verteilen, fügen Sie entsprechende Lizenz-Informationen hinzu:
- MIT License (frei verwendbar)
- GPL (Open Source erforderlich)
- Proprietär (Ihre eigenen Bedingungen)

Fügen Sie eine LICENSE.txt der Distribution hinzu.
