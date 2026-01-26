CREATE TABLE backup_bestaetigung (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER NOT NULL,
            zeitpunkt TEXT NOT NULL,
            bemerkung TEXT,
            status TEXT DEFAULT 'wartend',
            FOREIGN KEY (admin_id) REFERENCES benutzer(id)
        )

CREATE TABLE backup_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            letztes_backup TEXT NOT NULL,
            einsaetze_bei_backup INTEGER DEFAULT 0,
            durchgefuehrt_von INTEGER,
            bemerkung TEXT,
            FOREIGN KEY (durchgefuehrt_von) REFERENCES benutzer(id)
        )

CREATE TABLE bank_transaktionen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gemeinschaft_id INTEGER NOT NULL,
                buchungsdatum DATE NOT NULL,
                valutadatum DATE,
                verwendungszweck TEXT,
                empfaenger TEXT,
                kontonummer TEXT,
                bic TEXT,
                betrag REAL NOT NULL,
                waehrung TEXT DEFAULT 'EUR',
                transaktions_hash TEXT UNIQUE NOT NULL,
                benutzer_id INTEGER,
                zugeordnet BOOLEAN DEFAULT 0,
                importiert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                importiert_von INTEGER,
                bemerkung TEXT, zuordnung_typ TEXT DEFAULT NULL, zuordnung_id INTEGER DEFAULT NULL,
                FOREIGN KEY (gemeinschaft_id) REFERENCES gemeinschaften(id),
                FOREIGN KEY (benutzer_id) REFERENCES benutzer(id),
                FOREIGN KEY (importiert_von) REFERENCES benutzer(id)
            )

CREATE TABLE benutzer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    vorname TEXT,
    username TEXT UNIQUE,
    password_hash TEXT,
    adresse TEXT,
    telefon TEXT,
    email TEXT,
    mitglied_seit DATE,
    aktiv BOOLEAN DEFAULT 1,
    bemerkungen TEXT
, is_admin BOOLEAN DEFAULT 0, treibstoffkosten_preis REAL DEFAULT 1.50, backup_schwellwert INTEGER DEFAULT 50, letzter_treibstoffpreis REAL, admin_level INTEGER DEFAULT 0, nur_training BOOLEAN DEFAULT 0)

CREATE TABLE buchungen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                benutzer_id INTEGER NOT NULL,
                gemeinschaft_id INTEGER NOT NULL,
                datum DATE NOT NULL,
                betrag REAL NOT NULL,
                typ TEXT NOT NULL CHECK(typ IN (
                    'abrechnung',      -- Automatisch aus Abrechnungserstellung
                    'einzahlung',      -- Zahlung des Mitglieds
                    'auszahlung',      -- Auszahlung an Mitglied (z.B. Rückerstattung)
                    'korrektur',       -- Manuelle Korrektur durch Admin
                    'jahresuebertrag'  -- Übertrag Vorjahressaldo
                )),
                beschreibung TEXT,
                referenz_typ TEXT,     -- 'abrechnung', 'manually', etc.
                referenz_id INTEGER,   -- ID der Abrechnung oder NULL
                erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                erstellt_von INTEGER NOT NULL, -- Admin der die Buchung erstellt hat
                
                FOREIGN KEY (benutzer_id) REFERENCES benutzer(id),
                FOREIGN KEY (gemeinschaft_id) REFERENCES gemeinschaften(id),
                FOREIGN KEY (erstellt_von) REFERENCES benutzer(id)
            )

CREATE TABLE csv_import_konfiguration (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gemeinschaft_id INTEGER NOT NULL UNIQUE,
                trennzeichen TEXT DEFAULT ';',
                kodierung TEXT DEFAULT 'utf-8-sig',
                spalte_buchungsdatum TEXT DEFAULT 'Buchungstag',
                spalte_valutadatum TEXT DEFAULT 'Valutadatum',
                spalte_betrag TEXT DEFAULT 'Betrag',
                spalte_verwendungszweck TEXT DEFAULT 'Verwendungszweck',
                spalte_empfaenger TEXT DEFAULT 'Beguenstigter/Zahlungspflichtiger',
                spalte_kontonummer TEXT DEFAULT 'Kontonummer',
                spalte_bic TEXT DEFAULT 'BIC',
                dezimaltrennzeichen TEXT DEFAULT ',',
                tausendertrennzeichen TEXT DEFAULT '.',
                datumsformat TEXT DEFAULT '%d.%m.%Y',
                hat_kopfzeile BOOLEAN DEFAULT 1,
                zeilen_ueberspringen INTEGER DEFAULT 0,
                erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                geaendert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (gemeinschaft_id) REFERENCES gemeinschaften(id) ON DELETE CASCADE
            )

