-- Migration: Fehlende Spalten und Tabellen hinzufügen
-- Datum: 2026-02-01
-- Für PostgreSQL

-- 1. Status-Spalte zu maschinen_reservierungen hinzufügen
ALTER TABLE maschinen_reservierungen
ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'aktiv';

-- 2. geaendert_am Spalte zu maschinen_reservierungen hinzufügen
ALTER TABLE maschinen_reservierungen
ADD COLUMN IF NOT EXISTS geaendert_am TIMESTAMP;

-- 3. treibstoff_berechnen Spalte zu maschinen hinzufügen
ALTER TABLE maschinen
ADD COLUMN IF NOT EXISTS treibstoff_berechnen BOOLEAN DEFAULT FALSE;

-- 4. Tabelle für abgelaufene Reservierungen (Archiv)
CREATE TABLE IF NOT EXISTS reservierungen_abgelaufen (
    id SERIAL PRIMARY KEY,
    reservierung_id INTEGER NOT NULL,
    maschine_id INTEGER NOT NULL,
    maschine_bezeichnung TEXT,
    benutzer_id INTEGER NOT NULL,
    benutzer_name TEXT,
    datum DATE NOT NULL,
    uhrzeit_von TEXT,
    uhrzeit_bis TEXT,
    nutzungsdauer_stunden REAL,
    zweck TEXT,
    bemerkung TEXT,
    erstellt_am TIMESTAMP,
    archiviert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_res_abgelaufen_maschine ON reservierungen_abgelaufen(maschine_id);
CREATE INDEX IF NOT EXISTS idx_res_abgelaufen_benutzer ON reservierungen_abgelaufen(benutzer_id);

-- Bestehende Reservierungen auf 'aktiv' setzen falls noch NULL
UPDATE maschinen_reservierungen SET status = 'aktiv' WHERE status IS NULL;
