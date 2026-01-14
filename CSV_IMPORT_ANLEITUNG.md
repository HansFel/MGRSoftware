# Anleitung: CSV-Import konfigurieren

## Schritt-für-Schritt Anleitung

### 1. CSV-Datei vorbereiten

#### Was ist eine CSV-Datei?
CSV (Comma-Separated Values) ist ein einfaches Textformat für Tabellen. Jede Zeile ist eine Zeile in der Tabelle, und die Spalten sind durch ein bestimmtes Zeichen getrennt.

#### Beispiel einer CSV-Datei:
```
Datum;Betrag;Beschreibung
01.01.2026;100,50;Zahlung Mitglied
02.01.2026;-50,00;Treibstoff
```

### 2. CSV-Datei analysieren

#### Öffnen Sie die CSV-Datei mit einem Text-Editor
1. Rechtsklick auf die CSV-Datei
2. "Öffnen mit" → **Editor** (Notepad) oder **Notepad++** wählen
3. **NICHT** mit Excel öffnen! (Excel ändert manchmal das Format)

#### Was Sie herausfinden müssen:

##### A) Hat die Datei eine Kopfzeile?
**Mit Kopfzeile:** Erste Zeile enthält Spaltennamen
```
Buchungsdatum;Betrag;Verwendungszweck
01.01.2026;100,50;Zahlung
```

**Ohne Kopfzeile:** Erste Zeile sind bereits Daten
```
01.01.2026;100,50;Zahlung
02.01.2026;-50,00;Rechnung
```

##### B) Welches Trennzeichen wird verwendet?
Schauen Sie, welches Zeichen zwischen den Spalten steht:
- **Semikolon** `;` → in Deutschland häufig
- **Komma** `,` → in englischsprachigen Ländern
- **Tabulator** (unsichtbar, große Abstände) → selten
- **Pipe** `|` → sehr selten

**Beispiele:**
```
Semikolon:  01.01.2026;100,50;Zahlung
Komma:      01/01/2026,100.50,Payment
```

##### C) Wie sind Zahlen formatiert?

**Dezimaltrennzeichen:**
- Deutsche Banken: `1234,56` → Komma
- US-Banken: `1234.56` → Punkt

**Tausendertrennzeichen:**
- Deutsche Banken: `1.234,56` → Punkt
- US-Banken: `1,234.56` → Komma
- Oft auch: `1234,56` → Keins

##### D) Wie ist das Datum formatiert?

Schauen Sie auf ein Datum und bestimmen Sie das Format:
- `31.12.2025` → TT.MM.JJJJ
- `2025-12-31` → JJJJ-MM-TT
- `12/31/2025` → MM/TT/JJJJ
- `31/12/2025` → TT/MM/JJJJ

##### E) Welche Spalten gibt es?

Notieren Sie die Spaltennamen (bei Kopfzeile) oder zählen Sie die Spalten:

**Mit Kopfzeile:**
```
Buchungsdatum;Valutadatum;Betrag;Verwendungszweck;Empfänger
```
Spalten: `Buchungsdatum`, `Valutadatum`, `Betrag`, `Verwendungszweck`, `Empfänger`

**Ohne Kopfzeile:**
```
01.01.2026;02.01.2026;100,50;Zahlung;Max Mustermann
```
Spalten: `Spalte1`, `Spalte2`, `Spalte3`, `Spalte4`, `Spalte5`

### 3. Konfiguration im System eingeben

#### Navigation
1. Melden Sie sich als Administrator an
2. Gehen Sie zu **Admin** → **Abrechnungen & CSV-Import**
3. Klicken Sie auf **Format konfigurieren**

#### Allgemeine Einstellungen

##### Trennzeichen
Wählen Sie das Zeichen, das die Spalten trennt:
- Semikolon (;) - **Standard für deutsche Banken**
- Komma (,)
- Tabulator
- Pipe (|)

##### Zeichenkodierung
Normalerweise: **UTF-8 (mit BOM)** oder **UTF-8**

Wenn Sie Umlaute (ä, ö, ü) sehen, die falsch dargestellt werden:
- Probieren Sie **ISO-8859-1 (Latin-1)**
- Oder **Windows-1252**

