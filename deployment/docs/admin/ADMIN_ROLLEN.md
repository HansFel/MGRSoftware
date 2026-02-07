# Administrator-Rollen und Berechtigungen

## Übersicht

Das System unterstützt drei verschiedene Berechtigungsstufen:

### 1. Normaler Benutzer (Level 0)
- Kann eigene Maschineneinsätze erfassen
- Kann Reservierungen erstellen und stornieren
- Kann Nachrichten an Gemeinschaft senden
- Kann eigene stornierte Einsätze einsehen
- Kann eigene Einstellungen ändern

### 2. Gemeinschafts-Administrator (Level 1)
- **Alle Rechte des normalen Benutzers**
- Kann Benutzer und Maschinen **seiner zugewiesenen Gemeinschaften** verwalten
- Kann Einsätze der Mitglieder seiner Gemeinschaften einsehen und stornieren
- Sieht Backup-Warnungen, kann aber keine Backups bestätigen

**Wichtig:** Ein Gemeinschafts-Administrator muss explizit einer oder mehreren Gemeinschaften zugewiesen werden!

### 3. Haupt-Administrator (Level 2)
- **Alle Rechte des Gemeinschafts-Administrators**
- Kann **alle Gemeinschaften** verwalten
- Kann Administrator-Rollen vergeben und ändern
- Kann Gemeinschafts-Administratoren Gemeinschaften zuweisen
- **Kann Datenbank-Backups bestätigen** (mit Zwei-Personen-Regel)
- **Kann Notfall-Setup nutzen** (Backup-Restore mit Zwei-Personen-Regel)

---

## Zwei-Personen-Regel

Die Zwei-Personen-Regel gilt für alle kritischen Datenbankoperationen:
- Backup-Bestätigungen im Dashboard
- **Notfall-Wiederherstellung über /setup**

### Zweck
Aus Sicherheitsgründen müssen **immer zwei Haupt-Administratoren** unabhängig voneinander kritische Aktionen bestätigen. Dies verhindert versehentliche oder unautorisierte Änderungen.

---

## Zwei-Personen-Regel für Backup-Bestätigungen (Dashboard)

### Ablauf

1. **Erster Haupt-Administrator bestätigt:**
   - Sieht Backup-Warnung im Dashboard
   - Erstellt physisches Backup der Datenbank
   - Klickt "Backup durchgeführt - bestätigen"
   - Gibt optional eine Bemerkung ein (z.B. "Backup auf USB-Stick")
   - Bestätigung wird gespeichert mit Status "wartend"

2. **System zeigt Info:**
   - Alle Haupt-Administratoren sehen eine Info-Box
   - Name und Zeitpunkt der ersten Bestätigung wird angezeigt
   - Der erste Admin sieht: "Warten auf zweiten Administrator"
   - Andere Admins sehen: "Bitte zweite Bestätigung abgeben"

3. **Zweiter Haupt-Administrator bestätigt:**
   - Sieht die ausstehende Bestätigung
   - Klickt "Zweite Bestätigung abgeben"
   - Gibt optional eigene Bemerkung ein
   - Nach Bestätigung wird Backup als durchgeführt markiert
   - Backup-Warnung wird zurückgesetzt

### Zeitfenster
- Eine erste Bestätigung ist **24 Stunden gültig**
- Wenn innerhalb von 24 Stunden keine zweite Bestätigung erfolgt, verfällt die erste Bestätigung
- Ein neuer Backup-Prozess muss gestartet werden

---

## Zwei-Personen-Regel für Notfall-Setup (/setup)

### Zugriff
Das Notfall-Setup ermöglicht kritische Operationen ohne normalen Login:
- **URL:** `http://server:5000/setup?token=IHR_TOKEN`
- Erfordert spezielle Tokens in der Server-Konfiguration

### Konfiguration (.env auf Server)

**Einfacher Modus (NICHT empfohlen für Produktion):**
```
SETUP_TOKEN=geheimer-token
```
- Ein Token für alle Operationen
- Keine Zwei-Personen-Regel aktiv

**Zwei-Personen-Modus (EMPFOHLEN):**
```
SETUP_TOKEN_ADMIN1=geheimer-token-admin1
SETUP_TOKEN_ADMIN2=geheimer-token-admin2
```
- Jeder Haupt-Administrator erhält seinen eigenen Token
- Zwei-Personen-Regel ist automatisch aktiv
- `SETUP_TOKEN` wird ignoriert wenn beide Admin-Tokens gesetzt sind

### Ablauf Backup-Wiederherstellung

1. **Admin 1 startet Anfrage:**
   - Öffnet: `http://server:5000/setup?token=geheimer-token-admin1`
   - Klickt "Backup hochladen"
   - Wählt die .sql Backup-Datei aus
   - Lädt die Datei hoch
   - Erhält einen **Bestätigungs-Code** (z.B. `A1B2C3D4E5F6`)

2. **Admin 1 informiert Admin 2:**
   - Teilt den Bestätigungs-Code mit (Telefon, Chat, persönlich)
   - Teilt mit, welche Datei hochgeladen wurde

