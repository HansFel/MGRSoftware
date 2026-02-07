# Lokale Testversion

Diese Anleitung beschreibt, wie Sie die Maschinengemeinschaft-Software lokal auf einem Windows-PC testen können, ohne die Produktions-Server zu beeinflussen.

## Voraussetzungen

- Windows 10/11
- Python 3.10 oder höher (https://python.org)
- Git (optional, für Updates)

## Schnellstart

1. **Doppelklick auf `start_local.bat`**

   Das Skript:
   - Erstellt eine virtuelle Python-Umgebung (beim ersten Mal)
   - Installiert alle Abhängigkeiten
   - Startet den lokalen Server

2. **Browser öffnen:** http://localhost:5000

3. **Login:**
   - Benutzer: `admin`
   - Passwort: `admin123`

4. **Beenden:** `Strg+C` im Terminal drücken

## Technische Details

### Datenbank

Die lokale Version verwendet **SQLite** statt PostgreSQL:

| Eigenschaft | Lokal | Server |
|-------------|-------|--------|
| Datenbank | SQLite | PostgreSQL |
| Datei | `data/test_lokal.db` | PostgreSQL-Server |
| Daten | Testdaten | Produktionsdaten |

Die lokale Datenbank ist komplett getrennt von den Produktions-Servern.

### Verzeichnisstruktur

```
MGRSoftware/
├── start_local.bat      # Startskript
├── data/
│   └── test_lokal.db    # Lokale SQLite-Datenbank
├── deployment/          # Server-Version (modulare Struktur)
│   ├── web_app.py       # Flask-App (Wrapper)
│   ├── database.py      # Datenbank-Modul
│   ├── schema.sql       # SQLite-Schema
│   ├── routes/          # Routen (Blueprints)
│   ├── templates/       # HTML-Templates
│   └── static/          # CSS, JS, Fonts
└── .venv/               # Virtuelle Python-Umgebung
```

### Umgebungsvariablen

Das Startskript setzt automatisch:

```
DB_TYPE=sqlite
DB_PATH=../data/test_lokal.db
SECRET_KEY=lokaler-test-key-2026
FLASK_ENV=development
```

## Fehlerbehebung

### "Python ist nicht installiert"

1. Python von https://python.org herunterladen
2. Bei der Installation **"Add Python to PATH"** aktivieren
3. Terminal neu öffnen

### "Internal Server Error"

Datenbank zurücksetzen:

```cmd
del data\test_lokal.db
start_local.bat
```

### Port 5000 bereits belegt

Anderen Port verwenden - in `deployment/web_app.py` ändern:

```python
app.run(host='0.0.0.0', port=5001, debug=True)
```

## Datenbank manuell initialisieren

Falls nötig:

```cmd
cd deployment
..\.venv\Scripts\python.exe test_db.py
```

## Unterschiede zur Server-Version

| Feature | Lokal | Server |
|---------|-------|--------|
| Datenbank | SQLite | PostgreSQL |
| HTTPS | Nein | Ja (Caddy) |
| Backup | Manuell | Automatisch |
| Multi-User | Eingeschränkt | Vollständig |

## Tipps für Entwickler

- Änderungen an Templates werden sofort wirksam (Debug-Modus)
- Python-Code-Änderungen erfordern Neustart
- Browser-Cache leeren bei CSS/JS-Änderungen (`Strg+Shift+R`)

---

*Erstellt: Januar 2026*
