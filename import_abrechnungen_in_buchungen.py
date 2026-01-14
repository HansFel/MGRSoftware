#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Import bestehender Abrechnungen in das neue Buchungssystem

Konvertiert alle vorhandenen mitglieder_abrechnungen in Buchungen
und initialisiert die Mitgliederkonten.
"""

import sqlite3
import sys
from datetime import datetime

DB_PATH = 'maschinengemeinschaft.db'

def import_abrechnungen():
    """Importiert bestehende Abrechnungen als Buchungen"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("=== Import bestehender Abrechnungen ===\n")
        
        # Prüfe ob bereits Buchungen existieren
        cursor.execute("SELECT COUNT(*) FROM buchungen WHERE typ = 'abrechnung'")
        existing = cursor.fetchone()[0]
        if existing > 0:
            print(f"⚠️  Es existieren bereits {existing} Abrechnungs-Buchungen.")
            response = input("Trotzdem fortfahren? (j/n): ")
            if response.lower() != 'j':
                print("Abgebrochen.")
                return False
        
        # Hole alle Abrechnungen
        cursor.execute("""
            SELECT 
                id,
                benutzer_id,
                gemeinschaft_id,
                zeitraum_bis,  -- Verwende Enddatum als Buchungsdatum
                betrag_gesamt,
                erstellt_am
            FROM mitglieder_abrechnungen
            ORDER BY erstellt_am
        """)
        
        abrechnungen = cursor.fetchall()
        print(f"Gefunden: {len(abrechnungen)} Abrechnungen\n")
        
        imported = 0
        skipped = 0
        
        for abrechnung in abrechnungen:
            abr_id, benutzer_id, gem_id, datum, betrag, erstellt_am = abrechnung
            
            # Prüfe ob Buchung bereits existiert
            cursor.execute("""
                SELECT id FROM buchungen 
                WHERE referenz_typ = 'abrechnung' AND referenz_id = ?
            """, (abr_id,))
            
            if cursor.fetchone():
                skipped += 1
                continue
            
            # Erstelle Buchung (negativ = Schuld des Mitglieds)
            cursor.execute("""
                INSERT INTO buchungen (
                    benutzer_id,
                    gemeinschaft_id,
                    datum,
                    betrag,
                    typ,
                    beschreibung,
                    referenz_typ,
                    referenz_id,
                    erstellt_am,
                    erstellt_von
                ) VALUES (?, ?, ?, ?, 'abrechnung', ?, 'abrechnung', ?, ?, ?)
            """, (
                benutzer_id,
                gem_id,
                datum,
                -betrag,  # Negativ = Mitglied schuldet der Gemeinschaft
                f'Abrechnung #{abr_id} vom {datum}',
                abr_id,
                erstellt_am,
                1  # System-Admin ID
            ))
            
            imported += 1
            if imported % 10 == 0:
                print(f"  {imported} Buchungen importiert...")
        
        print(f"\n✓ {imported} neue Buchungen erstellt")
        if skipped > 0:
            print(f"  {skipped} bereits existierende übersprungen")
        
        # Initialisiere Mitgliederkonten
        print("\n=== Initialisiere Mitgliederkonten ===\n")
        
        cursor.execute("""
            SELECT DISTINCT benutzer_id, gemeinschaft_id
            FROM buchungen
        """)
        konten = cursor.fetchall()
        
        created = 0
        updated = 0
        
        for benutzer_id, gem_id in konten:
            # Berechne Saldo aus allen Buchungen
            cursor.execute("""
                SELECT COALESCE(SUM(betrag), 0)
                FROM buchungen
                WHERE benutzer_id = ? AND gemeinschaft_id = ?
            """, (benutzer_id, gem_id))
            saldo = cursor.fetchone()[0]
            
            # Prüfe ob Konto existiert
            cursor.execute("""
                SELECT id FROM mitglieder_konten
                WHERE benutzer_id = ? AND gemeinschaft_id = ?
            """, (benutzer_id, gem_id))
            
            if cursor.fetchone():
                # Update
                cursor.execute("""
                    UPDATE mitglieder_konten
                    SET saldo = ?, letzte_aktualisierung = CURRENT_TIMESTAMP
                    WHERE benutzer_id = ? AND gemeinschaft_id = ?
                """, (saldo, benutzer_id, gem_id))
                updated += 1
            else:
                # Create
                cursor.execute("""
                    INSERT INTO mitglieder_konten (
                        benutzer_id, gemeinschaft_id, saldo, saldo_vorjahr
                    ) VALUES (?, ?, ?, 0)
                """, (benutzer_id, gem_id, saldo))
                created += 1
        
        print(f"✓ {created} neue Konten erstellt")
        print(f"✓ {updated} bestehende Konten aktualisiert")
        
        # Zeige Zusammenfassung
        print("\n=== Kontoübersicht ===\n")
        cursor.execute("""
            SELECT 
                g.name as gemeinschaft,
                b.vorname || ' ' || b.name as mitglied,
                mk.saldo
            FROM mitglieder_konten mk
            JOIN gemeinschaften g ON mk.gemeinschaft_id = g.id
            JOIN benutzer b ON mk.benutzer_id = b.id
            ORDER BY g.name, mk.saldo
        """)
        
        for gem, mitglied, saldo in cursor.fetchall():
            status = "Guthaben" if saldo > 0 else "Schulden" if saldo < 0 else "Ausgeglichen"
            print(f"  {gem}: {mitglied} = {saldo:,.2f} € ({status})")
        
        conn.commit()
        
        print("\n=== Import erfolgreich abgeschlossen! ===")
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Datenbankfehler: {e}", file=sys.stderr)
        conn.rollback()
        return False
    except Exception as e:
        print(f"❌ Fehler: {e}", file=sys.stderr)
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    success = import_abrechnungen()
    sys.exit(0 if success else 1)
