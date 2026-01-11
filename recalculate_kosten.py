"""
Neu-Berechnung aller Maschinenkosten
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "maschinengemeinschaft.db")

def recalculate_all_kosten():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Berechne alle Maschinenkosten neu...")
    
    # Hole alle Einsätze
    cursor.execute("""
        SELECT e.id, e.maschine_id, e.anfangstand, e.endstand, 
               e.flaeche_menge, e.kosten_berechnet as alt_kosten,
               m.abrechnungsart, m.preis_pro_einheit, m.bezeichnung
        FROM maschineneinsaetze e
        JOIN maschinen m ON e.maschine_id = m.id
        ORDER BY e.id
    """)
    
    einsaetze = cursor.fetchall()
    updated = 0
    
    for einsatz_id, maschine_id, anfang, ende, flaeche, alt_kosten, abrechnungsart, preis, bezeichnung in einsaetze:
        kosten = None
        preis = preis or 0
        
        if abrechnungsart == 'stunden':
            kosten = (ende - anfang) * preis
        elif abrechnungsart in ['hektar', 'kilometer', 'stueck']:
            if flaeche and flaeche > 0:
                kosten = flaeche * preis
            else:
                kosten = 0.0
        
        if kosten != alt_kosten:
            cursor.execute(
                "UPDATE maschineneinsaetze SET kosten_berechnet = ? WHERE id = ?",
                (kosten, einsatz_id)
            )
            updated += 1
            print(f"  Einsatz #{einsatz_id} ({bezeichnung}): {alt_kosten:.2f}€ → {kosten:.2f}€")
    
    conn.commit()
    print(f"\n✓ {updated} Einsätze aktualisiert")
    
    # Zeige neue Summen
    cursor.execute("""
        SELECT SUM(kosten_berechnet) as gesamt_kosten
        FROM maschineneinsaetze
    """)
    gesamt = cursor.fetchone()[0] or 0
    print(f"✓ Gesamt Maschinenkosten: {gesamt:.2f}€")
    
    conn.close()

if __name__ == '__main__':
    print("Starte Neu-Berechnung der Maschinenkosten...\n")
    recalculate_all_kosten()
