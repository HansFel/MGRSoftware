"""
Prüft und aktualisiert fehlende Maschinenkosten
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "maschinengemeinschaft.db")

def check_and_fix_kosten():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Prüfe wie viele Einsätze NULL kosten haben
    cursor.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN kosten_berechnet IS NULL THEN 1 ELSE 0 END) as null_count
        FROM maschineneinsaetze
    """)
    total, null_count = cursor.fetchone()
    print(f"Gesamt Einsätze: {total}")
    print(f"Einsätze ohne berechnete Kosten: {null_count}")
    
    if null_count > 0:
        print("\nAktualisiere fehlende Kosten...")
        
        # Hole alle Einsätze ohne berechnete Kosten
        cursor.execute("""
            SELECT e.id, e.maschine_id, e.anfangstand, e.endstand, 
                   e.flaeche_menge, m.abrechnungsart, m.preis_pro_einheit
            FROM maschineneinsaetze e
            JOIN maschinen m ON e.maschine_id = m.id
            WHERE e.kosten_berechnet IS NULL
        """)
        
        einsaetze = cursor.fetchall()
        updated = 0
        
        for einsatz_id, maschine_id, anfang, ende, flaeche, abrechnungsart, preis in einsaetze:
            kosten = None
            
            if preis and preis > 0:
                if abrechnungsart == 'stunden':
                    kosten = (ende - anfang) * preis
                elif abrechnungsart in ['hektar', 'kilometer', 'stueck'] and flaeche:
                    kosten = flaeche * preis
            
            if kosten is not None:
                cursor.execute(
                    "UPDATE maschineneinsaetze SET kosten_berechnet = ? WHERE id = ?",
                    (kosten, einsatz_id)
                )
                updated += 1
        
        conn.commit()
        print(f"✓ {updated} Einsätze aktualisiert")
    
    # Zeige Beispiele
    print("\nBeispiel-Einsätze:")
    cursor.execute("""
        SELECT e.id, e.datum, m.bezeichnung, m.abrechnungsart, 
               m.preis_pro_einheit, e.betriebsstunden, 
               e.flaeche_menge, e.kosten_berechnet
        FROM maschineneinsaetze e
        JOIN maschinen m ON e.maschine_id = m.id
        ORDER BY e.id DESC
        LIMIT 5
    """)
    
    for row in cursor.fetchall():
        kosten_str = f"{row[7]:.2f}" if row[7] is not None else 'NULL'
        print(f"ID: {row[0]}, Datum: {row[1]}, Maschine: {row[2]}, "
              f"Art: {row[3]}, Preis: {row[4]:.2f}, Stunden: {row[5]:.1f}, "
              f"Fläche: {row[6] or 0}, Kosten: {kosten_str}")
    
    conn.close()

if __name__ == '__main__':
    print("Prüfe Maschinenkosten in der Datenbank...\n")
    check_and_fix_kosten()
