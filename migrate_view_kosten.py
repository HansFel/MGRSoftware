"""
Migration: Aktualisiert einsaetze_uebersicht View um kosten_berechnet zu inkludieren
"""

import sqlite3
import os

DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.dirname(__file__), "maschinengemeinschaft.db"))

def migrate():
    """Aktualisiert die View einsaetze_uebersicht"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("Lösche alte View...")
        cursor.execute("DROP VIEW IF EXISTS einsaetze_uebersicht")
        
        print("Erstelle neue View mit kosten_berechnet...")
        cursor.execute("""
            CREATE VIEW einsaetze_uebersicht AS
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
            ORDER BY e.datum DESC
        """)
        
        conn.commit()
        print("\n✓ View erfolgreich aktualisiert!")
        print("✓ Die Einsatzübersicht zeigt jetzt die berechneten Maschinenkosten an.")
        
    except Exception as e:
        print(f"✗ Fehler bei der Migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    print("Starte View-Migration...")
    print(f"Datenbank: {DB_PATH}\n")
    migrate()
