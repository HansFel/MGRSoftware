-- Datenbank-Schema für Maschinengemeinschaft
-- PostgreSQL Version
-- Erstellt: Januar 2026

-- Tabelle für Benutzer
CREATE TABLE IF NOT EXISTS benutzer (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    vorname TEXT,
    username TEXT UNIQUE,
    password_hash TEXT,
    is_admin BOOLEAN DEFAULT FALSE,
    admin_level INTEGER DEFAULT 0,
    adresse TEXT,
    telefon TEXT,
    email TEXT,
    mitglied_seit DATE,
    aktiv BOOLEAN DEFAULT TRUE,
    bemerkungen TEXT,
    treibstoffkosten_preis REAL DEFAULT 1.50,
    backup_schwellwert REAL DEFAULT 10.0,
    nur_training BOOLEAN DEFAULT FALSE
);

-- Tabelle für Gemeinschaften (muss vor maschinen erstellt werden wegen FK)
CREATE TABLE IF NOT EXISTS gemeinschaften (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    beschreibung TEXT,
    adresse TEXT,
    telefon TEXT,
    email TEXT,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    aktiv BOOLEAN DEFAULT TRUE
);

-- Standard-Gemeinschaft
INSERT INTO gemeinschaften (id, name, beschreibung)
VALUES (1, 'Hauptgemeinschaft', 'Standard-Gemeinschaft')
ON CONFLICT (id) DO NOTHING;

-- Sequenz für gemeinschaften anpassen
SELECT setval('gemeinschaften_id_seq', (SELECT MAX(id) FROM gemeinschaften));

-- Tabelle für Maschinen
CREATE TABLE IF NOT EXISTS maschinen (
    id SERIAL PRIMARY KEY,
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
    aktiv BOOLEAN DEFAULT TRUE,
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
    id SERIAL PRIMARY KEY,
    bezeichnung TEXT NOT NULL UNIQUE,
    beschreibung TEXT,
    aktiv BOOLEAN DEFAULT TRUE
);

-- Haupttabelle für Maschineneinsätze
CREATE TABLE IF NOT EXISTS maschineneinsaetze (
    id SERIAL PRIMARY KEY,
    datum DATE NOT NULL,
    benutzer_id INTEGER NOT NULL,
    maschine_id INTEGER NOT NULL,
    einsatzzweck_id INTEGER NOT NULL,
    anfangstand REAL NOT NULL,
    endstand REAL NOT NULL,
    betriebsstunden REAL GENERATED ALWAYS AS (endstand - anfangstand) STORED,
    treibstoffverbrauch REAL,
    treibstoffkosten REAL,
    flaeche_menge REAL,
    kosten_berechnet REAL,
    anmerkungen TEXT,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    geaendert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (benutzer_id) REFERENCES benutzer(id),
    FOREIGN KEY (maschine_id) REFERENCES maschinen(id),
    FOREIGN KEY (einsatzzweck_id) REFERENCES einsatzzwecke(id),
    CHECK (endstand >= anfangstand)
);

-- Index für bessere Performance
CREATE INDEX IF NOT EXISTS idx_einsaetze_datum ON maschineneinsaetze(datum);
CREATE INDEX IF NOT EXISTS idx_einsaetze_benutzer ON maschineneinsaetze(benutzer_id);
CREATE INDEX IF NOT EXISTS idx_einsaetze_maschine ON maschineneinsaetze(maschine_id);

-- Trigger-Funktion zum Aktualisieren des Änderungsdatums
CREATE OR REPLACE FUNCTION update_geaendert_am()
RETURNS TRIGGER AS $$
BEGIN
    NEW.geaendert_am = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger zum Aktualisieren des Änderungsdatums
DROP TRIGGER IF EXISTS update_maschineneinsaetze_timestamp ON maschineneinsaetze;
CREATE TRIGGER update_maschineneinsaetze_timestamp
    BEFORE UPDATE ON maschineneinsaetze
    FOR EACH ROW
    EXECUTE FUNCTION update_geaendert_am();

-- View für übersichtliche Ausgabe aller Einsätze
CREATE OR REPLACE VIEW einsaetze_uebersicht AS
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

-- Beispieldaten für Einsatzzwecke
INSERT INTO einsatzzwecke (bezeichnung, beschreibung) VALUES
    ('Mähen', 'Wiesen und Felder mähen'),
    ('Pflügen', 'Feldbearbeitung - Pflügen'),
    ('Säen', 'Aussaat von Getreide oder Gras'),
    ('Ernten', 'Ernte von Getreide, Heu, etc.'),
    ('Transportfahrten', 'Material- und Gütertransport'),
    ('Schneeräumung', 'Winterdienst und Schneeräumung'),
    ('Holzarbeiten', 'Holzrücken und Forstarbeiten'),
    ('Grünlandpflege', 'Weidepflege und Grünlandarbeiten'),
    ('Wegeinstandhaltung', 'Pflege und Instandhaltung von Wegen'),
    ('Sonstiges', 'Andere Einsätze')
