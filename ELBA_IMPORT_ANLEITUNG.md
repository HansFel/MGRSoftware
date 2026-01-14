# Raiffeisen Elba CSV-Import Anleitung

## Ihr Elba-Format

Die Datei `meinElba_umsaetze_AT503834600000204230_suche (4).csv` hat folgendes Format:

### Struktur
- **KEINE Kopfzeile** - Datei beginnt direkt mit Daten
- **Trennzeichen:** `;` (Semikolon)
- **Dezimaltrennzeichen:** `,` (Komma)
- **Datumsformat:** `TT.MM.JJJJ`

### Spalten-Reihenfolge
1. **Spalte 1** = Buchungsdatum (z.B. `30.12.2024`)
2. **Spalte 2** = Beschreibung/Zahlungsreferenz (langer Text mit Auftraggeber, Empfänger, IBAN, etc.)
3. **Spalte 3** = Valutadatum (z.B. `30.12.2024`)
4. **Spalte 4** = Betrag (z.B. `6116,70` oder `-140,00`)
5. **Spalte 5** = Währung (`EUR`)
6. **Spalte 6** = Zeitstempel (z.B. `30.12.2024 09:04:48:233`)

### Beispiel-Zeile
```
30.12.2024;"Auftraggeber: Josef Stadlober Zahlungsreferenz: Traktorabrechnung 2024 IBAN Auftraggeber: AT343834600009000381 BIC Auftraggeber: RZSTAT2G346";30.12.2024;6116,70;EUR;30.12.2024 09:04:48:233
```

## Konfiguration im System

### Option 1: Automatisches Konfigurations-Skript (EMPFOHLEN)

```bash
python configure_elba_format.py
```

Das Skript fragt nach der Gemeinschafts-ID und richtet alles automatisch ein.

### Option 2: Manuelle Konfiguration im Admin-Bereich

Gehen Sie zu: **Admin → Abrechnungen & CSV-Import → Format konfigurieren**

**Allgemeine Einstellungen:**
- Trennzeichen: **; (Semikolon)**
- Zeichenkodierung: **UTF-8 (mit BOM)** oder **UTF-8**
- Zeilen überspringen: **0**
- CSV hat Kopfzeile: **❌ NICHT AKTIVIERT** (wichtig!)

**Spalten-Namen:** (da keine Kopfzeile vorhanden)
- Buchungsdatum: **Spalte1**
- Valutadatum: **Spalte3**
- Betrag: **Spalte4**
- Verwendungszweck: **Spalte2**
- Empfänger/Zahler: **Spalte2** (enthält alle Infos)
- Kontonummer: *leer lassen*

**Zahlen- und Datumsformat:**
- Dezimaltrennzeichen: **, (Komma)**
- Tausendertrennzeichen: **(keins/leer)**
- Datumsformat: **TT.MM.JJJJ**

## CSV-Import durchführen

1. Gehen Sie zu: **Admin → Abrechnungen & CSV-Import**
2. Wählen Sie Ihre Gemeinschaft
3. Klicken Sie auf **"CSV importieren"**
4. Laden Sie die Elba-CSV-Datei hoch
5. Das System:
   - Erkennt automatisch Duplikate
   - Ordnet Zahlungen mit MGR-Referenz automatisch zu
   - Zeigt Ihnen eine Zusammenfassung

## Zahlungsreferenzen

Damit Zahlungen automatisch Mitgliedern zugeordnet werden, muss die **Zahlungsreferenz** im Verwendungszweck enthalten sein.

**Format:** `MGR-{Gemeinschaft}-{Benutzer}-{Prüfziffer}`

**Beispiel:** `MGR-1-5-12`

Diese Referenz wird automatisch in der Spalte2 (Beschreibung) gesucht.

## Wichtige Hinweise

⚠️ **Das Elba-Format hat KEINE Kopfzeile!**
- Deshalb arbeiten wir mit "Spalte1", "Spalte2", etc.
- Dies ist in der Konfiguration bereits berücksichtigt

✅ **Duplikatschutz aktiv**
- Jede Transaktion wird anhand von Datum, Betrag und Beschreibung identifiziert
- Bereits importierte Transaktionen werden automatisch übersprungen

✅ **Automatische Zuordnung**
- Wenn die MGR-Referenz im Text gefunden wird, erfolgt die Zuordnung automatisch
- Status wird auf "Zugeordnet" gesetzt

## Beispiel-Transaktion mit Zahlungsreferenz

```csv
20.01.2025;"Auftraggeber: Max Mustermann Zahlungsreferenz: MGR-1-5-12 Abrechnung 2024 IBAN: AT123...";20.01.2025;150,00;EUR;...
```

Diese Transaktion würde automatisch dem Benutzer mit ID 5 in Gemeinschaft 1 zugeordnet.
