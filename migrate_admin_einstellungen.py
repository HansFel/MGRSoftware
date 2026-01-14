#!/usr/bin/env python3
"""
Migration: Admin-Einstellungen für Backup-Schwellwert
"""

import sqlite3
import os

def migrate():
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'maschinengemeinschaft.db')
    if not os.path.exists(db_path):
        db_path = 'maschinengemeinschaft.db'
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Spalte für Backup-Schwellwert in benutzer-Tabelle hinzufügen
    try:
        cursor.execute('''
            ALTER TABLE benutzer 
            ADD COLUMN backup_schwellwert INTEGER DEFAULT 50
        ''')
        print("✓ Spalte backup_schwellwert hinzugefügt")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("✓ Spalte backup_schwellwert existiert bereits")
        else:
            raise
    
    # Spalte für letzten Treibstoffpreis hinzufügen
    try:
        cursor.execute('''
            ALTER TABLE benutzer 
            ADD COLUMN letzter_treibstoffpreis REAL
        ''')
        print("✓ Spalte letzter_treibstoffpreis hinzugefügt")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("✓ Spalte letzter_treibstoffpreis existiert bereits")
        else:
            raise
    
    conn.commit()
    conn.close()
    print("✓ Migration erfolgreich: Admin-Einstellungen und Treibstoffpreis-Tracking")

if __name__ == '__main__':
    migrate()
