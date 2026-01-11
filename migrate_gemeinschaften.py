"""
Migration: Fügt Gemeinschaften-Funktionalität hinzu
Datum: 11. Januar 2026

- Neue Tabelle: gemeinschaften
- Neue Tabelle: mitglied_gemeinschaft (N:M Beziehung)
- Neue Spalte in maschinen: gemeinschaft_id
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "maschinengemeinschaft.db")

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. Erstelle Gemeinschaften-Tabelle
        print("📋 Erstelle Tabelle 'gemeinschaften'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gemeinschaften (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                beschreibung TEXT,
                erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                aktiv BOOLEAN DEFAULT 1
            )
        """)
        
        # 2. Erstelle Standard-Gemeinschaft
        print("🏠 Erstelle Standard-Gemeinschaft...")
        cursor.execute("""
            INSERT OR IGNORE INTO gemeinschaften (id, name, beschreibung) 
            VALUES (1, 'Hauptgemeinschaft', 'Standard-Gemeinschaft für bestehende Daten')
        """)
        
        # 3. Prüfe ob gemeinschaft_id bereits in maschinen existiert
        cursor.execute("PRAGMA table_info(maschinen)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'gemeinschaft_id' not in columns:
            print("🔧 Füge gemeinschaft_id zu Tabelle 'maschinen' hinzu...")
            cursor.execute("""
                ALTER TABLE maschinen 
                ADD COLUMN gemeinschaft_id INTEGER DEFAULT 1 REFERENCES gemeinschaften(id)
            """)
        else:
            print("✓ Spalte gemeinschaft_id existiert bereits in maschinen")
        
        # 4. Erstelle Zuordnungstabelle Mitglied-Gemeinschaft
        print("👥 Erstelle Tabelle 'mitglied_gemeinschaft'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mitglied_gemeinschaft (
                mitglied_id INTEGER NOT NULL,
                gemeinschaft_id INTEGER NOT NULL,
                beigetreten_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                rolle TEXT DEFAULT 'mitglied',
                PRIMARY KEY (mitglied_id, gemeinschaft_id),
                FOREIGN KEY (mitglied_id) REFERENCES benutzer(id) ON DELETE CASCADE,
                FOREIGN KEY (gemeinschaft_id) REFERENCES gemeinschaften(id) ON DELETE CASCADE
            )
        """)
        
        # 5. Ordne alle bestehenden Benutzer der Hauptgemeinschaft zu
        print("👤 Ordne bestehende Benutzer der Hauptgemeinschaft zu...")
        cursor.execute("""
            INSERT OR IGNORE INTO mitglied_gemeinschaft (mitglied_id, gemeinschaft_id)
            SELECT id, 1 FROM benutzer WHERE aktiv = 1
        """)
        
        # 6. Erstelle Index für bessere Performance
        print("📊 Erstelle Indizes...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_maschinen_gemeinschaft 
            ON maschinen(gemeinschaft_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_mitglied_gemeinschaft_mitglied 
            ON mitglied_gemeinschaft(mitglied_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_mitglied_gemeinschaft_gemeinschaft 
            ON mitglied_gemeinschaft(gemeinschaft_id)
        """)
        
        # 7. Erstelle View für Gemeinschafts-Übersicht
        print("📈 Erstelle View 'gemeinschaften_uebersicht'...")
        cursor.execute("""
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
            GROUP BY g.id, g.name, g.beschreibung, g.aktiv
        """)
        
        conn.commit()
        print("\n✅ Migration erfolgreich abgeschlossen!")
        print("\nÜbersicht:")
        
        cursor.execute("SELECT COUNT(*) FROM gemeinschaften")
        print(f"  - Gemeinschaften: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM mitglied_gemeinschaft")
        print(f"  - Mitglied-Zuordnungen: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM maschinen WHERE gemeinschaft_id IS NOT NULL")
        print(f"  - Maschinen mit Gemeinschaft: {cursor.fetchone()[0]}")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Fehler bei der Migration: {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
