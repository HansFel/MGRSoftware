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
    admin_level INTEGER DEFAULT 0,
    adresse TEXT,
    telefon TEXT,
    email TEXT,
    mitglied_seit DATE,
    aktiv BOOLEAN DEFAULT 1,
    bemerkungen TEXT,
    treibstoffkosten_preis REAL DEFAULT 1.50,
    backup_schwellwert REAL DEFAULT 10.0
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

-- Tabelle für Gemeinschaften
CREATE TABLE IF NOT EXISTS gemeinschaften (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    beschreibung TEXT,
    adresse TEXT,
    telefon TEXT,
    email TEXT,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    aktiv BOOLEAN DEFAULT 1
);

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

-- Standard-Gemeinschaft
INSERT OR IGNORE INTO gemeinschaften (id, name, beschreibung) 
VALUES (1, 'Hauptgemeinschaft', 'Standard-Gemeinschaft');

-- Indizes für Performance
CREATE INDEX IF NOT EXISTS idx_maschinen_gemeinschaft ON maschinen(gemeinschaft_id);
CREATE INDEX IF NOT EXISTS idx_mitglied_gemeinschaft_mitglied ON mitglied_gemeinschaft(mitglied_id);
CREATE INDEX IF NOT EXISTS idx_mitglied_gemeinschaft_gemeinschaft ON mitglied_gemeinschaft(gemeinschaft_id);

-- View für Gemeinschafts-Übersicht
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

-- Tabelle für Gemeinschafts-Administratoren
CREATE TABLE IF NOT EXISTS gemeinschafts_admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    benutzer_id INTEGER NOT NULL,
    gemeinschaft_id INTEGER NOT NULL,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(benutzer_id, gemeinschaft_id),
    FOREIGN KEY (benutzer_id) REFERENCES benutzer(id) ON DELETE CASCADE,
    FOREIGN KEY (gemeinschaft_id) REFERENCES gemeinschaften(id) ON DELETE CASCADE
);

-- Tabelle für Backup-Bestätigungen
CREATE TABLE IF NOT EXISTS backup_bestaetigung (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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

CREATE TABLE IF NOT EXISTS backup_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    letztes_backup TIMESTAMP,
    einsaetze_bei_backup INTEGER,
    bemerkung TEXT
);    

-- Standard-Admin-Benutzer für neue Datenbanken
-- Wird nur angelegt, wenn noch kein Admin-Benutzer existiert
-- Login: Benutzername = admin, Passwort = admin123
-- Der password_hash ist der SHA-256 Hash von "admin123"
INSERT OR IGNORE INTO benutzer (id, name, vorname, username, password_hash, is_admin, admin_level, aktiv)
VALUES (1, 'Admin', 'System', 'admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 1, 2, 1);