CREATE TABLE einsatzzwecke (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bezeichnung TEXT NOT NULL UNIQUE,
    beschreibung TEXT,
    aktiv BOOLEAN DEFAULT 1
)

CREATE TABLE gemeinschaften (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                beschreibung TEXT,
                erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                aktiv BOOLEAN DEFAULT 1
            , anfangssaldo_bank REAL DEFAULT 0.0, anfangssaldo_datum DATE DEFAULT NULL, bank_name TEXT, bank_iban TEXT, bank_bic TEXT, bank_kontoinhaber TEXT)

CREATE TABLE gemeinschafts_admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            benutzer_id INTEGER NOT NULL,
            gemeinschaft_id INTEGER NOT NULL,
            erstellt_am TEXT NOT NULL,
            UNIQUE(benutzer_id, gemeinschaft_id),
            FOREIGN KEY (benutzer_id) REFERENCES benutzer(id),
            FOREIGN KEY (gemeinschaft_id) REFERENCES gemeinschaften(id)
        )

CREATE TABLE gemeinschafts_kosten (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gemeinschaft_id INTEGER NOT NULL,
                transaktion_id INTEGER,
                maschine_id INTEGER,
                kategorie TEXT DEFAULT 'sonstiges',
                betrag REAL NOT NULL,
                datum DATE NOT NULL,
                beschreibung TEXT,
                bemerkung TEXT,
                erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                erstellt_von INTEGER,
                FOREIGN KEY (gemeinschaft_id) REFERENCES gemeinschaften(id),
                FOREIGN KEY (transaktion_id) REFERENCES bank_transaktionen(id) ON DELETE SET NULL,
                FOREIGN KEY (maschine_id) REFERENCES maschinen(id) ON DELETE SET NULL,
                FOREIGN KEY (erstellt_von) REFERENCES benutzer(id)
            )

CREATE TABLE gemeinschafts_nachrichten (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gemeinschaft_id INTEGER NOT NULL,
            absender_id INTEGER NOT NULL,
            betreff TEXT NOT NULL,
            nachricht TEXT NOT NULL,
            erstellt_am TEXT NOT NULL,
            FOREIGN KEY (gemeinschaft_id) REFERENCES gemeinschaften(id),
            FOREIGN KEY (absender_id) REFERENCES benutzer(id)
        )

CREATE TABLE jahresabschluesse (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gemeinschaft_id INTEGER NOT NULL,
                jahr INTEGER NOT NULL,
                abschluss_datum DATE NOT NULL,
                erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                erstellt_von INTEGER NOT NULL,
                bemerkung TEXT,
                
                UNIQUE(gemeinschaft_id, jahr),
                FOREIGN KEY (gemeinschaft_id) REFERENCES gemeinschaften(id),
                FOREIGN KEY (erstellt_von) REFERENCES benutzer(id)
            )

CREATE TABLE maschinen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bezeichnung TEXT NOT NULL,
    hersteller TEXT,
    modell TEXT,
    baujahr INTEGER,
    kennzeichen TEXT,
    anschaffungsdatum DATE,
    stundenzaehler_aktuell REAL,
    naechste_wartung_bei REAL,
    aktiv BOOLEAN DEFAULT 1,
    bemerkungen TEXT
, abrechnungsart TEXT DEFAULT 'stunden', preis_pro_einheit REAL DEFAULT 0.0, wartungsintervall INTEGER DEFAULT 50, naechste_wartung REAL, anmerkungen TEXT, erfassungsmodus TEXT DEFAULT 'fortlaufend', gemeinschaft_id INTEGER DEFAULT 1 REFERENCES gemeinschaften(id), anschaffungspreis REAL DEFAULT 0.0, abschreibungsdauer_jahre INTEGER DEFAULT 10, treibstoff_berechnen BOOLEAN DEFAULT 0)

CREATE TABLE maschinen_aufwendungen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                maschine_id INTEGER NOT NULL,
                jahr INTEGER NOT NULL,
                wartungskosten REAL DEFAULT 0.0,
                reparaturkosten REAL DEFAULT 0.0,
                versicherung REAL DEFAULT 0.0,
                steuern REAL DEFAULT 0.0,
                sonstige_kosten REAL DEFAULT 0.0,
                bemerkung TEXT,
                erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                geaendert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (maschine_id) REFERENCES maschinen(id) ON DELETE CASCADE,
                UNIQUE(maschine_id, jahr)
            )

