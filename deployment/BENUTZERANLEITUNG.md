# Benutzeranleitung - Maschinengemeinschaft

## Inhaltsverzeichnis
1. [Erste Schritte](#erste-schritte)
2. [Dashboard](#dashboard)
3. [Neuen Einsatz erfassen](#neuen-einsatz-erfassen)
4. [Meine Einsätze](#meine-einsätze)
5. [Maschinen reservieren](#maschinen-reservieren)
6. [Einstellungen](#einstellungen)

---

## Erste Schritte

### Anmeldung
1. Öffnen Sie die Anwendung im Browser: `http://[SERVER-IP]:5000`
2. Geben Sie Ihren Benutzernamen und Ihr Passwort ein
3. Klicken Sie auf "Anmelden"

### Navigation
Die Hauptnavigation oben bietet folgende Menüpunkte:
- **Dashboard** - Übersicht Ihrer Aktivitäten
- **Neuer Einsatz** - Maschineneinsatz erfassen
- **Meine Einsätze** - Alle Ihre Einsätze anzeigen
- **Reservierungen** - Maschinenreservierungen verwalten
- **Kalender** - Kalenderansicht aller Reservierungen
- **Balkenansicht** - Gantt-Chart-Übersicht der Maschinenauslastung
- **Einstellungen** - Passwort und Treibstoffkosten ändern

---

## Dashboard

Das Dashboard zeigt Ihnen auf einen Blick:

### Statistiken
- **Anzahl Einsätze** - Wie oft Sie Maschinen genutzt haben
- **Betriebsstunden** - Summe aller Betriebsstunden
- **Treibstoffverbrauch** - Gesamter Treibstoffverbrauch in Litern
- **Treibstoffkosten** - Ihre persönlichen Treibstoffkosten
- **Maschinenkosten** - Kosten für Maschinennutzung
- **GESAMTKOSTEN** - Summe aus Treibstoff und Maschinenkosten

### Forderungen nach Gemeinschaft
Zeigt, welchen Gemeinschaften Sie wie viel für die Maschinennutzung schulden:
- Gemeinschaftsname
- Anzahl der Einsätze
- Maschinenkosten in EUR

**Hinweis:** Treibstoffkosten werden separat ausgewiesen und nicht den Gemeinschaften zugerechnet.

### Meine Reservierungen
Übersicht Ihrer aktiven Maschinenreservierungen:
- Datum und Uhrzeit
- Maschine
- Nutzungsdauer
- Stornierungsmöglichkeit

### Letzte Einsätze
Die 10 letzten erfassten Einsätze mit:
- Datum
- Maschine
- Verwendungszweck
- Menge (Stunden, Hektar, etc.)
- Treibstoffverbrauch

---

## Neuen Einsatz erfassen

### Schritt-für-Schritt Anleitung

1. **Navigation:** Klicken Sie auf "Neuer Einsatz" im Menü

2. **Datum auswählen:** Wählen Sie das Datum des Einsatzes

3. **Maschine wählen:** 
   - Wählen Sie die verwendete Maschine aus der Liste
   - Wenn eine Maschine heute reserviert ist, wird ein Hinweis angezeigt
   - Sie können direkt eine Reservierung anlegen mit dem Button "Maschine reservieren"

4. **Einsatzzweck:** Wählen Sie den Verwendungszweck (z.B. "Pflügen", "Mähen")

5. **Betriebsdaten erfassen:**

   **Bei fortlaufendem Stundenzähler:**
   - **Anfangstand:** Der Stundenzählerstand zu Beginn (wird automatisch vorgeschlagen)
   - **Endstand:** Der Stundenzählerstand am Ende
   - **Betriebsstunden:** Werden automatisch berechnet

   **Bei direkter Eingabe (je nach Maschine):**
   - **Stunden/Menge:** Direkte Eingabe der Betriebsstunden oder bearbeiteten Fläche
   - Die Art der Eingabe hängt von der Abrechnungsart ab (Stunden, Hektar, Kilometer, Stück)

6. **Fläche/Menge (optional):**
   - Bei Flächenarbeiten: Bearbeitete Fläche in Hektar
   - Bei anderen Abrechnungsarten entsprechend Kilometer oder Stückzahl

7. **Treibstoff:**
   - **Treibstoffverbrauch:** Liter Diesel/Benzin
   - **Treibstoffkosten:** Werden automatisch berechnet basierend auf Ihrem gespeicherten Preis pro Liter
   - Sie können den Preis manuell anpassen

8. **Anmerkungen (optional):** Zusätzliche Notizen zum Einsatz

9. **Speichern:** Klicken Sie auf "Einsatz speichern"

### Tipps
- Die Maschinenkosten werden automatisch berechnet basierend auf Betriebsstunden/Menge
- Ihr Treibstoffpreis wird aus den Einstellungen übernommen
- Bei Fragen zur Abrechnungsart wenden Sie sich an Ihren Administrator

---

## Meine Einsätze

### Übersicht
Zeigt alle Ihre erfassten Maschineneinsätze in einer Tabelle:
- Datum
- Maschine
- Verwendungszweck
- Betriebsstunden oder Menge
- Treibstoffverbrauch (Liter)
- Treibstoffkosten (EUR)
- Maschinenkosten (EUR)
- Gesamtkosten (EUR)

### Funktionen
- **Sortierung:** Klicken Sie auf die Spaltenüberschriften
- **CSV-Export:** Button "CSV exportieren" zum Download als Excel-Datei
- **Summen:** Am Ende der Tabelle werden Gesamtsummen angezeigt

### CSV-Export verwenden
1. Klicken Sie auf "CSV exportieren"
2. Datei wird heruntergeladen
3. Öffnen Sie die Datei mit Excel, LibreOffice oder einem Texteditor
4. Trennzeichen ist das Semikolon (;)

---

## Maschinen reservieren

### Reservierung erstellen

1. **Zugang:**
   - Über "Reservierungen" im Menü
   - Oder bei "Neuer Einsatz" → Maschine auswählen → "Maschine reservieren"

2. **Formular ausfüllen:**
   - **Datum:** Wann benötigen Sie die Maschine?
   - **Nutzungsdauer:** Wie viele Stunden (0.5 bis 24)?
   - **Von Uhrzeit:** Startzeit
   - **Bis Uhrzeit:** Wird automatisch berechnet
   - **Verwendungszweck (optional):** Wofür wird die Maschine benötigt?
   - **Bemerkung (optional):** Zusätzliche Informationen

3. **Überschneidungen vermeiden:**
   - Bestehende Reservierungen werden angezeigt
   - Das System prüft automatisch auf Überschneidungen
   - Sie können nur freie Zeiträume reservieren

4. **Speichern:** Klicken Sie auf "Reservieren"

### Reservierung stornieren

1. **Öffnen Sie:** "Reservierungen" im Menü oder Ihr Dashboard
2. **Wählen Sie:** Die zu stornierende Reservierung
3. **Klicken Sie:** Auf den Papierkorb-Button (🗑️)
4. **Bestätigen Sie:** Die Sicherheitsabfrage

**Wichtig:** Bitte stornieren Sie rechtzeitig, wenn Sie die Maschine doch nicht benötigen!

### Übersicht "Meine Reservierungen"

Zeigt alle Ihre aktiven Reservierungen:
- Zukünftige Reservierungen mit Status "Aktiv"
- Vergangene Reservierungen mit Status "Vergangen"
- Stornierungsmöglichkeit für zukünftige Termine
- Direktlink zum Erstellen weiterer Reservierungen für dieselbe Maschine

#### Gelöschte Reservierungen anzeigen

Alle stornierten Reservierungen bleiben für Ihre Übersicht erhalten:

1. **Zugang:** Klicken Sie auf "Gelöschte Reservierungen" auf der Reservierungsseite
2. **Anzeige:** Zeigt die letzten 100 gelöschten Reservierungen
3. **Informationen:** 
   - Wann wurde storniert
   - Alle Details der ursprünglichen Reservierung
   - Grund der Stornierung

**Nutzen:** Nachvollziehbarkeit aller Ihrer Planungen und Änderungen

---

## Reservierungen visualisieren

### Kalenderansicht

Die Kalenderansicht bietet eine chronologische Übersicht aller Reservierungen:

1. **Zugang:** Klicken Sie auf "Kalender" im Hauptmenü
2. **Ansicht:** 
   - Zeigt alle Reservierungen der nächsten 30 Tage
   - Gruppiert nach Datum
   - Übersichtliche Tagesansicht

3. **Farbcodierung:**
   - 🟣 **Lila:** Reservierungen anderer Benutzer
   - 🟢 **Grün:** Ihre eigenen Reservierungen

4. **Filter:** Wählen Sie eine Maschine aus, um nur deren Reservierungen zu sehen

5. **Details:** Jede Karte zeigt:
   - Maschinenbezeichnung
   - Zeitraum (von-bis) und Dauer
   - Benutzer
   - Verwendungszweck

**Ideal für:** Schneller Überblick über die nächsten Wochen

### Balkenansicht (Gantt-Chart)

Die Balkenansicht zeigt alle Maschinen und deren Auslastung in einer Gantt-Chart-ähnlichen Darstellung:

1. **Zugang:** Klicken Sie auf "Balkenansicht" im Hauptmenü

2. **Darstellung:**
   - Maschinen auf der Y-Achse (vertikal)
   - Zeit/Tage auf der X-Achse (horizontal)
   - Reservierungen als farbige Balken
   - Standard: 10 Tage Ansicht

3. **Farbcodierung:**
   - 🟣 **Lila:** Reservierungen anderer Benutzer
   - 🟢 **Grün:** Ihre eigenen Reservierungen
   - ⬜ **Grau hinterlegt:** Wochenenden

4. **Interaktion:**
   - Hover über Balken für Details (Benutzer, genaue Zeit)
   - Startdatum frei wählbar
   - Anzahl Tage anpassbar (3-30 Tage)

5. **Einstellungen:**
   - **Startdatum:** Beliebiges Datum wählen
   - **Anzahl Tage:** Zwischen 3 und 30 Tagen
   - Klick auf "Anzeigen" aktualisiert die Ansicht

**Ideal für:** 
- Planung mehrerer Maschinen
- Erkennen von Engpässen
- Koordination mit anderen Mitgliedern
- Übersicht der Maschinenauslastung

**Tipps:**
- Wochenenden sind grau hinterlegt für bessere Orientierung
- Nutzen Sie verschiedene Zeiträume für Kurz- und Langfristplanung
- Die Ansicht zeigt alle Maschinen gleichzeitig - perfekt für Gesamtübersicht

---

## Einstellungen

### Passwort ändern

1. Klicken Sie auf Ihren Benutzernamen → "Einstellungen"
2. Geben Sie Ihr altes Passwort ein
3. Geben Sie das neue Passwort ein (mindestens 4 Zeichen)
4. Wiederholen Sie das neue Passwort
5. Klicken Sie auf "Passwort ändern"

**Sicherheitshinweise:**
- Verwenden Sie ein sicheres Passwort
- Teilen Sie Ihr Passwort niemals mit anderen
- Ändern Sie Ihr Passwort regelmäßig

### Treibstoffkosten anpassen

1. Scrollen Sie im Einstellungen-Bereich nach unten zu "Treibstoffkosten"
2. Geben Sie Ihren aktuellen Preis pro Liter ein (z.B. 1.50)
3. Klicken Sie auf "Treibstoffkosten speichern"

**Hinweis:** Dieser Preis wird automatisch bei neuen Einsätzen vorgeschlagen, kann aber beim Erfassen eines Einsatzes individuell angepasst werden.

---

## Häufige Fragen (FAQ)

**F: Warum kann ich eine Maschine nicht auswählen?**
A: Sie können nur Maschinen nutzen, die zu Gemeinschaften gehören, in denen Sie Mitglied sind. Wenden Sie sich an Ihren Administrator.

**F: Kann ich einen erfassten Einsatz ändern?**
A: Nein, erfasste Einsätze können nicht geändert werden. Wenden Sie sich bei Fehlern an Ihren Administrator.

**F: Was bedeuten die verschiedenen Abrechnungsarten?**
A: 
- **Stunden:** Abrechnung nach Betriebsstunden
- **Hektar:** Abrechnung nach bearbeiteter Fläche
- **Kilometer:** Abrechnung nach gefahrener Strecke
- **Stück:** Abrechnung nach Anzahl (z.B. Ballen)

**F: Muss ich immer reservieren?**
A: Nein, Reservierungen sind optional. Sie helfen aber, Konflikte zu vermeiden und zeigen anderen Mitgliedern, wann eine Maschine benötigt wird.

**F: Wie finde ich schnell heraus, wann eine Maschine frei ist?**
A: Nutzen Sie die Balkenansicht! Sie zeigt auf einen Blick die Auslastung aller Maschinen über mehrere Tage hinweg.

**F: Kann ich sehen, welche Reservierungen ich storniert habe?**
A: Ja, unter "Gelöschte Reservierungen" finden Sie alle Ihre stornierten Reservierungen der letzten Zeit.

**F: Warum werden meine Treibstoffkosten nicht der Gemeinschaft zugerechnet?**
A: Die Treibstoffkosten bezahlt jedes Mitglied selbst. Nur die Maschinenkosten werden der Gemeinschaft zugeordnet.

---

## Kontakt und Support

Bei Fragen oder Problemen wenden Sie sich an:
- **Ihren Administrator** für Benutzerverwaltung und Berechtigungen
- **Technischen Support** bei technischen Problemen

**Version:** 2.1 (Januar 2026)

**Neue Features in Version 2.1:**
- Kalenderansicht für bessere Übersicht
- Balkenansicht (Gantt-Chart) zur Maschinenauslastung
- Archivierung gelöschter Reservierungen
