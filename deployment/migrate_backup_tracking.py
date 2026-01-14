#!/usr/bin/env python3
"""
Migration: Backup-Tracking und Nachrichtensystem
"""

import sqlite3
import os
from datetime import datetime

def migrate():
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'maschinengemeinschaft.db')
    if not os.path.exists(db_path):
        db_path = 'maschinengemeinschaft.db'
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tabelle für Backup-Tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS backup_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            letztes_backup TEXT NOT NULL,
            einsaetze_bei_backup INTEGER DEFAULT 0,
            durchgefuehrt_von INTEGER,
            bemerkung TEXT,
            FOREIGN KEY (durchgefuehrt_von) REFERENCES benutzer(id)
        )
    ''')
    
    # Initialen Eintrag erstellen falls Tabelle leer
    cursor.execute('SELECT COUNT(*) FROM backup_tracking')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO backup_tracking (letztes_backup, einsaetze_bei_backup, bemerkung)
            VALUES (?, 0, 'Initial')
        ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),))
    
    # Tabelle für Gemeinschaftsnachrichten
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gemeinschafts_nachrichten (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gemeinschaft_id INTEGER NOT NULL,
            absender_id INTEGER NOT NULL,
            betreff TEXT NOT NULL,
            nachricht TEXT NOT NULL,
            erstellt_am TEXT NOT NULL,
            FOREIGN KEY (gemeinschaft_id) REFERENCES gemeinschaften(id),
            FOREIGN KEY (absender_id) REFERENCES benutzer(id)
        )
    ''')
    
    # Tabelle für gelesene Nachrichten
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nachricht_gelesen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nachricht_id INTEGER NOT NULL,
            benutzer_id INTEGER NOT NULL,
            gelesen_am TEXT NOT NULL,
            UNIQUE(nachricht_id, benutzer_id),
            FOREIGN KEY (nachricht_id) REFERENCES gemeinschafts_nachrichten(id),
            FOREIGN KEY (benutzer_id) REFERENCES benutzer(id)
        )
    ''')
    
    # Indizes für Performance
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_nachrichten_gemeinschaft 
        ON gemeinschafts_nachrichten(gemeinschaft_id)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_nachrichten_erstellt 
        ON gemeinschafts_nachrichten(erstellt_am DESC)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_gelesen_benutzer 
        ON nachricht_gelesen(benutzer_id)
    ''')
    
    conn.commit()
    conn.close()
    print("✓ Migration erfolgreich: Backup-Tracking und Nachrichtensystem erstellt")

if __name__ == '__main__':
    migrate()
