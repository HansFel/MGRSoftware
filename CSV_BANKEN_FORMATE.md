# CSV-Import-Konfiguration - Beispiele für verschiedene Banken

## Deutsche Banken (Standard)

**Sparkasse, Volksbank, etc.**
- Trennzeichen: `;` (Semikolon)
- Dezimaltrennzeichen: `,` (Komma)
- Tausendertrennzeichen: `.` (Punkt)
- Datumsformat: `TT.MM.JJJJ`
- Kodierung: `utf-8-sig` oder `iso-8859-1`

Spalten:
- Buchungsdatum: `Buchungstag` oder `Buchungsdatum`
- Betrag: `Betrag` oder `Umsatz`
- Verwendungszweck: `Verwendungszweck`
- Empfänger: `Beguenstigter/Zahlungspflichtiger` oder `Empfänger`

---

## Raiffeisen Bank

- Trennzeichen: `;` (Semikolon)
- Dezimaltrennzeichen: `,` (Komma)
- Tausendertrennzeichen: `.` (Punkt)
- Datumsformat: `TT.MM.JJJJ`
- Kodierung: `utf-8-sig`

Spalten:
- Buchungsdatum: `Valutadatum` oder `Buchungsdatum`
- Betrag: `Betrag`
- Verwendungszweck: `Buchungstext` oder `Verwendungszweck`

---

## Englische/Amerikanische Banken

- Trennzeichen: `,` (Komma)
- Dezimaltrennzeichen: `.` (Punkt)
- Tausendertrennzeichen: `,` (Komma) oder keins
- Datumsformat: `MM/DD/YYYY` (USA) oder `DD/MM/YYYY` (UK)
- Kodierung: `utf-8`

Spalten (variiert stark):
- Buchungsdatum: `Date`, `Transaction Date`, `Posting Date`
- Betrag: `Amount`, `Value`, `Transaction Amount`
- Verwendungszweck: `Description`, `Reference`, `Memo`

---

## Schweizer Banken

- Trennzeichen: `;` (Semikolon) oder `,` (Komma)
- Dezimaltrennzeichen: `.` (Punkt) oder `,` (Komma)
- Tausendertrennzeichen: `'` (Apostroph) oder `.` (Punkt)
- Datumsformat: `TT.MM.JJJJ`
- Kodierung: `utf-8`

Spalten:
- Buchungsdatum: `Buchungsdatum` oder `Valuta`
- Betrag: `Betrag` oder `Belastung/Gutschrift`
- Verwendungszweck: `Beschreibung` oder `Mitteilung`

---

## Hinweise

1. **Spaltennamen exakt übernehmen**: Die Spaltennamen müssen genau so geschrieben werden, 
   wie sie in der ersten Zeile der CSV-Datei stehen (inkl. Groß-/Kleinschreibung).

2. **Testdatei prüfen**: Öffnen Sie die CSV-Datei mit einem Text-Editor (nicht Excel!), 
   um die genaue Struktur zu sehen.

3. **Zeilen überspringen**: Manche Banken fügen am Anfang der Datei Informationen ein 
   (Kontonummer, Datum, etc.). Diese Zeilen können übersprungen werden.

4. **Kodierung**: Bei Umlauten (ä, ö, ü) probieren Sie verschiedene Kodierungen:
   - `utf-8-sig`: UTF-8 mit Byte Order Mark (BOM)
   - `utf-8`: UTF-8 ohne BOM
   - `iso-8859-1`: Latin-1 (alte deutsche Kodierung)
   - `cp1252`: Windows-1252 (Windows-Standard)

5. **Dezimaltrennzeichen**: 
   - Deutsche Banken: `1.234,56` (Punkt für Tausender, Komma für Dezimal)
   - US/UK Banken: `1,234.56` (Komma für Tausender, Punkt für Dezimal)

6. **Datumsformat testen**: Falls der Import fehlschlägt, ist oft das Datumsformat falsch.
   Gängige Formate:
   - `%d.%m.%Y` = 31.12.2025
   - `%Y-%m-%d` = 2025-12-31
   - `%m/%d/%Y` = 12/31/2025 (US)
   - `%d/%m/%Y` = 31/12/2025 (UK)
