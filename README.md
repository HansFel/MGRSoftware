# MGRSoftware

Ein Open-Source-System zur gemeinschaftlichen Maschinennutzung, Verwaltung und fairen Abrechnung.

Ideal für Vereine, Werkstätten, Maker-Spaces, landwirtschaftliche Gemeinschaften und alle Gruppen, die Maschinen gemeinsam nutzen und transparent verwalten möchten.

## Funktionen

- **Nutzerverwaltung** - Rollen, Berechtigungen, Admin-Levels
- **Maschinenverwaltung** - Maschinen anlegen, Wartung, Stundenzähler
- **Einsatzerfassung** - Datum, Stunden, Treibstoff, automatische Berechnung
- **Reservierungssystem** - Maschinen reservieren, Kalenderübersicht
- **Abrechnungssystem** - Kosten pro Stunde, automatische Berechnung
- **Bank-Import** - CSV-Import von Kontoauszügen (ELBA, etc.)
- **Statistiken** - Nutzungshäufigkeit, Kostenübersicht, Auslastung
- **Multi-Gemeinschaft** - Mehrere Gemeinschaften in einer Instanz
- **Übungsmodus** - Gefahrloses Testen mit Beispieldaten

## Technologie

| Komponente | Technologie |
|------------|-------------|
| Backend | Python / Flask |
| Datenbank | PostgreSQL (Server) / SQLite (lokal) |
| Frontend | HTML, CSS, JavaScript |
| Reverse Proxy | Caddy (automatisches HTTPS) |
| Deployment | Docker / Docker Compose |

## Schnellstart

### Lokales Testen (Windows)

```cmd
git clone https://github.com/HansFel/MGRSoftware.git
cd MGRSoftware
start_local.bat
```

Browser öffnen: http://localhost:5000
Login: `admin` / `admin123`

Siehe [docs/LOKALE_TESTVERSION.md](docs/LOKALE_TESTVERSION.md) für Details.

### Server-Deployment (Docker)

```bash
cd deployment
cp .env.example .env
# .env anpassen (Passwörter, Domain)
docker compose up -d
```

Siehe [docs/system/POSTGRESQL_INSTALLATION.md](docs/system/POSTGRESQL_INSTALLATION.md) für Details.

## Dokumentation

| Dokument | Beschreibung |
|----------|--------------|
| [LOKALE_TESTVERSION.md](docs/LOKALE_TESTVERSION.md) | Lokales Testen auf Windows |
| [POSTGRESQL_INSTALLATION.md](docs/system/POSTGRESQL_INSTALLATION.md) | PostgreSQL Server-Setup |
| [SCHNELLSTART.md](docs/benutzer/SCHNELLSTART.md) | Benutzer-Schnellstart |
| [WEB_ANLEITUNG.md](docs/benutzer/WEB_ANLEITUNG.md) | Web-Oberfläche Anleitung |
| [CSV_IMPORT_ANLEITUNG.md](CSV_IMPORT_ANLEITUNG.md) | Bank-CSV Import |
| [ADMIN_ROLLEN.md](docs/admin/ADMIN_ROLLEN.md) | Admin-Rollen und Rechte |

## Projektstruktur

```
MGRSoftware/
├── deployment/          # Server-Deployment (Docker)
│   ├── web_app.py       # Flask-App (modular)
│   ├── database.py      # Datenbank-Modul
│   ├── routes/          # Routen (Blueprints)
│   ├── templates/       # HTML-Templates
│   ├── static/          # CSS, JS, Fonts
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── Caddyfile
├── docs/                # Dokumentation
├── data/                # Lokale Datenbanken
├── start_local.bat      # Lokaler Teststart (Windows)
└── schema.sql           # SQLite-Schema
```

## Lizenz

Dieses Projekt steht unter der [GPL-3.0-Lizenz](LICENSE).

## Unterstützen

Unterstütze die Entwicklung von MGRSoftware:

👉 [GitHub Sponsors](https://github.com/sponsors/HansFel)

Jeder Beitrag hilft, neue Features zu entwickeln und das Projekt langfristig zu pflegen.

---

*Stand: Januar 2026*
