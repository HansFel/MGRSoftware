"""
Generiert Beispieldaten für die Maschinengemeinschaft-Datenbank
"""

import sqlite3
import random
from datetime import datetime, timedelta
import hashlib
import os

# Pfad zur Datenbank
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'maschinengemeinschaft.db')

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def generate_data():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    cursor = conn.cursor()

    print(f"Verbinde mit Datenbank: {DB_PATH}")

    # ==================== GEMEINSCHAFTEN ====================
    gemeinschaften = [
        ('Hauptgemeinschaft', 'Standard-Maschinengemeinschaft', 10000.00, 'Sparkasse Tirol', 'AT12 3456 7890 1234 5678', 'SPTIAT21'),
        ('Alpenverein Landwirtschaft', 'Kooperation Bergbauern', 5000.00, 'Raiffeisenbank', 'AT98 7654 3210 9876 5432', 'RZTIAT22'),
        ('Tal-Kooperative', 'Gemeinschaft der Talbauern', 7500.00, 'Volksbank Tirol', 'AT55 1122 3344 5566 7788', 'VBTIAT33'),
    ]

    print("\nFüge Gemeinschaften hinzu...")
    for g in gemeinschaften:
        cursor.execute("""
            INSERT OR IGNORE INTO gemeinschaften (name, beschreibung, anfangssaldo_bank, bank_name, bank_iban, bank_bic)
            VALUES (?, ?, ?, ?, ?, ?)
        """, g)
    conn.commit()

    # Hole Gemeinschafts-IDs
    cursor.execute("SELECT id FROM gemeinschaften")
    gemeinschaft_ids = [row[0] for row in cursor.fetchall()]

    # ==================== BENUTZER ====================
    benutzer = [
        # (name, vorname, username, password, is_admin, admin_level, adresse, telefon, email, mitglied_seit)
        ('Huber', 'Johann', 'jhuber', 'passwort123', 0, 0, 'Bauernhof 1, 6020 Innsbruck', '+43 664 1234567', 'johann.huber@email.at', '2020-03-15'),
        ('Maier', 'Franz', 'fmaier', 'passwort123', 0, 0, 'Feldweg 5, 6020 Innsbruck', '+43 664 2345678', 'franz.maier@email.at', '2019-06-01'),
        ('Gruber', 'Maria', 'mgruber', 'passwort123', 0, 0, 'Wiesenstraße 12, 6100 Seefeld', '+43 664 3456789', 'maria.gruber@email.at', '2021-01-10'),
        ('Hofer', 'Peter', 'phofer', 'passwort123', 0, 0, 'Almweg 8, 6100 Seefeld', '+43 664 4567890', 'peter.hofer@email.at', '2018-09-20'),
        ('Steiner', 'Anna', 'asteiner', 'passwort123', 0, 0, 'Bergstraße 22, 6130 Schwaz', '+43 664 5678901', 'anna.steiner@email.at', '2022-04-05'),
        ('Berger', 'Thomas', 'tberger', 'passwort123', 1, 1, 'Dorfplatz 3, 6020 Innsbruck', '+43 664 6789012', 'thomas.berger@email.at', '2017-11-12'),
        ('Winkler', 'Elisabeth', 'ewinkler', 'passwort123', 0, 0, 'Sonnenweg 7, 6130 Schwaz', '+43 664 7890123', 'elisabeth.winkler@email.at', '2020-08-25'),
        ('Pichler', 'Josef', 'jpichler', 'passwort123', 0, 0, 'Kirchgasse 14, 6020 Innsbruck', '+43 664 8901234', 'josef.pichler@email.at', '2019-02-28'),
        ('Reiter', 'Katharina', 'kreiter', 'passwort123', 0, 0, 'Talgrund 9, 6100 Seefeld', '+43 664 9012345', 'katharina.reiter@email.at', '2021-07-18'),
        ('Eder', 'Markus', 'meder', 'passwort123', 0, 0, 'Ackerweg 16, 6130 Schwaz', '+43 664 0123456', 'markus.eder@email.at', '2018-12-03'),
        ('Bauer', 'Sabine', 'sbauer', 'passwort123', 0, 0, 'Hofstraße 4, 6020 Innsbruck', '+43 664 1112233', 'sabine.bauer@email.at', '2020-05-14'),
        ('Fischer', 'Hans', 'hfischer', 'passwort123', 0, 0, 'Mühlweg 11, 6100 Seefeld', '+43 664 2223344', 'hans.fischer@email.at', '2019-10-09'),
        ('Wagner', 'Christine', 'cwagner', 'passwort123', 0, 0, 'Waldrand 6, 6130 Schwaz', '+43 664 3334455', 'christine.wagner@email.at', '2022-01-22'),
        ('Moser', 'Friedrich', 'fmoser', 'passwort123', 0, 0, 'Heugasse 19, 6020 Innsbruck', '+43 664 4445566', 'friedrich.moser@email.at', '2017-08-07'),
        ('Schwarz', 'Gabriele', 'gschwarz', 'passwort123', 0, 0, 'Obstweg 2, 6100 Seefeld', '+43 664 5556677', 'gabriele.schwarz@email.at', '2021-11-30'),
    ]

    print("Füge Benutzer hinzu...")
    benutzer_ids = []
    for b in benutzer:
        cursor.execute("""
            INSERT OR IGNORE INTO benutzer
            (name, vorname, username, password_hash, is_admin, admin_level, adresse, telefon, email, mitglied_seit, aktiv)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (b[0], b[1], b[2], hash_password(b[3]), b[4], b[5], b[6], b[7], b[8], b[9]))
        if cursor.lastrowid:
            benutzer_ids.append(cursor.lastrowid)
    conn.commit()

    # Hole alle Benutzer-IDs (falls einige schon existierten)
    cursor.execute("SELECT id FROM benutzer WHERE aktiv = 1")
    benutzer_ids = [row[0] for row in cursor.fetchall()]
    print(f"  -> {len(benutzer_ids)} Benutzer vorhanden")

    # Mitglieder zu Gemeinschaften zuordnen
    print("Ordne Benutzer zu Gemeinschaften zu...")
    for bid in benutzer_ids:
        # Jeder Benutzer gehört zu 1-2 Gemeinschaften
        num_gemeinschaften = random.randint(1, 2)
        selected = random.sample(gemeinschaft_ids, min(num_gemeinschaften, len(gemeinschaft_ids)))
        for gid in selected:
            cursor.execute("""
                INSERT OR IGNORE INTO mitglied_gemeinschaft (mitglied_id, gemeinschaft_id, rolle)
                VALUES (?, ?, ?)
            """, (bid, gid, random.choice(['mitglied', 'mitglied', 'mitglied', 'vorstand'])))
    conn.commit()

    # ==================== MASCHINEN ====================
    maschinen = [
        # (bezeichnung, hersteller, modell, baujahr, kennzeichen, stundenzaehler, preis_pro_einheit, abrechnungsart, anschaffungspreis, gemeinschaft_id)
        ('Traktor Fendt 724', 'Fendt', '724 Vario', 2019, 'IL-T 1234', 1250.5, 45.00, 'stunden', 185000.00, 1),
        ('Traktor John Deere 6130R', 'John Deere', '6130R', 2020, 'IL-T 2345', 890.0, 42.00, 'stunden', 145000.00, 1),
        ('Mähdrescher Claas', 'Claas', 'Lexion 770', 2018, 'IL-M 3456', 620.0, 180.00, 'stunden', 420000.00, 1),
        ('Ladewagen Pöttinger', 'Pöttinger', 'Jumbo 6010', 2021, None, 0, 25.00, 'stunden', 75000.00, 1),
        ('Kreiselmäher Kuhn', 'Kuhn', 'FC 3160', 2020, None, 0, 18.00, 'hektar', 28000.00, 1),
        ('Güllefass Zunhammer', 'Zunhammer', 'SKE 18500', 2017, 'IL-G 4567', 0, 12.00, 'stunden', 65000.00, 1),
        ('Traktor Steyr 4130', 'Steyr', '4130 Profi', 2022, 'SZ-T 5678', 320.0, 40.00, 'stunden', 125000.00, 2),
        ('Heuwender Pöttinger', 'Pöttinger', 'Hit 8.91', 2019, None, 0, 15.00, 'hektar', 18000.00, 2),
        ('Rundballenpresse Krone', 'Krone', 'Comprima F 125', 2020, None, 0, 8.50, 'stueck', 48000.00, 2),
        ('Schneepflug Hauer', 'Hauer', 'HSP 2800', 2018, None, 0, 35.00, 'stunden', 12000.00, 2),
        ('Traktor Massey Ferguson', 'Massey Ferguson', '5711 S', 2021, 'SZ-T 6789', 450.0, 38.00, 'stunden', 115000.00, 3),
        ('Düngerstreuer Amazone', 'Amazone', 'ZA-TS 3200', 2019, None, 0, 6.00, 'hektar', 22000.00, 3),
        ('Pflug Lemken', 'Lemken', 'Juwel 8', 2018, None, 0, 28.00, 'hektar', 35000.00, 3),
        ('Sämaschine Horsch', 'Horsch', 'Pronto 4 DC', 2020, None, 0, 22.00, 'hektar', 85000.00, 3),
        ('Frontlader Stoll', 'Stoll', 'FZ 50.1', 2021, None, 0, 15.00, 'stunden', 18000.00, 3),
    ]

    print("Füge Maschinen hinzu...")
    for m in maschinen:
        cursor.execute("""
            INSERT OR IGNORE INTO maschinen
            (bezeichnung, hersteller, modell, baujahr, kennzeichen, stundenzaehler_aktuell,
             preis_pro_einheit, abrechnungsart, anschaffungspreis, gemeinschaft_id, aktiv,
             wartungsintervall, naechste_wartung_bei)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 50, ?)
        """, (m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[8], m[9], m[5] + 50))
    conn.commit()

    # Hole alle Maschinen-IDs
    cursor.execute("SELECT id, stundenzaehler_aktuell, abrechnungsart, preis_pro_einheit, gemeinschaft_id FROM maschinen WHERE aktiv = 1")
    maschinen_data = cursor.fetchall()
    print(f"  -> {len(maschinen_data)} Maschinen vorhanden")

    # Hole Einsatzzweck-IDs
    cursor.execute("SELECT id FROM einsatzzwecke WHERE aktiv = 1")
    einsatzzweck_ids = [row[0] for row in cursor.fetchall()]

    # ==================== MASCHINENEINSÄTZE ====================
    print("Generiere Maschineneinsätze...")

    # Generiere Einsätze für die letzten 2 Jahre
    start_date = datetime.now() - timedelta(days=730)
    end_date = datetime.now()

    einsatz_count = 0

    for maschine in maschinen_data:
        maschine_id, aktueller_stand, abrechnungsart, preis, gemeinschaft_id = maschine

        # Hole Benutzer dieser Gemeinschaft
        cursor.execute("""
            SELECT mitglied_id FROM mitglied_gemeinschaft WHERE gemeinschaft_id = ?
        """, (gemeinschaft_id,))
        gemeinschaft_benutzer = [row[0] for row in cursor.fetchall()]
        if not gemeinschaft_benutzer:
            gemeinschaft_benutzer = benutzer_ids[:5]  # Fallback

        # Generiere 20-80 Einsätze pro Maschine
        num_einsaetze = random.randint(20, 80)

        # Startstand für diese Maschine berechnen
        total_stunden = aktueller_stand if aktueller_stand else 0
        if total_stunden > 0:
            # Berechne durchschnittliche Stunden pro Einsatz
            avg_stunden = total_stunden / num_einsaetze
        else:
            avg_stunden = random.uniform(1.5, 4.0)

        current_stand = max(0, total_stunden - (avg_stunden * num_einsaetze))

        for i in range(num_einsaetze):
            # Zufälliges Datum
            random_days = random.randint(0, 730)
            einsatz_datum = start_date + timedelta(days=random_days)

            # Zufälliger Benutzer aus der Gemeinschaft
            benutzer_id = random.choice(gemeinschaft_benutzer)

            # Zufälliger Einsatzzweck
            einsatzzweck_id = random.choice(einsatzzweck_ids)

            # Betriebsstunden
            anfangstand = current_stand
            betriebsstunden = random.uniform(0.5, 8.0)
            endstand = anfangstand + betriebsstunden
            current_stand = endstand

            # Fläche/Menge (für ha/km/stück-Abrechnung)
            flaeche_menge = None
            if abrechnungsart == 'hektar':
                flaeche_menge = random.uniform(1.0, 15.0)
            elif abrechnungsart == 'stueck':
                flaeche_menge = random.randint(5, 50)
            elif abrechnungsart == 'kilometer':
                flaeche_menge = random.uniform(5.0, 80.0)

            # Kosten berechnen
            if abrechnungsart == 'stunden':
                kosten = betriebsstunden * preis
            elif flaeche_menge:
                kosten = flaeche_menge * preis
            else:
                kosten = betriebsstunden * preis

            # Treibstoffverbrauch und -kosten (manchmal)
            treibstoffverbrauch = None
            treibstoffkosten = None
            if random.random() < 0.3:  # 30% haben Treibstoffdaten
                treibstoffverbrauch = random.uniform(5.0, 35.0)
                treibstoffkosten = treibstoffverbrauch * random.uniform(1.40, 1.80)

            # Anmerkungen (manchmal)
            anmerkungen = None
            if random.random() < 0.15:  # 15% haben Anmerkungen
                anmerkungen_liste = [
                    'Gutes Wetter',
                    'Leichter Regen',
                    'Schwieriges Gelände',
                    'Schnelle Arbeit',
                    'Mehrere Felder bearbeitet',
                    'Ölstand geprüft',
                    'Kleine Reparatur nötig',
                    'Sehr steiles Gelände',
                    'Nasser Boden',
                    'Ideale Bedingungen',
                ]
                anmerkungen = random.choice(anmerkungen_liste)

            cursor.execute("""
                INSERT INTO maschineneinsaetze
                (datum, benutzer_id, maschine_id, einsatzzweck_id, anfangstand, endstand,
                 treibstoffverbrauch, treibstoffkosten, flaeche_menge, kosten_berechnet, anmerkungen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (einsatz_datum.strftime('%Y-%m-%d'), benutzer_id, maschine_id,
                  einsatzzweck_id, round(anfangstand, 1), round(endstand, 1),
                  round(treibstoffverbrauch, 1) if treibstoffverbrauch else None,
                  round(treibstoffkosten, 2) if treibstoffkosten else None,
                  round(flaeche_menge, 2) if flaeche_menge else None,
                  round(kosten, 2), anmerkungen))
            einsatz_count += 1

        # Aktualisiere Stundenzähler der Maschine
        cursor.execute("""
            UPDATE maschinen SET stundenzaehler_aktuell = ? WHERE id = ?
        """, (round(current_stand, 1), maschine_id))

    conn.commit()
    print(f"  -> {einsatz_count} Einsätze generiert")

    # ==================== ZUSAMMENFASSUNG ====================
    print("\n" + "="*50)
    print("ZUSAMMENFASSUNG")
    print("="*50)

    cursor.execute("SELECT COUNT(*) FROM gemeinschaften")
    print(f"Gemeinschaften: {cursor.fetchone()[0]}")

    cursor.execute("SELECT COUNT(*) FROM benutzer WHERE aktiv = 1")
    print(f"Benutzer: {cursor.fetchone()[0]}")

    cursor.execute("SELECT COUNT(*) FROM maschinen WHERE aktiv = 1")
    print(f"Maschinen: {cursor.fetchone()[0]}")

    cursor.execute("SELECT COUNT(*) FROM einsatzzwecke WHERE aktiv = 1")
    print(f"Einsatzzwecke: {cursor.fetchone()[0]}")

    cursor.execute("SELECT COUNT(*) FROM maschineneinsaetze")
    print(f"Maschineneinsätze: {cursor.fetchone()[0]}")

    cursor.execute("SELECT SUM(kosten_berechnet) FROM maschineneinsaetze")
    total = cursor.fetchone()[0]
    print(f"Gesamtkosten: {total:,.2f} EUR" if total else "Gesamtkosten: 0.00 EUR")

    conn.close()
    print("\nDatenbank erfolgreich mit Beispieldaten gefüllt!")

if __name__ == "__main__":
    generate_data()