3. **Admin 2 bestätigt:**
   - Öffnet: `http://server:5000/setup?token=geheimer-token-admin2`
   - Sieht die ausstehende Anfrage mit Details
   - Klickt "Bestätigen"
   - Bestätigt die Warnung
   - Backup wird eingespielt

### Zeitfenster
- Anfragen sind **30 Minuten gültig**
- Danach verfällt die Anfrage automatisch
- Ein neuer Versuch muss gestartet werden

### Sicherheitsregeln
- **Eigene Anfragen können nicht bestätigt werden**
- Jeder Admin kann nur mit seinem eigenen Token zugreifen
- Temporäre Backup-Dateien werden nach 30 Minuten gelöscht
- Anfragen können jederzeit abgebrochen werden

### Verfügbare Aktionen im Setup

| Aktion | Beschreibung | Zwei-Personen-Regel |
|--------|--------------|---------------------|
| Schema initialisieren | Erstellt leere Datenbanktabellen | Nein |
| Backup herunterladen | Lädt aktuelles Backup herunter | Nein |
| Backup wiederherstellen | Spielt Backup-Datei ein | **JA** |
| Administrator erstellen | Erstellt ersten Admin (nur wenn keine Benutzer existieren) | Nein |

---

## Administrator-Rollen verwalten

### Zugriff (nur Haupt-Administratoren)
1. Anmelden als Haupt-Administrator
2. Menü "Admin" → "Administrator-Rollen"

### Benutzer-Level ändern

**Level auf "Haupt-Administrator" setzen:**
1. Benutzer in Liste suchen
2. "Level" Dropdown öffnen
3. "Haupt-Administrator" auswählen
4. Benutzer hat nun volle Admin-Rechte

**Level auf "Gemeinschafts-Administrator" setzen:**
1. Benutzer in Liste suchen
2. "Level" Dropdown öffnen
3. "Gemeinschafts-Administrator" auswählen
4. **Wichtig:** Jetzt Gemeinschaften zuweisen!

**Level auf "Kein Admin" setzen:**
1. Benutzer in Liste suchen
2. "Level" Dropdown öffnen
3. "Kein Admin" auswählen
4. Benutzer hat nur noch Standard-Rechte

### Gemeinschaften zuweisen (nur Gemeinschafts-Admins)

1. Gemeinschafts-Admin in Liste suchen
2. Button "Gemeinschaft" klicken
3. Gemeinschaft aus Dropdown auswählen
4. "Hinzufügen" klicken
5. Gemeinschaft wird in der Spalte "Gemeinschafts-Admin für" angezeigt

**Mehrere Gemeinschaften:**
- Ein Gemeinschafts-Admin kann für mehrere Gemeinschaften zuständig sein
- Einfach den Vorgang für weitere Gemeinschaften wiederholen

**Gemeinschaft entfernen:**
- Funktion wird angezeigt, wenn Gemeinschaft bereits zugewiesen ist
- In der Gemeinschafts-Verwaltung kann die Zuweisung entfernt werden

---

## Best Practices

### Haupt-Administratoren
- **Empfehlung:** 2-3 Haupt-Administratoren
- Mindestens 2 erforderlich für Zwei-Personen-Regel
- Vertrauenswürdige Personen mit guter Verfügbarkeit
- Idealerweise verschiedene Personen für Vier-Augen-Prinzip
- **Jeder Haupt-Admin erhält eigenen Setup-Token**

### Gemeinschafts-Administratoren
- Für größere Gemeinschaften sinnvoll
- Entlastet Haupt-Administratoren
- Kann lokale Benutzer/Maschinen selbst verwalten
- Muss mindestens einer Gemeinschaft zugewiesen sein

### Token-Verwaltung
1. **Geheimhaltung:** Tokens niemals teilen oder öffentlich speichern
2. **Verschiedene Tokens:** Jeder Admin bekommt einen eigenen Token
3. **Sichere Aufbewahrung:** Tokens sicher aufbewahren (Passwort-Manager)
4. **Regelmäßig ändern:** Tokens bei Bedarf in .env aktualisieren

### Berechtigungen vergeben
1. **Vorsicht:** Haupt-Admin-Rechte nur an vertrauenswürdige Personen
2. **Prüfen:** Vor Level-Änderung Benutzer-Profil prüfen
3. **Dokumentieren:** Bemerkungsfeld bei Backup-Bestätigungen nutzen
4. **Regelmäßig:** Admin-Rollen überprüfen und ggf. anpassen

---

## Sicherheit

### Schutzmaßnahmen
- ✓ Zwei-Personen-Regel verhindert einseitige kritische Aktionen
- ✓ Mindestens 2 Haupt-Admins müssen erhalten bleiben (System verhindert Downgrade)
- ✓ 24-Stunden-Zeitfenster für Dashboard-Bestätigungen
- ✓ 30-Minuten-Zeitfenster für Setup-Anfragen
- ✓ Gemeinschafts-Admins können nur ihre Gemeinschaften verwalten
- ✓ Alle Admin-Aktionen werden protokolliert
- ✓ Separate Tokens für jeden Haupt-Administrator

