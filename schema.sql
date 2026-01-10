-- Datenbank-Schema für Maschinengemeinschaft
-- Erstellt: 6. Januar 2026

-- Tabelle für Benutzer
CREATE TABLE IF NOT EXISTS benutzer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    vorname TEXT,
    username TEXT UNIQUE,
    password_hash TEXT,
    is_admin BOOLEAN DEFAULT 0,
    adresse TEXT,
    telefon TEXT,
    email TEXT,
    mitglied_seit DATE,
    aktiv BOOLEAN DEFAULT 1,
    bemerkungen TEXT
);

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
    bemerkungen TEXT
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
    betriebsstunden REAL GENERATED ALWAYS AS (endstand - anfangstand) STORED,
    treibstoffverbrauch REAL,
    treibstoffkosten REAL,
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

-- Trigger zum Aktualisieren des Änderungsdatums
CREATE TRIGGER IF NOT EXISTS update_maschineneinsaetze_timestamp 
AFTER UPDATE ON maschineneinsaetze
BEGIN
    UPDATE maschineneinsaetze SET geaendert_am = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- View für übersichtliche Ausgabe aller Einsätze
CREATE VIEW IF NOT EXISTS einsaetze_uebersicht AS
SELECT 
    e.id,
    e.datum,
    b.name || ', ' || COALESCE(b.vorname, '') AS benutzer,
    m.bezeichnung AS maschine,
    ez.bezeichnung AS einsatzzweck,
    e.anfangstand,
    e.endstand,
    e.betriebsstunden,
    e.treibstoffverbrauch,
    e.treibstoffkosten,
    e.anmerkungen
FROM maschineneinsaetze e
JOIN benutzer b ON e.benutzer_id = b.id
JOIN maschinen m ON e.maschine_id = m.id
JOIN einsatzzwecke ez ON e.einsatzzweck_id = ez.id
ORDER BY e.datum DESC;

-- Beispieldaten für Einsatzzwecke
INSERT OR IGNORE INTO einsatzzwecke (bezeichnung, beschreibung) VALUES
    ('Mähen', 'Wiesen und Felder mähen'),
    ('Pflügen', 'Feldbearbeitung - Pflügen'),
    ('Säen', 'Aussaat von Getreide oder Gras'),
    ('Ernten', 'Ernte von Getreide, Heu, etc.'),
    ('Transportfahrten', 'Material- und Gütertransport'),
    ('Schneeräumung', 'Winterdienst und Schneeräumung'),
    ('Holzarbeiten', 'Holzrücken und Forstarbeiten'),
    ('Grünlandpflege', 'Weidepflege und Grünlandarbeiten'),
    ('Wegeinstandhaltung', 'Pflege und Instandhaltung von Wegen'),
    ('Sonstiges', 'Andere Einsätze');
