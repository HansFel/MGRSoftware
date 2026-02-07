# Update: Reservierungssystem erweitert
**Datum:** 14. Januar 2026

## Neue Features

### 1. Archivierung gelöschter Reservierungen
- Gelöschte/stornierte Reservierungen werden jetzt in einer separaten Tabelle gespeichert
- Vollständige Historie aller Reservierungen bleibt erhalten
- Neue Ansicht: "Gelöschte Reservierungen" zeigt alle stornierten Reservierungen

### 2. Grafische Kalenderansicht
- Neue Kalenderansicht für alle Reservierungen
- Übersicht über die nächsten 30 Tage
- Farbliche Unterscheidung:
  - Lila: Reservierungen anderer Benutzer
  - Grün: Eigene Reservierungen
- Filter nach einzelnen Maschinen möglich
- Anzeige von Datum, Zeit, Dauer und Benutzer

### 3. Verbesserte Navigation
- Neuer Menüpunkt "Kalender" in der Hauptnavigation
- Buttons für schnellen Zugriff auf Kalender und gelöschte Reservierungen
- Übersichtlichere Darstellung aller Reservierungen

## Installation

### Schritt 1: Migration ausführen
Die neue Datenbanktabelle muss erstellt werden:

```bash
# Im Hauptverzeichnis:
python migrate_geloeschte_reservierungen.py

# ODER im Deployment/Docker:
docker-compose exec web python3 migrate_geloeschte_reservierungen.py
```

### Schritt 2: Anwendung neu starten
```bash
# Lokale Installation:
# Starten Sie die Anwendung neu (z.B. über den Launcher)

# Docker Installation:
docker-compose restart web
```

## Neue Routen

- `/geloeschte-reservierungen` - Zeigt alle gelöschten Reservierungen des Benutzers
- `/reservierungen-kalender` - Kalenderansicht aller Reservierungen
- `/reservierungen-kalender?maschine_id=X` - Kalenderansicht für spezifische Maschine

## Datenbank-Änderungen

### Neue Tabelle: `reservierungen_geloescht`
Speichert gelöschte Reservierungen mit folgenden Feldern:
- `id` - Primärschlüssel
- `reservierung_id` - ID der ursprünglichen Reservierung
- `maschine_id` / `maschine_bezeichnung` - Maschineninfos
- `benutzer_id` / `benutzer_name` - Benutzerinfos
- `datum`, `uhrzeit_von`, `uhrzeit_bis` - Zeitinformationen
- `nutzungsdauer_stunden` - Geplante Dauer
- `zweck`, `bemerkung` - Zusatzinformationen
- `erstellt_am` - Wann wurde die Reservierung erstellt
- `geloescht_am` - Wann wurde sie gelöscht
- `geloescht_von` - Wer hat sie gelöscht
- `grund` - Grund der Löschung

## Änderungen an bestehenden Funktionen

### Reservierung stornieren
- Beim Stornieren wird die Reservierung jetzt automatisch archiviert
- Alle Daten bleiben erhalten für spätere Auswertungen
- Benutzer erhalten Bestätigung über erfolgreiche Archivierung

## Verwendung

### Gelöschte Reservierungen anzeigen
1. Navigation: "Reservierungen" → Button "Gelöschte Reservierungen"
2. Zeigt die letzten 100 gelöschten Reservierungen
3. Sortiert nach Löschdatum (neueste zuerst)

### Kalenderansicht verwenden
1. Navigation: Klick auf "Kalender" in der Hauptnavigation
2. ODER: "Reservierungen" → Button "Kalender-Ansicht"
3. Optional: Maschine aus Dropdown auswählen für gefilterte Ansicht
4. Übersicht über alle Reservierungen der nächsten 30 Tage

## Vorteile

- **Nachvollziehbarkeit:** Keine Reservierung geht mehr verloren
- **Transparenz:** Bessere Übersicht über Maschinenauslastung
- **Planung:** Kalenderansicht erleichtert Koordination zwischen Mitgliedern
- **Historie:** Auswertung von Nutzungsmustern möglich

## Technische Details

### Geänderte Dateien
- `web_app.py` - Neue Routes und aktualisierte Stornierungslogik
- `templates/geloeschte_reservierungen.html` - Neue Ansicht
- `templates/reservierungen_kalender.html` - Neue Kalenderansicht
- `templates/meine_reservierungen.html` - Erweiterte Buttons
- `templates/base.html` - Neuer Menüpunkt
- `migrate_geloeschte_reservierungen.py` - Neue Migration

### Deployment
Alle Änderungen wurden auch ins `deployment/`-Verzeichnis übernommen.

## Support

Bei Fragen oder Problemen:
1. Prüfen Sie, ob die Migration erfolgreich durchgelaufen ist
2. Überprüfen Sie die Logs auf Fehler
3. Stellen Sie sicher, dass alle Templates kopiert wurden
