"""
Datenbankmodul für Maschinengemeinschaft
Verwaltet alle Datenbankoperationen
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import os
import hashlib
import secrets


class MaschinenDB:
    """Hauptklasse für Datenbankverwaltung"""
    
    def __init__(self, db_path: str = "maschinengemeinschaft.db"):
        """Initialisiere Datenbankverbindung"""
        self.db_path = db_path
        self.connection = None
        self.cursor = None
        
    def connect(self):
        """Verbindung zur Datenbank herstellen"""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
        
    def close(self):
        """Datenbankverbindung schließen"""
        if self.connection:
            self.connection.close()
            
    def init_database(self):
        """Datenbank mit Schema initialisieren"""
        schema_file = os.path.join(os.path.dirname(__file__), 'schema.sql')
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        self.cursor.executescript(schema_sql)
        self.connection.commit()
        
    # ==================== BENUTZER ====================
    
    def add_benutzer(self, name: str, vorname: str = None, username: str = None,
                     password: str = None, is_admin: bool = False, adresse: str = None,
                     telefon: str = None, email: str = None, 
                     mitglied_seit: str = None, bemerkungen: str = None) -> int:
        """Neuen Benutzer hinzufügen"""
        password_hash = self._hash_password(password) if password else None
        
        sql = """INSERT INTO benutzer (name, vorname, username, password_hash, 
                                       is_admin, adresse, telefon, email, 
                                       mitglied_seit, bemerkungen)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        self.cursor.execute(sql, (name, vorname, username, password_hash,
                                  is_admin, adresse, telefon, email, 
                                  mitglied_seit, bemerkungen))
        self.connection.commit()
        return self.cursor.lastrowid
    
    def get_all_benutzer(self, nur_aktive: bool = True) -> List[Dict]:
        """Alle Benutzer abrufen"""
        sql = "SELECT * FROM benutzer"
        if nur_aktive:
            sql += " WHERE aktiv = 1"
        sql += " ORDER BY name, vorname"
        
        self.cursor.execute(sql)
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_benutzer(self, benutzer_id: int) -> Optional[Dict]:
        """Einzelnen Benutzer abrufen"""
        sql = "SELECT * FROM benutzer WHERE id = ?"
        self.cursor.execute(sql, (benutzer_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None
    
    def get_benutzer_by_id(self, benutzer_id: int) -> Optional[Dict]:
        """Einzelnen Benutzer abrufen (Alias für get_benutzer)"""
        return self.get_benutzer(benutzer_id)
    
    def update_benutzer(self, benutzer_id: int, **kwargs):
        """Benutzer aktualisieren"""
        fields = ', '.join([f"{key} = ?" for key in kwargs.keys()])
        sql = f"UPDATE benutzer SET {fields} WHERE id = ?"
        values = list(kwargs.values()) + [benutzer_id]
        self.cursor.execute(sql, values)
        self.connection.commit()
    
    def delete_benutzer(self, benutzer_id: int, soft_delete: bool = True):
        """Benutzer löschen (soft delete = nur deaktivieren)"""
        if soft_delete:
            self.cursor.execute("UPDATE benutzer SET aktiv = 0 WHERE id = ?", 
                              (benutzer_id,))
        else:
            self.cursor.execute("DELETE FROM benutzer WHERE id = ?", 
                              (benutzer_id,))
        self.connection.commit()
    
    def activate_benutzer(self, benutzer_id: int):
        """Benutzer reaktivieren"""
        self.cursor.execute("UPDATE benutzer SET aktiv = 1 WHERE id = ?", 
                          (benutzer_id,))
        self.connection.commit()
    
    def _hash_password(self, password: str) -> str:
        """Passwort hashen mit SHA-256"""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    def verify_login(self, username: str, password: str) -> Optional[Dict]:
        """Benutzer-Login überprüfen"""
        password_hash = self._hash_password(password)
        sql = """SELECT * FROM benutzer 
                 WHERE username = ? AND password_hash = ? AND aktiv = 1"""
        self.cursor.execute(sql, (username, password_hash))
        row = self.cursor.fetchone()
        return dict(row) if row else None
    
    def update_password(self, benutzer_id: int, new_password: str):
        """Passwort eines Benutzers ändern"""
        password_hash = self._hash_password(new_password)
        self.cursor.execute(
            "UPDATE benutzer SET password_hash = ? WHERE id = ?",
            (password_hash, benutzer_id)
        )
        self.connection.commit()
    
    def get_gemeinschafts_admin_ids(self, benutzer_id: int) -> List[int]:
        """Hole Gemeinschafts-IDs, für die ein Benutzer Admin ist"""
        self.cursor.execute("""
            SELECT gemeinschaft_id FROM gemeinschafts_admin
            WHERE benutzer_id = ?
        """, (benutzer_id,))
        return [row[0] for row in self.cursor.fetchall()]
    
    def add_gemeinschafts_admin(self, benutzer_id: int, gemeinschaft_id: int):
        """Benutzer als Gemeinschafts-Admin hinzufügen"""
        self.cursor.execute("""
            INSERT OR IGNORE INTO gemeinschafts_admin 
            (benutzer_id, gemeinschaft_id, erstellt_am)
            VALUES (?, ?, ?)
        """, (benutzer_id, gemeinschaft_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        self.connection.commit()
    
    def remove_gemeinschafts_admin(self, benutzer_id: int, gemeinschaft_id: int):
        """Gemeinschafts-Admin-Rechte entfernen"""
        self.cursor.execute("""
            DELETE FROM gemeinschafts_admin
            WHERE benutzer_id = ? AND gemeinschaft_id = ?
        """, (benutzer_id, gemeinschaft_id))
        self.connection.commit()
    
    def is_gemeinschafts_admin(self, benutzer_id: int, gemeinschaft_id: int) -> bool:
        """Prüfen ob Benutzer Admin einer Gemeinschaft ist"""
        self.cursor.execute("""
            SELECT COUNT(*) FROM gemeinschafts_admin
            WHERE benutzer_id = ? AND gemeinschaft_id = ?
        """, (benutzer_id, gemeinschaft_id))
        return self.cursor.fetchone()[0] > 0
    
    # ==================== MASCHINEN ====================
    
    def add_maschine(self, bezeichnung: str, hersteller: str = None,
                     modell: str = None, baujahr: int = None,
                     kennzeichen: str = None, anschaffungsdatum: str = None,
                     stundenzaehler_aktuell: float = 0,
                     wartungsintervall: int = 50,
                     naechste_wartung: float = None,
                     naechste_wartung_bei: float = None,
                     anmerkungen: str = None,
                     bemerkungen: str = None,
                     abrechnungsart: str = 'stunden',
                     preis_pro_einheit: float = 0.0,
                     erfassungsmodus: str = 'fortlaufend',
                     gemeinschaft_id: int = None,
                     anschaffungspreis: float = 0.0,
                     abschreibungsdauer_jahre: int = 10) -> int:
        """Neue Maschine hinzufügen"""
        # naechste_wartung hat Vorrang vor naechste_wartung_bei (Kompatibilität)
        wartung = naechste_wartung if naechste_wartung is not None else naechste_wartung_bei
        
        sql = """INSERT INTO maschinen (bezeichnung, hersteller, modell, baujahr,
                        kennzeichen, anschaffungsdatum, 
                        stundenzaehler_aktuell, wartungsintervall,
                        naechste_wartung_bei, bemerkungen,
                        abrechnungsart, preis_pro_einheit,
                        erfassungsmodus, gemeinschaft_id,
                        anschaffungspreis, abschreibungsdauer_jahre)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        self.cursor.execute(sql, (bezeichnung, hersteller, modell, baujahr,
                      kennzeichen, anschaffungsdatum,
                      stundenzaehler_aktuell, wartungsintervall,
                      wartung, anmerkungen or bemerkungen,
                      abrechnungsart, preis_pro_einheit,
                      erfassungsmodus, gemeinschaft_id,
                      anschaffungspreis, abschreibungsdauer_jahre))
        self.connection.commit()
        return self.cursor.lastrowid
    
    def get_all_maschinen(self, nur_aktive: bool = True) -> List[Dict]:
        """Alle Maschinen abrufen"""
        sql = "SELECT * FROM maschinen"
        if nur_aktive:
            sql += " WHERE aktiv = 1"
        sql += " ORDER BY bezeichnung"
        
        self.cursor.execute(sql)
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_maschine(self, maschine_id: int) -> Optional[Dict]:
        """Einzelne Maschine abrufen"""
        sql = "SELECT * FROM maschinen WHERE id = ?"
        self.cursor.execute(sql, (maschine_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None
    
    def get_maschine_by_id(self, maschine_id: int) -> Optional[Dict]:
        """Einzelne Maschine abrufen (Alias für get_maschine)"""
        return self.get_maschine(maschine_id)
    
    def update_maschine(self, maschine_id: int, **kwargs):
        """Maschine aktualisieren"""
        fields = ', '.join([f"{key} = ?" for key in kwargs.keys()])
        sql = f"UPDATE maschinen SET {fields} WHERE id = ?"
        values = list(kwargs.values()) + [maschine_id]
        self.cursor.execute(sql, values)
        self.connection.commit()
    
    def update_stundenzaehler(self, maschine_id: int, neuer_stand: float):
        """Stundenzähler einer Maschine aktualisieren"""
        self.update_maschine(maschine_id, stundenzaehler_aktuell=neuer_stand)
    
    def delete_maschine(self, maschine_id: int, soft_delete: bool = True):
        """Maschine löschen (soft delete = nur deaktivieren)"""
        if soft_delete:
            self.cursor.execute("UPDATE maschinen SET aktiv = 0 WHERE id = ?", 
                              (maschine_id,))
        else:
            self.cursor.execute("DELETE FROM maschinen WHERE id = ?", 
                              (maschine_id,))
        self.connection.commit()
    
    # ==================== EINSATZZWECKE ====================
    
    def add_einsatzzweck(self, bezeichnung: str, beschreibung: str = None) -> int:
        """Neuen Einsatzzweck hinzufügen"""
        sql = "INSERT INTO einsatzzwecke (bezeichnung, beschreibung) VALUES (?, ?)"
        self.cursor.execute(sql, (bezeichnung, beschreibung))
        self.connection.commit()
        return self.cursor.lastrowid
    
    def get_all_einsatzzwecke(self, nur_aktive: bool = True) -> List[Dict]:
        """Alle Einsatzzwecke abrufen"""
        sql = "SELECT * FROM einsatzzwecke"
        if nur_aktive:
            sql += " WHERE aktiv = 1"
        sql += " ORDER BY bezeichnung"
        
        self.cursor.execute(sql)
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_einsatzzweck_by_id(self, einsatzzweck_id: int) -> Optional[Dict]:
        """Einzelnen Einsatzzweck abrufen"""
        sql = "SELECT * FROM einsatzzwecke WHERE id = ?"
        self.cursor.execute(sql, (einsatzzweck_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None
    
    def update_einsatzzweck(self, einsatzzweck_id: int, **kwargs):
        """Einsatzzweck aktualisieren"""
        fields = ', '.join([f"{key} = ?" for key in kwargs.keys()])
        sql = f"UPDATE einsatzzwecke SET {fields} WHERE id = ?"
        values = list(kwargs.values()) + [einsatzzweck_id]
        self.cursor.execute(sql, values)
        self.connection.commit()
    
    def delete_einsatzzweck(self, einsatzzweck_id: int, soft_delete: bool = True):
        """Einsatzzweck löschen (soft delete = nur deaktivieren)"""
        if soft_delete:
            self.cursor.execute("UPDATE einsatzzwecke SET aktiv = 0 WHERE id = ?", 
                              (einsatzzweck_id,))
        else:
            self.cursor.execute("DELETE FROM einsatzzwecke WHERE id = ?", 
                              (einsatzzweck_id,))
        self.connection.commit()
    
    def activate_einsatzzweck(self, einsatzzweck_id: int):
        """Einsatzzweck reaktivieren"""
        self.cursor.execute("UPDATE einsatzzwecke SET aktiv = 1 WHERE id = ?", 
                          (einsatzzweck_id,))
        self.connection.commit()
    
    # ==================== MASCHINENEINSÄTZE ====================
    
    def add_einsatz(self, datum: str, benutzer_id: int, maschine_id: int,
                    einsatzzweck_id: int, anfangstand: float, endstand: float,
                    treibstoffverbrauch: float = None, treibstoffkosten: float = None,
                    anmerkungen: str = None, flaeche_menge: float = None) -> int:
        """Neuen Maschineneinsatz hinzufügen"""
        if endstand < anfangstand:
            raise ValueError("Endstand muss größer oder gleich Anfangstand sein!")
        
        # Kosten berechnen basierend auf Maschinen-Abrechnungsart
        kosten_berechnet = None
        maschine = self.get_maschine_by_id(maschine_id)
        if maschine:
            abrechnungsart = maschine.get('abrechnungsart', 'stunden')
            preis = maschine.get('preis_pro_einheit', 0) or 0
            
            if abrechnungsart == 'stunden':
                # Berechne basierend auf Betriebsstunden
                kosten_berechnet = (endstand - anfangstand) * preis
            elif abrechnungsart in ['hektar', 'kilometer', 'stueck']:
                # Berechne basierend auf Fläche/Menge, falls vorhanden
                if flaeche_menge and flaeche_menge > 0:
                    kosten_berechnet = flaeche_menge * preis
                else:
                    # Fallback: 0 Euro wenn keine Menge angegeben
                    kosten_berechnet = 0.0
        
        sql = """INSERT INTO maschineneinsaetze (datum, benutzer_id, maschine_id,
                                                 einsatzzweck_id, anfangstand, endstand,
                                                 treibstoffverbrauch, treibstoffkosten,
                                                 anmerkungen, flaeche_menge, kosten_berechnet)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        self.cursor.execute(sql, (datum, benutzer_id, maschine_id, einsatzzweck_id,
                                  anfangstand, endstand, treibstoffverbrauch,
                                  treibstoffkosten, anmerkungen, flaeche_menge,
                                  kosten_berechnet))
        self.connection.commit()
        
        # Stundenzähler der Maschine automatisch aktualisieren
        self.update_stundenzaehler(maschine_id, endstand)
        
        return self.cursor.lastrowid
    
    def get_all_einsaetze(self, limit: int = None) -> List[Dict]:
        """Alle Einsätze abrufen (übersichtlich formatiert)"""
        sql = "SELECT * FROM einsaetze_uebersicht"
        if limit:
            sql += f" LIMIT {limit}"
        
        self.cursor.execute(sql)
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_einsaetze_by_benutzer(self, benutzer_id: int) -> List[Dict]:
        """Einsätze eines bestimmten Benutzers abrufen"""
        sql = "SELECT * FROM einsaetze_uebersicht WHERE benutzer LIKE ?"
        benutzer = self.get_benutzer(benutzer_id)
        if not benutzer:
            return []
        
        search_pattern = f"%{benutzer['name']}%"
        self.cursor.execute(sql, (search_pattern,))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_einsaetze_by_maschine(self, maschine_id: int) -> List[Dict]:
        """Einsätze einer bestimmten Maschine abrufen"""
        maschine = self.get_maschine(maschine_id)
        if not maschine:
            return []
        
        sql = "SELECT * FROM einsaetze_uebersicht WHERE maschine = ?"
        self.cursor.execute(sql, (maschine['bezeichnung'],))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_einsaetze_by_zeitraum(self, von: str, bis: str) -> List[Dict]:
        """Einsätze in einem Zeitraum abrufen"""
        sql = """SELECT * FROM einsaetze_uebersicht 
                 WHERE datum BETWEEN ? AND ?"""
        self.cursor.execute(sql, (von, bis))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_statistik_benutzer(self, benutzer_id: int) -> Dict:
        """Statistik für einen Benutzer"""
        sql = """SELECT 
                    COUNT(*) as anzahl_einsaetze,
                    SUM(betriebsstunden) as gesamt_stunden,
                    SUM(treibstoffverbrauch) as gesamt_treibstoff,
                    SUM(treibstoffkosten) as gesamt_kosten,
                    SUM(kosten_berechnet) as gesamt_maschinenkosten
                 FROM maschineneinsaetze
                 WHERE benutzer_id = ?"""
        self.cursor.execute(sql, (benutzer_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else {}
    
    def get_statistik_maschine(self, maschine_id: int) -> Dict:
        """Statistik für eine Maschine"""
        sql = """SELECT 
                    COUNT(*) as anzahl_einsaetze,
                    SUM(betriebsstunden) as gesamt_stunden,
                    SUM(treibstoffverbrauch) as gesamt_treibstoff,
                    COUNT(DISTINCT benutzer_id) as anzahl_benutzer
                 FROM maschineneinsaetze
                 WHERE maschine_id = ?"""
        self.cursor.execute(sql, (maschine_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else {}


# Context Manager Support
class MaschinenDBContext(MaschinenDB):
    """Context Manager für automatische Verbindungsverwaltung"""
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.connection.commit()
        else:
            self.connection.rollback()
        self.close()
        return False


if __name__ == "__main__":
    # Testcode
    print("Initialisiere Datenbank...")
    with MaschinenDBContext() as db:
        db.init_database()
        print("✓ Datenbank erfolgreich initialisiert!")
        
        # Zeige vorhandene Einsatzzwecke
        zwecke = db.get_all_einsatzzwecke()
        print(f"\n✓ {len(zwecke)} Einsatzzwecke verfügbar")
