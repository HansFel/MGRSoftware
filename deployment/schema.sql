-- Datenbank-Schema für Maschinengemeinschaft
-- SQLite Version
-- Erstellt: Januar 2026

-- Tabelle für Benutzer
CREATE TABLE IF NOT EXISTS benutzer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    vorname TEXT,
    username TEXT UNIQUE,
    password_hash TEXT,
    is_admin BOOLEAN DEFAULT 0,
    admin_level INTEGER DEFAULT 0,
    adresse TEXT,
    telefon TEXT,
    email TEXT,
    mitglied_seit DATE,
    aktiv BOOLEAN DEFAULT 1,
    bemerkungen TEXT,
    treibstoffkosten_preis REAL DEFAULT 1.50,
    backup_schwellwert REAL DEFAULT 10.0,
    nur_training BOOLEAN DEFAULT 0,
    letzter_treibstoffpreis REAL
);

-- Tabelle für Gemeinschaften
CREATE TABLE IF NOT EXISTS gemeinschaften (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    beschreibung TEXT,
    adresse TEXT,
    telefon TEXT,
    email TEXT,
    erstellt_am DATETIME DEFAULT CURRENT_TIMESTAMP,
    aktiv BOOLEAN DEFAULT 1
);

-- Standard-Gemeinschaft
INSERT OR IGNORE INTO gemeinschaften (id, name, beschreibung)
VALUES (1, 'Hauptgemeinschaft', 'Standard-Gemeinschaft');

-- Tabelle für Maschinen
CREATE TABLE IF NOT EXISTS maschinen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bezeichnung TEXT NOT NULL,
    hersteller TEXT,
    modell TEXT,
    baujahr INTEGER,
    kennzeichen TEXT,
    anschaffungsdatum DATE,
    stundenzaehler_aktuell REAL,
    wartungsintervall INTEGER DEFAULT 50,
    naechste_wartung REAL,
    naechste_wartung_bei REAL,
    aktiv BOOLEAN DEFAULT 1,
    anmerkungen TEXT,
    bemerkungen TEXT,
    erfassungsmodus TEXT DEFAULT 'fortlaufend',
    abrechnungsart TEXT DEFAULT 'stunden',
    preis_pro_einheit REAL DEFAULT 0.0,
    gemeinschaft_id INTEGER DEFAULT 1 REFERENCES gemeinschaften(id),
    anschaffungspreis REAL DEFAULT 0.0,
    abschreibungsdauer_jahre INTEGER DEFAULT 10
);

-- Tabelle für Einsatzzwecke
CREATE TABLE IF NOT EXISTS einsatzzwecke (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bezeichnung TEXT NOT NULL UNIQUE,
    beschreibung TEXT,
    aktiv BOOLEAN DEFAULT 1
);

-- Haupttabelle für Maschineneinsätze
CREATE TABLE IF NOT EXISTS maschineneinsaetze (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    datum DATE NOT NULL,
    benutzer_id INTEGER NOT NULL,
    maschine_id INTEGER NOT NULL,
    einsatzzweck_id INTEGER NOT NULL,
    anfangstand REAL NOT NULL,
    endstand REAL NOT NULL,
    betriebsstunden REAL,
    treibstoffverbrauch REAL,
    treibstoffkosten REAL,
    flaeche_menge REAL,
    kosten_berechnet REAL,
    anmerkungen TEXT,
    erstellt_am DATETIME DEFAULT CURRENT_TIMESTAMP,
    geaendert_am DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (benutzer_id) REFERENCES benutzer(id),
    FOREIGN KEY (maschine_id) REFERENCES maschinen(id),
    FOREIGN KEY (einsatzzweck_id) REFERENCES einsatzzwecke(id),
    CHECK (endstand >= anfangstand)
);

-- Indizes für Performance
CREATE INDEX IF NOT EXISTS idx_einsaetze_datum ON maschineneinsaetze(datum);
CREATE INDEX IF NOT EXISTS idx_einsaetze_benutzer ON maschineneinsaetze(benutzer_id);
CREATE INDEX IF NOT EXISTS idx_einsaetze_maschine ON maschineneinsaetze(maschine_id);

-- Beispieldaten für Einsatzzwecke
INSERT OR IGNORE INTO einsatzzwecke (bezeichnung, beschreibung) VALUES
    ('Mähen', 'Wiesen und Felder mähen');
INSERT OR IGNORE INTO einsatzzwecke (bezeichnung, beschreibung) VALUES
    ('Pflügen', 'Feldbearbeitung - Pflügen');
INSERT OR IGNORE INTO einsatzzwecke (bezeichnung, beschreibung) VALUES
    ('Säen', 'Aussaat von Getreide oder Gras');