##### Zeilen überspringen
Manche CSV-Dateien haben am Anfang Leerzeilen oder Überschriften.
Wenn Sie z.B. die ersten 2 Zeilen überspringen wollen: `2`

##### CSV hat Kopfzeile
- ☑️ **Häkchen setzen**: Wenn die erste Zeile Spaltennamen enthält
- ☐ **Kein Häkchen**: Wenn die erste Zeile bereits Daten enthält (wie bei Raiffeisen Elba)

#### Spalten-Namen

**MIT Kopfzeile:**
Geben Sie die **exakten** Spaltennamen aus der ersten Zeile ein:
- Buchungsdatum: `Buchungstag`
- Betrag: `Betrag`
- Verwendungszweck: `Verwendungszweck`

⚠️ **Wichtig:** Groß-/Kleinschreibung beachten! Leerzeichen beachten!

**OHNE Kopfzeile:**
Verwenden Sie `Spalte1`, `Spalte2`, `Spalte3`, etc.
- Erste Spalte = `Spalte1`
- Zweite Spalte = `Spalte2`
- usw.

**Beispiel ohne Kopfzeile:**
```
30.12.2024;"Text";30.12.2024;6116,70;EUR;timestamp
```
Einstellungen:
- Buchungsdatum: `Spalte1`
- Verwendungszweck: `Spalte2`
- Valutadatum: `Spalte3`
- Betrag: `Spalte4`

#### Pflichtfelder
Diese Felder **müssen** ausgefüllt werden:
- ✅ Buchungsdatum
- ✅ Betrag
- ✅ Verwendungszweck

Optional:
- ⭕ Valutadatum (wenn nicht vorhanden: Buchungsdatum wird verwendet)
- ⭕ Empfänger/Zahler
- ⭕ Kontonummer/IBAN

#### Zahlen- und Datumsformat

##### Dezimaltrennzeichen
Was trennt die Nachkommastellen?
- `1234,56` → **Komma** (Deutschland)
- `1234.56` → **Punkt** (USA)

##### Tausendertrennzeichen
Was trennt die Tausender?
- `1.234,56` → **Punkt**
- `1,234.56` → **Komma**
- `1234,56` → **Keins**

##### Datumsformat
Wie ist das Datum aufgebaut?
- `31.12.2025` → **TT.MM.JJJJ**
- `2025-12-31` → **JJJJ-MM-TT**
- `12/31/2025` → **MM/TT/JJJJ**
- `31/12/2025` → **TT/MM/JJJJ**

### 4. Beispiele für verschiedene Banken

#### Raiffeisen Elba

**CSV-Format:**
```
30.12.2024;"SEPA Überweisung Eingang...";30.12.2024;6116,70;EUR;30.12.2024
31.12.2024;"SEPA Überweisung Ausgang...";31.12.2024;-140,00;EUR;31.12.2024
```

**Konfiguration:**
```
Allgemein:
✓ Trennzeichen: Semikolon (;)
✓ Kodierung: UTF-8
✓ Zeilen überspringen: 0
✓ Hat Kopfzeile: NEIN (kein Häkchen!)

Spalten:
✓ Buchungsdatum: Spalte1
✓ Verwendungszweck: Spalte2
✓ Valutadatum: Spalte3
✓ Betrag: Spalte4
✓ Empfänger: (leer lassen)
✓ Kontonummer: (leer lassen)

Format:
✓ Dezimaltrennzeichen: Komma (,)
✓ Tausendertrennzeichen: Keins
✓ Datumsformat: TT.MM.JJJJ
```

#### Sparkasse (mit Kopfzeile)

**CSV-Format:**
```
Buchungstag;Wertstellung;Betrag;Verwendungszweck;Empfänger;IBAN
01.01.2026;02.01.2026;1.234,56;Mitgliedsbeitrag;Maier Josef;AT123456789
```

