# Maschinengemeinschaft - Verwaltungssoftware

Datenbanksystem zur Verwaltung von Maschineneinsätzen für eine Maschinengemeinschaft.

## Funktionen

### 📋 Einsätze erfassen
- Datum des Einsatzes
- Benutzer (aus Benutzertabelle)
- Maschine (aus Maschinentabelle)
- Einsatzzweck (aus Einsatzzweck-Tabelle)
- Anfangstand und Endstand des Stundenzählers
- Automatische Berechnung der Betriebsstunden
- Treibstoffverbrauch und -kosten
- Anmerkungen

### 👥 Benutzerverwaltung
- Name, Vorname
- Kontaktdaten (Telefon, E-Mail, Adresse)
- Mitgliedschaft seit
- Bemerkungen

### 🚜 Maschinenverwaltung
- Bezeichnung, Hersteller, Modell
- Baujahr, Kennzeichen
- Aktueller Stundenzähler (wird automatisch aktualisiert)
- Wartungsintervalle
- Bemerkungen

### 📊 Statistiken
- Einsätze pro Benutzer
- Einsätze pro Maschine
- Betriebsstunden-Übersicht
- Treibstoffverbrauch
- Kostenübersicht

## Installation

### Voraussetzungen
- Python 3.8 oder höher
- Tkinter (normalerweise bereits in Python enthalten)

### Schritt 1: Python installieren
Falls noch nicht installiert, laden Sie Python von [python.org](https://www.python.org/downloads/) herunter.

### Schritt 2: Anwendung starten
```powershell
# Im Projektverzeichnis
python main.py
```

Beim ersten Start wird automatisch die Datenbank erstellt und mit Beispiel-Einsatzzwecken gefüllt.

## Verwendung

### 1. Stammdaten einrichten

Bevor Sie Einsätze erfassen können, müssen Sie zunächst die Stammdaten anlegen:

#### Benutzer anlegen
1. Menü: **Stammdaten → Benutzer verwalten**
2. Klicken Sie auf **Neuer Benutzer**
3. Geben Sie mindestens den Namen ein
4. Klicken Sie auf **Speichern**

#### Maschinen anlegen
1. Menü: **Stammdaten → Maschinen verwalten**
2. Klicken Sie auf **Neue Maschine**
3. Geben Sie mindestens die Bezeichnung ein
4. Tragen Sie den aktuellen Stundenzähler-Stand ein
5. Klicken Sie auf **Speichern**

#### Einsatzzwecke (optional)
Die Datenbank wird bereits mit Standard-Einsatzzwecken gefüllt:
- Mähen
- Pflügen
- Säen
- Ernten
- Transportfahrten
- Schneeräumung
- Holzarbeiten
- Grünlandpflege
- Wegeinstandhaltung
- Sonstiges

Sie können weitere über **Stammdaten → Einsatzzwecke verwalten** hinzufügen.

### 2. Einsätze erfassen

#### Tab "Neuer Einsatz"
1. **Datum**: Wird automatisch auf heute gesetzt
2. **Benutzer**: Wählen Sie den Benutzer aus
3. **Maschine**: Wählen Sie die Maschine aus (Anfangstand wird automatisch vorgeschlagen)
4. **Einsatzzweck**: Wählen Sie den Zweck aus
5. **Anfangstand**: Stundenzähler zu Beginn
6. **Endstand**: Stundenzähler am Ende
7. **Betriebsstunden**: Werden automatisch berechnet
8. **Treibstoffverbrauch**: Optional in Litern
9. **Treibstoffkosten**: Optional in Euro
10. **Anmerkungen**: Freier Text
11. Klicken Sie auf **Einsatz speichern**

**Wichtig**: Der Stundenzähler der Maschine wird automatisch auf den Endstand aktualisiert!

### 3. Einsätze anzeigen

#### Tab "Einsatzübersicht"
- Zeigt die letzten 100 Einsätze
- Sortiert nach Datum (neueste zuerst)
- Klicken Sie auf **Aktualisieren**, um die Liste zu aktualisieren

### 4. Statistiken ansehen

#### Tab "Statistiken"
- **Benutzer-Statistik**: Wählen Sie einen Benutzer aus
  - Anzahl Einsätze
  - Gesamte Betriebsstunden
  - Gesamter Treibstoffverbrauch
  - Gesamte Kosten

- **Maschinen-Statistik**: Wählen Sie eine Maschine aus
  - Aktueller Stundenzähler
  - Anzahl Einsätze
  - Gesamte Betriebsstunden
  - Gesamter Treibstoffverbrauch
  - Anzahl verschiedener Benutzer

## Datenbankstruktur

### Tabellen
1. **benutzer**: Alle Mitglieder der Gemeinschaft
2. **maschinen**: Alle Maschinen/Geräte
3. **einsatzzwecke**: Zwecke für Maschineneinsätze
4. **maschineneinsaetze**: Haupttabelle mit allen Einsätzen

### Datenbank-Datei
Die SQLite-Datenbank wird als `maschinengemeinschaft.db` im Programmverzeichnis gespeichert.

## Datensicherung

**Wichtig**: Sichern Sie regelmäßig Ihre Datenbank!

Die Datei `maschinengemeinschaft.db` enthält alle Ihre Daten. Kopieren Sie diese Datei regelmäßig an einen sicheren Ort.

```powershell
# Beispiel: Backup erstellen
Copy-Item maschinengemeinschaft.db maschinengemeinschaft_backup_$(Get-Date -Format 'yyyyMMdd').db
```

## Fehlerbehebung

### Problem: "Datenbank nicht gefunden"
**Lösung**: Starten Sie die Anwendung neu. Die Datenbank wird automatisch erstellt.

### Problem: "Keine Benutzer/Maschinen in der Auswahl"
**Lösung**: Legen Sie zunächst Stammdaten an (siehe oben).

### Problem: "Endstand muss größer als Anfangstand sein"
**Lösung**: Überprüfen Sie die eingegebenen Stundenzähler-Werte.

## Technische Details

### Dateien
- `schema.sql`: Datenbank-Schema (Tabellendefinitionen)
- `database.py`: Datenbankmodul mit allen Funktionen
- `main.py`: GUI-Anwendung
- `maschinengemeinschaft.db`: SQLite-Datenbank (wird automatisch erstellt)

### Verwendete Technologien
- **Python 3**: Programmiersprache
- **SQLite**: Eingebettete Datenbank
- **Tkinter**: GUI-Framework (plattformübergreifend)

### Besondere Features
- **Automatische Stundenzähler-Aktualisierung**: Beim Speichern eines Einsatzes wird der Stundenzähler der Maschine automatisch aktualisiert
- **Berechnete Felder**: Betriebsstunden werden automatisch aus Anfang- und Endstand berechnet
- **Datenintegrität**: Fremdschlüssel stellen sicher, dass keine ungültigen Referenzen entstehen
- **Soft Delete**: Benutzer und Maschinen werden nur deaktiviert, nicht gelöscht

## Erweiterungsmöglichkeiten

Das System kann bei Bedarf erweitert werden um:
- Export nach Excel/CSV
- Rechnungserstellung
- Wartungserinnerungen
- Mehrbenutzer-Zugriff mit Benutzeranmeldung
- Druckfunktionen
- Erweiterte Auswertungen und Berichte

## Lizenz

Dieses Programm wurde für die Maschinengemeinschaft erstellt.

## Kontakt

Bei Fragen oder Problemen wenden Sie sich an den Administrator Ihrer Gemeinschaft.

---

**Version**: 1.0  
**Erstellt**: Januar 2026