INSERT OR IGNORE INTO einsatzzwecke (bezeichnung, beschreibung) VALUES
    ('Ernten', 'Ernte von Getreide, Heu, etc.');
INSERT OR IGNORE INTO einsatzzwecke (bezeichnung, beschreibung) VALUES
    ('Transportfahrten', 'Material- und Gütertransport');
INSERT OR IGNORE INTO einsatzzwecke (bezeichnung, beschreibung) VALUES
    ('Schneeräumung', 'Winterdienst und Schneeräumung');
INSERT OR IGNORE INTO einsatzzwecke (bezeichnung, beschreibung) VALUES
    ('Holzarbeiten', 'Holzrücken und Forstarbeiten');
INSERT OR IGNORE INTO einsatzzwecke (bezeichnung, beschreibung) VALUES
    ('Grünlandpflege', 'Weidepflege und Grünlandarbeiten');
INSERT OR IGNORE INTO einsatzzwecke (bezeichnung, beschreibung) VALUES
    ('Wegeinstandhaltung', 'Pflege und Instandhaltung von Wegen');
INSERT OR IGNORE INTO einsatzzwecke (bezeichnung, beschreibung) VALUES
    ('Sonstiges', 'Andere Einsätze');

-- Zuordnungstabelle: Mitglieder <-> Gemeinschaften (N:M)
CREATE TABLE IF NOT EXISTS mitglied_gemeinschaft (
    mitglied_id INTEGER NOT NULL,
    gemeinschaft_id INTEGER NOT NULL,
    beigetreten_am DATETIME DEFAULT CURRENT_TIMESTAMP,
    rolle TEXT DEFAULT 'mitglied',
    PRIMARY KEY (mitglied_id, gemeinschaft_id),
    FOREIGN KEY (mitglied_id) REFERENCES benutzer(id) ON DELETE CASCADE,
    FOREIGN KEY (gemeinschaft_id) REFERENCES gemeinschaften(id) ON DELETE CASCADE
);

-- Indizes
CREATE INDEX IF NOT EXISTS idx_maschinen_gemeinschaft ON maschinen(gemeinschaft_id);
CREATE INDEX IF NOT EXISTS idx_mitglied_gemeinschaft_mitglied ON mitglied_gemeinschaft(mitglied_id);
CREATE INDEX IF NOT EXISTS idx_mitglied_gemeinschaft_gemeinschaft ON mitglied_gemeinschaft(gemeinschaft_id);

-- Tabelle für Gemeinschafts-Administratoren
CREATE TABLE IF NOT EXISTS gemeinschafts_admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    benutzer_id INTEGER NOT NULL,
    gemeinschaft_id INTEGER NOT NULL,
    erstellt_am DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(benutzer_id, gemeinschaft_id),
    FOREIGN KEY (benutzer_id) REFERENCES benutzer(id) ON DELETE CASCADE,
    FOREIGN KEY (gemeinschaft_id) REFERENCES gemeinschaften(id) ON DELETE CASCADE
);

-- Tabelle für Backup-Bestätigungen
CREATE TABLE IF NOT EXISTS backup_bestaetigung (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id INTEGER NOT NULL,
    zeitpunkt DATETIME NOT NULL,
    bemerkung TEXT,
    status TEXT DEFAULT 'wartend',
    FOREIGN KEY (admin_id) REFERENCES benutzer(id) ON DELETE CASCADE
);

-- Backup-Tracking
CREATE TABLE IF NOT EXISTS backup_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    letztes_backup DATETIME,
    einsaetze_bei_backup INTEGER,
    bemerkung TEXT,
    durchgefuehrt_von INTEGER REFERENCES benutzer(id)
);

-- Tabelle für stornierte Einsätze
CREATE TABLE IF NOT EXISTS maschineneinsaetze_storniert (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_id INTEGER NOT NULL,
    datum DATE NOT NULL,
    benutzer_id INTEGER NOT NULL,
    maschine_id INTEGER NOT NULL,
    einsatzzweck_id INTEGER NOT NULL,
    anfangstand REAL NOT NULL,
    endstand REAL NOT NULL,
    betriebsstunden REAL,
    treibstoffverbrauch REAL,
    treibstoffkosten REAL,
    flaeche_menge REAL,
    kosten_berechnet REAL,
    anmerkungen TEXT,
    erstellt_am DATETIME,
    storniert_am DATETIME DEFAULT CURRENT_TIMESTAMP,
    storniert_von INTEGER REFERENCES benutzer(id),
    storno_grund TEXT
);