ON CONFLICT (bezeichnung) DO NOTHING;

-- Zuordnungstabelle: Mitglieder <-> Gemeinschaften (N:M)
CREATE TABLE IF NOT EXISTS mitglied_gemeinschaft (
    mitglied_id INTEGER NOT NULL,
    gemeinschaft_id INTEGER NOT NULL,
    beigetreten_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rolle TEXT DEFAULT 'mitglied',
    PRIMARY KEY (mitglied_id, gemeinschaft_id),
    FOREIGN KEY (mitglied_id) REFERENCES benutzer(id) ON DELETE CASCADE,
    FOREIGN KEY (gemeinschaft_id) REFERENCES gemeinschaften(id) ON DELETE CASCADE
);

-- Indizes für Performance
CREATE INDEX IF NOT EXISTS idx_maschinen_gemeinschaft ON maschinen(gemeinschaft_id);
CREATE INDEX IF NOT EXISTS idx_mitglied_gemeinschaft_mitglied ON mitglied_gemeinschaft(mitglied_id);
CREATE INDEX IF NOT EXISTS idx_mitglied_gemeinschaft_gemeinschaft ON mitglied_gemeinschaft(gemeinschaft_id);

-- View für Gemeinschafts-Übersicht
CREATE OR REPLACE VIEW gemeinschaften_uebersicht AS
SELECT
    g.id,
    g.name,
    g.beschreibung,
    g.aktiv,
    COUNT(DISTINCT m.id) as anzahl_maschinen,
    COUNT(DISTINCT bg.betrieb_id) as anzahl_mitglieder
FROM gemeinschaften g
LEFT JOIN maschinen m ON g.id = m.gemeinschaft_id AND m.aktiv = TRUE
LEFT JOIN betriebe_gemeinschaften bg ON g.id = bg.gemeinschaft_id
GROUP BY g.id, g.name, g.beschreibung, g.aktiv;

-- Tabelle für Gemeinschafts-Administratoren
CREATE TABLE IF NOT EXISTS gemeinschafts_admin (
    id SERIAL PRIMARY KEY,
    benutzer_id INTEGER NOT NULL,
    gemeinschaft_id INTEGER NOT NULL,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(benutzer_id, gemeinschaft_id),
    FOREIGN KEY (benutzer_id) REFERENCES benutzer(id) ON DELETE CASCADE,
    FOREIGN KEY (gemeinschaft_id) REFERENCES gemeinschaften(id) ON DELETE CASCADE
);

-- Tabelle für Backup-Bestätigungen
CREATE TABLE IF NOT EXISTS backup_bestaetigung (
    id SERIAL PRIMARY KEY,
    admin_id INTEGER NOT NULL,
    zeitpunkt TIMESTAMP NOT NULL,
    bemerkung TEXT,
    status TEXT DEFAULT 'wartend',
    FOREIGN KEY (admin_id) REFERENCES benutzer(id) ON DELETE CASCADE
);

-- Indizes für Performance
CREATE INDEX IF NOT EXISTS idx_gemeinschafts_admin_benutzer
    ON gemeinschafts_admin(benutzer_id);

CREATE INDEX IF NOT EXISTS idx_gemeinschafts_admin_gemeinschaft
    ON gemeinschafts_admin(gemeinschaft_id);

CREATE INDEX IF NOT EXISTS idx_backup_bestaetigung_status
    ON backup_bestaetigung(status);

-- Backup-Tracking
CREATE TABLE IF NOT EXISTS backup_tracking (
    id SERIAL PRIMARY KEY,
    letztes_backup TIMESTAMP,
    einsaetze_bei_backup INTEGER,
    bemerkung TEXT,
    durchgefuehrt_von INTEGER REFERENCES benutzer(id)
);

-- Tabelle für stornierte Einsätze
CREATE TABLE IF NOT EXISTS maschineneinsaetze_storniert (
    id SERIAL PRIMARY KEY,
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
    erstellt_am TIMESTAMP,
    storniert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    storniert_von INTEGER REFERENCES benutzer(id),
    storno_grund TEXT
);

-- Tabelle für Gemeinschafts-Nachrichten
CREATE TABLE IF NOT EXISTS gemeinschafts_nachrichten (
    id SERIAL PRIMARY KEY,
    gemeinschaft_id INTEGER NOT NULL REFERENCES gemeinschaften(id) ON DELETE CASCADE,
    absender_id INTEGER NOT NULL REFERENCES benutzer(id),
    betreff TEXT NOT NULL,
    inhalt TEXT NOT NULL,
    prioritaet TEXT DEFAULT 'normal',
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    gueltig_bis DATE
);

