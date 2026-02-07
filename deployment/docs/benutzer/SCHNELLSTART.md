# Schnellstart-Anleitung

## Erste Schritte

### 1. Programm starten
```powershell
python main.py
```

### 2. Stammdaten anlegen (in dieser Reihenfolge!)

#### a) Benutzer hinzufügen
- Menü: **Stammdaten → Benutzer verwalten**
- Button: **Neuer Benutzer**
- Mindestens **Name** eingeben
- **Speichern**

#### b) Maschinen hinzufügen
- Menü: **Stammdaten → Maschinen verwalten**
- Button: **Neue Maschine**
- **Bezeichnung** eingeben (z.B. "Traktor Fendt")
- **Stundenzähler** eingeben (aktueller Stand)
- **Speichern**

### 3. Ersten Einsatz erfassen

Im Hauptfenster, Tab **"Neuer Einsatz"**:
1. **Datum**: (bereits ausgefüllt)
2. **Benutzer**: Auswählen
3. **Maschine**: Auswählen (Anfangstand wird automatisch vorgeschlagen)
4. **Einsatzzweck**: Auswählen (z.B. "Mähen")
5. **Endstand**: Eingeben (z.B. Anfangstand + gearbeitete Stunden)
6. Optional: **Treibstoffverbrauch** und **Kosten**
7. Button: **Einsatz speichern**

✅ Fertig! Der Einsatz ist gespeichert und der Stundenzähler der Maschine wurde aktualisiert.

## Tipps

- Die **Betriebsstunden** werden automatisch berechnet
- Der **Anfangstand** wird automatisch von der Maschine übernommen
- Beim Speichern wird der **Stundenzähler der Maschine** automatisch aktualisiert
- Im Tab **"Einsatzübersicht"** sehen Sie alle Einsätze
- Im Tab **"Statistiken"** können Sie Auswertungen ansehen

## Beispiel-Workflow

```
1. Heute, 8:00 Uhr → Traktor nehmen → Stundenzähler: 1234.5 h
2. Arbeit: Wiese mähen
3. Heute, 12:00 Uhr → Fertig → Stundenzähler: 1238.0 h
4. Tankstelle: 15 Liter getankt für 25,50 €

→ Im Programm erfassen:
   - Benutzer: Müller, Hans
   - Maschine: Traktor Fendt
   - Zweck: Mähen
   - Anfang: 1234.5
   - Ende: 1238.0
   - Treibstoff: 15
   - Kosten: 25.50
   - Speichern
```

Der nächste Benutzer sieht dann automatisch 1238.0 als Anfangstand!