CREATE TABLE maschinen_reservierungen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                maschine_id INTEGER NOT NULL,
                benutzer_id INTEGER NOT NULL,
                datum DATE NOT NULL,
                uhrzeit_von TIME NOT NULL,
                uhrzeit_bis TIME NOT NULL,
                nutzungsdauer_stunden REAL NOT NULL,
                zweck TEXT,
                bemerkung TEXT,
                status TEXT DEFAULT 'aktiv',
                erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                geaendert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (maschine_id) REFERENCES maschinen(id) ON DELETE CASCADE,
                FOREIGN KEY (benutzer_id) REFERENCES benutzer(id) ON DELETE CASCADE
            )

CREATE TABLE maschineneinsaetze (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    datum DATE NOT NULL,
    benutzer_id INTEGER NOT NULL,
    maschine_id INTEGER NOT NULL,
    einsatzzweck_id INTEGER NOT NULL,
    anfangstand REAL NOT NULL,
    endstand REAL NOT NULL,
    betriebsstunden REAL GENERATED ALWAYS AS (endstand - anfangstand) STORED,
    treibstoffverbrauch REAL,
    treibstoffkosten REAL,
    anmerkungen TEXT,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    geaendert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP, flaeche_menge REAL, kosten_berechnet REAL,
    FOREIGN KEY (benutzer_id) REFERENCES benutzer(id),
    FOREIGN KEY (maschine_id) REFERENCES maschinen(id),
    FOREIGN KEY (einsatzzweck_id) REFERENCES einsatzzwecke(id),
    CHECK (endstand >= anfangstand)
)

CREATE TABLE maschineneinsaetze_storniert (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_einsatz_id INTEGER NOT NULL,
            datum TEXT NOT NULL,
            benutzer_id INTEGER NOT NULL,
            maschine_id INTEGER NOT NULL,
            einsatzzweck_id INTEGER,
            stundenzaehler_anfang REAL,
            stundenzaehler_ende REAL,
            betriebsstunden REAL,
            hektar REAL,
            kilometer REAL,
            stueck INTEGER,
            treibstoffverbrauch REAL,
            treibstoffkosten REAL,
            maschinenkosten REAL,
            gesamtkosten REAL,
            bemerkung TEXT,
            storniert_am TEXT NOT NULL,
            storniert_von INTEGER NOT NULL,
            stornierungsgrund TEXT,
            FOREIGN KEY (benutzer_id) REFERENCES benutzer(id),
            FOREIGN KEY (maschine_id) REFERENCES maschinen(id),
            FOREIGN KEY (einsatzzweck_id) REFERENCES einsatzzwecke(id),
            FOREIGN KEY (storniert_von) REFERENCES benutzer(id)
        )

CREATE TABLE mitglied_gemeinschaft (
                mitglied_id INTEGER NOT NULL,
                gemeinschaft_id INTEGER NOT NULL,
                beigetreten_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                rolle TEXT DEFAULT 'mitglied',
                PRIMARY KEY (mitglied_id, gemeinschaft_id),
                FOREIGN KEY (mitglied_id) REFERENCES benutzer(id) ON DELETE CASCADE,
                FOREIGN KEY (gemeinschaft_id) REFERENCES gemeinschaften(id) ON DELETE CASCADE
            )

CREATE TABLE mitglieder_abrechnungen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gemeinschaft_id INTEGER NOT NULL,
                benutzer_id INTEGER NOT NULL,
                abrechnungszeitraum TEXT NOT NULL,
                zeitraum_von DATE NOT NULL,
                zeitraum_bis DATE NOT NULL,
                betrag_gesamt REAL NOT NULL,
                betrag_treibstoff REAL DEFAULT 0,
                betrag_maschinen REAL DEFAULT 0,
                betrag_sonstiges REAL DEFAULT 0,
                status TEXT DEFAULT 'offen',
                erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                erstellt_von INTEGER,
                bezahlt_am TIMESTAMP,
                bemerkung TEXT,
                FOREIGN KEY (gemeinschaft_id) REFERENCES gemeinschaften(id),
                FOREIGN KEY (benutzer_id) REFERENCES benutzer(id),
                FOREIGN KEY (erstellt_von) REFERENCES benutzer(id)
            )

CREATE TABLE mitglieder_konten (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                benutzer_id INTEGER NOT NULL,
                gemeinschaft_id INTEGER NOT NULL,
                saldo REAL DEFAULT 0,           -- Aktueller Kontostand
                saldo_vorjahr REAL DEFAULT 0,   -- Saldo vom Jahresabschluss
                letzte_aktualisierung TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(benutzer_id, gemeinschaft_id),
                FOREIGN KEY (benutzer_id) REFERENCES benutzer(id),
                FOREIGN KEY (gemeinschaft_id) REFERENCES gemeinschaften(id)
            )