CREATE INDEX IF NOT EXISTS idx_nachrichten_gemeinschaft ON gemeinschafts_nachrichten(gemeinschaft_id);
CREATE INDEX IF NOT EXISTS idx_nachrichten_absender ON gemeinschafts_nachrichten(absender_id);

-- Tabelle für gelesene Nachrichten
CREATE TABLE IF NOT EXISTS nachricht_gelesen (
    nachricht_id INTEGER NOT NULL REFERENCES gemeinschafts_nachrichten(id) ON DELETE CASCADE,
    benutzer_id INTEGER NOT NULL REFERENCES benutzer(id) ON DELETE CASCADE,
    gelesen_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (nachricht_id, benutzer_id)
);

-- Tabelle für Maschinen-Reservierungen
CREATE TABLE IF NOT EXISTS maschinen_reservierungen (
    id SERIAL PRIMARY KEY,
    maschine_id INTEGER NOT NULL REFERENCES maschinen(id),
    benutzer_id INTEGER NOT NULL REFERENCES benutzer(id),
    datum DATE NOT NULL,
    ganztags BOOLEAN DEFAULT TRUE,
    uhrzeit_von TIME,
    uhrzeit_bis TIME,
    zweck TEXT,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    storniert BOOLEAN DEFAULT FALSE,
    storniert_am TIMESTAMP,
    status VARCHAR(20) DEFAULT 'aktiv',
    UNIQUE(maschine_id, datum, benutzer_id)
);

CREATE INDEX IF NOT EXISTS idx_reservierungen_maschine ON maschinen_reservierungen(maschine_id);
CREATE INDEX IF NOT EXISTS idx_reservierungen_benutzer ON maschinen_reservierungen(benutzer_id);
CREATE INDEX IF NOT EXISTS idx_reservierungen_datum ON maschinen_reservierungen(datum);

-- Tabelle für Maschinen-Aufwendungen
CREATE TABLE IF NOT EXISTS maschinen_aufwendungen (
    id SERIAL PRIMARY KEY,
    maschine_id INTEGER NOT NULL REFERENCES maschinen(id),
    datum DATE NOT NULL,
    art TEXT NOT NULL,
    beschreibung TEXT,
    betrag REAL NOT NULL,
    beleg_nr TEXT,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    erstellt_von INTEGER REFERENCES benutzer(id)
);

CREATE INDEX IF NOT EXISTS idx_aufwendungen_maschine ON maschinen_aufwendungen(maschine_id);
CREATE INDEX IF NOT EXISTS idx_aufwendungen_datum ON maschinen_aufwendungen(datum);

-- Tabelle für Bank-Transaktionen
CREATE TABLE IF NOT EXISTS bank_transaktionen (
    id SERIAL PRIMARY KEY,
    buchungsdatum DATE NOT NULL,
    valutadatum DATE,
    betrag REAL NOT NULL,
    waehrung TEXT DEFAULT 'EUR',
    verwendungszweck TEXT,
    auftraggeber TEXT,
    iban TEXT,
    bic TEXT,
    importiert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    importiert_von INTEGER REFERENCES benutzer(id),
    zugeordnet BOOLEAN DEFAULT FALSE,
    zugeordnet_zu_mitglied INTEGER REFERENCES benutzer(id),
    zugeordnet_am TIMESTAMP,
    import_hash TEXT UNIQUE
);

CREATE INDEX IF NOT EXISTS idx_bank_trans_datum ON bank_transaktionen(buchungsdatum);
CREATE INDEX IF NOT EXISTS idx_bank_trans_zugeordnet ON bank_transaktionen(zugeordnet);

-- Tabelle für Mitglieder-Konten
CREATE TABLE IF NOT EXISTS mitglieder_konten (
    id SERIAL PRIMARY KEY,
    benutzer_id INTEGER NOT NULL REFERENCES benutzer(id),
    gemeinschaft_id INTEGER NOT NULL REFERENCES gemeinschaften(id),
    kontostand REAL DEFAULT 0.0,
    saldo REAL DEFAULT 0.0,
    anfangssaldo REAL DEFAULT 0.0,
    letzte_aktualisierung TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(benutzer_id, gemeinschaft_id)
);

-- Tabelle für Buchungen
CREATE TABLE IF NOT EXISTS buchungen (
    id SERIAL PRIMARY KEY,
    konto_id INTEGER NOT NULL REFERENCES mitglieder_konten(id),
    benutzer_id INTEGER REFERENCES benutzer(id),
    datum DATE NOT NULL,
    betrag REAL NOT NULL,
    buchungsart TEXT NOT NULL,
    referenz_typ TEXT,
    referenz_id INTEGER,
    beschreibung TEXT,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    erstellt_von INTEGER REFERENCES benutzer(id)
);