### Was tun bei...

**...nur noch ein Haupt-Admin:**
- System verhindert automatisch Level-Downgrade
- Meldung: "Es müssen mindestens 2 Haupt-Administratoren vorhanden bleiben!"
- Lösung: Zuerst neuen Haupt-Admin ernennen

**...Backup-Bestätigung fehlt:**
- Nach 24 Stunden verfällt erste Bestätigung automatisch
- Backup-Warnung bleibt bestehen
- Neuer Versuch kann gestartet werden

**...Setup-Anfrage verfällt:**
- Nach 30 Minuten wird Anfrage automatisch gelöscht
- Temporäre Backup-Datei wird entfernt
- Admin 1 muss erneut Backup hochladen

**...Gemeinschafts-Admin hat keine Rechte:**
- Prüfen: Ist mindestens eine Gemeinschaft zugewiesen?
- Prüfen: Ist admin_level auf 1 gesetzt?
- Prüfen: Ist is_admin auf 1 gesetzt?

**...Token vergessen/verloren:**
- Tokens sind in `.env` auf dem Server gespeichert
- Server-Administrator kann Tokens einsehen/ändern
- Nach Änderung: `docker-compose restart web`

---

## Technische Details

### Datenbank-Tabellen

**benutzer** (erweitert):
- `admin_level` INTEGER: 0=kein Admin, 1=Gemeinschafts-Admin, 2=Haupt-Admin
- `is_admin` INTEGER: 0=kein Admin, 1=Admin (für Kompatibilität)

**gemeinschafts_admin**:
- `benutzer_id`: Referenz auf Benutzer
- `gemeinschaft_id`: Referenz auf Gemeinschaft
- `erstellt_am`: Zeitstempel der Zuweisung

**backup_bestaetigung**:
- `admin_id`: Haupt-Administrator der bestätigt hat
- `zeitpunkt`: Zeitpunkt der Bestätigung
- `bemerkung`: Optionale Notiz
- `status`: 'wartend' oder 'abgeschlossen'

### Umgebungsvariablen für Setup

| Variable | Beschreibung |
|----------|--------------|
| `SETUP_TOKEN` | Einfacher Modus: Ein Token für alle |
| `SETUP_TOKEN_ADMIN1` | Token für Haupt-Administrator 1 |
| `SETUP_TOKEN_ADMIN2` | Token für Haupt-Administrator 2 |

**Hinweis:** Wenn `SETUP_TOKEN_ADMIN1` und `SETUP_TOKEN_ADMIN2` gesetzt sind, wird `SETUP_TOKEN` ignoriert und die Zwei-Personen-Regel ist automatisch aktiv.

### Migration
```bash
python migrate_admin_rollen.py
```
- Fügt admin_level zu benutzer hinzu
- Migriert bestehende Admins zu Haupt-Admins
- Erstellt neue Tabellen für Rollen und Backup-Bestätigungen

---

## Häufige Fragen

**F: Kann ich einen Benutzer direkt beim Anlegen zum Admin machen?**
A: Nein, Benutzer müssen erst angelegt und dann in der Rollen-Verwaltung hochgestuft werden.

**F: Was passiert wenn beide Haupt-Admins ausfallen?**
A: Ein Server-Administrator kann direkt in der Datenbank den admin_level setzen, oder über das Setup (wenn noch ein Token bekannt ist) einen neuen Admin erstellen.

**F: Können Gemeinschafts-Admins auch Backups sehen?**
A: Ja, sie sehen die Backup-Warnung, können aber nicht bestätigen. Nur Info-Charakter.

**F: Wie viele Gemeinschafts-Admins kann ich haben?**
A: Unbegrenzt. Jeder Benutzer kann für beliebig viele Gemeinschaften Admin sein.

**F: Was passiert mit alten Backup-Bestätigungen?**
A: Nach Ablauf (>24h) oder Abschluss bleiben sie in der Datenbank zur Dokumentation.

**F: Kann ich mehr als 2 Haupt-Administratoren für das Setup haben?**
A: Aktuell unterstützt das Setup genau 2 Admin-Tokens. Für mehr Flexibilität können mehrere Personen denselben Token kennen, aber die Zwei-Personen-Regel erfordert immer 2 verschiedene Tokens.

**F: Was passiert wenn ich nur SETUP_TOKEN setze?**
A: Das System arbeitet im einfachen Modus ohne Zwei-Personen-Regel. Jeder mit dem Token kann sofort Backups einspielen. **Nicht empfohlen für Produktion!**

**F: Wie teste ich die Zwei-Personen-Regel?**
A: Öffne zwei Browser (oder Inkognito-Fenster), melde dich mit verschiedenen Admin-Tokens an und führe den Ablauf durch.

---

**Version:** 2.0 (Februar 2026)
**Migration:** migrate_admin_rollen.py
**Neu:** Zwei-Personen-Regel für Notfall-Setup (/setup)
