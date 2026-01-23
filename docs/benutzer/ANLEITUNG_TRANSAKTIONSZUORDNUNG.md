# Anleitung: Transaktionszuordnung

## Übersicht

Das System importiert nun **ALLE Transaktionen** aus CSV-Dateien:
- **Eingänge** (positive Beträge) → können Benutzern zugeordnet werden
- **Ausgänge** (negative Beträge) → können Maschinen oder Gemeinschaftskosten zugeordnet werden

**Wichtig:** Jede Gemeinschaft hat ihre eigenen Transaktionen und ihren eigenen Banksaldo!

## Anfangssaldo eingeben

### Warum ist der Anfangssaldo wichtig?

Der Anfangssaldo ist der Kontostand Ihres Gemeinschaftskontos, bevor Sie mit dem Import beginnen.

**Berechnung:**
```
Aktueller Saldo = Anfangssaldo + Eingänge - Ausgänge
```

### Anfangssaldo festlegen

1. **Admin** → **Abrechnungen & CSV-Import**
2. Gemeinschaft auswählen → **Transaktionen**
3. Oben rechts auf **"Anfangssaldo"** klicken
4. Anfangssaldo eingeben:
   - **Betrag:** z.B. 5432,18 (mit Komma!)
   - **Stichtag:** Datum des Kontostands (optional)
5. **"Anfangssaldo speichern"** klicken

### Beispiel

**Ausgangssituation:**
- Kontostand am 01.01.2026: **5.000,00 €**
- Sie möchten ab diesem Datum Transaktionen importieren

**Eingabe:**
- Anfangssaldo: `5000,00`
- Stichtag: `01.01.2026`

**Nach CSV-Import:**
```
Anfangssaldo:        5.000,00 €
+ Eingänge:         +2.500,00 €
- Ausgänge:         -1.200,00 €
─────────────────────────────────
= Aktueller Saldo:   6.300,00 €
```

### Anfangssaldo korrigieren

Sie können den Anfangssaldo jederzeit ändern:
1. **Anfangssaldo-Button** → Neuen Wert eingeben
2. Die Änderung wirkt sich sofort auf alle Saldo-Anzeigen aus
3. Bereits importierte Transaktionen bleiben unverändert

## CSV-Import

**Wichtig:** CSV-Importe sind gemeinschaftsspezifisch! Jede Gemeinschaft hat:
- ✅ Eigene Transaktionen
- ✅ Eigenen Anfangssaldo
- ✅ Eigene Import-Historie
- ✅ Eigene CSV-Format-Konfiguration

### Schritt 1: CSV-Datei vorbereiten
1. CSV-Datei von Ihrer Bank herunterladen (z.B. Raiffeisen Elba)
2. Alle Transaktionen werden importiert (Ein- und Ausgänge)

### Schritt 2: Import durchführen
1. Admin → Abrechnungen & CSV-Import
2. Gemeinschaft auswählen
3. CSV-Datei hochladen
4. System importiert automatisch:
   - **Eingänge** mit Zahlungsreferenz werden automatisch zugeordnet
   - **Eingänge ohne Referenz** bleiben unzugeordnet
   - **Ausgänge** bleiben unzugeordnet (manuelle Zuordnung erforderlich)

## Transaktionsverwaltung

### Filter-Ansichten
- **Alle**: Zeigt alle Transaktionen
- **Eingänge**: Nur positive Beträge (Zahlungen von Mitgliedern)
- **Ausgänge**: Nur negative Beträge (Rechnungen, Kosten)
- **Unzugeordnet**: Transaktionen ohne Zuordnung (mit Badge-Anzahl)

### Statistik-Übersicht
Oben auf der Seite sehen Sie:
- Anzahl Transaktionen gesamt
- Anzahl zugeordnete Transaktionen
- Summe Eingänge (grün)
- Summe Ausgänge (rot)
- Saldo (schwarz)

## Zuordnung von Eingängen

### Wann zuordnen?
- Wenn Mitglied ohne Zahlungsreferenz überwiesen hat
- Bei manuellen Korrekturen
- Bei Bareinzahlungen

### Wie zuordnen?
1. Filter auf "Eingänge" oder "Unzugeordnet" setzen
2. Bei gewünschter Transaktion auf **"Zuordnen"** klicken
3. Im Modal:
   - Betrag, Datum und Verwendungszweck werden angezeigt
   - **Benutzer auswählen** aus Dropdown
   - **"Zuordnen"** klicken

### Was passiert?
- Transaktion wird dem Benutzer zugeordnet
- Betrag wird auf Mitgliedskonto gutgeschrieben
- Status wechselt auf "Zugeordnet" (grünes Häkchen)
- Badge mit Benutzername wird angezeigt

## Zuordnung von Ausgängen

### Option 1: Maschine zuordnen
**Wann verwenden?**
- Reparaturen
- Wartungskosten
- Ersatzteile
- Treibstoff für bestimmte Maschine

**Vorgehen:**
1. Bei Ausgang auf **"Zuordnen"** klicken
2. **"Maschine"** wählen
3. Maschine aus Dropdown auswählen
4. Optional: Beschreibung eingeben (z.B. "Ölwechsel")
5. **"Zuordnen"** klicken

**Ergebnis:**
- Kosten werden Maschine zugerechnet
- Erscheint in Gemeinschaftskosten mit Maschinenlink
- Badge "Maschine: [Name]" wird angezeigt

### Option 2: Gemeinschaftskosten
**Wann verwenden?**
- Versicherungen
- Verwaltungskosten
- Gemeinschaftliche Ausgaben
- Allgemeine Kosten

