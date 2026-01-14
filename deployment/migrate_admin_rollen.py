#!/usr/bin/env python3
"""
Migration: Differenzierte Administrator-Rechte
"""

import sqlite3
import os

def migrate():
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'maschinengemeinschaft.db')
    if not os.path.exists(db_path):
        db_path = 'maschinengemeinschaft.db'
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Spalte für Admin-Level hinzufügen
    # 0 = kein Admin, 1 = Gemeinschafts-Admin, 2 = Haupt-Admin
    try:
        cursor.execute('''
            ALTER TABLE benutzer 
            ADD COLUMN admin_level INTEGER DEFAULT 0
        ''')
        print("✓ Spalte admin_level hinzugefügt")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("✓ Spalte admin_level existiert bereits")
        else:
            raise
    
    # Bestehende Admins zu Haupt-Admins machen
    cursor.execute("""
        UPDATE benutzer 
        SET admin_level = 2 
        WHERE is_admin = 1
    """)
    print(f"✓ {cursor.rowcount} bestehende Admins zu Haupt-Administratoren migriert")
    
    # Tabelle für Gemeinschafts-Administratoren
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gemeinschafts_admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            benutzer_id INTEGER NOT NULL,
            gemeinschaft_id INTEGER NOT NULL,
            erstellt_am TEXT NOT NULL,
            UNIQUE(benutzer_id, gemeinschaft_id),
            FOREIGN KEY (benutzer_id) REFERENCES benutzer(id),
            FOREIGN KEY (gemeinschaft_id) REFERENCES gemeinschaften(id)
        )
    ''')
    print("✓ Tabelle gemeinschafts_admin erstellt")
    
    # Tabelle für Backup-Bestätigungen
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS backup_bestaetigung (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER NOT NULL,
            zeitpunkt TEXT NOT NULL,
            bemerkung TEXT,
            status TEXT DEFAULT 'wartend',
            FOREIGN KEY (admin_id) REFERENCES benutzer(id)
        )
    ''')
    print("✓ Tabelle backup_bestaetigung erstellt")
    
    # Index für Performance
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_gemeinschafts_admin_benutzer 
        ON gemeinschafts_admin(benutzer_id)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_gemeinschafts_admin_gemeinschaft 
        ON gemeinschafts_admin(gemeinschaft_id)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_backup_bestaetigung_status 
        ON backup_bestaetigung(status)
    ''')
    
    conn.commit()
    conn.close()
    print("✓ Migration erfolgreich: Differenzierte Administrator-Rechte")

if __name__ == '__main__':
    migrate()