CREATE TABLE nachricht_gelesen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nachricht_id INTEGER NOT NULL,
            benutzer_id INTEGER NOT NULL,
            gelesen_am TEXT NOT NULL,
            UNIQUE(nachricht_id, benutzer_id),
            FOREIGN KEY (nachricht_id) REFERENCES gemeinschafts_nachrichten(id),
            FOREIGN KEY (benutzer_id) REFERENCES benutzer(id)
        )

CREATE TABLE reservierungen_abgelaufen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reservierung_id INTEGER,
                maschine_id INTEGER NOT NULL,
                maschine_bezeichnung TEXT,
                benutzer_id INTEGER NOT NULL,
                benutzer_name TEXT,
                datum DATE NOT NULL,
                uhrzeit_von TIME NOT NULL,
                uhrzeit_bis TIME NOT NULL,
                nutzungsdauer_stunden REAL NOT NULL,
                zweck TEXT,
                bemerkung TEXT,
                erstellt_am TIMESTAMP,
                abgelaufen_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )

CREATE TABLE reservierungen_geloescht (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reservierung_id INTEGER,
                maschine_id INTEGER NOT NULL,
                maschine_bezeichnung TEXT,
                benutzer_id INTEGER NOT NULL,
                benutzer_name TEXT,
                datum DATE NOT NULL,
                uhrzeit_von TIME NOT NULL,
                uhrzeit_bis TIME NOT NULL,
                nutzungsdauer_stunden REAL NOT NULL,
                zweck TEXT,
                bemerkung TEXT,
                erstellt_am TIMESTAMP,
                geloescht_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                geloescht_von INTEGER,
                grund TEXT
            )

CREATE TABLE sqlite_sequence(name,seq)

CREATE TABLE zahlungs_zuordnungen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaktion_id INTEGER NOT NULL,
                abrechnung_id INTEGER NOT NULL,
                betrag REAL NOT NULL,
                zugeordnet_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                zugeordnet_von INTEGER,
                FOREIGN KEY (transaktion_id) REFERENCES bank_transaktionen(id) ON DELETE CASCADE,
                FOREIGN KEY (abrechnung_id) REFERENCES mitglieder_abrechnungen(id) ON DELETE CASCADE,
                FOREIGN KEY (zugeordnet_von) REFERENCES benutzer(id)
            )

CREATE TABLE zahlungsreferenzen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                benutzer_id INTEGER NOT NULL,
                gemeinschaft_id INTEGER NOT NULL,
                referenznummer TEXT UNIQUE NOT NULL,
                erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                aktiv BOOLEAN DEFAULT 1,
                FOREIGN KEY (benutzer_id) REFERENCES benutzer(id) ON DELETE CASCADE,
                FOREIGN KEY (gemeinschaft_id) REFERENCES gemeinschaften(id) ON DELETE CASCADE,
                UNIQUE(benutzer_id, gemeinschaft_id)
            )

CREATE VIEW einsaetze_uebersicht AS
            SELECT 
                e.id,
                e.datum,
                b.name || ', ' || COALESCE(b.vorname, '') AS benutzer,
                m.bezeichnung AS maschine,
                m.abrechnungsart AS abrechnungsart,
                m.preis_pro_einheit AS preis_pro_einheit,
                ez.bezeichnung AS einsatzzweck,
                e.anfangstand,
                e.endstand,
                e.betriebsstunden,
                e.treibstoffverbrauch,
                e.treibstoffkosten,
                e.flaeche_menge,
                e.kosten_berechnet,
                e.anmerkungen
            FROM maschineneinsaetze e
            JOIN benutzer b ON e.benutzer_id = b.id
            JOIN maschinen m ON e.maschine_id = m.id
            JOIN einsatzzwecke ez ON e.einsatzzweck_id = ez.id
            ORDER BY e.datum DESC

CREATE VIEW gemeinschaften_uebersicht AS
            SELECT 
                g.id,
                g.name,
                g.beschreibung,
                g.aktiv,
                COUNT(DISTINCT m.id) as anzahl_maschinen,
                COUNT(DISTINCT mg.mitglied_id) as anzahl_mitglieder
            FROM gemeinschaften g
            LEFT JOIN maschinen m ON g.id = m.gemeinschaft_id AND m.aktiv = 1
            LEFT JOIN mitglied_gemeinschaft mg ON g.id = mg.gemeinschaft_id
            GROUP BY g.id, g.name, g.beschreibung, g.aktiv