CREATE INDEX IF NOT EXISTS idx_buchungen_konto ON buchungen(konto_id);
CREATE INDEX IF NOT EXISTS idx_buchungen_datum ON buchungen(datum);

-- Tabelle für Mitglieder-Abrechnungen
CREATE TABLE IF NOT EXISTS mitglieder_abrechnungen (
    id SERIAL PRIMARY KEY,
    benutzer_id INTEGER NOT NULL REFERENCES benutzer(id),
    gemeinschaft_id INTEGER NOT NULL REFERENCES gemeinschaften(id),
    von_datum DATE NOT NULL,
    bis_datum DATE NOT NULL,
    gesamtbetrag REAL NOT NULL,
    status TEXT DEFAULT 'offen',
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    bezahlt_am TIMESTAMP
);

-- Tabelle für Zahlungs-Zuordnungen
CREATE TABLE IF NOT EXISTS zahlungs_zuordnungen (
    id SERIAL PRIMARY KEY,
    transaktion_id INTEGER NOT NULL REFERENCES bank_transaktionen(id),
    benutzer_id INTEGER NOT NULL REFERENCES benutzer(id),
    zugeordnet_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    zugeordnet_von INTEGER REFERENCES benutzer(id)
);

-- Tabelle für Zahlungsreferenzen
CREATE TABLE IF NOT EXISTS zahlungsreferenzen (
    id SERIAL PRIMARY KEY,
    benutzer_id INTEGER NOT NULL REFERENCES benutzer(id),
    gemeinschaft_id INTEGER REFERENCES gemeinschaften(id),
    referenz TEXT NOT NULL,
    aktiv BOOLEAN DEFAULT TRUE,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(benutzer_id, referenz)
);

-- Tabelle für CSV-Import-Konfiguration
CREATE TABLE IF NOT EXISTS csv_import_konfiguration (
    id SERIAL PRIMARY KEY,
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
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabelle für Gemeinschafts-Kosten
CREATE TABLE IF NOT EXISTS gemeinschafts_kosten (
    id SERIAL PRIMARY KEY,
    gemeinschaft_id INTEGER NOT NULL REFERENCES gemeinschaften(id),
    bezeichnung TEXT NOT NULL,
    betrag REAL NOT NULL,
    datum DATE NOT NULL,
    kategorie TEXT,
    beschreibung TEXT,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    erstellt_von INTEGER REFERENCES benutzer(id)
);

-- Tabelle für Jahresabschlüsse
CREATE TABLE IF NOT EXISTS jahresabschluesse (
    id SERIAL PRIMARY KEY,
    gemeinschaft_id INTEGER NOT NULL REFERENCES gemeinschaften(id),
    jahr INTEGER NOT NULL,
    abgeschlossen_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    abgeschlossen_von INTEGER REFERENCES benutzer(id),
    gesamteinnahmen REAL,
    gesamtausgaben REAL,
    bemerkung TEXT,
    UNIQUE(gemeinschaft_id, jahr)
);

-- Standard-Admin-Benutzer für neue Datenbanken
-- Login: Benutzername = admin, Passwort = admin123
-- Der password_hash ist der SHA-256 Hash von "admin123"
INSERT INTO benutzer (id, name, vorname, username, password_hash, is_admin, admin_level, aktiv)
VALUES (1, 'Admin', 'System', 'admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', TRUE, 2, TRUE)
ON CONFLICT (id) DO NOTHING;

-- Sequenz für benutzer anpassen
SELECT setval('benutzer_id_seq', (SELECT MAX(id) FROM benutzer));

-- Tabelle für Replication-Konfiguration
CREATE TABLE IF NOT EXISTS replication_config (
    id SERIAL PRIMARY KEY,
    standby_host TEXT,
    standby_port INTEGER DEFAULT 5432,
    standby_user TEXT DEFAULT 'replicator',
    replication_slot TEXT DEFAULT 'mgr_slot',
    aktiv BOOLEAN DEFAULT FALSE,
    sync_modus TEXT DEFAULT 'async',
    letzter_status TEXT,
    letzter_check TIMESTAMP,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    geaendert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabelle für Replication-Log
CREATE TABLE IF NOT EXISTS replication_log (
    id SERIAL PRIMARY KEY,
    zeitpunkt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    aktion TEXT NOT NULL,
    status TEXT NOT NULL,
    details TEXT,
    ausgefuehrt_von INTEGER REFERENCES benutzer(id)
);

CREATE INDEX IF NOT EXISTS idx_replication_log_zeitpunkt ON replication_log(zeitpunkt DESC);

-- Initiale Replication-Konfiguration
INSERT INTO replication_config (id, aktiv) VALUES (1, FALSE) ON CONFLICT (id) DO NOTHING;
