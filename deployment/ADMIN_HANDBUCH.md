# Administrator-Handbuch - Maschinengemeinschaft

## Inhaltsverzeichnis
1. [Übersicht](#übersicht)
2. [Admin-Dashboard](#admin-dashboard)
3. [Benutzerverwaltung](#benutzerverwaltung)
4. [Maschinenverwaltung](#maschinenverwaltung)
5. [Gemeinschaftsverwaltung](#gemeinschaftsverwaltung)
6. [Einsatzzwecke verwalten](#einsatzzwecke-verwalten)
7. [Alle Einsätze](#alle-einsätze)
8. [Rentabilitätsrechnung](#rentabilitätsrechnung)
9. [Aufwendungen erfassen](#aufwendungen-erfassen)
10. [Abrechnungen](#abrechnungen)

---

## Übersicht

Als Administrator haben Sie Zugriff auf erweiterte Funktionen:
- Vollständige Benutzerverwaltung
- Maschinen anlegen, bearbeiten und verwalten
- Gemeinschaften organisieren
- Einsatzzwecke definieren
- Alle Einsätze einsehen und verwalten
- Rentabilitätsrechnungen erstellen
- Jahresabrechnungen für Gemeinschaften

**Admin-Menü:** Klicken Sie auf "Admin" in der Hauptnavigation

---

## Admin-Dashboard

### Übersicht
Das Admin-Dashboard zeigt:
- **Gesamtstatistiken** über alle Benutzer und Maschinen
- Anzahl aktiver Benutzer und Maschinen
- Gesamtbetriebsstunden
- Letzte Aktivitäten

### Schnellzugriff
Direkte Links zu:
- Benutzerverwaltung
- Maschinenverwaltung
- Gemeinschaften
- Einsatzzwecke
- Alle Einsätze
- Abrechnungen

---

## Benutzerverwaltung

### Benutzerübersicht
**Pfad:** Admin → Benutzer

Zeigt alle registrierten Benutzer:
- Name, Vorname
- Benutzername
- Admin-Status
- Aktiv/Inaktiv Status
- Mitglied seit
- Aktionen (Bearbeiten, Deaktivieren, Passwort zurücksetzen)

### Neuen Benutzer anlegen

1. Klicken Sie auf "Neuer Benutzer"
2. **Pflichtfelder:**
   - Name (Nachname)
   - Benutzername (für Login, muss eindeutig sein)
   - Passwort (mindestens 4 Zeichen)
3. **Optional:**
   - Vorname
   - Adresse
   - Telefon
   - E-Mail
   - Mitglied seit (Datum)
   - Treibstoffkosten (EUR/Liter, Standard: 1.50)
   - Bemerkungen
4. **Administrator:** Häkchen setzen für Admin-Rechte
5. Klicken Sie auf "Benutzer anlegen"

### Benutzer bearbeiten

1. Klicken Sie auf "Bearbeiten" beim gewünschten Benutzer
2. Ändern Sie die gewünschten Felder
3. Klicken Sie auf "Änderungen speichern"

**Hinweis:** Das Passwort wird nur geändert, wenn ein neues eingegeben wird.

### Benutzer deaktivieren/reaktivieren

- **Deaktivieren:** Benutzer kann sich nicht mehr anmelden, alle Daten bleiben erhalten
- **Reaktivieren:** Benutzer kann sich wieder anmelden
- **Nicht löschen:** Benutzer werden nie gelöscht, um Datenintegrität zu wahren

### Passwort zurücksetzen

1. Bearbeiten Sie den Benutzer
2. Geben Sie ein neues Passwort ein
3. Speichern Sie die Änderungen
4. Informieren Sie den Benutzer über das neue Passwort

---

## Maschinenverwaltung

### Maschinenübersicht
**Pfad:** Admin → Maschinen

Zeigt alle Maschinen mit:
- Bezeichnung
- Hersteller, Modell
- Stundenzähler
- Gemeinschaft
- Abrechnungsart
- Preis pro Einheit
- Status (Aktiv/Inaktiv)
- Aktionen (Bearbeiten, Rentabilität, Deaktivieren)

### Neue Maschine anlegen

1. Klicken Sie auf "Neue Maschine"
2. **Pflichtfelder:**
   - Bezeichnung (z.B. "Traktor Fendt 312")
   - Baujahr
   - Gemeinschaft (Zuordnung)
   - Abrechnungsart
   - Preis pro Einheit
3. **Optional:**
   - Hersteller
   - Modell
   - Kennzeichen
   - Anschaffungsdatum
   - Stundenzähler aktuell
   - Wartungsintervall (Standard: 50h)
   - Nächste Wartung bei (Stundenzähler)
   - Erfassungsmodus
   - **Rentabilität:**
     - Anschaffungspreis (EUR)
     - Abschreibungsdauer (Jahre, Standard: 10)
   - Anmerkungen

### Erfassungsmodus

**Fortlaufend (Standard):**
- Benutzer gibt Anfangs- und Endstand des Stundenzählers ein
- Betriebsstunden werden automatisch berechnet
- Geeignet für: Traktoren, Maschinen mit Betriebsstundenzähler

**Direkt:**
- Benutzer gibt direkt Stunden/Menge ein
- Kein Stundenzähler erforderlich
- Geeignet für: Anhänger, Geräte ohne eigenen Zähler

### Abrechnungsarten

**Stunden:**
- Abrechnung nach Betriebsstunden
- Preis pro Stunde (z.B. 25.00 EUR/h)

**Hektar:**
- Abrechnung nach bearbeiteter Fläche
- Preis pro Hektar (z.B. 30.00 EUR/ha)

**Kilometer:**
- Abrechnung nach gefahrener Strecke
- Preis pro Kilometer (z.B. 2.50 EUR/km)

**Stück:**
- Abrechnung nach Anzahl (z.B. gepresste Ballen)
- Preis pro Stück (z.B. 5.00 EUR/Stück)

### Maschine bearbeiten

1. Klicken Sie auf "Bearbeiten"
2. Ändern Sie die gewünschten Felder
3. **Wichtig:** Änderungen an Abrechnungsart und Preis betreffen nur zukünftige Einsätze
4. Klicken Sie auf "Änderungen speichern"

### Maschine deaktivieren

- Deaktivierte Maschinen können nicht mehr für neue Einsätze verwendet werden
- Alle historischen Daten bleiben erhalten
- Zur Reaktivierung: Bearbeiten → "Aktiv" wieder aktivieren

---

## Gemeinschaftsverwaltung

### Gemeinschaften-Übersicht
**Pfad:** Admin → Gemeinschaften

Zeigt alle Gemeinschaften:
- Name
- Beschreibung
- Anzahl Mitglieder
- Anzahl Maschinen
- Erstellt am
- Status
- Aktionen (Mitglieder, Abrechnung, Bearbeiten)

### Neue Gemeinschaft anlegen

1. Klicken Sie auf "Neue Gemeinschaft"
2. **Pflichtfeld:**
   - Name (muss eindeutig sein)
3. **Optional:**
   - Beschreibung
4. Klicken Sie auf "Gemeinschaft anlegen"

### Mitglieder verwalten

1. Klicken Sie auf "Mitglieder" bei der Gemeinschaft
2. **Mitglied hinzufügen:**
   - Wählen Sie Benutzer aus der Liste
   - Klicken Sie auf "Hinzufügen"
3. **Mitglied entfernen:**
   - Klicken Sie auf "Entfernen" beim Mitglied
   - Bestätigen Sie die Aktion

**Hinweis:** Benutzer sehen nur Maschinen von Gemeinschaften, in denen sie Mitglied sind.

### Gemeinschaftsabrechnung

1. Klicken Sie auf "Abrechnung" bei der Gemeinschaft
2. Wählen Sie optional ein Jahr (Standard: aktuelles Jahr)
3. Die Abrechnung zeigt:
   - Alle Mitglieder der Gemeinschaft
   - Anzahl Einsätze pro Mitglied
   - Maschinenkosten pro Mitglied
   - Gesamtsummen
4. **CSV-Export:** Klicken Sie auf "CSV exportieren"

**Wichtig:** Treibstoffkosten werden NICHT in der Gemeinschaftsabrechnung berücksichtigt (jedes Mitglied zahlt Treibstoff selbst).

---

## Einsatzzwecke verwalten

### Übersicht
**Pfad:** Admin → Einsatzzwecke

Einsatzzwecke werden bei der Erfassung von Einsätzen ausgewählt (z.B. "Pflügen", "Mähen", "Transport").

### Neuen Einsatzzweck anlegen

1. Klicken Sie auf "Neuer Einsatzzweck"
2. **Pflichtfeld:**
   - Bezeichnung (z.B. "Grubbern")
3. **Optional:**
   - Beschreibung
4. Klicken Sie auf "Einsatzzweck anlegen"

### Einsatzzweck bearbeiten/deaktivieren

- **Bearbeiten:** Bezeichnung und Beschreibung ändern
- **Deaktivieren:** Nicht mehr in der Auswahlliste sichtbar, historische Daten bleiben
- **Reaktivieren:** "Aktiv" wieder setzen

---

## Alle Einsätze

### Übersicht
**Pfad:** Admin → Alle Einsätze

Zeigt **alle** Maschineneinsätze aller Benutzer:
- Datum
- Benutzer
- Maschine
- Einsatzzweck
- Betriebsstunden/Menge
- Treibstoffverbrauch
- Kosten

### Funktionen

**Filtern:**
- Nach Datum (Von-Bis)
- Nach Benutzer
- Nach Maschine
- Nach Gemeinschaft

**Exportieren:**
- CSV-Export aller angezeigten Einsätze
- Öffnet in Excel/LibreOffice

**Einsatz löschen:**
1. Klicken Sie auf das Papierkorb-Symbol
2. Bestätigen Sie die Löschung
3. **Wichtig:** Gelöschte Einsätze können nicht wiederhergestellt werden!

**Wann löschen?**
- Doppelt erfasste Einsätze
- Offensichtliche Fehleingaben
- Nach Rücksprache mit dem Benutzer

---

## Rentabilitätsrechnung

### Übersicht
**Pfad:** Admin → Maschinen → Rentabilität (bei einer Maschine)

Die Rentabilitätsrechnung zeigt die wirtschaftliche Auswertung einer Maschine.

### Kennzahlen

**Anschaffung & Abschreibung:**
- Anschaffungspreis
- Abschreibungsdauer (Jahre)
- Abschreibung pro Jahr (linear)
- Alter der Maschine
- Abschreibung bisher
- Aktueller Restwert

**Einsatz & Einnahmen:**
- Anzahl Einsätze
- Gesamte Betriebsstunden
- Einnahmen gesamt (aus allen Einsätzen)

**Aufwendungen:**
- Wartungskosten
- Reparaturkosten
- Versicherung
- Steuern
- Sonstige Kosten
- Aufwendungen gesamt

**Ergebnis:**
- Deckungsbeitrag = Einnahmen - Abschreibung - Aufwendungen
- Rentabilität in % = Deckungsbeitrag / Anschaffungspreis × 100

### Jahresübersicht

Zeigt pro Jahr:
- Anzahl Einsätze
- Betriebsstunden
- Einnahmen
- Aufwendungen
- Gewinn (Einnahmen - Aufwendungen)

### PDF-Export

1. Klicken Sie auf "PDF"
2. PDF wird im Browser geöffnet
3. Kann gespeichert oder gedruckt werden
4. Enthält vollständigen Rentabilitätsbericht

**Verwendung:**
- Dokumentation für Steuerberater
- Entscheidungsgrundlage für Neuanschaffungen
- Transparenz für Gemeinschaftsmitglieder

---

## Aufwendungen erfassen

### Zugang
**Pfad:** Admin → Maschinen → Rentabilität → Button "Aufwendungen"

### Zweck
Erfassen Sie alle jährlichen Kosten für eine Maschine:
- Wartungskosten (Ölwechsel, Inspektionen)
- Reparaturkosten (Ersatzteile, Werkstatt)
- Versicherung (Jahresbeitrag)
- Steuern (KFZ-Steuer)
- Sonstige Kosten (Stellplatz, Sonstiges)

### Aufwendungen eingeben

1. **Aktuelles Jahr:**
   - Felder für alle Kostenkategorien
   - Bemerkungsfeld für Notizen
   - "Speichern" überschreibt vorhandene Daten

2. **Vergangene Jahre:**
   - Tabelle zeigt Aufwendungen vergangener Jahre
   - Summen werden automatisch berechnet
   - Bearbeiten durch Klick auf Stift-Symbol

### Best Practices

**Wann erfassen?**
- Am Jahresende alle Aufwendungen zusammenfassen
- Bei größeren Reparaturen sofort erfassen
- Regelmäßig Belege sammeln

**Dokumentation:**
- Nutzen Sie das Bemerkungsfeld für Details
- Bewahren Sie Belege auf
- Rechnung = Reparatur, Wartung getrennt halten

**Vollständigkeit:**
- Erfassen Sie alle Kosten
- Auch kleine Beträge summieren sich
- Für genaue Rentabilitätsrechnung

---

## Abrechnungen

### Gemeinschaftsabrechnung erstellen

1. **Pfad:** Admin → Gemeinschaften → Abrechnung
2. **Jahr auswählen:** Standard = aktuelles Jahr
3. **Ansicht:**
   - Alle Mitglieder mit ihren Einsätzen
   - Maschinenkosten pro Mitglied
   - Gesamtsumme der Gemeinschaft
4. **Exportieren:** CSV-Export für Excel-Weiterverarbeitung

### Abrechnung für Mitglieder

**Variante A: Individuell**
- Jedes Mitglied sieht seine Forderungen im Dashboard
- CSV-Export der eigenen Einsätze möglich
- Mitglied kann eigenständig Überweisung tätigen

**Variante B: Gesammelt**
1. Gemeinschaftsabrechnung als CSV exportieren
2. In Excel öffnen und formatieren
3. Per E-Mail an alle Mitglieder senden
4. Zahlungseingang überprüfen

### Jahresabschluss

**Checkliste:**
- [ ] Alle Einsätze des Jahres erfasst
- [ ] Aufwendungen für alle Maschinen eingegeben
- [ ] Gemeinschaftsabrechnungen erstellt und versendet
- [ ] Rentabilitätsberichte erstellt
- [ ] PDF-Berichte archiviert
- [ ] Zahlungseingänge überprüft

---

## Wartung und Pflege

### Regelmäßige Aufgaben

**Wöchentlich:**
- Neue Benutzer anlegen bei Bedarf
- Einsätze auf Plausibilität prüfen
- Reservierungen überwachen

**Monatlich:**
- Stundenzählerstände aktualisieren
- Wartungstermine überprüfen
- Inaktive Benutzer identifizieren

**Jährlich:**
- Aufwendungen für alle Maschinen erfassen
- Gemeinschaftsabrechnungen erstellen
- Rentabilitätsberichte generieren
- Maschinenpreise überprüfen und anpassen
- Abschreibungen überprüfen

### Datensicherheit

**Backup:**
- Die Datenbank liegt in `/data/maschinengemeinschaft.db` (Docker)
- Erstellen Sie regelmäßige Backups
- Testen Sie die Wiederherstellung

**Datenschutz:**
- Nur Administratoren haben Zugriff auf alle Daten
- Benutzer sehen nur eigene Einsätze
- Passwörter sind verschlüsselt gespeichert

---

## Tipps und Best Practices

### Maschinenverwaltung

1. **Klare Bezeichnungen:** "Traktor Fendt 312" statt nur "Traktor"
2. **Gemeinschaften sinnvoll:** Separate Gemeinschaften für verschiedene Maschinengruppen
3. **Preise realistisch:** Orientierung an Maschinenringen oder Marktpreisen
4. **Wartungsintervalle:** Nicht zu kurz, nicht zu lang (Herstellerangaben)

### Benutzerverwaltung

1. **Eindeutige Benutzernamen:** Vorname.Nachname oder Kürzel
2. **Starke Passwörter:** Mindestens 8 Zeichen, initial vergeben
3. **Admin-Rechte sparsam:** Nur vertrauenswürdige Personen
4. **Inaktive Benutzer:** Deaktivieren statt löschen

### Abrechnungen

1. **Transparenz:** Klare Kommunikation der Abrechnungsmodalitäten
2. **Regelmäßigkeit:** Quartalsweise oder jährlich
3. **Nachvollziehbar:** Detaillierte Aufstellung
4. **Zahlungsfristen:** Klare Termine setzen

### Rentabilität

1. **Vollständig:** Alle Aufwendungen erfassen
2. **Aktuell:** Abschreibungsdauer realistisch
3. **Vergleichen:** Mehrere Maschinen analysieren
4. **Entscheiden:** Basis für Neuanschaffungen

---

## Problembehandlung

### Benutzer kann sich nicht anmelden
- Ist der Benutzer aktiv?
- Passwort korrekt? → Zurücksetzen
- Benutzername korrekt geschrieben?

### Benutzer sieht keine Maschinen
- Ist der Benutzer Mitglied einer Gemeinschaft?
- Sind der Gemeinschaft Maschinen zugeordnet?
- Sind die Maschinen aktiv?

### Einsatz kann nicht gespeichert werden
- Alle Pflichtfelder ausgefüllt?
- Endstand > Anfangstand?
- Maschine noch aktiv?
- Berechtigung vorhanden?

### Kosten werden nicht berechnet
- Ist ein Preis pro Einheit hinterlegt?
- Stimmt die Abrechnungsart?
- Bei Hektar/Kilometer: Fläche/Strecke eingegeben?

---

## Support und Weiterentwicklung

Bei technischen Problemen oder Funktionswünschen:
- Dokumentieren Sie das Problem genau
- Screenshots helfen bei der Fehlersuche
- Kontaktieren Sie den technischen Support

**Version:** 2.0 (Januar 2026)