-- Tabelle für Gemeinschafts-Nachrichten
CREATE TABLE IF NOT EXISTS gemeinschafts_nachrichten (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gemeinschaft_id INTEGER NOT NULL REFERENCES gemeinschaften(id) ON DELETE CASCADE,
    absender_id INTEGER NOT NULL REFERENCES benutzer(id),
    betreff TEXT NOT NULL,
    inhalt TEXT NOT NULL,
    prioritaet TEXT DEFAULT 'normal',
    erstellt_am DATETIME DEFAULT CURRENT_TIMESTAMP,
    gueltig_bis DATE
);

CREATE INDEX IF NOT EXISTS idx_nachrichten_gemeinschaft ON gemeinschafts_nachrichten(gemeinschaft_id);
CREATE INDEX IF NOT EXISTS idx_nachrichten_absender ON gemeinschafts_nachrichten(absender_id);

-- Tabelle für gelesene Nachrichten
CREATE TABLE IF NOT EXISTS nachricht_gelesen (
    nachricht_id INTEGER NOT NULL REFERENCES gemeinschafts_nachrichten(id) ON DELETE CASCADE,
    benutzer_id INTEGER NOT NULL REFERENCES benutzer(id) ON DELETE CASCADE,
    gelesen_am DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (nachricht_id, benutzer_id)
);

-- Tabelle für Maschinen-Reservierungen
CREATE TABLE IF NOT EXISTS maschinen_reservierungen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    maschine_id INTEGER NOT NULL REFERENCES maschinen(id),
    benutzer_id INTEGER NOT NULL REFERENCES benutzer(id),
    datum DATE NOT NULL,
    ganztags BOOLEAN DEFAULT 1,
    von_zeit TEXT,
    bis_zeit TEXT,
    uhrzeit_von TEXT,
    uhrzeit_bis TEXT,
    zweck TEXT,
    status TEXT DEFAULT 'aktiv',
    erstellt_am DATETIME DEFAULT CURRENT_TIMESTAMP,
    storniert BOOLEAN DEFAULT 0,
    storniert_am DATETIME,
    UNIQUE(maschine_id, datum, benutzer_id)
);

CREATE INDEX IF NOT EXISTS idx_reservierungen_maschine ON maschinen_reservierungen(maschine_id);
CREATE INDEX IF NOT EXISTS idx_reservierungen_benutzer ON maschinen_reservierungen(benutzer_id);
CREATE INDEX IF NOT EXISTS idx_reservierungen_datum ON maschinen_reservierungen(datum);

-- Tabelle für Maschinen-Aufwendungen
CREATE TABLE IF NOT EXISTS maschinen_aufwendungen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    maschine_id INTEGER NOT NULL REFERENCES maschinen(id),
    datum DATE NOT NULL,
    art TEXT NOT NULL,
    beschreibung TEXT,
    betrag REAL NOT NULL,
    beleg_nr TEXT,
    erstellt_am DATETIME DEFAULT CURRENT_TIMESTAMP,
    erstellt_von INTEGER REFERENCES benutzer(id)
);

CREATE INDEX IF NOT EXISTS idx_aufwendungen_maschine ON maschinen_aufwendungen(maschine_id);
CREATE INDEX IF NOT EXISTS idx_aufwendungen_datum ON maschinen_aufwendungen(datum);

-- Tabelle für Bank-Transaktionen
CREATE TABLE IF NOT EXISTS bank_transaktionen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    buchungsdatum DATE NOT NULL,
    valutadatum DATE,
    betrag REAL NOT NULL,
    waehrung TEXT DEFAULT 'EUR',
    verwendungszweck TEXT,
    auftraggeber TEXT,
    iban TEXT,
    bic TEXT,
    importiert_am DATETIME DEFAULT CURRENT_TIMESTAMP,
    importiert_von INTEGER REFERENCES benutzer(id),
    zugeordnet BOOLEAN DEFAULT 0,
    zugeordnet_zu_mitglied INTEGER REFERENCES benutzer(id),
    zugeordnet_am DATETIME,
    import_hash TEXT UNIQUE
);

CREATE INDEX IF NOT EXISTS idx_bank_trans_datum ON bank_transaktionen(buchungsdatum);
CREATE INDEX IF NOT EXISTS idx_bank_trans_zugeordnet ON bank_transaktionen(zugeordnet);

-- Tabelle für Mitglieder-Konten
CREATE TABLE IF NOT EXISTS mitglieder_konten (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    benutzer_id INTEGER NOT NULL REFERENCES benutzer(id),
    gemeinschaft_id INTEGER NOT NULL REFERENCES gemeinschaften(id),
    kontostand REAL DEFAULT 0.0,
    letzte_aktualisierung DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(benutzer_id, gemeinschaft_id)
);

