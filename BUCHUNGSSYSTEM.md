# Buchungssystem - Dokumentation

## Übersicht

Das Buchungssystem implementiert eine doppelte Buchführung für Maschinengemeinschaften. Jedes Mitglied hat ein Konto pro Gemeinschaft, auf dem alle Transaktionen verbucht werden.

## Konzept

### Mitgliederkonten
- Jedes Mitglied hat ein Konto pro Gemeinschaft
- Der **Saldo** zeigt den aktuellen Kontostand:
  - **Negativ** = Mitglied schuldet der Gemeinschaft Geld
  - **Positiv** = Mitglied hat Guthaben bei der Gemeinschaft
  - **0** = Konto ist ausgeglichen

### Buchungstypen

1. **Abrechnung** (automatisch)
   - Wird erstellt wenn Admin Abrechnungen für einen Zeitraum erstellt
   - Betrag ist negativ (Mitglied schuldet)
   - Verlinkt mit der Abrechnung (referenz_id)

2. **Einzahlung**
   - Mitglied zahlt Geld ein
   - Betrag ist positiv (reduziert Schulden oder erhöht Guthaben)
   - Kann offene Abrechnungen automatisch als "bezahlt" markieren

3. **Auszahlung**
   - Rückerstattung an Mitglied
   - Betrag ist negativ (erhöht Schulden oder reduziert Guthaben)

4. **Korrektur**
   - Manuelle Anpassung durch Admin
   - Für Fehlerkorrektur oder Sonderfälle

5. **Jahresübertrag**
   - Überträgt Saldo vom Vorjahr ins neue Jahr
   - Wird beim Jahresabschluss erstellt

## Datenbank-Tabellen

### `buchungen`
Alle Transaktionen eines Mitglieds:
- `benutzer_id` - Mitglied
- `gemeinschaft_id` - Gemeinschaft
- `datum` - Buchungsdatum
- `betrag` - Betrag (negativ = Schuld, positiv = Guthaben)
- `typ` - Buchungstyp (siehe oben)
- `beschreibung` - Beschreibungstext
- `referenz_typ` / `referenz_id` - Verweis auf Abrechnung
- `erstellt_von` - Admin der die Buchung erstellt hat

### `mitglieder_konten`
Cache für Kontostände:
- `benutzer_id` / `gemeinschaft_id` - Eindeutig
- `saldo` - Aktueller Kontostand (Summe aller Buchungen)
- `saldo_vorjahr` - Stand vom letzten Jahresabschluss

### `jahresabschluesse`
Historie der Jahresabschlüsse:
- `gemeinschaft_id` / `jahr` - Eindeutig
- `abschluss_datum` - Wann wurde abgeschlossen
- `erstellt_von` - Welcher Admin

## Admin-Funktionen

### Kontenübersicht (`/admin/gemeinschaften/<id>/konten`)
- Zeigt alle Mitglieder mit Kontostand
- Statistiken: Guthaben, Schulden, Ausgeglichen
- Letzte 20 Buchungen
- Zugriff auf:
  - Kontoverlauf (Detail)
  - Zahlung verbuchen
  - Neue Buchung erstellen

### Zahlung verbuchen
- Erfasst eingegangene Zahlungen von Mitgliedern
- Markiert offene Abrechnungen automatisch als "bezahlt"
- Vorschlag: Summe aller offenen Abrechnungen

### Manuelle Buchung
- Für Einzahlungen, Auszahlungen, Korrekturen
- Freie Auswahl von Mitglied, Betrag, Datum
- Erfordert Beschreibung (für Transparenz)

## Mitglieder-Funktionen

### Mein Konto (`/mein-konto/<gemeinschaft_id>`)
- Aktueller Kontostand mit Status
- Offene Abrechnungen mit PDF-Links
- Bankverbindung der Gemeinschaft
- Vollständiger Kontoverlauf mit laufendem Saldo
- Navigation über Dropdown "Meine Konten" im Hauptmenü

## Automatische Integration

### Abrechnungserstellung
Wenn ein Admin Abrechnungen erstellt:
1. Abrechnung wird in `mitglieder_abrechnungen` erstellt
2. Automatisch wird eine Buchung (Typ: 'abrechnung') erstellt
3. Mitgliederkonto wird aktualisiert (Saldo reduziert)

### Zahlungseingang
Wenn eine Zahlung verbucht wird:
1. Buchung (Typ: 'einzahlung') wird erstellt
2. Mitgliederkonto wird aktualisiert (Saldo erhöht)
3. System prüft ob offene Abrechnungen beglichen werden können
4. Abrechnungen werden als 'bezahlt' markiert

## Jahresabschluss (geplant)

1. Admin startet Jahresabschluss für eine Gemeinschaft
2. System berechnet Salden aller Mitglieder
3. Für jedes Mitglied:
   - Aktueller Saldo wird als `saldo_vorjahr` gespeichert
   - Jahresübertragsbuchung wird erstellt
4. Jahresabschluss wird in `jahresabschluesse` protokolliert

## Migration bestehender Daten

### Durchgeführte Schritte:
```bash
python migrate_buchungssystem.py       # Tabellen erstellen
python import_abrechnungen_in_buchungen.py  # Bestehende Abrechnungen importieren
```

Ergebnis:
- 10 Abrechnungen wurden als Buchungen importiert
- 10 Mitgliederkonten wurden initialisiert
- Alle Salden korrekt berechnet (negativ = Schulden)

## Verwendungsbeispiele

### Szenario 1: Mitglied zahlt bar
1. Admin geht zu "Kontenübersicht"
2. Klickt bei Mitglied auf "Zahlung verbuchen"
3. Gibt Betrag und Datum ein
4. System verbucht Einzahlung und markiert Abrechnungen als bezahlt

### Szenario 2: Fehlerhafte Abrechnung
1. Admin erstellt Korrektur-Buchung mit negativem Betrag
2. Beschreibung: "Korrektur Abrechnung #5 - Doppelte Erfassung"
3. Bei Bedarf: Neue korrekte Abrechnung manuell erstellen

### Szenario 3: Mitglied möchte Überblick
1. Mitglied klickt auf "Meine Konten" > [Gemeinschaft]
2. Sieht sofort: Aktueller Kontostand und offene Beträge
3. Kann alle Buchungen mit Details einsehen
4. Findet Bankverbindung für Überweisung

## Vorteile des Systems

- ✅ **Transparenz**: Jede Buchung ist nachvollziehbar
- ✅ **Automatisierung**: Abrechnungen erstellen Buchungen automatisch
- ✅ **Flexibilität**: Manuelle Korrekturen möglich
- ✅ **Historie**: Alle Transaktionen bleiben erhalten
- ✅ **Jahresabschluss**: Vorbereitet für saubere Jahresüberträge
- ✅ **Mitgliedersicht**: Jeder kann sein Konto einsehen

## Zukünftige Erweiterungen

1. **Kontoauszug als PDF** - Druckbare Übersicht für Mitglieder
2. **Excel-Export** - Für externe Buchhaltung
3. **Zahlungserinnerungen** - Automatische E-Mails bei offenen Beträgen
4. **Ratenzahlung** - Große Beträge in Raten zahlen
5. **SEPA-Import** - Automatischer Abgleich mit Kontoauszügen

## Support

Bei Fragen zum Buchungssystem:
- Siehe Anleitung in dieser Datei
- Admin-Level 2 hat vollen Zugriff auf alle Funktionen
- Gemeinschafts-Admins (Level 1) nur für ihre Gemeinschaften
