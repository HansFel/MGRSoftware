# Erweiterung: Rollenverteilung und Vereinsfunktionen

## Übersicht

Erweiterung des Administrator-Systems um zusätzliche Rollen mit spezifischen Berechtigungen für Vereinsaufgaben.

---

## 1. Erweiterung der Buchhaltung

### 1.1 Jahresabschluss

- **Jahresabschluss durchführen** - Geschäftsjahr abschließen
- **Zugriff auf abgeschlossene Jahre** - Historische Daten einsehen (nur lesen)
- **Jahresüberträge** - Automatische Saldenübernahme ins neue Jahr (wie in der doppelten Buchführung üblich)

### 1.2 Neue Kontotypen

- **Kunden und Lieferanten** - Verwaltung externer Geschäftspartner
- **Anlagenkonten** - Verwaltung von Einlagekapital
  - Einlagekapital kann verzinst werden
  - Zinssatz konfigurierbar

---

## 2. Neue Administrator-Rollen

### 2.1 Obmann

**Berechtigungen:**
- [x] Alle Administratorrechte
- [x] Kann andere Rollen vergeben
- [x] Vertritt die Gemeinschaft nach außen

---

### 2.2 Kassier

**Berechtigungen:**
- [x] Zugriff auf Finanzübersicht und Abrechnungen
- [x] Zahlungen verbuchen
- [x] Kassabericht erstellen
- [x] Importieren von Bankdaten und Buchungen
- [x] Kunden- und Lieferantenverwaltung
- [x] Anlagenkonten und Einlagekapital verwalten
- [x] Jahresabschluss durchführen
- [x] Zugriff auf abgeschlossene Jahre (nur lesen)

**Erreichbar über:**
- Admin-Menü > Finanzen

---

### 2.3 Schriftführer

**Berechtigungen:**

1. **Protokolle verwalten**
   - Protokolle anlegen (mit Titel, Datum)
   - Protokolle bearbeiten
   - Protokolle abschließen/archivieren
   - Abstimmungs- und Wahlergebnisse ins Protokoll übernehmen

2. **Abstimmungen ausschreiben**
   - Titel und Überschrift festlegen
   - Beschreibungstext verfassen
   - Ablaufzeit/Frist setzen
   - Ergebnisse einsehen
   - Abstimmungen als geheim oder offen festlegen

3. **Wahlen durchführen**
   - Wahl ausschreiben für Funktionen:
     - Obmann
     - Kassier
     - Schriftführer
     - Kassaprüfer 1
     - Kassaprüfer 2
   - Wahlen als geheim oder offen festlegen
   - Kandidaten auswählen (müssen registrierte Benutzer sein)
   - Wahlergebnis auswerten

**Erreichbar über:**
- Admin-Menü > Schriftführung (neu)

---

### 2.4 Kassaprüfer (1 und 2)

**Berechtigungen:**
- [x] Einsicht in alle Finanzdaten (nur lesen)
- [x] Kassaprüfbericht erstellen
- [ ] *(weitere Berechtigungen?)*

---

## 3. Benutzer-Funktionen

### 3.1 Abstimmungen

- [x] Offene Abstimmungen anzeigen
- [x] Stimme abgeben (Ja/Nein/Enthaltung)
- [x] Eigene abgegebene Stimmen einsehen
- [x] Anträge zur Abstimmung einbringen

### 3.2 Wahlen

- [x] Offene Wahlen anzeigen
- [x] Kandidaten sehen
- [x] Stimme abgeben
- [x] Wahlergebnis einsehen (nach Abschluss)

### 3.3 Protokolle

- [x] Abgeschlossene Protokolle einsehen (alle Mitglieder)
- [x] Protokolle als PDF herunterladen

---

## 4. Technische Umsetzung

### 4.1 Neue Datenbanktabellen

```sql
-- Protokolle
protokolle (
    id, titel, inhalt, erstellt_am, erstellt_von,
    status (entwurf/abgeschlossen), abgeschlossen_am
)

-- Abstimmungen
abstimmungen (
    id, titel, beschreibung, ablauf_datum, erstellt_von,
    status (offen/abgeschlossen), geheim (ja/nein)
)

abstimmung_stimmen (
    id, abstimmung_id, benutzer_id,
    stimme (ja/nein/enthaltung), abgegeben_am
)

-- Anträge
antraege (
    id, titel, beschreibung, benutzer_id, erstellt_am,
    status (eingereicht/angenommen/abgelehnt)
)

-- Wahlen
wahlen (
    id, funktion, beschreibung, ablauf_datum, erstellt_von,
    status (offen/abgeschlossen), geheim (ja/nein)
)

wahl_kandidaten (
    id, wahl_id, benutzer_id
)

wahl_stimmen (
    id, wahl_id, benutzer_id, kandidat_id, abgegeben_am
)

-- Buchhaltung-Erweiterung
geschaeftsjahre (
    id, gemeinschaft_id, jahr, von_datum, bis_datum,
    status (offen/abgeschlossen), abgeschlossen_am, abgeschlossen_von
)

jahresuebertraege (
    id, geschaeftsjahr_id, konto_typ, benutzer_id,
    saldo_alt, saldo_neu, erstellt_am
)

kunden_lieferanten (
    id, gemeinschaft_id, name, typ (kunde/lieferant),
    adresse, kontakt, notizen, aktiv
)

anlagen_konten (
    id, gemeinschaft_id, benutzer_id, bezeichnung, einlage_betrag,
    zinssatz, letzte_verzinsung, erstellt_am
)
```

### 4.2 Neue Routen

**Schriftführer:**
- `/admin/protokolle` - Protokollverwaltung
- `/admin/abstimmungen` - Abstimmungsverwaltung
- `/admin/wahlen` - Wahlverwaltung
- `/admin/antraege` - Antragsverwaltung

**Kassier:**
- `/admin/kunden-lieferanten` - Kunden/Lieferanten-Verwaltung
- `/admin/anlagen` - Anlagenkonten-Verwaltung
- `/admin/jahresabschluss` - Jahresabschluss durchführen
- `/admin/geschaeftsjahre` - Übersicht abgeschlossener Jahre

**Benutzer:**
- `/abstimmungen` - Benutzeransicht Abstimmungen
- `/wahlen` - Benutzeransicht Wahlen
- `/protokolle` - Protokolle einsehen
- `/antrag-stellen` - Neuen Antrag einreichen

---

## 5. Entscheidungen

| Frage | Entscheidung |
|-------|--------------|
| Obmann-Rolle? | Ja |
| Protokolle für alle einsehbar? | Ja, alle Mitglieder |
| Geheime/offene Abstimmungen? | Beides möglich, pro Abstimmung wählbar |
| Geheime/offene Wahlen? | Beides möglich, pro Wahl wählbar |
| Geschäftsjahre-Speicherung? | Eine Datenbank mit Geschäftsjahr-Kennzeichnung |

---

## 6. Status

- [x] Planung
- [ ] In Entwicklung
- [ ] Testing
- [ ] Abgeschlossen

---

## 7. Priorisierung (Vorschlag)

1. **Phase 1:** Protokolle (einfachste Funktion)
2. **Phase 2:** Abstimmungen + Anträge
3. **Phase 3:** Wahlen
4. **Phase 4:** Buchhaltungs-Erweiterung (Kunden/Lieferanten, Anlagen)