-- Tabelle für Buchungen
CREATE TABLE IF NOT EXISTS buchungen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    konto_id INTEGER NOT NULL REFERENCES mitglieder_konten(id),
    datum DATE NOT NULL,
    betrag REAL NOT NULL,
    buchungsart TEXT NOT NULL,
    referenz_typ TEXT,
    referenz_id INTEGER,
    beschreibung TEXT,
    erstellt_am DATETIME DEFAULT CURRENT_TIMESTAMP,
    erstellt_von INTEGER REFERENCES benutzer(id)
);

CREATE INDEX IF NOT EXISTS idx_buchungen_konto ON buchungen(konto_id);
CREATE INDEX IF NOT EXISTS idx_buchungen_datum ON buchungen(datum);

-- Tabelle für Mitglieder-Abrechnungen
CREATE TABLE IF NOT EXISTS mitglieder_abrechnungen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    benutzer_id INTEGER NOT NULL REFERENCES benutzer(id),
    gemeinschaft_id INTEGER NOT NULL REFERENCES gemeinschaften(id),
    zeitraum_von DATE NOT NULL,
    zeitraum_bis DATE NOT NULL,
    betrag_maschinen REAL DEFAULT 0.0,
    betrag_treibstoff REAL DEFAULT 0.0,
    status TEXT DEFAULT 'offen',
    erstellt_am DATETIME DEFAULT CURRENT_TIMESTAMP,
    bezahlt_am DATETIME
);

-- Tabelle für Zahlungs-Zuordnungen
CREATE TABLE IF NOT EXISTS zahlungs_zuordnungen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaktion_id INTEGER NOT NULL REFERENCES bank_transaktionen(id),
    benutzer_id INTEGER NOT NULL REFERENCES benutzer(id),
    zugeordnet_am DATETIME DEFAULT CURRENT_TIMESTAMP,
    zugeordnet_von INTEGER REFERENCES benutzer(id)
);

-- Tabelle für Zahlungsreferenzen
CREATE TABLE IF NOT EXISTS zahlungsreferenzen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    benutzer_id INTEGER NOT NULL REFERENCES benutzer(id),
    gemeinschaft_id INTEGER REFERENCES gemeinschaften(id),
    referenz TEXT NOT NULL,
    aktiv BOOLEAN DEFAULT 1,
    erstellt_am DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(benutzer_id, referenz)
);

-- Tabelle für CSV-Import-Konfiguration
CREATE TABLE IF NOT EXISTS csv_import_konfiguration (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    bank_name TEXT,
    datum_spalte INTEGER,
    betrag_spalte INTEGER,
    verwendungszweck_spalte INTEGER,
    auftraggeber_spalte INTEGER,
    iban_spalte INTEGER,
    header_zeilen INTEGER DEFAULT 1,
    trennzeichen TEXT DEFAULT ';',
    dezimaltrennzeichen TEXT DEFAULT ',',
    datumsformat TEXT DEFAULT '%d.%m.%Y',
    encoding TEXT DEFAULT 'utf-8',
    erstellt_am DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabelle für Gemeinschafts-Kosten
CREATE TABLE IF NOT EXISTS gemeinschafts_kosten (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gemeinschaft_id INTEGER NOT NULL REFERENCES gemeinschaften(id),
    bezeichnung TEXT NOT NULL,
    betrag REAL NOT NULL,
    datum DATE NOT NULL,
    kategorie TEXT,
    beschreibung TEXT,
    erstellt_am DATETIME DEFAULT CURRENT_TIMESTAMP,
    erstellt_von INTEGER REFERENCES benutzer(id)
);

-- Tabelle für Jahresabschlüsse
CREATE TABLE IF NOT EXISTS jahresabschluesse (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gemeinschaft_id INTEGER NOT NULL REFERENCES gemeinschaften(id),
    jahr INTEGER NOT NULL,
    abgeschlossen_am DATETIME DEFAULT CURRENT_TIMESTAMP,
    abgeschlossen_von INTEGER REFERENCES benutzer(id),
    gesamteinnahmen REAL,
    gesamtausgaben REAL,
    bemerkung TEXT,
    UNIQUE(gemeinschaft_id, jahr)
);

-- Standard-Admin-Benutzer
-- Login: admin / admin123
INSERT OR IGNORE INTO benutzer (id, name, vorname, username, password_hash, is_admin, admin_level, aktiv)
VALUES (1, 'Admin', 'System', 'admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 1, 2, 1);

-- Views für SQLite (vereinfacht)
CREATE VIEW IF NOT EXISTS einsaetze_uebersicht AS
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
ORDER BY e.datum DESC;

CREATE VIEW IF NOT EXISTS gemeinschaften_uebersicht AS
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
GROUP BY g.id, g.name, g.beschreibung, g.aktiv;
