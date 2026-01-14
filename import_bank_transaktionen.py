#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Importiert zugeordnete Bank-Transaktionen als Buchungen ins Buchungssystem

Wandelt alle bank_transaktionen mit benutzer_id (zugeordnet = 1) 
in Einzahlungs-Buchungen um.
"""

import sqlite3
import sys
from datetime import datetime

DB_PATH = 'maschinengemeinschaft.db'

def import_bank_transaktionen():
    """Importiert zugeordnete Bank-Transaktionen als Buchungen"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("=== Import Bank-Transaktionen ins Buchungssystem ===\n")
        
        # Hole alle zugeordneten Transaktionen die noch nicht importiert wurden
        cursor.execute("""
            SELECT 
                t.id,
                t.gemeinschaft_id,
                t.buchungsdatum,
                t.betrag,
                t.verwendungszweck,
                t.benutzer_id,
                t.importiert_von,
                b.vorname || ' ' || b.name as mitglied_name,
                g.name as gemeinschaft_name
            FROM bank_transaktionen t
            LEFT JOIN benutzer b ON t.benutzer_id = b.id
            LEFT JOIN gemeinschaften g ON t.gemeinschaft_id = g.id
            WHERE t.benutzer_id IS NOT NULL 
            AND t.zugeordnet = 1
            AND t.betrag > 0
            ORDER BY t.buchungsdatum
        """)
        
        transaktionen = cursor.fetchall()
        
        if not transaktionen:
            print("ℹ️  Keine zugeordneten Transaktionen zum Importieren gefunden\n")
            return True
        
        print(f"Gefunden: {len(transaktionen)} zugeordnete Transaktionen\n")
        
        importiert = 0
        bereits_vorhanden = 0
        fehler = 0
        
        for transaktion in transaktionen:
            t_id, gem_id, datum, betrag, verwendung, benutzer_id, importiert_von, mitglied, gemeinschaft = transaktion
            
            # Prüfe ob bereits als Buchung importiert
            cursor.execute("""
                SELECT id FROM buchungen 
                WHERE referenz_typ = 'bank_transaktion' 
                AND referenz_id = ?
            """, (t_id,))
            
            if cursor.fetchone():
                print(f"  ⏭️  Transaktion #{t_id} bereits importiert (überspringe)")
                bereits_vorhanden += 1
                continue
            
            try:
                # Kürze Beschreibung
                beschreibung = f"Bankzahlung: {verwendung[:100]}"
                if len(verwendung) > 100:
                    beschreibung += "..."
                
                # Erstelle Buchung
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
                        erstellt_von
                    ) VALUES (?, ?, ?, ?, 'einzahlung', ?, 'bank_transaktion', ?, ?)
                """, (
                    benutzer_id,
                    gem_id,
                    datum,
                    betrag,  # Positiv = Einzahlung
                    beschreibung,
                    t_id,
                    importiert_von or 1  # Falls kein importiert_von vorhanden, verwende Admin-ID 1
                ))
                
                buchung_id = cursor.lastrowid
                
                # Aktualisiere Mitgliederkonto
                cursor.execute("""
                    INSERT INTO mitglieder_konten (benutzer_id, gemeinschaft_id, saldo, saldo_vorjahr)
                    VALUES (?, ?, ?, 0)
                    ON CONFLICT(benutzer_id, gemeinschaft_id) 
                    DO UPDATE SET 
                        saldo = saldo + ?,
                        letzte_aktualisierung = CURRENT_TIMESTAMP
                """, (benutzer_id, gem_id, betrag, betrag))
                
                # Prüfe ob damit Abrechnungen beglichen werden können
                cursor.execute("""
                    SELECT id, betrag_gesamt 
                    FROM mitglieder_abrechnungen
                    WHERE benutzer_id = ? 
                    AND gemeinschaft_id = ?
                    AND status = 'offen'
                    ORDER BY zeitraum_bis
                """, (benutzer_id, gem_id))
                
                offene_abrechnungen = cursor.fetchall()
                verbleibend = betrag
                bezahlte_abrechnungen = 0
                
                for abr_id, abr_betrag in offene_abrechnungen:
                    if verbleibend >= abr_betrag:
                        # Abrechnung vollständig bezahlt
                        cursor.execute("""
                            UPDATE mitglieder_abrechnungen
                            SET status = 'bezahlt'
                            WHERE id = ?
                        """, (abr_id,))
                        verbleibend -= abr_betrag
                        bezahlte_abrechnungen += 1
                    else:
                        break
                
                print(f"  ✅ Transaktion #{t_id}: {betrag:,.2f} € von {mitglied} ({gemeinschaft})")
                if bezahlte_abrechnungen > 0:
                    print(f"     → {bezahlte_abrechnungen} Abrechnung(en) als bezahlt markiert")
                
                importiert += 1
                
            except Exception as e:
                print(f"  ❌ Fehler bei Transaktion #{t_id}: {e}")
                fehler += 1
                conn.rollback()
                continue
        
        if fehler == 0:
            conn.commit()
            print(f"\n{'='*60}")
            print(f"✅ {importiert} Bank-Transaktionen erfolgreich importiert")
            if bereits_vorhanden > 0:
                print(f"ℹ️  {bereits_vorhanden} bereits vorhanden (übersprungen)")
            print(f"{'='*60}")
        else:
            print(f"\n⚠️  {fehler} Fehler beim Import")
            return False
        
        # Zeige aktualisierte Kontostände
        print("\n=== Aktualisierte Kontostände ===\n")
        cursor.execute("""
            SELECT 
                g.name as gemeinschaft,
                b.vorname || ' ' || b.name as mitglied,
                mk.saldo
            FROM mitglieder_konten mk
            JOIN gemeinschaften g ON mk.gemeinschaft_id = g.id
            JOIN benutzer b ON mk.benutzer_id = b.id
            WHERE mk.benutzer_id IN (
                SELECT DISTINCT benutzer_id 
                FROM bank_transaktionen 
                WHERE benutzer_id IS NOT NULL
            )
            ORDER BY g.name, b.name
        """)
        
        for gem, mitglied, saldo in cursor.fetchall():
            status = "Guthaben" if saldo > 0 else "Schulden" if saldo < 0 else "Ausgeglichen"
            print(f"  {gem}: {mitglied} = {saldo:,.2f} € ({status})")
        
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
    success = import_bank_transaktionen()
    sys.exit(0 if success else 1)
