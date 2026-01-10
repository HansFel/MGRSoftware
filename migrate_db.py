"""
Migrations-Skript: Fügt username und password_hash zur benutzer-Tabelle hinzu
"""

import sqlite3
import os

DB_PATH = "maschinengemeinschaft.db"

def migrate_database():
    """Datenbank migrieren"""
    if not os.path.exists(DB_PATH):
        print("❌ Datenbank nicht gefunden. Bitte initialisieren Sie zuerst die Datenbank.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Prüfen ob Spalten bereits existieren
        cursor.execute("PRAGMA table_info(benutzer)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'username' not in columns:
            print("➕ Füge 'username' Spalte hinzu...")
            cursor.execute("ALTER TABLE benutzer ADD COLUMN username TEXT")
            print("✅ 'username' Spalte hinzugefügt")
        else:
            print("ℹ️  'username' Spalte existiert bereits")
        
        if 'password_hash' not in columns:
            print("➕ Füge 'password_hash' Spalte hinzu...")
            cursor.execute("ALTER TABLE benutzer ADD COLUMN password_hash TEXT")
            print("✅ 'password_hash' Spalte hinzugefügt")
        else:
            print("ℹ️  'password_hash' Spalte existiert bereits")
        
        conn.commit()
        print("\n✅ Migration erfolgreich abgeschlossen!")
        print("\n📝 Nächste Schritte:")
        print("1. Öffnen Sie die Desktop-Anwendung (main.py)")
        print("2. Bearbeiten Sie jeden Benutzer und setzen Sie Benutzername + Passwort")
        print("3. Starten Sie dann die Web-App (python web_app.py)")
        
    except Exception as e:
        print(f"❌ Fehler bei der Migration: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔄 Starte Datenbank-Migration...\n")
    migrate_database()
