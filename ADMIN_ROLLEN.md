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

## Zwei-Personen-Regel für Backups

### Zweck
Aus Sicherheitsgründen müssen **immer zwei Haupt-Administratoren** unabhängig voneinander die Durchführung einer Datenbank-Sicherung bestätigen.

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

### Wichtige Regeln
- **Mindestens 2 Haupt-Administratoren** müssen im System vorhanden sein
- Derselbe Admin kann **nicht zweimal** hintereinander bestätigen
- Nur **Haupt-Administratoren (Level 2)** können Backups bestätigen
- Gemeinschafts-Admins sehen zwar die Warnung, können aber nicht bestätigen

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

## Best Practices

### Haupt-Administratoren
- **Empfehlung:** 2-3 Haupt-Administratoren
- Mindestens 2 erforderlich für Backup-Regel
- Vertrauenswürdige Personen mit guter Verfügbarkeit
- Idealerweise verschiedene Personen für Vier-Augen-Prinzip

### Gemeinschafts-Administratoren
- Für größere Gemeinschaften sinnvoll
- Entlastet Haupt-Administratoren
- Kann lokale Benutzer/Maschinen selbst verwalten
- Muss mindestens einer Gemeinschaft zugewiesen sein

### Berechtigungen vergeben
1. **Vorsicht:** Haupt-Admin-Rechte nur an vertrauenswürdige Personen
2. **Prüfen:** Vor Level-Änderung Benutzer-Profil prüfen
3. **Dokumentieren:** Bemerkungsfeld bei Backup-Bestätigungen nutzen
4. **Regelmäßig:** Admin-Rollen überprüfen und ggf. anpassen

## Sicherheit

### Schutzmaßnahmen
- ✓ Zwei-Personen-Regel verhindert einseitige Backup-Bestätigungen
- ✓ Mindestens 2 Haupt-Admins müssen erhalten bleiben (System verhindert Downgrade)
- ✓ 24-Stunden-Zeitfenster für Bestätigungen
- ✓ Gemeinschafts-Admins können nur ihre Gemeinschaften verwalten
- ✓ Alle Admin-Aktionen werden protokolliert

### Was tun bei...

**...nur noch ein Haupt-Admin:**
- System verhindert automatisch Level-Downgrade
- Meldung: "Es müssen mindestens 2 Haupt-Administratoren vorhanden bleiben!"
- Lösung: Zuerst neuen Haupt-Admin ernennen

**...Backup-Bestätigung fehlt:**
- Nach 24 Stunden verfällt erste Bestätigung automatisch
- Backup-Warnung bleibt bestehen
- Neuer Versuch kann gestartet werden

**...Gemeinschafts-Admin hat keine Rechte:**
- Prüfen: Ist mindestens eine Gemeinschaft zugewiesen?
- Prüfen: Ist admin_level auf 1 gesetzt?
- Prüfen: Ist is_admin auf 1 gesetzt?

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

### Migration
```bash
python migrate_admin_rollen.py
```
- Fügt admin_level zu benutzer hinzu
- Migriert bestehende Admins zu Haupt-Admins
- Erstellt neue Tabellen für Rollen und Backup-Bestätigungen

## Häufige Fragen

**F: Kann ich einen Benutzer direkt beim Anlegen zum Admin machen?**
A: Nein, Benutzer müssen erst angelegt und dann in der Rollen-Verwaltung hochgestuft werden.

**F: Was passiert wenn beide Haupt-Admins ausfallen?**
A: Ein Datenbank-Administrator kann direkt in der Datenbank den admin_level setzen oder ein neues Admin-Konto erstellen.

**F: Können Gemeinschafts-Admins auch Backups sehen?**
A: Ja, sie sehen die Backup-Warnung, können aber nicht bestätigen. Nur Info-Charakter.

**F: Wie viele Gemeinschafts-Admins kann ich haben?**
A: Unbegrenzt. Jeder Benutzer kann für beliebig viele Gemeinschaften Admin sein.

**F: Was passiert mit alten Backup-Bestätigungen?**
A: Nach Ablauf (>24h) oder Abschluss bleiben sie in der Datenbank zur Dokumentation.

---

**Version:** 1.0 (Januar 2026)  
**Migration:** migrate_admin_rollen.py