**Konfiguration:**
```
Allgemein:
✓ Trennzeichen: Semikolon (;)
✓ Kodierung: UTF-8 (mit BOM)
✓ Zeilen überspringen: 0
✓ Hat Kopfzeile: JA (Häkchen setzen!)

Spalten:
✓ Buchungsdatum: Buchungstag
✓ Verwendungszweck: Verwendungszweck
✓ Valutadatum: Wertstellung
✓ Betrag: Betrag
✓ Empfänger: Empfänger
✓ Kontonummer: IBAN

Format:
✓ Dezimaltrennzeichen: Komma (,)
✓ Tausendertrennzeichen: Punkt (.)
✓ Datumsformat: TT.MM.JJJJ
```

#### US-Bank (englisches Format)

**CSV-Format:**
```
Date,Amount,Description,Payee
12/31/2025,1234.56,Payment,John Doe
```

**Konfiguration:**
```
Allgemein:
✓ Trennzeichen: Komma (,)
✓ Kodierung: UTF-8
✓ Zeilen überspringen: 0
✓ Hat Kopfzeile: JA

Spalten:
✓ Buchungsdatum: Date
✓ Verwendungszweck: Description
✓ Valutadatum: (leer)
✓ Betrag: Amount
✓ Empfänger: Payee
✓ Kontonummer: (leer)

Format:
✓ Dezimaltrennzeichen: Punkt (.)
✓ Tausendertrennzeichen: Komma (,)
✓ Datumsformat: MM/TT/JJJJ
```

### 5. Testen

1. Konfiguration speichern
2. Zurück zur Import-Seite
3. Kleine Test-CSV hochladen (z.B. nur 3-5 Zeilen)
4. Ergebnis prüfen:
   - Werden alle Zeilen importiert?
   - Sind die Beträge korrekt?
   - Sind die Daten richtig?

### 6. Häufige Fehler

#### "Ungültiges Datumsformat"
**Problem:** Das Datumsformat stimmt nicht.
**Lösung:** Schauen Sie sich ein Datum in der CSV an und wählen Sie das passende Format.

#### "Fehlende Pflichtfelder"
**Problem:** Die Spaltennamen stimmen nicht.
**Lösung:** 
- Bei Kopfzeile: Exakten Namen aus erster Zeile kopieren
- Ohne Kopfzeile: Spalte1, Spalte2, ... verwenden

#### "Betrag ist 0 oder falsch"
**Problem:** Dezimal-/Tausendertrennzeichen falsch.
**Lösung:** Format prüfen:
- Deutsche Banken: Dezimal=Komma, Tausender=Punkt
- US-Banken: Dezimal=Punkt, Tausender=Komma

#### "Umlaute werden falsch angezeigt"
**Problem:** Falsche Kodierung.
**Lösung:** Probieren Sie:
1. UTF-8 (mit BOM)
2. UTF-8
3. ISO-8859-1
4. Windows-1252

#### "Duplikate übersprungen"
**Das ist normal!** Das System erkennt bereits importierte Transaktionen und überspringt sie automatisch.

### 7. Tipps & Tricks

#### Schneller testen
Erstellen Sie eine kleine Test-CSV mit nur 2-3 Zeilen zum Ausprobieren.

#### Spalten zählen
Öffnen Sie die CSV im Editor und zählen Sie die Trennzeichen:
```
30.12.2024;"Text";30.12.2024;6116,70;EUR
     ↓       ↓        ↓       ↓      ↓
  Spalte1  Spalte2 Spalte3 Spalte4 Spalte5
```

#### Kopfzeile erkennen
Wenn die erste Zeile **Text** statt **Zahlen/Datum** enthält → Kopfzeile vorhanden

#### Backup
Bewahren Sie eine Kopie Ihrer Original-CSV auf, falls Sie sie nochmal importieren müssen.

### 8. Support

**Problem nicht gelöst?**
1. Prüfen Sie die Fehlermeldung genau
2. Schauen Sie in die CSV-Datei im Text-Editor
3. Vergleichen Sie mit den Beispielen oben
4. Testen Sie mit einer kleinen Datei

**Wichtige Informationen für Support:**
- Name Ihrer Bank
- Hat die CSV eine Kopfzeile? (Ja/Nein)
- Wie sieht die erste Zeile aus?
- Welches Trennzeichen wird verwendet?

---

**Erstellt:** 14. Januar 2026  
**Autor:** Maschinengemeinschaft Support-Team