**Vorgehen:**
1. Bei Ausgang auf **"Zuordnen"** klicken
2. **"Gemeinschaftskosten"** wählen
3. Kategorie auswählen:
   - Sonstiges
   - Versicherung
   - Reparatur
   - Treibstoff
   - Wartung
   - Verwaltung
4. Optional: Beschreibung eingeben
5. **"Zuordnen"** klicken

**Ergebnis:**
- Kosten werden Gemeinschaft zugerechnet
- Erscheint in Gemeinschaftskosten
- Badge "Gemeinschaft" wird angezeigt

## Zuordnung aufheben

Falls eine Zuordnung falsch war:
1. Bei zugeordneter Transaktion auf **"Aufheben"** klicken
2. Bestätigen
3. Transaktion ist wieder unzugeordnet
4. Kann neu zugeordnet werden

**Wichtig:** 
- Bei Eingängen wird Betrag vom Mitgliedskonto abgezogen
- Bei Ausgängen werden Gemeinschaftskosten gelöscht

## Transaktionen löschen

### Einzelne Transaktion löschen

**Wann verwenden?**
- Falsche Transaktion importiert
- Duplikat manuell entfernen
- Test-Daten aufräumen

**Vorgehen:**
1. In der Transaktionsliste bei gewünschter Zeile
2. Auf **Papierkorb-Symbol** 🗑️ klicken (ganz rechts)
3. Sicherheitsabfrage bestätigen
4. ✅ Transaktion wird gelöscht

**Was wird gelöscht:**
- Die Transaktion selbst
- Zugehörige Gemeinschaftskosten (falls vorhanden)
- Zuordnung zu Benutzer/Maschine

⚠️ **Achtung:** Dies kann nicht rückgängig gemacht werden!

### Ganzen Import löschen

**Wann verwenden?**
- Falsche CSV-Datei importiert
- Import mit falschen Einstellungen
- Test-Import rückgängig machen

**Vorgehen:**
1. Oben rechts auf **"Importe verwalten"** klicken
2. Modal zeigt alle Import-Durchgänge mit:
   - Import-Datum
   - Wer hat importiert
   - Anzahl Transaktionen
3. Bei gewünschtem Import auf **"Import löschen"** klicken
4. Sicherheitsabfrage bestätigen (zeigt Anzahl an)
5. ✅ Alle Transaktionen dieses Imports werden gelöscht

**Was wird gelöscht:**
- ALLE Transaktionen des Import-Durchgangs
- Alle zugehörigen Gemeinschaftskosten
- Alle Zuordnungen

**Beispiel:**
```
Import-Datum: 14.01.2026
Importiert von: Max Mustermann
Anzahl: 45 Transaktionen
→ [Import löschen]
```
Nach Bestätigung: Alle 45 Transaktionen vom 14.01.2026 werden entfernt.

⚠️ **Achtung:** 
- Dies löscht ALLE Transaktionen des Tages von diesem Benutzer
- Kann nicht rückgängig gemacht werden
- Macht nur Sinn unmittelbar nach einem falschen Import

## Farb-Kodierung

| Farbe | Bedeutung |
|-------|-----------|
| 🟢 Grün | Eingänge (positive Beträge) |
| 🔴 Rot | Ausgänge (negative Beträge) |
| 🟡 Gelb | Unzugeordnete Transaktionen |
| ✅ Grünes Häkchen | Zugeordnet |
| ⚠️ Gelbes Ausrufezeichen | Nicht zugeordnet |

## Badges in Zuordnung-Spalte

- 🟢 **[Person] Name** = Benutzer zugeordnet
- 🔵 **[Zahnrad] Maschine** = Maschine zugeordnet
- 🔷 **[Personen] Gemeinschaft** = Gemeinschaftskosten
- 🟡 **[?] Offen** = Noch nicht zugeordnet

## Best Practices

### Regelmäßiger Import
- CSV-Daten monatlich importieren
- System erkennt Duplikate automatisch

### Sofortige Zuordnung
- Unzugeordnete Transaktionen zeitnah zuordnen
- Filter "Unzugeordnet" zeigt offene Aufgaben

### Konsistente Kategorien
- Bei Gemeinschaftskosten einheitliche Kategorien verwenden
- Beschreibungen helfen bei späterer Nachvollziehbarkeit

### Kontrolle
- Statistik oben zeigt Vollständigkeit
- Saldo sollte mit Bankkonto übereinstimmen

## Datenbank-Struktur

### Neue Tabellen
**gemeinschafts_kosten**
- Speichert zugeordnete Ausgänge
- Verknüpfung zu Transaktion, Maschine oder Gemeinschaft
- Kategorien für Auswertungen

**bank_transaktionen** (erweitert)
- `zuordnung_typ`: benutzer, maschine, gemeinschaft
- `zuordnung_id`: ID der zugeordneten Entität
- `zugeordnet`: Status-Flag (0/1)

## Migration

Die Migration wurde automatisch ausgeführt:
```bash
python migrate_gemeinschaftskosten.py
```

Folgende Änderungen:
- Tabelle `gemeinschafts_kosten` erstellt
- Spalten `zuordnung_typ` und `zuordnung_id` hinzugefügt
- Indizes für Performance erstellt

## Support

Bei Fragen oder Problemen:
1. Prüfen Sie Filter-Einstellungen
2. Kontrollieren Sie CSV-Konfiguration
3. Überprüfen Sie Berechtigungen (Gemeinschafts-Admin)

---

**Datum:** 14. Januar 2026  
**Version:** 2.0 - Vollständige Transaktionsverwaltung
