# -*- coding: utf-8 -*-
"""
Flask-Webanwendung für Maschinengemeinschaft
Ermöglicht Benutzern den Zugriff von extern (z.B. Mobiltelefon)
"""


import os
import csv
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify, make_response
from database import MaschinenDBContext
from datetime import datetime
from io import StringIO, BytesIO
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))  # Für Session-Management

# Datenbank-Pfad aus Umgebungsvariable oder Standard-Pfad
DB_PATH = os.environ.get('DB_PATH', './data/maschinengemeinschaft.db')


def login_required(f):
    """Decorator für geschützte Routen"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'benutzer_id' not in session:
            flash('Bitte melden Sie sich an.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator für Admin-Routen - Level 1 oder höher"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'benutzer_id' not in session:
            flash('Bitte melden Sie sich an.', 'warning')
            return redirect(url_for('login'))
        if not session.get('is_admin'):
            flash('Zugriff verweigert. Administrator-Rechte erforderlich.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def hauptadmin_required(f):
    """Decorator für Haupt-Administrator-Routen - Level 2"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'benutzer_id' not in session:
            flash('Bitte melden Sie sich an.', 'warning')
            return redirect(url_for('login'))
        if not session.get('is_admin'):
            flash('Zugriff verweigert. Administrator-Rechte erforderlich.', 'danger')
            return redirect(url_for('dashboard'))
        if session.get('admin_level', 0) < 2:
            flash('Zugriff verweigert. Haupt-Administrator-Rechte erforderlich.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def archiviere_abgelaufene_reservierungen():
    """Verschiebt abgelaufene Reservierungen in die Archiv-Tabelle"""
    try:
        with MaschinenDBContext(DB_PATH) as db:
            cursor = db.connection.cursor()
            
            # Finde alle abgelaufenen Reservierungen (Datum + Endzeit liegt in der Vergangenheit)
            cursor.execute("""
                SELECT r.*, m.bezeichnung as maschine_bezeichnung, 
                       b.name || ' ' || COALESCE(b.vorname, '') as benutzer_name
                FROM maschinen_reservierungen r
                JOIN maschinen m ON r.maschine_id = m.id
                JOIN benutzer b ON r.benutzer_id = b.id
                WHERE r.status = 'aktiv'
                AND datetime(r.datum || ' ' || r.uhrzeit_bis) < datetime('now', 'localtime')
            """)
            
            abgelaufene = cursor.fetchall()
            
            if abgelaufene:
                columns = [desc[0] for desc in cursor.description]
                
                for row in abgelaufene:
                    reservierung = dict(zip(columns, row))
                    
                    # In Archiv-Tabelle kopieren
                    cursor.execute("""
                        INSERT INTO reservierungen_abgelaufen 
                        (reservierung_id, maschine_id, maschine_bezeichnung, benutzer_id, 
                         benutzer_name, datum, uhrzeit_von, uhrzeit_bis, nutzungsdauer_stunden, 
                         zweck, bemerkung, erstellt_am)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (reservierung['id'], reservierung['maschine_id'], 
                          reservierung['maschine_bezeichnung'], reservierung['benutzer_id'],
                          reservierung['benutzer_name'], reservierung['datum'], 
                          reservierung['uhrzeit_von'], reservierung['uhrzeit_bis'],
                          reservierung['nutzungsdauer_stunden'], reservierung.get('zweck'),
                          reservierung.get('bemerkung'), reservierung['erstellt_am']))
                    
                    # Status auf 'abgelaufen' setzen
                    cursor.execute("""
                        UPDATE maschinen_reservierungen
                        SET status = 'abgelaufen', geaendert_am = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (reservierung['id'],))
                
                db.connection.commit()
                return len(abgelaufene)
            
            return 0
            
    except Exception as e:
        print(f"Fehler beim Archivieren abgelaufener Reservierungen: {e}")
        return 0


@app.route('/')
def index():
    """Startseite - Weiterleitung"""
    # Archiviere abgelaufene Reservierungen beim Seitenaufruf
    archiviere_abgelaufene_reservierungen()
    
    if 'benutzer_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login-Seite"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        with MaschinenDBContext(DB_PATH) as db:
            benutzer = db.verify_login(username, password)
            
            if benutzer:
                session['benutzer_id'] = benutzer['id']
                session['benutzer_name'] = f"{benutzer['name']}, {benutzer['vorname']}"
                session['is_admin'] = bool(benutzer.get('is_admin', False))
                session['admin_level'] = benutzer.get('admin_level', 0)
                
                # Gemeinschafts-Admin Zuordnungen laden
                if session['admin_level'] == 1:
                    gemeinschafts_ids = db.get_gemeinschafts_admin_ids(benutzer['id'])
                    session['gemeinschafts_admin_ids'] = gemeinschafts_ids
                else:
                    session['gemeinschafts_admin_ids'] = []
                
                # Lade Gemeinschaften des Benutzers für das Menü
                cursor = db.connection.cursor()
                cursor.execute("""
                    SELECT g.id, g.name
                    FROM gemeinschaften g
                    JOIN mitglied_gemeinschaft mg ON g.id = mg.gemeinschaft_id
                    WHERE mg.mitglied_id = ? AND g.aktiv = 1
                    ORDER BY g.name
                """, (benutzer['id'],))
                gemeinschaften = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
                session['gemeinschaften'] = gemeinschaften
                
                flash(f"Willkommen, {benutzer['vorname']}!", 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Ungültiger Benutzername oder Passwort.', 'danger')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    flash('Sie wurden abgemeldet.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard - Übersicht für den Benutzer"""
    # Archiviere abgelaufene Reservierungen
    archiviere_abgelaufene_reservierungen()
    
    with MaschinenDBContext(DB_PATH) as db:
        benutzer_id = session['benutzer_id']
        
        # Statistiken laden
        statistik = db.get_statistik_benutzer(benutzer_id)
        
        # Gesamtkosten berechnen
        treibstoffkosten = statistik.get('gesamt_kosten', 0) or 0
        maschinenkosten = statistik.get('gesamt_maschinenkosten', 0) or 0
        statistik['gesamtkosten'] = treibstoffkosten + maschinenkosten
        
        # Letzte Einsätze
        einsaetze = db.get_einsaetze_by_benutzer(benutzer_id)
        letzte_einsaetze = einsaetze[:10] if einsaetze else []
        
        # Schulden nach Gemeinschaft (nur Maschinenkosten, keine Treibstoffkosten)
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT 
                g.id,
                g.name,
                COUNT(e.id) as anzahl_einsaetze,
                SUM(
                    CASE 
                        WHEN m.abrechnungsart = 'stunden' THEN (e.endstand - e.anfangstand) * COALESCE(m.preis_pro_einheit, 0)
                        ELSE COALESCE(e.flaeche_menge, 0) * COALESCE(m.preis_pro_einheit, 0)
                    END
                ) as maschinenkosten
            FROM maschineneinsaetze e
            JOIN maschinen m ON e.maschine_id = m.id
            JOIN gemeinschaften g ON m.gemeinschaft_id = g.id
            WHERE e.benutzer_id = ?
            GROUP BY g.id, g.name
            ORDER BY g.name
        """, (benutzer_id,))
        
        columns = [desc[0] for desc in cursor.description]
        schulden_nach_gemeinschaft = []
        for row in cursor.fetchall():
            d = dict(zip(columns, row))
            d['bezeichnung'] = d['name']  # Mapping für Template
            d['gesamtkosten'] = d['maschinenkosten'] or 0
            schulden_nach_gemeinschaft.append(d)
        
        # Meine aktiven Reservierungen laden
        cursor.execute("""
            SELECT r.*, m.bezeichnung as maschine_bezeichnung
            FROM maschinen_reservierungen r
            JOIN maschinen m ON r.maschine_id = m.id
            WHERE r.benutzer_id = ?
              AND r.datum >= date('now')
              AND r.status = 'aktiv'
            ORDER BY r.datum, r.uhrzeit_von
        """, (benutzer_id,))
        
        columns = [desc[0] for desc in cursor.description]
        reservierungen = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Ungelesene Nachrichten zählen
        cursor.execute("""
            SELECT COUNT(*) FROM gemeinschafts_nachrichten n
            JOIN mitglied_gemeinschaft mg ON n.gemeinschaft_id = mg.gemeinschaft_id
            LEFT JOIN nachricht_gelesen ng ON n.id = ng.nachricht_id AND ng.benutzer_id = ?
            WHERE mg.mitglied_id = ? AND ng.id IS NULL
        """, (benutzer_id, benutzer_id))
        
        ungelesene_nachrichten = cursor.fetchone()[0]
        
        # Zahlungsreferenzen des Benutzers laden
        cursor.execute("""
            SELECT z.*, g.name as gemeinschaft_name
            FROM zahlungsreferenzen z
            JOIN gemeinschaften g ON z.gemeinschaft_id = g.id
            WHERE z.benutzer_id = ? AND z.aktiv = 1
            ORDER BY g.name
        """, (benutzer_id,))
        
        columns = [desc[0] for desc in cursor.description]
        zahlungsreferenzen = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return render_template('dashboard.html', 
                         statistik=statistik,
                         einsaetze=letzte_einsaetze,
                         schulden_nach_gemeinschaft=schulden_nach_gemeinschaft,
                         reservierungen=reservierungen,
                         ungelesene_nachrichten=ungelesene_nachrichten,
                         zahlungsreferenzen=zahlungsreferenzen)


@app.route('/neuer-einsatz', methods=['GET', 'POST'])
@login_required
def neuer_einsatz():
    """Neuen Einsatz erfassen"""
    if request.method == 'POST':
        try:
            datum = request.form.get('datum')
            maschine_id = int(request.form.get('maschine_id'))
            einsatzzweck_id = int(request.form.get('einsatzzweck_id'))
            anmerkungen = request.form.get('anmerkungen')
            treibstoff = request.form.get('treibstoffverbrauch')
            kosten = request.form.get('treibstoffkosten')
            flaeche_menge = request.form.get('flaeche_menge')
            
            # Hole Maschine für Erfassungsmodus
            with MaschinenDBContext(DB_PATH) as db:
                maschine = db.get_maschine_by_id(maschine_id)
                erfassungsmodus = maschine.get('erfassungsmodus', 'fortlaufend')
                
                if erfassungsmodus == 'direkt':
                    # Direkter Modus - Wert direkt eingeben
                    direkt_wert = float(request.form.get('direkt_wert', 0))
                    if direkt_wert <= 0:
                        flash('Bitte geben Sie einen Wert ein!', 'danger')
                        return redirect(url_for('neuer_einsatz'))
                    
                    # Verwende aktuellen Stundenzähler als Anfang, berechne Ende
                    aktueller_stand = maschine.get('stundenzaehler_aktuell', 0) or 0
                    anfangstand = aktueller_stand
                    
                    # Bei Stundenabrechnung: Ende = Anfang + Wert
                    # Bei anderen: Ende = Anfang + Wert (damit Betriebsstunden = Wert)
                    if maschine.get('abrechnungsart') == 'stunden':
                        endstand = anfangstand + direkt_wert
                    else:
                        # Bei Hektar/km/Stück: Stunden ≈ Wert (vereinfacht)
                        endstand = anfangstand + direkt_wert
                        if not flaeche_menge:
                            flaeche_menge = str(direkt_wert)
                else:
                    # Fortlaufender Modus - Start/Ende
                    anfangstand = float(request.form.get('anfangstand'))
                    endstand = float(request.form.get('endstand'))
                    
                    if endstand < anfangstand:
                        flash('Endstand muss größer oder gleich Anfangstand sein!', 'danger')
                        return redirect(url_for('neuer_einsatz'))
                
                db.add_einsatz(
                    datum=datum,
                    benutzer_id=session['benutzer_id'],
                    maschine_id=maschine_id,
                    einsatzzweck_id=einsatzzweck_id,
                    anfangstand=anfangstand,
                    endstand=endstand,
                    treibstoffverbrauch=float(treibstoff) if treibstoff else None,
                    treibstoffkosten=float(kosten) if kosten else None,
                    anmerkungen=anmerkungen if anmerkungen else None,
                    flaeche_menge=float(flaeche_menge) if flaeche_menge else None
                )
                
                # Speichere letzten Treibstoffpreis für Vorschlag
                if kosten:
                    cursor = db.connection.cursor()
                    cursor.execute("""
                        UPDATE benutzer 
                        SET letzter_treibstoffpreis = ? 
                        WHERE id = ?
                    """, (float(kosten), session['benutzer_id']))
                    db.connection.commit()
            
            flash('Einsatz wurde erfolgreich gespeichert!', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            flash(f'Fehler beim Speichern: {str(e)}', 'danger')
            return redirect(url_for('neuer_einsatz'))
    
    # GET - Formular anzeigen
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        
        # Hole nur Maschinen aus Gemeinschaften, in denen der Benutzer Mitglied ist
        cursor.execute("""
            SELECT DISTINCT m.* 
            FROM maschinen m
            JOIN gemeinschaften g ON m.gemeinschaft_id = g.id
            JOIN mitglied_gemeinschaft mg ON g.id = mg.gemeinschaft_id
            WHERE mg.mitglied_id = ? 
              AND m.aktiv = 1 
              AND g.aktiv = 1
            ORDER BY m.bezeichnung
        """, (session['benutzer_id'],))
        
        columns = [desc[0] for desc in cursor.description]
        maschinen = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Prüfe aktuelle Reservierungen für heute
        heute_datum = datetime.now().strftime('%Y-%m-%d')
        
        for maschine in maschinen:
            cursor.execute("""
                SELECT r.*, b.name || ' ' || COALESCE(b.vorname, '') as benutzer_name
                FROM maschinen_reservierungen r
                JOIN benutzer b ON r.benutzer_id = b.id
                WHERE r.maschine_id = ? 
                  AND r.datum = ?
                  AND r.status = 'aktiv'
                ORDER BY r.uhrzeit_von
                LIMIT 1
            """, (maschine['id'], heute_datum))
            
            res = cursor.fetchone()
            if res:
                res_dict = dict(zip([desc[0] for desc in cursor.description], res))
                maschine['reservierung_aktiv'] = True
                maschine['reservierung_info'] = f"Heute reserviert: {res_dict['uhrzeit_von']}-{res_dict['uhrzeit_bis']} ({res_dict['benutzer_name']})"
            else:
                maschine['reservierung_aktiv'] = False
        
        einsatzzwecke = db.get_all_einsatzzwecke()
        
        # Hole Treibstoffkosten des Benutzers
        benutzer = db.get_benutzer(session['benutzer_id'])
        treibstoffkosten_preis = benutzer.get('treibstoffkosten_preis', 1.50)
        
        # Hole letzten Treibstoffpreis des Benutzers für Vorschlag
        cursor.execute("""
            SELECT letzter_treibstoffpreis FROM benutzer WHERE id = ?
        """, (session['benutzer_id'],))
        result = cursor.fetchone()
        letzter_treibstoffpreis = result[0] if result and result[0] else None
    
    return render_template('neuer_einsatz.html',
                         maschinen=maschinen,
                         einsatzzwecke=einsatzzwecke,
                         heute=datetime.now().strftime('%Y-%m-%d'),
                         treibstoffkosten_preis=treibstoffkosten_preis,
                         letzter_treibstoffpreis=letzter_treibstoffpreis)


@app.route('/meine-einsaetze')
@login_required
def meine_einsaetze():
    """Liste aller eigenen Einsätze"""
    with MaschinenDBContext(DB_PATH) as db:
        einsaetze = db.get_einsaetze_by_benutzer(session['benutzer_id'])
        # None-Werte für Summenfelder durch 0 ersetzen
        for e in einsaetze:
            for key in ['anfangstand', 'endstand', 'flaeche_menge', 'betriebsstunden', 'treibstoffverbrauch', 'treibstoffkosten', 'kosten_berechnet']:
                if e.get(key) is None:
                    e[key] = 0
            # Einheit bestimmen
            abrechnungsart = e.get('abrechnungsart', 'stunden')
            preis = e.get('preis_pro_einheit', 0)
            if abrechnungsart == 'hektar':
                einheit = 'ha'
            elif abrechnungsart == 'kilometer':
                einheit = 'km'
            elif abrechnungsart == 'stueck':
                einheit = 'St'
            else:
                einheit = 'h'
            # Menge berechnen
            if e.get('erfassungsmodus', 'fortlaufend') == 'fortlaufend':
                menge = e['endstand'] - e['anfangstand']
            else:
                menge = e.get('flaeche_menge', 0)
            # Maschinenkosten berechnen
            maschinenkosten = menge * preis
            # Formatierung
            if einheit == 'ha':
                menge_str = f"{menge:.2f} ha"
            elif einheit == 'km':
                menge_str = f"{menge:.1f} km"
            elif einheit == 'St':
                menge_str = f"{menge:.0f} St"
            else:
                menge_str = f"{menge:.1f} h"
            e['menge_berechnet'] = menge_str
            e['einheit'] = einheit
            e['maschinenkosten_berechnet'] = maschinenkosten
        # Summen berechnen
        summe_treibstoff = sum(e.get('treibstoffkosten', 0) for e in einsaetze)
        summe_maschine = sum(e.get('maschinenkosten_berechnet', 0) for e in einsaetze)
        summe_gesamt = summe_maschine  # Treibstoffkosten werden nicht mehr addiert
    return render_template('meine_einsaetze.html', 
                         einsaetze=einsaetze,
                         summe_treibstoff=summe_treibstoff,
                         summe_maschine=summe_maschine,
                         summe_gesamt=summe_gesamt)


@app.route('/einsatz/<int:einsatz_id>/stornieren', methods=['GET', 'POST'])
@login_required
def einsatz_stornieren(einsatz_id):
    """Einsatz stornieren"""
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        
        # Einsatz laden
        cursor.execute("""
            SELECT e.*, m.bezeichnung as maschine_name, 
                   b.name as benutzer_name, b.vorname as benutzer_vorname
            FROM maschineneinsaetze e
            JOIN maschinen m ON e.maschine_id = m.id
            JOIN benutzer b ON e.benutzer_id = b.id
            WHERE e.id = ?
        """, (einsatz_id,))
        
        columns = [desc[0] for desc in cursor.description]
        einsatz = dict(zip(columns, cursor.fetchone()))
        
        if not einsatz:
            flash('Einsatz nicht gefunden.', 'danger')
            return redirect(url_for('meine_einsaetze'))
        
        # Berechtigungsprüfung: Nur eigener Einsatz oder Admin
        if einsatz['benutzer_id'] != session['benutzer_id'] and not session.get('is_admin'):
            flash('Keine Berechtigung zum Stornieren dieses Einsatzes.', 'danger')
            return redirect(url_for('meine_einsaetze'))
        
        if request.method == 'POST':
            stornierungsgrund = request.form.get('stornierungsgrund', '')
            
            # Einsatz in Storno-Tabelle kopieren
            cursor.execute("""
                INSERT INTO maschineneinsaetze_storniert 
                (original_einsatz_id, datum, benutzer_id, maschine_id, einsatzzweck_id,
                 stundenzaehler_anfang, stundenzaehler_ende, betriebsstunden,
                 hektar, kilometer, stueck, treibstoffverbrauch, treibstoffkosten,
                 maschinenkosten, gesamtkosten, bemerkung, storniert_am, storniert_von, stornierungsgrund)
                SELECT id, datum, benutzer_id, maschine_id, einsatzzweck_id,
                       anfangstand, endstand, betriebsstunden,
                       flaeche_menge, flaeche_menge, flaeche_menge, treibstoffverbrauch, treibstoffkosten,
                       kosten_berechnet, (COALESCE(treibstoffkosten, 0) + COALESCE(kosten_berechnet, 0)), anmerkungen, ?, ?, ?
                FROM maschineneinsaetze
                WHERE id = ?
            """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                  session['benutzer_id'], 
                  stornierungsgrund, 
                  einsatz_id))
            
            # Original löschen
            cursor.execute("DELETE FROM maschineneinsaetze WHERE id = ?", (einsatz_id,))
            db.connection.commit()
            
            flash('Einsatz wurde erfolgreich storniert.', 'success')
            
            if session.get('is_admin'):
                return redirect(url_for('admin_alle_einsaetze'))
            else:
                return redirect(url_for('meine_einsaetze'))
        
        # GET - Bestätigungsformular anzeigen
        return render_template('einsatz_stornieren.html', einsatz=einsatz)


@app.route('/meine-stornierten-einsaetze')
@login_required
def meine_stornierten_einsaetze():
    """Liste aller eigenen stornierten Einsätze"""
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        
        cursor.execute("""
            SELECT s.*, m.bezeichnung as maschine_name,
                   b.name as benutzer_name, b.vorname as benutzer_vorname,
                   sv.name as storniert_von_name, sv.vorname as storniert_von_vorname,
                   ez.bezeichnung as einsatzzweck_name
            FROM maschineneinsaetze_storniert s
            JOIN maschinen m ON s.maschine_id = m.id
            JOIN benutzer b ON s.benutzer_id = b.id
            JOIN benutzer sv ON s.storniert_von = sv.id
            LEFT JOIN einsatzzwecke ez ON s.einsatzzweck_id = ez.id
            WHERE s.benutzer_id = ?
            ORDER BY s.storniert_am DESC
        """, (session['benutzer_id'],))
        
        columns = [desc[0] for desc in cursor.description]
        stornierte_einsaetze = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return render_template('meine_stornierten_einsaetze.html', 
                         stornierte_einsaetze=stornierte_einsaetze)


@app.route('/maschine/<int:maschine_id>/reservieren', methods=['GET', 'POST'])
@login_required
def maschine_reservieren(maschine_id):
    """Maschine reservieren"""
    from datetime import datetime, timedelta
    
    # Archiviere abgelaufene Reservierungen
    archiviere_abgelaufene_reservierungen()
    
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        maschine = db.get_maschine_by_id(maschine_id)
        
        if request.method == 'POST':
            datum = request.form.get('datum')
            uhrzeit_von = request.form.get('uhrzeit_von')
            nutzungsdauer = float(request.form.get('nutzungsdauer'))
            uhrzeit_bis = request.form.get('uhrzeit_bis')
            zweck = request.form.get('zweck')
            bemerkung = request.form.get('bemerkung')
            
            # Prüfen ob Zeitraum verfügbar ist
            cursor.execute("""
                SELECT COUNT(*) FROM maschinen_reservierungen
                WHERE maschine_id = ? 
                  AND datum = ?
                  AND status = 'aktiv'
                  AND (
                    (uhrzeit_von <= ? AND uhrzeit_bis > ?)
                    OR (uhrzeit_von < ? AND uhrzeit_bis >= ?)
                    OR (uhrzeit_von >= ? AND uhrzeit_bis <= ?)
                  )
            """, (maschine_id, datum, uhrzeit_von, uhrzeit_von, uhrzeit_bis, uhrzeit_bis, uhrzeit_von, uhrzeit_bis))
            
            if cursor.fetchone()[0] > 0:
                flash('Der gewählte Zeitraum überschneidet sich mit einer bestehenden Reservierung!', 'danger')
                return redirect(url_for('maschine_reservieren', maschine_id=maschine_id))
            
            # Reservierung erstellen
            cursor.execute("""
                INSERT INTO maschinen_reservierungen 
                (maschine_id, benutzer_id, datum, uhrzeit_von, uhrzeit_bis, nutzungsdauer_stunden, zweck, bemerkung)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (maschine_id, session['benutzer_id'], datum, uhrzeit_von, uhrzeit_bis, nutzungsdauer, zweck, bemerkung))
            
            db.connection.commit()
            flash(f'Maschine "{maschine["bezeichnung"]}" wurde erfolgreich für {datum} reserviert!', 'success')
            return redirect(url_for('dashboard'))
        
        # GET: Zeige Formular
        einsatzzwecke = db.get_all_einsatzzwecke()
        
        # Hole aktuelle und zukünftige Reservierungen
        cursor.execute("""
            SELECT r.*, b.name || ' ' || COALESCE(b.vorname, '') as benutzer_name
            FROM maschinen_reservierungen r
            JOIN benutzer b ON r.benutzer_id = b.id
            WHERE r.maschine_id = ? 
              AND r.datum >= date('now')
              AND r.status = 'aktiv'
            ORDER BY r.datum, r.uhrzeit_von
        """, (maschine_id,))
        
        columns = [desc[0] for desc in cursor.description]
        reservierungen = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Meine Reservierungen für diese Maschine
        cursor.execute("""
            SELECT * FROM maschinen_reservierungen
            WHERE maschine_id = ? 
              AND benutzer_id = ?
              AND datum >= date('now')
              AND status = 'aktiv'
            ORDER BY datum, uhrzeit_von
        """, (maschine_id, session['benutzer_id']))
        
        columns = [desc[0] for desc in cursor.description]
        meine_reservierungen = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return render_template('maschine_reservieren.html',
                         maschine=maschine,
                         einsatzzwecke=einsatzzwecke,
                         reservierungen=reservierungen,
                         meine_reservierungen=meine_reservierungen,
                         heute=datetime.now().strftime('%Y-%m-%d'))


@app.route('/reservierungen-kalender')
@login_required
def reservierungen_kalender():
    """Kalenderansicht aller Reservierungen (alle Maschinen)"""
    from datetime import datetime, timedelta
    
    # Optional: Maschinen-Filter
    maschine_id = request.args.get('maschine_id', type=int)
    
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        
        # Alle aktiven Maschinen für Filter
        maschinen = db.get_all_maschinen()
        
        # Reservierungen der nächsten 30 Tage laden
        heute = datetime.now()
        bis_datum = (heute + timedelta(days=30)).strftime('%Y-%m-%d')
        
        if maschine_id:
            cursor.execute("""
                SELECT r.*, m.bezeichnung as maschine_bezeichnung,
                       b.name || ' ' || COALESCE(b.vorname, '') as benutzer_name
                FROM maschinen_reservierungen r
                JOIN maschinen m ON r.maschine_id = m.id
                JOIN benutzer b ON r.benutzer_id = b.id
                WHERE r.maschine_id = ?
                  AND r.datum >= date('now')
                  AND r.datum <= ?
                  AND r.status = 'aktiv'
                ORDER BY r.datum, r.uhrzeit_von
            """, (maschine_id, bis_datum))
        else:
            cursor.execute("""
                SELECT r.*, m.bezeichnung as maschine_bezeichnung,
                       b.name || ' ' || COALESCE(b.vorname, '') as benutzer_name
                FROM maschinen_reservierungen r
                JOIN maschinen m ON r.maschine_id = m.id
                JOIN benutzer b ON r.benutzer_id = b.id
                WHERE r.datum >= date('now')
                  AND r.datum <= ?
                  AND r.status = 'aktiv'
                ORDER BY r.datum, m.bezeichnung, r.uhrzeit_von
            """, (bis_datum,))
        
        columns = [desc[0] for desc in cursor.description]
        reservierungen = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return render_template('reservierungen_kalender.html',
                         reservierungen=reservierungen,
                         maschinen=maschinen,
                         selected_maschine_id=maschine_id,
                         heute=heute.strftime('%Y-%m-%d'))


@app.route('/reservierungen-balken')
@login_required
def reservierungen_balken():
    """Balkendiagramm-Ansicht der Reservierungen (10 Tage)"""
    from datetime import datetime, timedelta
    
    # Zeitraum-Parameter
    tage = int(request.args.get('tage', 10))
    start_datum = request.args.get('start_datum')
    
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        
        # Alle aktiven Maschinen
        maschinen = db.get_all_maschinen()
        
        # Start- und Enddatum berechnen
        if start_datum:
            start = datetime.strptime(start_datum, '%Y-%m-%d')
        else:
            # Standard: Gestern starten, damit man auch vergangene Reservierungen sieht
            start = datetime.now() - timedelta(days=1)
        
        ende = start + timedelta(days=tage)
        
        # Alle Reservierungen im Zeitraum laden
        cursor.execute("""
            SELECT r.*, m.bezeichnung as maschine_bezeichnung,
                   b.name || ' ' || COALESCE(b.vorname, '') as benutzer_name
            FROM maschinen_reservierungen r
            JOIN maschinen m ON r.maschine_id = m.id
            JOIN benutzer b ON r.benutzer_id = b.id
            WHERE r.datum >= ?
              AND r.datum < ?
              AND r.status = 'aktiv'
            ORDER BY m.bezeichnung, r.datum, r.uhrzeit_von
        """, (start.strftime('%Y-%m-%d'), ende.strftime('%Y-%m-%d')))
        
        columns = [desc[0] for desc in cursor.description]
        reservierungen = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    # Tage für Timeline generieren
    tage_liste = []
    for i in range(tage):
        tag = start + timedelta(days=i)
        tage_liste.append({
            'datum': tag.strftime('%Y-%m-%d'),
            'tag': tag.strftime('%d.%m'),
            'wochentag': ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'][tag.weekday()]
        })
    
    return render_template('reservierungen_balken.html',
                         reservierungen=reservierungen,
                         maschinen=maschinen,
                         tage_liste=tage_liste,
                         start_datum=start.strftime('%Y-%m-%d'),
                         tage_anzahl=tage)


@app.route('/meine-reservierungen')
@login_required
def meine_reservierungen():
    """Übersicht aller eigenen Reservierungen"""
    from datetime import datetime
    
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        
        # Alle Reservierungen des Benutzers
        cursor.execute("""
            SELECT r.*, m.bezeichnung as maschine_bezeichnung
            FROM maschinen_reservierungen r
            JOIN maschinen m ON r.maschine_id = m.id
            WHERE r.benutzer_id = ?
              AND r.status = 'aktiv'
            ORDER BY r.datum, r.uhrzeit_von
        """, (session['benutzer_id'],))
        
        columns = [desc[0] for desc in cursor.description]
        reservierungen = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return render_template('meine_reservierungen.html', 
                         reservierungen=reservierungen,
                         today=datetime.now().strftime('%Y-%m-%d'))


@app.route('/reservierung/<int:reservierung_id>/stornieren', methods=['POST'])
@login_required
def reservierung_stornieren(reservierung_id):
    """Reservierung stornieren"""
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        
        # Reservierung vollständig laden
        cursor.execute("""
            SELECT r.*, m.bezeichnung as maschine_bezeichnung, 
                   b.name || ' ' || COALESCE(b.vorname, '') as benutzer_name
            FROM maschinen_reservierungen r
            JOIN maschinen m ON r.maschine_id = m.id
            JOIN benutzer b ON r.benutzer_id = b.id
            WHERE r.id = ? AND r.benutzer_id = ?
        """, (reservierung_id, session['benutzer_id']))
        
        result = cursor.fetchone()
        if not result:
            flash('Reservierung nicht gefunden oder keine Berechtigung!', 'danger')
            return redirect(url_for('dashboard'))
        
        # Als Dictionary speichern
        columns = [desc[0] for desc in cursor.description]
        reservierung = dict(zip(columns, result))
        maschine_id = reservierung['maschine_id']
        
        # In Archiv-Tabelle kopieren
        cursor.execute("""
            INSERT INTO reservierungen_geloescht 
            (reservierung_id, maschine_id, maschine_bezeichnung, benutzer_id, 
             benutzer_name, datum, uhrzeit_von, uhrzeit_bis, nutzungsdauer_stunden, 
             zweck, bemerkung, erstellt_am, geloescht_von, grund)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (reservierung_id, reservierung['maschine_id'], 
              reservierung['maschine_bezeichnung'], reservierung['benutzer_id'],
              reservierung['benutzer_name'], reservierung['datum'], 
              reservierung['uhrzeit_von'], reservierung['uhrzeit_bis'],
              reservierung['nutzungsdauer_stunden'], reservierung.get('zweck'),
              reservierung.get('bemerkung'), reservierung['erstellt_am'],
              session['benutzer_id'], 'Benutzer-Stornierung'))
        
        # Status auf 'storniert' setzen
        cursor.execute("""
            UPDATE maschinen_reservierungen
            SET status = 'storniert', geaendert_am = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (reservierung_id,))
        
        db.connection.commit()
        flash('Reservierung wurde storniert und archiviert.', 'success')
        
    return redirect(url_for('maschine_reservieren', maschine_id=maschine_id))


@app.route('/geloeschte-reservierungen')
@login_required
def geloeschte_reservierungen():
    """Übersicht aller gelöschten/stornierten Reservierungen"""
    from datetime import datetime
    
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        
        # Alle gelöschten Reservierungen des Benutzers
        cursor.execute("""
            SELECT * FROM reservierungen_geloescht
            WHERE benutzer_id = ?
            ORDER BY geloescht_am DESC
            LIMIT 100
        """, (session['benutzer_id'],))
        
        columns = [desc[0] for desc in cursor.description]
        geloeschte = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return render_template('geloeschte_reservierungen.html', 
                         geloeschte=geloeschte,
                         today=datetime.now().strftime('%Y-%m-%d'))


@app.route('/abgelaufene-reservierungen')
@login_required
def abgelaufene_reservierungen():
    """Übersicht aller abgelaufenen Reservierungen"""
    from datetime import datetime
    
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        
        # Alle abgelaufenen Reservierungen des Benutzers
        cursor.execute("""
            SELECT * FROM reservierungen_abgelaufen
            WHERE benutzer_id = ?
            ORDER BY abgelaufen_am DESC
            LIMIT 100
        """, (session['benutzer_id'],))
        
        columns = [desc[0] for desc in cursor.description]
        abgelaufene = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return render_template('abgelaufene_reservierungen.html', 
                         abgelaufene=abgelaufene,
                         today=datetime.now().strftime('%Y-%m-%d'))


@app.route('/api/maschine/<int:maschine_id>/stundenzaehler')
@login_required
def get_stundenzaehler(maschine_id):
    """API: Aktuellen Stundenzählerstand abrufen"""
    with MaschinenDBContext(DB_PATH) as db:
        maschine = db.get_maschine_by_id(maschine_id)
        if maschine:
            return {'success': True, 'stundenzaehler': maschine.get('stundenzaehler_aktuell', 0)}, 200
        return {'success': False}, 404


@app.route('/meine-einsaetze/csv')
@login_required
def meine_einsaetze_csv():
    """Exportiere eigene Einsätze als CSV"""
    with MaschinenDBContext(DB_PATH) as db:
        einsaetze = db.get_einsaetze_by_benutzer(session['benutzer_id'])
    
    # CSV in StringIO erstellen
    csv_buffer = StringIO()
    writer = csv.writer(csv_buffer, delimiter=';')
    
    # Header
    writer.writerow([
        'Datum', 'Benutzer', 'Maschine', 'Einsatzzweck',
        'Abrechnungsart', 'Preis pro Einheit',
        'Anfangstand', 'Endstand', 'Betriebsstunden',
        'Treibstoffverbrauch (l)', 'Treibstoffkosten (€)',
        'Fläche/Menge', 'Maschinenkosten (€)', 'Anmerkungen'
    ])
    
    # Daten
    def de_format(val, decimals=2):
        if val is None or val == '':
            return ''
        try:
            return f"{float(val):.{decimals}f}".replace('.', ',')
        except Exception:
            return str(val)

    def de_date(val):
        # Erwartet ISO-Format (YYYY-MM-DD) oder datetime-Objekt
        import datetime
        if not val:
            return ''
        if isinstance(val, datetime.date):
            return val.strftime('%d.%m.%Y')
        try:
            return datetime.datetime.strptime(str(val), '%Y-%m-%d').strftime('%d.%m.%Y')
        except Exception:
            return str(val)

    for e in einsaetze:
        writer.writerow([
            de_date(e.get('datum', '')),
            e.get('benutzer', ''),
            e.get('maschine', ''),
            e.get('einsatzzweck', ''),
            e.get('abrechnungsart', 'stunden'),
            de_format(e.get('preis_pro_einheit'), 2),
            de_format(e.get('anfangstand'), 1),
            de_format(e.get('endstand'), 1),
            de_format(e.get('betriebsstunden'), 1),
            de_format(e.get('treibstoffverbrauch'), 1),
            de_format(e.get('treibstoffkosten'), 2),
            de_format(e.get('flaeche_menge'), 1),
            de_format(e.get('kosten_berechnet'), 2),
            e.get('anmerkungen', '')
        ])
    
    # BytesIO für send_file
    csv_bytes = BytesIO(csv_buffer.getvalue().encode('utf-8-sig'))
    csv_bytes.seek(0)
    
    filename = f'meine_einsaetze_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    return send_file(
        csv_bytes,
        mimetype='text/csv; charset=utf-8',
        as_attachment=True,
        download_name=filename
    )


@app.route('/api/maschine/<int:maschine_id>')
@login_required
def api_maschine_details(maschine_id):
    """API-Endpunkt für Maschinen-Details (fÃ¼r AJAX)"""
    with MaschinenDBContext(DB_PATH) as db:
        maschine = db.get_maschine(maschine_id)
    
    if maschine:
        return {
            'success': True,
            'stundenzaehler': maschine['stundenzaehler_aktuell']
        }
    return {'success': False}, 404


@app.route('/nachrichten')
@login_required
def nachrichten():
    """Nachrichten der eigenen Gemeinschaften anzeigen"""
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        
        # Hole alle Nachrichten der Gemeinschaften, in denen der Benutzer Mitglied ist
        cursor.execute("""
            SELECT DISTINCT n.*, 
                   g.name as gemeinschaft_name,
                   b.name as absender_name, b.vorname as absender_vorname,
                   CASE WHEN ng.gelesen_am IS NOT NULL THEN 1 ELSE 0 END as gelesen
            FROM gemeinschafts_nachrichten n
            JOIN gemeinschaften g ON n.gemeinschaft_id = g.id
            JOIN benutzer b ON n.absender_id = b.id
            JOIN mitglied_gemeinschaft mg ON g.id = mg.gemeinschaft_id
            LEFT JOIN nachricht_gelesen ng ON n.id = ng.nachricht_id AND ng.benutzer_id = ?
            WHERE mg.mitglied_id = ?
            ORDER BY n.erstellt_am DESC
        """, (session['benutzer_id'], session['benutzer_id']))
        
        columns = [desc[0] for desc in cursor.description]
        nachrichten_list = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Zähle ungelesene Nachrichten
        ungelesen = sum(1 for n in nachrichten_list if not n['gelesen'])
    
    return render_template('nachrichten.html', 
                         nachrichten=nachrichten_list,
                         ungelesen=ungelesen)


@app.route('/nachricht/<int:nachricht_id>/lesen')
@login_required
def nachricht_lesen(nachricht_id):
    """Nachricht als gelesen markieren"""
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        
        # PrÃ¼fe ob Benutzer berechtigt ist
        cursor.execute("""
            SELECT n.* FROM gemeinschafts_nachrichten n
            JOIN mitglied_gemeinschaft mg ON n.gemeinschaft_id = mg.gemeinschaft_id
            WHERE n.id = ? AND mg.mitglied_id = ?
        """, (nachricht_id, session['benutzer_id']))
        
        if cursor.fetchone():
            # Als gelesen markieren
            cursor.execute("""
                INSERT OR IGNORE INTO nachricht_gelesen (nachricht_id, benutzer_id, gelesen_am)
                VALUES (?, ?, ?)
            """, (nachricht_id, session['benutzer_id'], datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            db.connection.commit()
    
    return redirect(url_for('nachrichten'))


@app.route('/nachricht/neu', methods=['GET', 'POST'])
@login_required
def nachricht_neu():
    """Neue Nachricht an Gemeinschaft senden"""
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        
        if request.method == 'POST':
            gemeinschaft_id = int(request.form.get('gemeinschaft_id'))
            betreff = request.form.get('betreff')
            nachricht = request.form.get('nachricht')
            
            # PrÃ¼fe ob Benutzer Mitglied der Gemeinschaft ist
            cursor.execute("""
                SELECT COUNT(*) FROM mitglied_gemeinschaft
                WHERE gemeinschaft_id = ? AND mitglied_id = ?
            """, (gemeinschaft_id, session['benutzer_id']))
            
            if cursor.fetchone()[0] > 0:
                cursor.execute("""
                    INSERT INTO gemeinschafts_nachrichten 
                    (gemeinschaft_id, absender_id, betreff, nachricht, erstellt_am)
                    VALUES (?, ?, ?, ?, ?)
                """, (gemeinschaft_id, session['benutzer_id'], betreff, nachricht,
                      datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                db.connection.commit()
                
                flash('Nachricht wurde an alle Mitglieder der Gemeinschaft gesendet!', 'success')
                return redirect(url_for('nachrichten'))
            else:
                flash('Sie sind nicht Mitglied dieser Gemeinschaft.', 'danger')
        
        # Hole Gemeinschaften des Benutzers
        cursor.execute("""
            SELECT DISTINCT g.* FROM gemeinschaften g
            JOIN mitglied_gemeinschaft mg ON g.id = mg.gemeinschaft_id
            WHERE mg.mitglied_id = ? AND g.aktiv = 1
            ORDER BY g.name
        """, (session['benutzer_id'],))
        
        columns = [desc[0] for desc in cursor.description]
        gemeinschaften = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return render_template('nachricht_neu.html', gemeinschaften=gemeinschaften)


@app.route('/admin/backup-bestaetigen', methods=['POST'])
@admin_required
def admin_backup_bestaetigen():
    """Backup-Durchführung bestätigen - Alle Administratoren können bestätigen"""
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        
        bemerkung = request.form.get('bemerkung', '')
        
        # Prüfe ob bereits eine offene Bestätigung existiert
        cursor.execute("""
            SELECT * FROM backup_bestaetigung
            WHERE status = 'wartend'
            AND datetime(zeitpunkt, '+24 hours') > datetime('now')
            ORDER BY zeitpunkt DESC
            LIMIT 1
        """)
        offene_bestaetigung = cursor.fetchone()
        
        if offene_bestaetigung:
            # Prüfe ob es vom selben Admin ist
            if offene_bestaetigung[1] == session['benutzer_id']:
                flash('Sie haben bereits eine Bestätigung abgegeben. Ein zweiter Administrator muss die Sicherung bestätigen.', 'warning')
                return redirect(url_for('admin_dashboard'))
            
            # Zweiter Admin bestätigt - Backup durchführen
            cursor.execute('SELECT COUNT(*) FROM maschineneinsaetze')
            anzahl_einsaetze = cursor.fetchone()[0]
            
            # Backup-Eintrag erstellen
            cursor.execute("""
                INSERT INTO backup_tracking 
                (letztes_backup, einsaetze_bei_backup, durchgefuehrt_von, bemerkung)
                VALUES (?, ?, ?, ?)
            """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                  anzahl_einsaetze,
                  f"{offene_bestaetigung[1]}, {session['benutzer_id']}",
                  f"Admin 1: {offene_bestaetigung[3] or 'keine'} | Admin 2: {bemerkung or 'keine'}"))
            
            # Status der Bestätigung auf 'abgeschlossen' setzen
            cursor.execute("""
                UPDATE backup_bestaetigung
                SET status = 'abgeschlossen'
                WHERE id = ?
            """, (offene_bestaetigung[0],))
            
            db.connection.commit()
            
            flash('Backup-Durchführung wurde von zwei Administratoren bestätigt. Warnung wird zurückgesetzt.', 'success')
        else:
            # Erster Admin bestätigt - warte auf zweiten
            cursor.execute("""
                INSERT INTO backup_bestaetigung 
                (admin_id, zeitpunkt, bemerkung, status)
                VALUES (?, ?, ?, 'wartend')
            """, (session['benutzer_id'],
                  datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                  bemerkung))
            
            db.connection.commit()
            
            flash('Ihre Bestätigung wurde gespeichert. Ein zweiter Haupt-Administrator muss die Sicherung innerhalb von 24 Stunden bestätigen.', 'info')
    
    return redirect(url_for('admin_dashboard'))


@app.route('/meine-abrechnungen')
@login_required
def meine_abrechnungen():
    """Zeigt alle Abrechnungen des angemeldeten Mitglieds"""
    benutzer_id = session.get('benutzer_id')
    
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        
        # Hole alle Abrechnungen für diesen Benutzer
        cursor.execute("""
            SELECT 
                ma.id,
                ma.zeitraum_von,
                ma.zeitraum_bis,
                ma.betrag_maschinen,
                ma.betrag_treibstoff,
                ma.status,
                ma.erstellt_am,
                ma.bezahlt_am,
                g.name as gemeinschaft_name,
                g.id as gemeinschaft_id
            FROM mitglieder_abrechnungen ma
            JOIN gemeinschaften g ON ma.gemeinschaft_id = g.id
            WHERE ma.benutzer_id = ?
            ORDER BY ma.erstellt_am DESC
        """, (benutzer_id,))
        
        abrechnungen = []
        for row in cursor.fetchall():
            abrechnungen.append({
                'id': row[0],
                'zeitraum_von': row[1],
                'zeitraum_bis': row[2],
                'betrag_maschinen': row[3],
                'betrag_treibstoff': row[4],
                'betrag_gesamt': row[3] + row[4],
                'status': row[5],
                'erstellt_am': row[6],
                'bezahlt_am': row[7],
                'gemeinschaft_name': row[8],
                'gemeinschaft_id': row[9]
            })
        
        # Berechne Statistiken
        summe_offen = sum(a['betrag_gesamt'] for a in abrechnungen if a['status'] == 'offen')
        summe_bezahlt = sum(a['betrag_gesamt'] for a in abrechnungen if a['status'] == 'bezahlt')
        anzahl_offen = sum(1 for a in abrechnungen if a['status'] == 'offen')
        
        return render_template('meine_abrechnungen.html',
                             abrechnungen=abrechnungen,
                             summe_offen=summe_offen,
                             summe_bezahlt=summe_bezahlt,
                             anzahl_offen=anzahl_offen)


@app.route('/abrechnung/<int:abrechnung_id>/pdf')
@login_required
def abrechnung_pdf(abrechnung_id):
    """Generiert PDF für eine Abrechnung"""
    benutzer_id = session.get('benutzer_id')
    
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        
        # Prüfe ob Abrechnung dem Benutzer gehört
        cursor.execute("""
            SELECT 
                ma.id,
                ma.zeitraum_von,
                ma.zeitraum_bis,
                ma.betrag_maschinen,
                ma.betrag_treibstoff,
                ma.status,
                ma.erstellt_am,
                g.name as gemeinschaft_name,
                g.bank_name,
                g.bank_iban,
                g.bank_bic,
                g.bank_kontoinhaber,
                b.name,
                b.vorname,
                b.email
            FROM mitglieder_abrechnungen ma
            JOIN gemeinschaften g ON ma.gemeinschaft_id = g.id
            JOIN benutzer b ON ma.benutzer_id = b.id
            WHERE ma.id = ? AND ma.benutzer_id = ?
        """, (abrechnung_id, benutzer_id))
        
        row = cursor.fetchone()
        if not row:
            flash('Abrechnung nicht gefunden!', 'danger')
            return redirect(url_for('meine_abrechnungen'))
        
        abrechnung = {
            'id': row[0],
            'zeitraum_von': row[1],
            'zeitraum_bis': row[2],
            'betrag_maschinen': row[3],
            'betrag_treibstoff': row[4],
            'betrag_gesamt': row[3] + row[4],
            'status': row[5],
            'erstellt_am': row[6],
            'gemeinschaft_name': row[7],
            'bank_name': row[8],
            'bank_iban': row[9],
            'bank_bic': row[10],
            'bank_kontoinhaber': row[11],
            'mitglied_name': f"{row[13]} {row[12]}",
            'mitglied_email': row[14]
        }
        
        # Hole Maschineneinsätze für diese Abrechnung (NUR Maschinen der Gemeinschaft!)
        # Hole zuerst die gemeinschaft_id aus der Abrechnung
        cursor.execute("SELECT gemeinschaft_id FROM mitglieder_abrechnungen WHERE id = ?", (abrechnung_id,))
        abrechnung_gemeinschaft_id = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT 
                m.bezeichnung,
                me.datum,
                me.endstand - me.anfangstand as betriebsstunden,
                m.preis_pro_einheit,
                me.kosten_berechnet,
                me.treibstoffverbrauch,
                me.treibstoffkosten,
                m.treibstoff_berechnen
            FROM maschineneinsaetze me
            JOIN maschinen m ON me.maschine_id = m.id
            WHERE me.benutzer_id = ? 
            AND me.datum >= ? 
            AND me.datum <= ?
            AND m.gemeinschaft_id = ?
            ORDER BY me.datum
        """, (benutzer_id, abrechnung['zeitraum_von'], abrechnung['zeitraum_bis'], abrechnung_gemeinschaft_id))
        
        einsaetze = []
        for row in cursor.fetchall():
            treibstoff_berechnen = row[7]
            einsaetze.append({
                'maschine': row[0],
                'datum': row[1],
                'betriebsstunden': row[2] if row[2] else 0,
                'preis_pro_stunde': row[3] if row[3] else 0,
                'betrag_maschine': row[4] if row[4] else 0,
                'treibstoff_liter': row[5] if treibstoff_berechnen and row[5] else 0,
                'treibstoffkosten': row[6] if treibstoff_berechnen and row[6] else 0,
                'treibstoff_berechnen': treibstoff_berechnen
            })
        
        # Einfaches HTML-PDF (ohne externe Library)
        html = render_template('abrechnung_pdf.html',
                             abrechnung=abrechnung,
                             einsaetze=einsaetze)
        
        response = make_response(html)
        response.headers['Content-Type'] = 'text/html'
        response.headers['Content-Disposition'] = f'inline; filename=Abrechnung_{abrechnung_id}.html'
        
        return response


@app.route('/passwort-aendern', methods=['GET', 'POST'])
@login_required
def passwort_aendern():
    """Passwort und Einstellungen Ã¤ndern"""
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        
        if form_type == 'passwort':
            # Passwort Ã¤ndern
            altes_passwort = request.form.get('altes_passwort')
            neues_passwort = request.form.get('neues_passwort')
            neues_passwort_wdh = request.form.get('neues_passwort_wdh')
            
            if neues_passwort != neues_passwort_wdh:
                flash('Die PasswÃ¶rter stimmen nicht Ã¼berein!', 'danger')
                return redirect(url_for('passwort_aendern'))
            
            with MaschinenDBContext(DB_PATH) as db:
                # Altes Passwort Ã¼berprÃ¼fen
                benutzer = db.get_benutzer(session['benutzer_id'])
                if not db.verify_login(benutzer['username'], altes_passwort):
                    flash('Altes Passwort ist falsch!', 'danger')
                    return redirect(url_for('passwort_aendern'))
                
                # Neues Passwort setzen
                db.update_password(session['benutzer_id'], neues_passwort)
                flash('Passwort wurde erfolgreich geÃ¤ndert!', 'success')
                return redirect(url_for('dashboard'))
        
        elif form_type == 'treibstoff':
            # Treibstoffkosten Ã¤ndern
            treibstoffkosten = request.form.get('treibstoffkosten_preis')
            try:
                treibstoffkosten = float(treibstoffkosten)
                with MaschinenDBContext(DB_PATH) as db:
                    cursor = db.connection.cursor()
                    cursor.execute(
                        "UPDATE benutzer SET treibstoffkosten_preis = ? WHERE id = ?",
                        (treibstoffkosten, session['benutzer_id'])
                    )
                    db.connection.commit()
                flash(f'Treibstoffkosten wurden auf {treibstoffkosten:.2f} EUR/L gesetzt!', 'success')
            except ValueError:
                flash('UngÃ¼ltiger Preis!', 'danger')
            return redirect(url_for('passwort_aendern'))
        
        elif form_type == 'backup_schwellwert':
            # Backup-Schwellwert Ã¤ndern (nur fÃ¼r Admins)
            if session.get('is_admin'):
                schwellwert = request.form.get('backup_schwellwert')
                try:
                    schwellwert = int(schwellwert)
                    if schwellwert < 1:
                        raise ValueError("Schwellwert muss mindestens 1 sein")
                    with MaschinenDBContext(DB_PATH) as db:
                        cursor = db.connection.cursor()
                        cursor.execute(
                            "UPDATE benutzer SET backup_schwellwert = ? WHERE id = ?",
                            (schwellwert, session['benutzer_id'])
                        )
                        db.connection.commit()
                    flash(f'Backup-Warnung wird nun nach {schwellwert} neuen EinsÃ¤tzen angezeigt!', 'success')
                except ValueError as e:
                    flash(f'UngÃ¼ltiger Wert: {str(e)}', 'danger')
            return redirect(url_for('passwort_aendern'))
    
    # GET: Zeige Formular mit aktuellen Werten
    with MaschinenDBContext(DB_PATH) as db:
        benutzer = db.get_benutzer(session['benutzer_id'])
    
    return render_template('passwort_aendern.html', benutzer=benutzer)


# ==================== ADMIN-BEREICH ====================

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin-Dashboard"""
    with MaschinenDBContext(DB_PATH) as db:
        # Alle Einsätze
        alle_einsaetze = db.get_all_einsaetze(limit=50)
        
        # Statistiken
        benutzer = db.get_all_benutzer()
        maschinen = db.get_all_maschinen()
        
        # Gesamt-Statistiken
        cursor = db.cursor
        cursor.execute("""
            SELECT 
                COUNT(*) as gesamt_einsaetze,
                SUM(betriebsstunden) as gesamt_stunden,
                SUM(treibstoffverbrauch) as gesamt_treibstoff
            FROM maschineneinsaetze
        """)
        gesamt_stats = dict(cursor.fetchone())
        
        # Backup-Status prüfen
        backup_warnung = False
        einsaetze_seit_backup = 0
        letztes_backup = None
        offene_bestaetigung = None
        
        # Hole Backup-Schwellwert des aktuellen Admins
        cursor.execute("""
            SELECT backup_schwellwert FROM benutzer WHERE id = ?
        """, (session['benutzer_id'],))
        schwellwert_row = cursor.fetchone()
        BACKUP_SCHWELLWERT = schwellwert_row[0] if schwellwert_row and schwellwert_row[0] else 50
        
        # Prüfe auf offene Backup-Bestätigung (für alle Admins)
        cursor.execute("""
            SELECT b.id, b.admin_id, b.zeitpunkt, b.bemerkung,
                   u.name, u.vorname
            FROM backup_bestaetigung b
            JOIN benutzer u ON b.admin_id = u.id
            WHERE b.status = 'wartend'
            AND datetime(b.zeitpunkt, '+24 hours') > datetime('now')
            ORDER BY b.zeitpunkt DESC
            LIMIT 1
        """)
        offene_row = cursor.fetchone()
        if offene_row:
            offene_bestaetigung = {
                'id': offene_row[0],
                'admin_id': offene_row[1],
                'zeitpunkt': offene_row[2],
                'bemerkung': offene_row[3],
                'admin_name': f"{offene_row[5]} {offene_row[4]}",
                'ist_eigene': offene_row[1] == session['benutzer_id']
            }
        
        cursor.execute("""
            SELECT letztes_backup, einsaetze_bei_backup
            FROM backup_tracking
            ORDER BY letztes_backup DESC
            LIMIT 1
        """)
        backup_row = cursor.fetchone()
        
        if backup_row:
            letztes_backup = backup_row[0]
            einsaetze_bei_letztem_backup = backup_row[1]
            aktuelle_einsaetze = gesamt_stats.get('gesamt_einsaetze', 0) or 0
            einsaetze_seit_backup = aktuelle_einsaetze - einsaetze_bei_letztem_backup
            
            if einsaetze_seit_backup >= BACKUP_SCHWELLWERT:
                backup_warnung = True
    
    return render_template('admin_dashboard.html',
                         einsaetze=alle_einsaetze,
                         benutzer=benutzer,
                         maschinen=maschinen,
                         stats=gesamt_stats,
                         backup_warnung=backup_warnung,
                         einsaetze_seit_backup=einsaetze_seit_backup,
                         letztes_backup=letztes_backup,
                         backup_schwellwert=BACKUP_SCHWELLWERT,
                         offene_bestaetigung=offene_bestaetigung)


@app.route('/admin/alle-einsaetze')
@admin_required
def admin_alle_einsaetze():
    """Alle Einsätze aller Benutzer"""
    with MaschinenDBContext(DB_PATH) as db:
        einsaetze = db.get_all_einsaetze()
    
    return render_template('admin_alle_einsaetze.html', einsaetze=einsaetze)


@app.route('/admin/stornierte-einsaetze')
@admin_required
def admin_stornierte_einsaetze():
    """Alle stornierten Einsätze"""
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        
        cursor.execute("""
            SELECT s.*, m.bezeichnung as maschine_name,
                   b.name as benutzer_name, b.vorname as benutzer_vorname,
                   sv.name as storniert_von_name, sv.vorname as storniert_von_vorname,
                   ez.bezeichnung as einsatzzweck_name
            FROM maschineneinsaetze_storniert s
            JOIN maschinen m ON s.maschine_id = m.id
            JOIN benutzer b ON s.benutzer_id = b.id
            JOIN benutzer sv ON s.storniert_von = sv.id
            LEFT JOIN einsatzzwecke ez ON s.einsatzzweck_id = ez.id
            ORDER BY s.storniert_am DESC
        """)
        
        columns = [desc[0] for desc in cursor.description]
        stornierte_einsaetze = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return render_template('admin_stornierte_einsaetze.html', 
                         stornierte_einsaetze=stornierte_einsaetze)


@app.route('/admin/benutzer')
@admin_required
def admin_benutzer():
    """Benutzerverwaltung"""
    with MaschinenDBContext(DB_PATH) as db:
        benutzer = db.get_all_benutzer(nur_aktive=False)
    
    return render_template('admin_benutzer.html', benutzer=benutzer)


@app.route('/admin/benutzer/neu', methods=['GET', 'POST'])
@admin_required
def admin_benutzer_neu():
    """Neuen Benutzer anlegen"""
    if request.method == 'POST':
        with MaschinenDBContext(DB_PATH) as db:
            db.add_benutzer(
                name=request.form['name'],
                vorname=request.form.get('vorname'),
                username=request.form.get('username'),
                password=request.form.get('password'),
                is_admin=bool(request.form.get('is_admin')),
                telefon=request.form.get('telefon'),
                email=request.form.get('email')
            )
        flash('Benutzer erfolgreich angelegt!', 'success')
        return redirect(url_for('admin_benutzer'))
    return render_template('admin_benutzer_form.html', benutzer=None)


@app.route('/admin/benutzer/<int:benutzer_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_benutzer_edit(benutzer_id):
    """Benutzer bearbeiten"""
    with MaschinenDBContext(DB_PATH) as db:
        if request.method == 'POST':
            update_data = {
                'name': request.form['name'],
                'vorname': request.form.get('vorname'),
                'username': request.form.get('username'),
                'is_admin': bool(request.form.get('is_admin')),
                'telefon': request.form.get('telefon'),
                'email': request.form.get('email')
            }
            # Passwort nur Ã¤ndern wenn angegeben
            if request.form.get('password'):
                db.update_password(benutzer_id, request.form['password'])
            db.update_benutzer(benutzer_id, **update_data)
            flash('Benutzer erfolgreich aktualisiert!', 'success')
            return redirect(url_for('admin_benutzer'))
        
        benutzer = db.get_benutzer_by_id(benutzer_id)
    return render_template('admin_benutzer_form.html', benutzer=benutzer)


@app.route('/admin/benutzer/<int:benutzer_id>/delete', methods=['POST'])
@admin_required
def admin_benutzer_delete(benutzer_id):
    """Benutzer lÃ¶schen"""
    with MaschinenDBContext(DB_PATH) as db:
        benutzer = db.get_benutzer_by_id(benutzer_id)
        # Hard delete: tatsÃ¤chlich aus Datenbank lÃ¶schen
        db.delete_benutzer(benutzer_id, soft_delete=False)
    flash(f'Benutzer {benutzer["name"]} wurde gelÃ¶scht.', 'success')
    return redirect(url_for('admin_benutzer'))


@app.route('/admin/benutzer/<int:benutzer_id>/activate', methods=['POST'])
@admin_required
def admin_benutzer_activate(benutzer_id):
    """Benutzer reaktivieren"""
    with MaschinenDBContext(DB_PATH) as db:
        benutzer = db.get_benutzer_by_id(benutzer_id)
        db.activate_benutzer(benutzer_id)
    flash(f'Benutzer {benutzer["name"]} wurde reaktiviert.', 'success')
    return redirect(url_for('admin_benutzer'))


@app.route('/admin/maschinen')
@admin_required
def admin_maschinen():
    """Maschinenverwaltung"""
    with MaschinenDBContext(DB_PATH) as db:
        maschinen = db.get_all_maschinen(nur_aktive=False)
    
    return render_template('admin_maschinen.html', maschinen=maschinen)


@app.route('/admin/maschinen/<int:maschine_id>/rentabilitaet')
@admin_required
def admin_maschinen_rentabilitaet(maschine_id):
    """RentabilitÃ¤tsbericht fÃ¼r eine Maschine"""
    from datetime import datetime
    
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.cursor
        # Maschine laden
        maschine = db.get_maschine_by_id(maschine_id)

        # Gesamteinsätze und Einnahmen
        cursor.execute("""
            SELECT 
                COUNT(e.id) as anzahl_einsaetze,
                SUM(e.endstand - e.anfangstand) as betriebsstunden_gesamt,
                SUM(
                    CASE 
                        WHEN m.abrechnungsart = 'stunden' THEN (e.endstand - e.anfangstand) * COALESCE(m.preis_pro_einheit, 0)
                        ELSE COALESCE(e.flaeche_menge, 0) * COALESCE(m.preis_pro_einheit, 0)
                    END
                ) as einnahmen_gesamt
            FROM maschineneinsaetze e
            JOIN maschinen m ON e.maschine_id = m.id
            WHERE m.id = ?
        """, (maschine_id,))
        row = cursor.fetchone()
        anzahl_einsaetze = row[0] or 0
        betriebsstunden = row[1] or 0
        einnahmen = row[2] or 0

        # Abschreibung berechnen
        anschaffungspreis = maschine.get('anschaffungspreis', 0) or 0
        abschreibungsdauer = maschine.get('abschreibungsdauer_jahre', 10) or 10
        anschaffungsdatum = maschine.get('anschaffungsdatum')
        abschreibung_pro_jahr = anschaffungspreis / abschreibungsdauer if abschreibungsdauer > 0 else 0
        alter_jahre_float = 0
        alter_jahre = 0
        alter_error = None
        if anschaffungsdatum:
            try:
                datum = datetime.strptime(anschaffungsdatum, '%Y-%m-%d')
                tage = (datetime.now() - datum).days
                alter_jahre_float = tage / 365.25
                alter_jahre = max(0, int(tage // 365))
            except Exception as e:
                alter_error = f"Ungültiges Anschaffungsdatum: {anschaffungsdatum} ({str(e)})"
                alter_jahre_float = 0
                alter_jahre = 0
        elif anschaffungsdatum is None or anschaffungsdatum == '':
            alter_error = "Kein Anschaffungsdatum hinterlegt"
        abschreibung_bisher = min(abschreibung_pro_jahr * alter_jahre_float, anschaffungspreis)
        restwert = max(anschaffungspreis - abschreibung_bisher, 0)

        # Für Template: Fehlertext und beide Alterswerte bereitstellen
        aufwendungen_gesamt = 0  # Vorinitialisierung, damit Variable immer existiert
        rentabilitaet = {
            'anschaffungspreis': anschaffungspreis,
            'abschreibungsdauer': abschreibungsdauer,
            'abschreibung_pro_jahr': abschreibung_pro_jahr,
            'alter_jahre': alter_jahre,
            'alter_jahre_float': alter_jahre_float,
            'alter_error': alter_error,
            'abschreibung_bisher': abschreibung_bisher,
            'restwert': restwert,
            'anzahl_einsaetze': anzahl_einsaetze,
            'betriebsstunden': betriebsstunden,
            'einnahmen_gesamt': einnahmen,
            'aufwendungen_gesamt': aufwendungen_gesamt,
            'bankkosten_gesamt': 0,  # wird später gesetzt
            'deckungsbeitrag': 0,   # wird später gesetzt,
        }

        # Aufwendungen laden (alle Jahre)
        cursor.execute("""
            SELECT 
                jahr,
                wartungskosten,
                reparaturkosten,
                versicherung,
                steuern,
                sonstige_kosten
            FROM maschinen_aufwendungen
            WHERE maschine_id = ?
            ORDER BY jahr
        """, (maschine_id,))
        columns = [desc[0] for desc in cursor.description]
        alle_aufwendungen = [dict(zip(columns, row)) for row in cursor.fetchall()]
        aufwendungen_gesamt = sum(
            a['wartungskosten'] + a['reparaturkosten'] + a['versicherung'] + 
            a['steuern'] + a['sonstige_kosten']
            for a in alle_aufwendungen
        )

        # Bankgebuchte Kosten (Buchungen mit referenz_typ='maschine')
        cursor.execute("""
            SELECT datum, betrag, beschreibung, typ FROM buchungen
            WHERE referenz_typ = 'maschine' AND referenz_id = ?
            ORDER BY datum
        """, (maschine_id,))
        bankbuchungen = [dict(zip([desc[0] for desc in cursor.description], row)) for row in cursor.fetchall()]
        bankkosten_gesamt = sum(b['betrag'] for b in bankbuchungen)

        # Einsätze pro Jahr
        cursor.execute("""
            SELECT 
                strftime('%Y', e.datum) as jahr,
                COUNT(e.id) as anzahl,
                SUM(e.endstand - e.anfangstand) as stunden,
                SUM(
                    CASE 
                        WHEN m.abrechnungsart = 'stunden' THEN (e.endstand - e.anfangstand) * COALESCE(m.preis_pro_einheit, 0)
                        ELSE COALESCE(e.flaeche_menge, 0) * COALESCE(m.preis_pro_einheit, 0)
                    END
                ) as einnahmen
            FROM maschineneinsaetze e
            JOIN maschinen m ON e.maschine_id = m.id
            WHERE m.id = ?
            GROUP BY jahr
            ORDER BY jahr DESC
        """, (maschine_id,))
        columns = [desc[0] for desc in cursor.description]
        einsaetze_pro_jahr = [dict(zip(columns, row)) for row in cursor.fetchall()]
        # Aufwendungen zu einsaetze_pro_jahr hinzufuegen
        aufwendungen_dict = {str(a['jahr']): a for a in alle_aufwendungen}
        for einsatz in einsaetze_pro_jahr:
            jahr = einsatz['jahr']
            if jahr in aufwendungen_dict:
                a = aufwendungen_dict[jahr]
                einsatz['aufwendungen'] = (
                    a['wartungskosten'] + a['reparaturkosten'] + 
                    a['versicherung'] + a['steuern'] + a['sonstige_kosten']
                )
            else:
                einsatz['aufwendungen'] = 0
            einsatz['gewinn'] = einsatz['einnahmen'] - einsatz['aufwendungen']

        # Gesamtkosten: Aufwendungen + Bankbuchungen
        gesamtkosten = aufwendungen_gesamt + bankkosten_gesamt
        # Rentabilität neu berechnen (Einnahmen - Abschreibung - Gesamtkosten)
        deckungsbeitrag = einnahmen - abschreibung_bisher - gesamtkosten
        rentabilitaet_prozent = (deckungsbeitrag / anschaffungspreis * 100) if anschaffungspreis > 0 else 0

        rentabilitaet = {
            'anzahl_einsaetze': anzahl_einsaetze,
            'betriebsstunden': betriebsstunden,
            'einnahmen_gesamt': einnahmen,
            'aufwendungen_gesamt': aufwendungen_gesamt,
            'bankkosten_gesamt': bankkosten_gesamt,
            'gesamtkosten': gesamtkosten,
            'anschaffungspreis': anschaffungspreis,
            'abschreibungsdauer': abschreibungsdauer,
            'abschreibung_pro_jahr': abschreibung_pro_jahr,
            'alter_jahre': alter_jahre,
            'abschreibung_bisher': abschreibung_bisher,
            'restwert': restwert,
            'deckungsbeitrag': deckungsbeitrag,
            'rentabilitaet_prozent': rentabilitaet_prozent
        }

    return render_template('admin_maschinen_rentabilitaet.html', 
                         maschine=maschine,
                         rentabilitaet=rentabilitaet,
                         einsaetze_pro_jahr=einsaetze_pro_jahr,
                         bankbuchungen=bankbuchungen)


@app.route('/admin/maschinen/<int:maschine_id>/rentabilitaet/pdf')
@admin_required
def admin_maschinen_rentabilitaet_pdf(maschine_id):
    """RentabilitÃ¤tsbericht als PDF exportieren"""
    from datetime import datetime
    from io import BytesIO
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import os
    
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.cursor
        maschine = db.get_maschine_by_id(maschine_id)
        
        # Alle Daten wie in der HTML-Ansicht laden
        cursor.execute("""
            SELECT 
                COUNT(e.id) as anzahl_einsaetze,
                SUM(e.endstand - e.anfangstand) as betriebsstunden_gesamt,
                SUM(
                    CASE 
                        WHEN m.abrechnungsart = 'stunden' THEN (e.endstand - e.anfangstand) * COALESCE(m.preis_pro_einheit, 0)
                        ELSE COALESCE(e.flaeche_menge, 0) * COALESCE(m.preis_pro_einheit, 0)
                    END
                ) as einnahmen_gesamt
            FROM maschineneinsaetze e
            JOIN maschinen m ON e.maschine_id = m.id
            WHERE m.id = ?
        """, (maschine_id,))
        
        row = cursor.fetchone()
        anzahl_einsaetze = row[0] or 0
        betriebsstunden = row[1] or 0
        einnahmen = row[2] or 0
        
        # Abschreibung
        anschaffungspreis = maschine.get('anschaffungspreis', 0) or 0
        abschreibungsdauer = maschine.get('abschreibungsdauer_jahre', 10) or 10
        anschaffungsdatum = maschine.get('anschaffungsdatum')
        abschreibung_pro_jahr = anschaffungspreis / abschreibungsdauer if abschreibungsdauer > 0 else 0
        
        alter_jahre_float = 0
        alter_jahre = 0
        alter_error = None
        if anschaffungsdatum:
            try:
                datum = datetime.strptime(anschaffungsdatum, '%Y-%m-%d')
                tage = (datetime.now() - datum).days
                alter_jahre_float = tage / 365.25
                alter_jahre = max(0, int(tage // 365))
            except Exception as e:
                alter_error = f"Ungültiges Anschaffungsdatum: {anschaffungsdatum} ({str(e)})"
                alter_jahre_float = 0
                alter_jahre = 0
        elif anschaffungsdatum is None or anschaffungsdatum == '':
            alter_error = "Kein Anschaffungsdatum hinterlegt"
        
        abschreibung_bisher = min(abschreibung_pro_jahr * alter_jahre, anschaffungspreis)
        restwert = max(anschaffungspreis - abschreibung_bisher, 0)
        
        # Aufwendungen
        cursor.execute("""
            SELECT jahr, wartungskosten, reparaturkosten, versicherung, steuern, sonstige_kosten
            FROM maschinen_aufwendungen
            WHERE maschine_id = ?
            ORDER BY jahr
        """, (maschine_id,))
        
        columns = [desc[0] for desc in cursor.description]
        alle_aufwendungen = [dict(zip(columns, row)) for row in cursor.fetchall()]
        aufwendungen_gesamt = sum(
            a['wartungskosten'] + a['reparaturkosten'] + a['versicherung'] + 
            a['steuern'] + a['sonstige_kosten'] for a in alle_aufwendungen
        )
        
        # Einsätze pro Jahr
        cursor.execute("""
            SELECT 
                strftime('%Y', e.datum) as jahr,
                COUNT(e.id) as anzahl,
                SUM(e.endstand - e.anfangstand) as stunden,
                SUM(
                    CASE 
                        WHEN m.abrechnungsart = 'stunden' THEN (e.endstand - e.anfangstand) * COALESCE(m.preis_pro_einheit, 0)
                        ELSE COALESCE(e.flaeche_menge, 0) * COALESCE(m.preis_pro_einheit, 0)
                    END
                ) as einnahmen
            FROM maschineneinsaetze e
            JOIN maschinen m ON e.maschine_id = m.id
            WHERE m.id = ?
            GROUP BY jahr
            ORDER BY jahr DESC
        """, (maschine_id,))
        
        columns = [desc[0] for desc in cursor.description]
        einsaetze_pro_jahr = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Aufwendungen zu Jahresübersicht hinzufügen
        aufwendungen_dict = {str(a['jahr']): a for a in alle_aufwendungen}
        for einsatz in einsaetze_pro_jahr:
            jahr = einsatz['jahr']
            if jahr in aufwendungen_dict:
                a = aufwendungen_dict[jahr]
                einsatz['aufwendungen'] = (a['wartungskosten'] + a['reparaturkosten'] + 
                                          a['versicherung'] + a['steuern'] + a['sonstige_kosten'])
            else:
                einsatz['aufwendungen'] = 0
            einsatz['gewinn'] = einsatz['einnahmen'] - einsatz['aufwendungen']
        
        deckungsbeitrag = einnahmen - abschreibung_bisher - aufwendungen_gesamt
        rentabilitaet_prozent = (deckungsbeitrag / anschaffungspreis * 100) if anschaffungspreis > 0 else 0
    
    # PDF erstellen
    # DejaVu Sans einbinden (für Umlaute)
    font_path = os.path.join(os.path.dirname(__file__), 'static', 'fonts', 'DejaVuSans.ttf')
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
        default_font = 'DejaVuSans'
    else:
        default_font = 'Helvetica'

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    
    elements = []
    styles = getSampleStyleSheet()
    # Standard-Schriftart auf DejaVu Sans setzen
    for style in styles.byName.values():
        style.fontName = default_font

    # Titel
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, spaceAfter=30, fontName=default_font)
    elements.append(Paragraph(f"Rentabilitätsbericht: {maschine['bezeichnung']}", title_style))
    elements.append(Paragraph(f"Erstellt am: {datetime.now().strftime('%d.%m.%Y %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))
    
    # Maschinendaten
    maschinen_data = [
        ['Hersteller:', maschine.get('hersteller', '-')],
        ['Modell:', maschine.get('modell', '-')],
        ['Baujahr:', str(maschine.get('baujahr', '-'))],
        ['Kennzeichen:', maschine.get('kennzeichen', '-')],
    ]

    maschinen_table = Table(maschinen_data, colWidths=[5*cm, 12*cm])
    maschinen_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), default_font),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(maschinen_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # Kennzahlen
    elements.append(Paragraph("Kennzahlen", styles['Heading2']))
    kennzahlen_data = [
        ['Anschaffungspreis:', f"{anschaffungspreis:.2f} €"],
        ['Restwert (aktuell):', f"{restwert:.2f} €"],
        ['Einnahmen gesamt:', f"{einnahmen:.2f} €"],
        ['Aufwendungen gesamt:', f"{aufwendungen_gesamt:.2f} €"],
        ['Deckungsbeitrag:', f"{deckungsbeitrag:.2f} €"],
        ['Rentabilität:', f"{rentabilitaet_prozent:.1f} %"],
    ]

    kennzahlen_table = Table(kennzahlen_data, colWidths=[10*cm, 7*cm])
    kennzahlen_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), default_font),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LINEABOVE', (0, -2), (-1, -2), 1, colors.black),
        ('BACKGROUND', (0, -2), (-1, -1), colors.lightgrey),
    ]))
    elements.append(kennzahlen_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # Abschreibung
    elements.append(Paragraph("Abschreibung", styles['Heading2']))
    abschreibung_data = [
        ['Abschreibungsdauer:', f"{abschreibungsdauer} Jahre"],
        ['Abschreibung (Jahr):', f"{abschreibung_pro_jahr:.2f} € pro Jahr"],
        ['Alter der Maschine:', f"{alter_jahre} Jahre (%.1f Jahre exakt)" % alter_jahre_float if not alter_error else alter_error],
        ['Abschreibung bisher (Info):', f"{abschreibung_bisher:.2f} €"],
    ]

    abschreibung_table = Table(abschreibung_data, colWidths=[10*cm, 7*cm])
    abschreibung_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), default_font),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(abschreibung_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # Jahresübersicht
    if einsaetze_pro_jahr:
        elements.append(Paragraph("Einsätze pro Jahr", styles['Heading2']))
        jahr_data = [['Jahr', 'Einsätze', 'Stunden', 'Einnahmen', 'Aufwend.', 'Gewinn']]
        for e in einsaetze_pro_jahr:
            jahr_data.append([
                e['jahr'],
                str(e['anzahl']),
                f"{e['stunden']:.1f}",
                f"{e['einnahmen']:.2f} €",
                f"{e['aufwendungen']:.2f} €",
                f"{e['gewinn']:.2f} €",
            ])

        jahr_table = Table(jahr_data, colWidths=[2*cm, 2*cm, 2.5*cm, 3.5*cm, 3.5*cm, 3.5*cm])
        jahr_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), default_font),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(jahr_table)
    
    # PDF generieren
    doc.build(elements)
    buffer.seek(0)
    
    return buffer.getvalue(), 200, {
        'Content-Type': 'application/pdf',
        'Content-Disposition': f'inline; filename="Rentabilitaet_{maschine["bezeichnung"]}_{datetime.now().strftime("%Y%m%d")}.pdf"'
    }


@app.route('/admin/maschinen/<int:maschine_id>/aufwendungen', methods=['GET', 'POST'])
@admin_required
def admin_maschinen_aufwendungen(maschine_id):
    """JÃ¤hrliche Aufwendungen fÃ¼r eine Maschine verwalten"""
    from datetime import datetime
    
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        maschine = db.get_maschine_by_id(maschine_id)
        aktuelles_jahr = datetime.now().year
        
        if request.method == 'POST':
            jahr = int(request.form.get('jahr', aktuelles_jahr))
            wartungskosten = float(request.form.get('wartungskosten', 0))
            reparaturkosten = float(request.form.get('reparaturkosten', 0))
            versicherung = float(request.form.get('versicherung', 0))
            steuern = float(request.form.get('steuern', 0))
            sonstige_kosten = float(request.form.get('sonstige_kosten', 0))
            bemerkung = request.form.get('bemerkung', '')
            
            # INSERT or UPDATE
            cursor.execute("""
                INSERT INTO maschinen_aufwendungen 
                (maschine_id, jahr, wartungskosten, reparaturkosten, versicherung, steuern, sonstige_kosten, bemerkung)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(maschine_id, jahr) DO UPDATE SET
                    wartungskosten = excluded.wartungskosten,
                    reparaturkosten = excluded.reparaturkosten,
                    versicherung = excluded.versicherung,
                    steuern = excluded.steuern,
                    sonstige_kosten = excluded.sonstige_kosten,
                    bemerkung = excluded.bemerkung,
                    geaendert_am = CURRENT_TIMESTAMP
            """, (maschine_id, jahr, wartungskosten, reparaturkosten, versicherung, steuern, sonstige_kosten, bemerkung))
            
            db.connection.commit()
            flash(f'Aufwendungen fÃ¼r {jahr} gespeichert.', 'success')
            return redirect(url_for('admin_maschinen_aufwendungen', maschine_id=maschine_id))
        
        # Aktuelle Aufwendungen laden
        cursor.execute("""
            SELECT * FROM maschinen_aufwendungen
            WHERE maschine_id = ? AND jahr = ?
        """, (maschine_id, aktuelles_jahr))
        
        row = cursor.fetchone()
        aktuelle_aufwendung = {}
        if row:
            columns = [desc[0] for desc in cursor.description]
            aktuelle_aufwendung = dict(zip(columns, row))
        
        # Historische Aufwendungen laden (auÃŸer aktuelles Jahr)
        cursor.execute("""
            SELECT * FROM maschinen_aufwendungen
            WHERE maschine_id = ? AND jahr != ?
            ORDER BY jahr DESC
        """, (maschine_id, aktuelles_jahr))
        
        columns = [desc[0] for desc in cursor.description]
        aufwendungen_historie = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Summen berechnen
        summe = {
            'wartungskosten': sum(a.get('wartungskosten', 0) for a in aufwendungen_historie),
            'reparaturkosten': sum(a.get('reparaturkosten', 0) for a in aufwendungen_historie),
            'versicherung': sum(a.get('versicherung', 0) for a in aufwendungen_historie),
            'steuern': sum(a.get('steuern', 0) for a in aufwendungen_historie),
            'sonstige_kosten': sum(a.get('sonstige_kosten', 0) for a in aufwendungen_historie)
        }
        summe['gesamt'] = sum(summe.values())
    
    return render_template('admin_maschinen_aufwendungen.html',
                         maschine=maschine,
                         aktuelles_jahr=aktuelles_jahr,
                         aktuelle_aufwendung=aktuelle_aufwendung,
                         aufwendungen_historie=aufwendungen_historie,
                         summe=summe)


@app.route('/admin/maschinen/<int:maschine_id>/aufwendungen/<int:jahr>/bearbeiten', methods=['POST'])
@admin_required
def admin_maschinen_aufwendungen_bearbeiten(maschine_id, jahr):
    """Bearbeite Aufwendungen eines vergangenen Jahres"""
    # Einfach zurÃ¼ck zur Hauptseite mit dem Jahr als vorbefÃ¼lltes Formular
    # (kÃ¶nnte spÃ¤ter erweitert werden)
    return redirect(url_for('admin_maschinen_aufwendungen', maschine_id=maschine_id))


@app.route('/admin/maschinen/neu', methods=['GET', 'POST'])
@admin_required
def admin_maschinen_neu():
    """Neue Maschine anlegen"""
    with MaschinenDBContext(DB_PATH) as db:
        if request.method == 'POST':
            maschine_id = db.add_maschine(
                bezeichnung=request.form['bezeichnung'],
                hersteller=request.form.get('hersteller'),
                modell=request.form.get('modell'),
                baujahr=int(request.form['baujahr']) if request.form.get('baujahr') else None,
                kennzeichen=request.form.get('kennzeichen'),
                stundenzaehler_aktuell=float(request.form.get('stundenzaehler_aktuell', 0)),
                wartungsintervall=int(request.form.get('wartungsintervall', 50)),
                naechste_wartung=float(request.form.get('naechste_wartung')) if request.form.get('naechste_wartung') else None,
                anmerkungen=request.form.get('anmerkungen'),
                abrechnungsart=request.form.get('abrechnungsart', 'stunden'),
                preis_pro_einheit=float(request.form.get('preis_pro_einheit', 0)),
                erfassungsmodus=request.form.get('erfassungsmodus', 'fortlaufend'),
                gemeinschaft_id=int(request.form['gemeinschaft_id']),
                anschaffungspreis=float(request.form.get('anschaffungspreis', 0)),
                abschreibungsdauer_jahre=int(request.form.get('abschreibungsdauer_jahre', 10)),
                anschaffungsdatum=request.form.get('anschaffungsdatum') if request.form.get('anschaffungsdatum') else None
            )
            
            # Treibstoff-Berechnungseinstellung setzen
            cursor = db.connection.cursor()
            treibstoff_berechnen = 1 if request.form.get('treibstoff_berechnen') else 0
            cursor.execute("""
                UPDATE maschinen 
                SET treibstoff_berechnen = ?
                WHERE id = ?
            """, (treibstoff_berechnen, maschine_id))
            
            flash('Maschine erfolgreich angelegt!', 'success')
            return redirect(url_for('admin_maschinen'))
        
        # Hole Gemeinschaften fÃ¼r Dropdown
        cursor = db.cursor
        cursor.execute("SELECT id, name FROM gemeinschaften WHERE aktiv = 1 ORDER BY name")
        gemeinschaften = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
        
    return render_template('admin_maschinen_form.html', maschine=None, gemeinschaften=gemeinschaften)


@app.route('/admin/maschinen/<int:maschine_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_maschinen_edit(maschine_id):
    """Maschine bearbeiten"""
    with MaschinenDBContext(DB_PATH) as db:
        if request.method == 'POST':
            update_data = {
                'bezeichnung': request.form['bezeichnung'],
                'hersteller': request.form.get('hersteller'),
                'modell': request.form.get('modell'),
                'baujahr': int(request.form['baujahr']) if request.form.get('baujahr') else None,
                'kennzeichen': request.form.get('kennzeichen'),
                'stundenzaehler_aktuell': float(request.form.get('stundenzaehler_aktuell', 0)),
                'wartungsintervall': int(request.form.get('wartungsintervall', 50)),
                'naechste_wartung': float(request.form.get('naechste_wartung')) if request.form.get('naechste_wartung') else None,
                'anmerkungen': request.form.get('anmerkungen'),
                'abrechnungsart': request.form.get('abrechnungsart', 'stunden'),
                'preis_pro_einheit': float(request.form.get('preis_pro_einheit', 0)),
                'erfassungsmodus': request.form.get('erfassungsmodus', 'fortlaufend'),
                'gemeinschaft_id': int(request.form['gemeinschaft_id']),
                'anschaffungspreis': float(request.form.get('anschaffungspreis', 0)),
                'abschreibungsdauer_jahre': int(request.form.get('abschreibungsdauer_jahre', 10)),
                'anschaffungsdatum': request.form.get('anschaffungsdatum') if request.form.get('anschaffungsdatum') else None
            }
            db.update_maschine(maschine_id, **update_data)
            
            # Treibstoff-Berechnungseinstellung separat aktualisieren
            cursor = db.connection.cursor()
            treibstoff_berechnen = 1 if request.form.get('treibstoff_berechnen') else 0
            cursor.execute("""
                UPDATE maschinen 
                SET treibstoff_berechnen = ?
                WHERE id = ?
            """, (treibstoff_berechnen, maschine_id))
            
            flash('Maschine erfolgreich aktualisiert!', 'success')
            return redirect(url_for('admin_maschinen'))
        
        maschine = db.get_maschine_by_id(maschine_id)
        
        # Hole treibstoff_berechnen Wert
        cursor = db.connection.cursor()
        cursor.execute("SELECT treibstoff_berechnen FROM maschinen WHERE id = ?", (maschine_id,))
        result = cursor.fetchone()
        maschine['treibstoff_berechnen'] = result[0] if result else 0
        
        # Hole Gemeinschaften fÃ¼r Dropdown
        cursor.execute("SELECT id, name FROM gemeinschaften WHERE aktiv = 1 ORDER BY name")
        gemeinschaften = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
        
    return render_template('admin_maschinen_form.html', maschine=maschine, gemeinschaften=gemeinschaften)


@app.route('/admin/maschinen/<int:maschine_id>/delete', methods=['POST'])
@admin_required
def admin_maschinen_delete(maschine_id):
    """Maschine lÃ¶schen"""
    with MaschinenDBContext(DB_PATH) as db:
        maschine = db.get_maschine_by_id(maschine_id)
        db.delete_maschine(maschine_id)
    flash(f'Maschine {maschine["bezeichnung"]} wurde gelÃ¶scht.', 'success')
    return redirect(url_for('admin_maschinen'))


@app.route('/admin/einsatzzwecke')
@admin_required
def admin_einsatzzwecke():
    """Einsatzzwecke verwalten"""
    with MaschinenDBContext(DB_PATH) as db:
        einsatzzwecke = db.get_all_einsatzzwecke(nur_aktive=False)
    
    return render_template('admin_einsatzzwecke.html', einsatzzwecke=einsatzzwecke)


@app.route('/admin/einsatzzwecke/neu', methods=['GET', 'POST'])
@admin_required
def admin_einsatzzwecke_neu():
    """Neuer Einsatzzweck"""
    if request.method == 'POST':
        with MaschinenDBContext(DB_PATH) as db:
            db.add_einsatzzweck(
                bezeichnung=request.form['bezeichnung'],
                beschreibung=request.form.get('beschreibung')
            )
        flash('Einsatzzweck erfolgreich angelegt!', 'success')
        return redirect(url_for('admin_einsatzzwecke'))
    
    return render_template('admin_einsatzzwecke_form.html', einsatzzweck=None)


@app.route('/admin/einsatzzwecke/<int:einsatzzweck_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_einsatzzwecke_edit(einsatzzweck_id):
    """Einsatzzweck bearbeiten"""
    with MaschinenDBContext(DB_PATH) as db:
        if request.method == 'POST':
            update_data = {
                'bezeichnung': request.form['bezeichnung'],
                'beschreibung': request.form.get('beschreibung'),
                'aktiv': 1 if request.form.get('aktiv') else 0
            }
            db.update_einsatzzweck(einsatzzweck_id, **update_data)
            flash('Einsatzzweck erfolgreich aktualisiert!', 'success')
            return redirect(url_for('admin_einsatzzwecke'))
        
        einsatzzweck = db.get_einsatzzweck_by_id(einsatzzweck_id)
    
    return render_template('admin_einsatzzwecke_form.html', einsatzzweck=einsatzzweck)


@app.route('/admin/einsatzzwecke/<int:einsatzzweck_id>/delete', methods=['POST'])
@admin_required
def admin_einsatzzwecke_delete(einsatzzweck_id):
    """Einsatzzweck lÃ¶schen"""
    with MaschinenDBContext(DB_PATH) as db:
        einsatzzweck = db.get_einsatzzweck_by_id(einsatzzweck_id)
        db.delete_einsatzzweck(einsatzzweck_id, soft_delete=False)
    flash(f'Einsatzzweck {einsatzzweck["bezeichnung"]} wurde gelÃ¶scht.', 'success')
    return redirect(url_for('admin_einsatzzwecke'))


# ==================== GEMEINSCHAFTEN-VERWALTUNG ====================

@app.route('/admin/gemeinschaften')
@admin_required
def admin_gemeinschaften():
    """Gemeinschaften verwalten"""
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.cursor
        cursor.execute("""
            SELECT * FROM gemeinschaften_uebersicht
            ORDER BY name
        """)
        columns = [desc[0] for desc in cursor.description]
        gemeinschaften = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return render_template('admin_gemeinschaften.html', gemeinschaften=gemeinschaften)


@app.route('/admin/gemeinschaften/neu', methods=['GET', 'POST'])
@admin_required
def admin_gemeinschaften_neu():
    """Neue Gemeinschaft"""
    if request.method == 'POST':
        with MaschinenDBContext(DB_PATH) as db:
            cursor = db.cursor
            cursor.execute("""
                INSERT INTO gemeinschaften (name, beschreibung, aktiv)
                VALUES (?, ?, ?)
            """, (
                request.form['name'],
                request.form.get('beschreibung'),
                1 if request.form.get('aktiv') else 0
            ))
            db.connection.commit()
        flash('Gemeinschaft erfolgreich angelegt!', 'success')
        return redirect(url_for('admin_gemeinschaften'))
    
    return render_template('admin_gemeinschaften_form.html', gemeinschaft=None)


@app.route('/admin/gemeinschaften/<int:gemeinschaft_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_gemeinschaften_edit(gemeinschaft_id):
    """Gemeinschaft bearbeiten"""
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.cursor
        
        if request.method == 'POST':
            cursor.execute("""
                UPDATE gemeinschaften 
                SET name = ?, 
                    beschreibung = ?, 
                    aktiv = ?,
                    bank_name = ?,
                    bank_iban = ?,
                    bank_bic = ?,
                    bank_kontoinhaber = ?
                WHERE id = ?
            """, (
                request.form['name'],
                request.form.get('beschreibung'),
                1 if request.form.get('aktiv') else 0,
                request.form.get('bank_name'),
                request.form.get('bank_iban'),
                request.form.get('bank_bic'),
                request.form.get('bank_kontoinhaber'),
                gemeinschaft_id
            ))
            db.connection.commit()
            flash('Gemeinschaft erfolgreich aktualisiert!', 'success')
            return redirect(url_for('admin_gemeinschaften'))
        
        cursor.execute("SELECT * FROM gemeinschaften WHERE id = ?", (gemeinschaft_id,))
        columns = [desc[0] for desc in cursor.description]
        gemeinschaft = dict(zip(columns, cursor.fetchone()))
    
    return render_template('admin_gemeinschaften_form.html', gemeinschaft=gemeinschaft)


@app.route('/admin/gemeinschaften/<int:gemeinschaft_id>/konten')
@admin_required
def admin_konten(gemeinschaft_id):
    """Mitgliederkonten-Übersicht"""
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        
        # Gemeinschaft laden
        cursor.execute("SELECT * FROM gemeinschaften WHERE id = ?", (gemeinschaft_id,))
        columns = [desc[0] for desc in cursor.description]
        gemeinschaft = dict(zip(columns, cursor.fetchone()))
        
        # Konten mit Details
        cursor.execute("""
            SELECT 
                mk.benutzer_id,
                b.vorname || ' ' || b.name as mitglied_name,
                b.email,
                mk.saldo,
                (SELECT COUNT(*) FROM mitglieder_abrechnungen 
                 WHERE benutzer_id = mk.benutzer_id 
                 AND gemeinschaft_id = mk.gemeinschaft_id 
                 AND status = 'offen') as offene_abrechnungen,
                (SELECT COUNT(*) FROM buchungen 
                 WHERE benutzer_id = mk.benutzer_id 
                 AND gemeinschaft_id = mk.gemeinschaft_id) as anzahl_buchungen,
                (SELECT MAX(datum) FROM buchungen 
                 WHERE benutzer_id = mk.benutzer_id 
                 AND gemeinschaft_id = mk.gemeinschaft_id) as letzte_buchung
            FROM mitglieder_konten mk
            JOIN benutzer b ON mk.benutzer_id = b.id
            WHERE mk.gemeinschaft_id = ?
            ORDER BY mk.saldo ASC
        """, (gemeinschaft_id,))
        
        columns = [desc[0] for desc in cursor.description]
        konten = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Statistiken
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN saldo > 0 THEN saldo ELSE 0 END) as guthaben,
                SUM(CASE WHEN saldo < 0 THEN saldo ELSE 0 END) as schulden,
                SUM(saldo) as saldo_gesamt,
                COUNT(CASE WHEN saldo > 0.01 THEN 1 END) as anzahl_guthaben,
                COUNT(CASE WHEN saldo < -0.01 THEN 1 END) as anzahl_schulden,
                COUNT(CASE WHEN saldo >= -0.01 AND saldo <= 0.01 THEN 1 END) as anzahl_ausgeglichen
            FROM mitglieder_konten
            WHERE gemeinschaft_id = ?
        """, (gemeinschaft_id,))
        
        stat_row = cursor.fetchone()
        statistik = {
            'guthaben': stat_row[0] or 0,
            'schulden': stat_row[1] or 0,
            'saldo_gesamt': stat_row[2] or 0,
            'anzahl_guthaben': stat_row[3] or 0,
            'anzahl_schulden': stat_row[4] or 0,
            'anzahl_ausgeglichen': stat_row[5] or 0
        }
        
        # Letzte 20 Buchungen
        cursor.execute("""
            SELECT 
                bu.datum,
                b.vorname || ' ' || b.name as mitglied_name,
                bu.typ,
                bu.beschreibung,
                bu.betrag,
                erstellt.vorname || ' ' || erstellt.name as erstellt_von
            FROM buchungen bu
            JOIN benutzer b ON bu.benutzer_id = b.id
            JOIN benutzer erstellt ON bu.erstellt_von = erstellt.id
            WHERE bu.gemeinschaft_id = ?
            ORDER BY bu.erstellt_am DESC
            LIMIT 20
        """, (gemeinschaft_id,))
        
        columns = [desc[0] for desc in cursor.description]
        letzte_buchungen = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return render_template('admin_konten.html', 
                         gemeinschaft=gemeinschaft,
                         konten=konten,
                         statistik=statistik,
                         letzte_buchungen=letzte_buchungen)


@app.route('/admin/gemeinschaften/<int:gemeinschaft_id>/konten/buchung-neu', methods=['GET', 'POST'])
@admin_required
def admin_konten_buchung_neu(gemeinschaft_id):
    """Neue manuelle Buchung erstellen"""
    benutzer_id = session.get('benutzer_id')
    
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        
        # Gemeinschaft laden
        cursor.execute("SELECT * FROM gemeinschaften WHERE id = ?", (gemeinschaft_id,))
        columns = [desc[0] for desc in cursor.description]
        gemeinschaft = dict(zip(columns, cursor.fetchone()))
        
        if request.method == 'POST':
            mitglied_id = request.form['benutzer_id']
            typ = request.form['typ']
            betrag_input = float(request.form['betrag'])
            datum = request.form['datum']
            beschreibung = request.form['beschreibung']
            
            # Betrag je nach Typ anpassen
            if typ == 'einzahlung':
                betrag = betrag_input  # Positiv = Guthaben für Mitglied
            elif typ == 'auszahlung':
                betrag = -betrag_input  # Negativ = Schulden für Mitglied
            elif typ == 'korrektur':
                # Bei Korrektur kann Admin entscheiden (hier positiv wie eingegeben)
                betrag = betrag_input
            else:
                flash('Ungültiger Buchungstyp!', 'danger')
                return redirect(url_for('admin_konten_buchung_neu', gemeinschaft_id=gemeinschaft_id))
            
            # Buchung erstellen
            cursor.execute("""
                INSERT INTO buchungen (
                    benutzer_id,
                    gemeinschaft_id,
                    datum,
                    betrag,
                    typ,
                    beschreibung,
                    referenz_typ,
                    erstellt_von
                ) VALUES (?, ?, ?, ?, ?, ?, 'manually', ?)
            """, (mitglied_id, gemeinschaft_id, datum, betrag, typ, beschreibung, benutzer_id))
            
            # Konto aktualisieren
            cursor.execute("""
                INSERT INTO mitglieder_konten (benutzer_id, gemeinschaft_id, saldo, saldo_vorjahr)
                VALUES (?, ?, ?, 0)
                ON CONFLICT(benutzer_id, gemeinschaft_id) 
                DO UPDATE SET 
                    saldo = saldo + ?,
                    letzte_aktualisierung = CURRENT_TIMESTAMP
            """, (mitglied_id, gemeinschaft_id, betrag, betrag))
            
            db.connection.commit()
            
            flash(f'Buchung erfolgreich erstellt: {betrag:,.2f} €', 'success')
            return redirect(url_for('admin_konten', gemeinschaft_id=gemeinschaft_id))
        
        # GET: Mitglieder mit aktuellen Salden laden
        cursor.execute("""
            SELECT 
                b.id,
                b.vorname || ' ' || b.name as name,
                COALESCE(mk.saldo, 0) as saldo
            FROM benutzer b
            JOIN mitglied_gemeinschaft mg ON b.id = mg.mitglied_id
            LEFT JOIN mitglieder_konten mk ON b.id = mk.benutzer_id 
                AND mk.gemeinschaft_id = mg.gemeinschaft_id
            WHERE mg.gemeinschaft_id = ?
            ORDER BY b.name
        """, (gemeinschaft_id,))
        
        columns = [desc[0] for desc in cursor.description]
        mitglieder = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        from datetime import datetime
        heute = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('admin_konten_buchung_neu.html',
                         gemeinschaft=gemeinschaft,
                         mitglieder=mitglieder,
                         heute=heute)


@app.route('/admin/gemeinschaften/<int:gemeinschaft_id>/konten/zahlung/<int:benutzer_id>', methods=['GET', 'POST'])
@admin_required
def admin_konten_zahlung(gemeinschaft_id, benutzer_id):
    """Zahlung für offene Abrechnungen verbuchen"""
    admin_id = session.get('benutzer_id')
    
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        
        # Gemeinschaft laden
        cursor.execute("SELECT * FROM gemeinschaften WHERE id = ?", (gemeinschaft_id,))
        columns = [desc[0] for desc in cursor.description]
        gemeinschaft = dict(zip(columns, cursor.fetchone()))
        
        cursor.execute("SELECT * FROM benutzer WHERE id = ?", (benutzer_id,))
        columns = [desc[0] for desc in cursor.description]
        mitglied = dict(zip(columns, cursor.fetchone()))
        
        if request.method == 'POST':
            betrag = float(request.form['betrag'])
            datum = request.form['datum']
            beschreibung = request.form.get('beschreibung', f'Zahlung von {mitglied["vorname"]} {mitglied["name"]}')
            
            # Einzahlungsbuchung
            cursor.execute("""
                INSERT INTO buchungen (
                    benutzer_id,
                    gemeinschaft_id,
                    datum,
                    betrag,
                    typ,
                    beschreibung,
                    referenz_typ,
                    erstellt_von
                ) VALUES (?, ?, ?, ?, 'einzahlung', ?, 'zahlung', ?)
            """, (benutzer_id, gemeinschaft_id, datum, betrag, beschreibung, admin_id))
            
            # Konto aktualisieren
            cursor.execute("""
                INSERT INTO mitglieder_konten (benutzer_id, gemeinschaft_id, saldo)
                VALUES (?, ?, ?)
                ON CONFLICT(benutzer_id, gemeinschaft_id) 
                DO UPDATE SET 
                    saldo = saldo + ?,
                    letzte_aktualisierung = CURRENT_TIMESTAMP
            """, (benutzer_id, gemeinschaft_id, betrag, betrag))
            
            # Prüfe ob damit Abrechnungen beglichen werden können
            cursor.execute("""
                SELECT id, betrag_gesamt 
                FROM mitglieder_abrechnungen
                WHERE benutzer_id = ? 
                AND gemeinschaft_id = ?
                AND status = 'offen'
                ORDER BY zeitraum_bis
            """, (benutzer_id, gemeinschaft_id))
            
            offene_abrechnungen = cursor.fetchall()
            verbleibend = betrag
            
            for abr_id, abr_betrag in offene_abrechnungen:
                if verbleibend >= abr_betrag:
                    # Abrechnung vollständig bezahlt
                    cursor.execute("""
                        UPDATE mitglieder_abrechnungen
                        SET status = 'bezahlt'
                        WHERE id = ?
                    """, (abr_id,))
                    verbleibend -= abr_betrag
                else:
                    break  # Nicht genug für diese Abrechnung
            
            db.connection.commit()
            
            flash(f'Zahlung von {betrag:,.2f} € erfolgreich verbucht!', 'success')
            return redirect(url_for('admin_konten', gemeinschaft_id=gemeinschaft_id))
        
        # GET: Offene Abrechnungen laden
        cursor.execute("""
            SELECT 
                id,
                zeitraum_von,
                zeitraum_bis,
                betrag_gesamt,
                erstellt_am
            FROM mitglieder_abrechnungen
            WHERE benutzer_id = ?
            AND gemeinschaft_id = ?
            AND status = 'offen'
            ORDER BY zeitraum_bis DESC
        """, (benutzer_id, gemeinschaft_id))
        
        columns = [desc[0] for desc in cursor.description]
        offene_abrechnungen = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Aktueller Saldo
        cursor.execute("""
            SELECT COALESCE(saldo, 0)
            FROM mitglieder_konten
            WHERE benutzer_id = ? AND gemeinschaft_id = ?
        """, (benutzer_id, gemeinschaft_id))
        saldo = cursor.fetchone()[0]
        
        from datetime import datetime
        heute = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('admin_konten_zahlung.html',
                         gemeinschaft=gemeinschaft,
                         mitglied=mitglied,
                         offene_abrechnungen=offene_abrechnungen,
                         saldo=saldo,
                         heute=heute)


@app.route('/admin/gemeinschaften/<int:gemeinschaft_id>/konten/detail/<int:benutzer_id>')
@admin_required
def admin_konten_detail(gemeinschaft_id, benutzer_id):
    """Detaillierter Kontoverlauf eines Mitglieds"""
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        
        # Gemeinschaft und Mitglied laden
        cursor.execute("SELECT * FROM gemeinschaften WHERE id = ?", (gemeinschaft_id,))
        columns = [desc[0] for desc in cursor.description]
        gemeinschaft = dict(zip(columns, cursor.fetchone()))
        
        cursor.execute("SELECT * FROM benutzer WHERE id = ?", (benutzer_id,))
        columns = [desc[0] for desc in cursor.description]
        mitglied = dict(zip(columns, cursor.fetchone()))
        
        # Konto und Saldo
        cursor.execute("""
            SELECT saldo, saldo_vorjahr
            FROM mitglieder_konten
            WHERE benutzer_id = ? AND gemeinschaft_id = ?
        """, (benutzer_id, gemeinschaft_id))
        konto_row = cursor.fetchone()
        saldo = konto_row[0] if konto_row else 0
        saldo_vorjahr = konto_row[1] if konto_row else 0
        
        # Buchungen
        cursor.execute("""
            SELECT 
                datum,
                typ,
                beschreibung,
                betrag,
                referenz_typ,
                referenz_id
            FROM buchungen
            WHERE benutzer_id = ? AND gemeinschaft_id = ?
            ORDER BY datum DESC, erstellt_am DESC
        """, (benutzer_id, gemeinschaft_id))
        
        columns = [desc[0] for desc in cursor.description]
        alle_bewegungen = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Statistiken
        cursor.execute("""
            SELECT COUNT(*) FROM mitglieder_abrechnungen
            WHERE benutzer_id = ? AND gemeinschaft_id = ? AND status = 'offen'
        """, (benutzer_id, gemeinschaft_id))
        offene_abrechnungen_count = cursor.fetchone()[0]
    
    return render_template('admin_konten_detail.html',
                         gemeinschaft=gemeinschaft,
                         mitglied=mitglied,
                         saldo=saldo,
                         saldo_vorjahr=saldo_vorjahr,
                         buchungen=alle_bewegungen,
                         offene_abrechnungen_count=offene_abrechnungen_count)


@app.route('/mein-konto/<int:gemeinschaft_id>')
@login_required
def mein_konto(gemeinschaft_id):
    """Mein Konto für eine Gemeinschaft"""
    benutzer_id = session.get('benutzer_id')
    
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        
        # Gemeinschaft laden
        cursor.execute("SELECT * FROM gemeinschaften WHERE id = ?", (gemeinschaft_id,))
        columns = [desc[0] for desc in cursor.description]
        gemeinschaft_row = cursor.fetchone()
        if not gemeinschaft_row:
            flash('Gemeinschaft nicht gefunden!', 'danger')
            return redirect(url_for('dashboard'))
        gemeinschaft = dict(zip(columns, gemeinschaft_row))
        
        # Prüfe ob Mitglied in dieser Gemeinschaft ist
        cursor.execute("""
            SELECT 1 FROM mitglied_gemeinschaft
            WHERE mitglied_id = ? AND gemeinschaft_id = ?
        """, (benutzer_id, gemeinschaft_id))
        if not cursor.fetchone():
            flash('Sie sind kein Mitglied dieser Gemeinschaft!', 'danger')
            return redirect(url_for('dashboard'))
        
        # Konto und Saldo
        cursor.execute("""
            SELECT saldo, saldo_vorjahr
            FROM mitglieder_konten
            WHERE benutzer_id = ? AND gemeinschaft_id = ?
        """, (benutzer_id, gemeinschaft_id))
        konto_row = cursor.fetchone()
        saldo = konto_row[0] if konto_row else 0
        saldo_vorjahr = konto_row[1] if konto_row else 0
        
        # Buchungen
        cursor.execute("""
            SELECT 
                datum,
                typ,
                beschreibung,
                betrag,
                referenz_typ,
                referenz_id
            FROM buchungen
            WHERE benutzer_id = ? AND gemeinschaft_id = ?
            ORDER BY datum DESC, erstellt_am DESC
        """, (benutzer_id, gemeinschaft_id))
        
        columns = [desc[0] for desc in cursor.description]
        buchungen = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Offene Abrechnungen
        cursor.execute("""
            SELECT 
                id,
                zeitraum_von,
                zeitraum_bis,
                betrag_maschinen,
                betrag_treibstoff,
                betrag_gesamt,
                erstellt_am
            FROM mitglieder_abrechnungen
            WHERE benutzer_id = ?
            AND gemeinschaft_id = ?
            AND status = 'offen'
            ORDER BY zeitraum_bis DESC
        """, (benutzer_id, gemeinschaft_id))
        offene_abrechnungen = []
        for row in cursor.fetchall():
            offene_abrechnungen.append({
                'id': row[0],
                'zeitraum_von': row[1],
                'zeitraum_bis': row[2],
                'betrag_maschinen': row[3],
                'betrag_treibstoff': row[4],
                'betrag_gesamt': row[5],
                'erstellt_am': row[6],
            })
    
    return render_template('mein_konto.html',
                         gemeinschaft=gemeinschaft,
                         saldo=saldo,
                         saldo_vorjahr=saldo_vorjahr,
                         buchungen=buchungen,
                         offene_abrechnungen=offene_abrechnungen)


@app.route('/admin/gemeinschaften/<int:gemeinschaft_id>/abrechnung')
@admin_required
def admin_gemeinschaften_abrechnung(gemeinschaft_id):
    """Abrechnung fÃ¼r eine Gemeinschaft"""
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.cursor
        
        # Gemeinschaft laden
        cursor.execute("SELECT * FROM gemeinschaften WHERE id = ?", (gemeinschaft_id,))
        columns = [desc[0] for desc in cursor.description]
        gemeinschaft = dict(zip(columns, cursor.fetchone()))
        
        # Abrechnung pro Mitglied (nur Maschinenkosten)
        cursor.execute("""
            SELECT 
                b.id,
                b.name,
                b.vorname,
                COUNT(e.id) as anzahl_einsaetze,
                SUM(e.endstand - e.anfangstand) as betriebsstunden,
                SUM(
                    CASE 
                        WHEN m.abrechnungsart = 'stunden' THEN (e.endstand - e.anfangstand) * COALESCE(m.preis_pro_einheit, 0)
                        ELSE COALESCE(e.flaeche_menge, 0) * COALESCE(m.preis_pro_einheit, 0)
                    END
                ) as einnahmen_gesamt
            FROM benutzer b
            JOIN mitglied_gemeinschaft mg ON b.id = mg.mitglied_id
            LEFT JOIN einsaetze e ON b.id = e.benutzer_id
            LEFT JOIN maschinen m ON e.maschine_id = m.id AND m.gemeinschaft_id = ?
            WHERE mg.gemeinschaft_id = ?
            GROUP BY b.id, b.name, b.vorname
            ORDER BY b.name, b.vorname
        """, (gemeinschaft_id, gemeinschaft_id))
        
        columns = [desc[0] for desc in cursor.description]
        mitglieder_abrechnung = []
        for row in cursor.fetchall():
            d = dict(zip(columns, row))
            d['gesamtkosten'] = d['maschinenkosten'] or 0
            mitglieder_abrechnung.append(d)
        
        # Gesamtsummen
        gesamtsummen = {
            'anzahl_einsaetze': sum(m['anzahl_einsaetze'] or 0 for m in mitglieder_abrechnung),
            'betriebsstunden': sum(m['betriebsstunden'] or 0 for m in mitglieder_abrechnung),
            'maschinenkosten': sum(m['maschinenkosten'] or 0 for m in mitglieder_abrechnung),
            'gesamtkosten': sum(m['gesamtkosten'] or 0 for m in mitglieder_abrechnung)
        }
    
    return render_template('admin_gemeinschaften_abrechnung.html', 
                         gemeinschaft=gemeinschaft,
                         mitglieder_abrechnung=mitglieder_abrechnung,
                         gesamtsummen=gesamtsummen)


@app.route('/admin/gemeinschaften/<int:gemeinschaft_id>/abrechnung/csv')
@admin_required
def admin_gemeinschaften_abrechnung_csv(gemeinschaft_id):
    """CSV Export der Gemeinschafts-Abrechnung"""
    import io
    from datetime import datetime
    
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.cursor
        
        # Gemeinschaft laden
        cursor.execute("SELECT * FROM gemeinschaften WHERE id = ?", (gemeinschaft_id,))
        columns = [desc[0] for desc in cursor.description]
        gemeinschaft = dict(zip(columns, cursor.fetchone()))
        
        # Abrechnung pro Mitglied (nur Maschinenkosten fÃ¼r CSV)
        cursor.execute("""
            SELECT 
                b.id,
                b.name,
                b.vorname,
                COUNT(e.id) as anzahl_einsaetze,
                SUM(e.endstand - e.anfangstand) as betriebsstunden,
                SUM(
                    CASE 
                        WHEN m.abrechnungsart = 'stunden' THEN (e.endstand - e.anfangstand) * COALESCE(m.preis_pro_einheit, 0)
                        ELSE COALESCE(e.flaeche_menge, 0) * COALESCE(m.preis_pro_einheit, 0)
                    END
                ) as maschinenkosten
            FROM benutzer b
            JOIN mitglied_gemeinschaft mg ON b.id = mg.mitglied_id
            LEFT JOIN einsaetze e ON b.id = e.benutzer_id
            LEFT JOIN maschinen m ON e.maschine_id = m.id AND m.gemeinschaft_id = ?
            WHERE mg.gemeinschaft_id = ?
            GROUP BY b.id, b.name, b.vorname
            ORDER BY b.name, b.vorname
        """, (gemeinschaft_id, gemeinschaft_id))
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
    
    # CSV erstellen
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    
    # Header
    writer.writerow([f'Abrechnung: {gemeinschaft["name"]}'])
    writer.writerow([f'Erstellt am: {datetime.now().strftime("%d.%m.%Y %H:%M")}'])
    writer.writerow([])
    writer.writerow(['Name', 'Vorname', 'Anzahl EinsÃ¤tze', 'Betriebsstunden', 
                    'Maschinenkosten (EUR)'])
    
    # Daten
    gesamt_einsaetze = 0
    gesamt_stunden = 0
    gesamt_maschinenkosten = 0
    
    for row in rows:
        maschinenkosten = row[5] or 0
        
        writer.writerow([
            row[1],  # name
            row[2],  # vorname
            row[3] or 0,  # anzahl_einsaetze
            f"{row[4] or 0:.1f}",  # betriebsstunden
            f"{maschinenkosten:.2f}"
        ])
        
        gesamt_einsaetze += row[3] or 0
        gesamt_stunden += row[4] or 0
        gesamt_maschinenkosten += maschinenkosten
    
    # Summenzeile
    writer.writerow([])
    writer.writerow(['GESAMT', '', gesamt_einsaetze, f"{gesamt_stunden:.1f}", 
                    f"{gesamt_maschinenkosten:.2f}"])
    
    # Response erstellen
    response = make_response(output.getvalue().encode('utf-8-sig'))
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename=abrechnung_{gemeinschaft["name"].replace(" ", "_")}_{datetime.now().strftime("%Y%m%d")}.csv'
    
    return response


@app.route('/admin/gemeinschaften/<int:gemeinschaft_id>/mitglieder', methods=['GET', 'POST'])
@admin_required
def admin_gemeinschaften_mitglieder(gemeinschaft_id):
    """Mitglieder einer Gemeinschaft verwalten"""
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.cursor
        
        if request.method == 'POST':
            action = request.form.get('action')
            
            if action == 'hinzufuegen':
                mitglieder = request.form.getlist('mitglieder')
                for mitglied_id in mitglieder:
                    cursor.execute("""
                        INSERT OR IGNORE INTO mitglied_gemeinschaft (mitglied_id, gemeinschaft_id)
                        VALUES (?, ?)
                    """, (mitglied_id, gemeinschaft_id))
                db.connection.commit()
                flash(f'{len(mitglieder)} Mitglied(er) hinzugefÃ¼gt!', 'success')
                
            elif action == 'entfernen':
                mitglieder = request.form.getlist('entfernen')
                for mitglied_id in mitglieder:
                    cursor.execute("""
                        DELETE FROM mitglied_gemeinschaft 
                        WHERE mitglied_id = ? AND gemeinschaft_id = ?
                    """, (mitglied_id, gemeinschaft_id))
                db.connection.commit()
                flash(f'{len(mitglieder)} Mitglied(er) entfernt!', 'success')
            
            return redirect(url_for('admin_gemeinschaften_mitglieder', gemeinschaft_id=gemeinschaft_id))
        
        # Hole Gemeinschaftsinfo
        cursor.execute("SELECT * FROM gemeinschaften WHERE id = ?", (gemeinschaft_id,))
        columns = [desc[0] for desc in cursor.description]
        gemeinschaft = dict(zip(columns, cursor.fetchone()))
        
        # Aktuelle Mitglieder
        cursor.execute("""
            SELECT b.* FROM benutzer b
            JOIN mitglied_gemeinschaft mg ON b.id = mg.mitglied_id
            WHERE mg.gemeinschaft_id = ? AND b.aktiv = 1
            ORDER BY b.name
        """, (gemeinschaft_id,))
        columns = [desc[0] for desc in cursor.description]
        aktuelle_mitglieder = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # VerfÃ¼gbare Benutzer (noch nicht in Gemeinschaft)
        cursor.execute("""
            SELECT b.* FROM benutzer b
            WHERE b.aktiv = 1 AND b.id NOT IN (
                SELECT mitglied_id FROM mitglied_gemeinschaft 
                WHERE gemeinschaft_id = ?
            )
            ORDER BY b.name
        """, (gemeinschaft_id,))
        columns = [desc[0] for desc in cursor.description]
        verfuegbare_benutzer = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return render_template('admin_gemeinschaften_mitglieder.html',
                         gemeinschaft=gemeinschaft,
                         aktuelle_mitglieder=aktuelle_mitglieder,
                         verfuegbare_benutzer=verfuegbare_benutzer)


@app.route('/admin/einsatzzwecke/<int:einsatzzweck_id>/activate', methods=['POST'])
@admin_required
def admin_einsatzzwecke_activate(einsatzzweck_id):
    """Einsatzzweck reaktivieren"""
    with MaschinenDBContext(DB_PATH) as db:
        einsatzzweck = db.get_einsatzzweck_by_id(einsatzzweck_id)
        db.activate_einsatzzweck(einsatzzweck_id)
    flash(f'Einsatzzweck {einsatzzweck["bezeichnung"]} wurde reaktiviert.', 'success')
    return redirect(url_for('admin_einsatzzwecke'))


@app.route('/admin/export/json')
@admin_required
def admin_export_json():
    """Alle Daten als JSON exportieren"""
    with MaschinenDBContext(DB_PATH) as db:
        data = {
            'export_datum': datetime.now().isoformat(),
            'benutzer': db.get_all_benutzer(nur_aktive=False),
            'maschinen': db.get_all_maschinen(nur_aktive=False),
            'einsatzzwecke': db.get_all_einsatzzwecke(nur_aktive=False),
            'einsaetze': db.get_all_einsaetze()
        }
    
    # JSON in BytesIO schreiben
    json_str = json.dumps(data, indent=2, ensure_ascii=False, default=str)
    json_bytes = BytesIO(json_str.encode('utf-8'))
    json_bytes.seek(0)
    
    filename = f'maschinengemeinschaft_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    return send_file(
        json_bytes,
        mimetype='application/json',
        as_attachment=True,
        download_name=filename
    )


@app.route('/admin/export/csv')
@admin_required
def admin_export_csv():
    """Alle Daten als CSV-ZIP exportieren"""
    with MaschinenDBContext(DB_PATH) as db:
        benutzer = db.get_all_benutzer(nur_aktive=False)
        maschinen = db.get_all_maschinen(nur_aktive=False)
        einsatzzwecke = db.get_all_einsatzzwecke(nur_aktive=False)
        einsaetze = db.get_all_einsaetze()
    
    # ZIP-Datei im Speicher erstellen
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Benutzer CSV
        if benutzer:
            csv_buffer = StringIO()
            writer = csv.DictWriter(csv_buffer, fieldnames=benutzer[0].keys())
            writer.writeheader()
            writer.writerows(benutzer)
            zip_file.writestr('benutzer.csv', csv_buffer.getvalue())
        
        # Maschinen CSV
        if maschinen:
            csv_buffer = StringIO()
            writer = csv.DictWriter(csv_buffer, fieldnames=maschinen[0].keys())
            writer.writeheader()
            writer.writerows(maschinen)
            zip_file.writestr('maschinen.csv', csv_buffer.getvalue())
        
        # Einsatzzwecke CSV
        if einsatzzwecke:
            csv_buffer = StringIO()
            writer = csv.DictWriter(csv_buffer, fieldnames=einsatzzwecke[0].keys())
            writer.writeheader()
            writer.writerows(einsatzzwecke)
            zip_file.writestr('einsatzzwecke.csv', csv_buffer.getvalue())
        
        # Einsätze CSV
        if einsaetze:
            csv_buffer = StringIO()
            writer = csv.DictWriter(csv_buffer, fieldnames=einsaetze[0].keys())
            writer.writeheader()
            writer.writerows(einsaetze)
            zip_file.writestr('einsaetze.csv', csv_buffer.getvalue())
    
    zip_buffer.seek(0)
    filename = f'maschinengemeinschaft_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
    
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=filename
    )


@app.route('/admin/backup/database')
@admin_required
def admin_backup_database():
    """Komplette SQLite-Datenbank herunterladen"""
    if not os.path.exists(DB_PATH):
        flash('Datenbankdatei nicht gefunden!', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    filename = f'maschinengemeinschaft_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    return send_file(
        DB_PATH,
        mimetype='application/x-sqlite3',
        as_attachment=True,
        download_name=filename
    )


@app.route('/admin/einsaetze/loeschen', methods=['GET', 'POST'])
@admin_required
def admin_einsaetze_loeschen():
    """Einsätze nach Zeitraum löschen"""
    if request.method == 'POST':
        von_datum = request.form.get('von_datum')
        bis_datum = request.form.get('bis_datum')
        bestaetigung = request.form.get('bestaetigung')
        
        if bestaetigung != 'LOESCHEN':
            flash('Bestätigung nicht korrekt. Bitte "LOESCHEN" eingeben.', 'danger')
            return redirect(url_for('admin_einsaetze_loeschen'))
        
        try:
            with MaschinenDBContext(DB_PATH) as db:
                # Zähle Einsätze im Zeitraum
                cursor = db.cursor
                cursor.execute("""
                    SELECT COUNT(*) FROM maschineneinsaetze 
                    WHERE datum BETWEEN ? AND ?
                """, (von_datum, bis_datum))
                anzahl = cursor.fetchone()[0]
                
                if anzahl == 0:
                    flash('Keine Einsätze im angegebenen Zeitraum gefunden.', 'warning')
                    return redirect(url_for('admin_einsaetze_loeschen'))
                
                # Lösche Einsätze
                cursor.execute("""
                    DELETE FROM maschineneinsaetze 
                    WHERE datum BETWEEN ? AND ?
                """, (von_datum, bis_datum))
                db.connection.commit()
                
                flash(f'{anzahl} Einsätze erfolgreich gelöscht!', 'success')
                return redirect(url_for('admin_dashboard'))
                
        except Exception as e:
            flash(f'Fehler beim Löschen: {str(e)}', 'danger')
            return redirect(url_for('admin_einsaetze_loeschen'))
    
    # GET - Zeige Formular
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.cursor
        # Hole ältesten und neuesten Einsatz
        cursor.execute("""
            SELECT MIN(datum) as min_datum, MAX(datum) as max_datum, COUNT(*) as anzahl
            FROM maschineneinsaetze
        """)
        zeitraum = cursor.fetchone()
    
    return render_template('admin_einsaetze_loeschen.html', zeitraum=zeitraum)


@app.route('/admin/backup')
@admin_required
def admin_database_backup():
    """Erstellt ein Backup der Datenbank als Download"""
    import shutil
    from datetime import datetime
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"maschinengemeinschaft_backup_{timestamp}.db"
        
        # Erstelle temporäres Backup
        import tempfile
        temp_dir = tempfile.gettempdir()
        temp_backup_path = os.path.join(temp_dir, backup_filename)
        
        # Kopiere Datenbank
        shutil.copy2(DB_PATH, temp_backup_path)
        
        # Sende als Download
        return send_file(
            temp_backup_path,
            as_attachment=True,
            download_name=backup_filename,
            mimetype='application/x-sqlite3'
        )
    except Exception as e:
        flash(f'Fehler beim Erstellen des Backups: {str(e)}', 'danger')
        return redirect(url_for('admin_dashboard'))


@app.route('/admin/restore', methods=['GET', 'POST'])
@hauptadmin_required
def admin_database_restore():
    """Datenbank-Wiederherstellung (nur Haupt-Administratoren)"""
    if request.method == 'POST':
        if 'backup_file' not in request.files:
            flash('Keine Datei ausgewählt!', 'danger')
            return redirect(url_for('admin_database_restore'))
        
        backup_file = request.files['backup_file']
        
        if backup_file.filename == '':
            flash('Keine Datei ausgewählt!', 'danger')
            return redirect(url_for('admin_database_restore'))
        
        if not backup_file.filename.endswith('.db'):
            flash('Ungültiges Dateiformat! Nur .db Dateien sind erlaubt.', 'danger')
            return redirect(url_for('admin_database_restore'))
        
        try:
            import shutil
            import tempfile
            
            # Speichere Upload temporär
            temp_dir = tempfile.gettempdir()
            temp_upload_path = os.path.join(temp_dir, 'temp_restore.db')
            backup_file.save(temp_upload_path)
            
            # Validiere dass es eine SQLite Datenbank ist
            try:
                import sqlite3
                test_conn = sqlite3.connect(temp_upload_path)
                test_cursor = test_conn.cursor()
                test_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = test_cursor.fetchall()
                test_conn.close()
                
                if not tables:
                    raise Exception("Keine Tabellen in der Datenbank gefunden")
            except Exception as e:
                os.remove(temp_upload_path)
                flash(f'Ungültige Datenbank-Datei: {str(e)}', 'danger')
                return redirect(url_for('admin_database_restore'))
            
            # Erstelle Backup der aktuellen Datenbank
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_current = f"{DB_PATH}.backup_{timestamp}"
            shutil.copy2(DB_PATH, backup_current)
            
            # Ersetze aktuelle Datenbank
            shutil.copy2(temp_upload_path, DB_PATH)
            os.remove(temp_upload_path)
            
            flash(f'Datenbank erfolgreich wiederhergestellt! Alte Datenbank gesichert als: {os.path.basename(backup_current)}', 'success')
            flash('WICHTIG: Bitte starten Sie die Anwendung neu!', 'warning')
            
            return redirect(url_for('admin_dashboard'))
            
        except Exception as e:
            flash(f'Fehler bei der Wiederherstellung: {str(e)}', 'danger')
            return redirect(url_for('admin_database_restore'))
    
    return render_template('admin_restore.html')


@app.route('/admin/export/alle-einsaetze-csv')
@admin_required
def admin_export_alle_einsaetze_csv():
    """Exportiert alle Einsätze als CSV für Jahresabschluss"""
    import io
    from datetime import datetime
    
    try:
        with MaschinenDBContext(DB_PATH) as db:
            cursor = db.cursor
            cursor.execute("""
                SELECT 
                    m.datum,
                    b.name as benutzer,
                    ma.name as maschine,
                    z.zweck as einsatzzweck,
                    ma.abrechnungsart,
                    ma.preis_pro_einheit,
                    m.flaeche_menge,
                    m.treibstoff_liter,
                    m.treibstoff_preis,
                    m.treibstoff_kosten,
                    m.kosten_berechnet as maschinenkosten,
                    (m.treibstoff_kosten + m.kosten_berechnet) as gesamtkosten,
                    m.stundenzaehler_start,
                    m.stundenzaehler_ende,
                    m.bemerkung
                FROM maschineneinsaetze m
                JOIN benutzer b ON m.benutzer_id = b.id
                JOIN maschinen ma ON m.maschine_id = ma.id
                JOIN einsatzzwecke z ON m.einsatzzweck_id = z.id
                ORDER BY m.datum DESC, m.id DESC
            """)
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
        
        # CSV erstellen
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')
        
        # Header
        writer.writerow(columns)
        
        # Daten
        for row in rows:
            writer.writerow(row)
        
        # Summenzeile
        writer.writerow([])
        writer.writerow(['GESAMT', '', '', '', '', '', '', '', '',
                        sum(r[9] for r in rows),  # Treibstoffkosten
                        sum(r[10] for r in rows),  # Maschinenkosten
                        sum(r[11] for r in rows),  # Gesamtkosten
                        '', '', ''])
        
        # Download vorbereiten
        output.seek(0)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        response = make_response(output.getvalue().encode('utf-8-sig'))
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=alle_einsaetze_{timestamp}.csv'
        
        return response
        
    except Exception as e:
        flash(f'Fehler beim Exportieren: {str(e)}', 'danger')
        return redirect(url_for('admin_dashboard'))


@app.route('/admin/rollen')
@hauptadmin_required
def admin_rollen():
    """Verwaltung von Admin-Rollen (nur fÃ¼r Haupt-Administratoren)"""
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        
        # Hole alle Benutzer mit ihren Rollen
        cursor.execute("""
            SELECT b.id, b.name, b.vorname, b.username, 
                   b.admin_level, b.is_admin,
                   GROUP_CONCAT(g.name, ', ') as gemeinschaften
            FROM benutzer b
            LEFT JOIN gemeinschafts_admin ga ON b.id = ga.benutzer_id
            LEFT JOIN gemeinschaften g ON ga.gemeinschaft_id = g.id
            WHERE b.aktiv = 1
            GROUP BY b.id, b.name, b.vorname, b.username, b.admin_level, b.is_admin
            ORDER BY b.admin_level DESC, b.name
        """)
        
        columns = [desc[0] for desc in cursor.description]
        benutzer = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Hole alle Gemeinschaften
        cursor.execute("SELECT * FROM gemeinschaften WHERE aktiv = 1 ORDER BY name")
        columns = [desc[0] for desc in cursor.description]
        gemeinschaften = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return render_template('admin_rollen.html', 
                         benutzer=benutzer, 
                         gemeinschaften=gemeinschaften)


@app.route('/admin/rollen/set-level', methods=['POST'])
@hauptadmin_required
def admin_rollen_set_level():
    """Admin-Level eines Benutzers setzen"""
    benutzer_id = int(request.form.get('benutzer_id'))
    level = int(request.form.get('level'))
    
    if level not in [0, 1, 2]:
        flash('UngÃ¼ltiger Admin-Level!', 'danger')
        return redirect(url_for('admin_rollen'))
    
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        
        # PrÃ¼fe, dass nicht der letzte Haupt-Admin entfernt wird
        if level < 2:
            cursor.execute('SELECT COUNT(*) FROM benutzer WHERE admin_level = 2 AND aktiv = 1')
            anzahl_haupt_admins = cursor.fetchone()[0]
            
            cursor.execute("SELECT admin_level FROM benutzer WHERE id = ?", (benutzer_id,))
            aktueller_level = cursor.fetchone()[0]
            
            if aktueller_level == 2 and anzahl_haupt_admins <= 2:
                flash('Es mÃ¼ssen mindestens 2 Haupt-Administratoren vorhanden bleiben!', 'danger')
                return redirect(url_for('admin_rollen'))
        
        # Level setzen
        cursor.execute("""
            UPDATE benutzer 
            SET admin_level = ?,
                is_admin = ?
            WHERE id = ?
        """, (level, 1 if level > 0 else 0, benutzer_id))
        
        db.connection.commit()
        
        level_text = {0: 'Kein Admin', 1: 'Gemeinschafts-Administrator', 2: 'Haupt-Administrator'}
        flash(f'Admin-Level auf "{level_text[level]}" gesetzt!', 'success')
    
    return redirect(url_for('admin_rollen'))


@app.route('/admin/rollen/add-gemeinschaft', methods=['POST'])
@hauptadmin_required
def admin_rollen_add_gemeinschaft():
    """Gemeinschafts-Admin-Rechte hinzufÃ¼gen"""
    benutzer_id = int(request.form.get('benutzer_id'))
    gemeinschaft_id = int(request.form.get('gemeinschaft_id'))
    
    with MaschinenDBContext(DB_PATH) as db:
        db.add_gemeinschafts_admin(benutzer_id, gemeinschaft_id)
        flash('Gemeinschafts-Admin-Rechte hinzugefÃ¼gt!', 'success')
    
    return redirect(url_for('admin_rollen'))


@app.route('/admin/rollen/remove-gemeinschaft', methods=['POST'])
@hauptadmin_required
def admin_rollen_remove_gemeinschaft():
    """Gemeinschafts-Admin-Rechte entfernen"""
    benutzer_id = int(request.form.get('benutzer_id'))
    gemeinschaft_id = int(request.form.get('gemeinschaft_id'))
    
    with MaschinenDBContext(DB_PATH) as db:
        db.remove_gemeinschafts_admin(benutzer_id, gemeinschaft_id)
        flash('Gemeinschafts-Admin-Rechte entfernt!', 'success')
    
    return redirect(url_for('admin_rollen'))


# ===== Abrechnungssystem für Gemeinschaftsadministratoren =====

@app.route('/admin/abrechnungen')
@admin_required
def admin_abrechnungen():
    """Abrechnungsübersicht für Gemeinschaftsadministratoren"""
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        
        # Gemeinschaften des Admins laden
        if session.get('admin_level', 0) >= 2:
            # Hauptadmin sieht alle Gemeinschaften
            cursor.execute("SELECT id, name FROM gemeinschaften WHERE aktiv = 1")
        else:
            # Gemeinschafts-Admin sieht nur seine Gemeinschaften
            cursor.execute(""" 
                SELECT g.id, g.name 
                FROM gemeinschaften g
                JOIN gemeinschafts_admin ga ON g.id = ga.gemeinschaft_id
                WHERE ga.benutzer_id = ? AND g.aktiv = 1
            """, (session['benutzer_id'],))
        
        gemeinschaften = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
        
        # Statistiken
        statistiken = {}
        for gem in gemeinschaften:
            cursor.execute(""" 
                SELECT 
                    COUNT(*) as anzahl_offen,
                    COALESCE(SUM(betrag_gesamt), 0) as summe_offen
                FROM mitglieder_abrechnungen
                WHERE gemeinschaft_id = ? AND status = 'offen'
            """, (gem['id'],))
            
            row = cursor.fetchone()
            statistiken[gem['id']] = {
                'anzahl_offen': row[0],
                'summe_offen': row[1]
            }
    
    return render_template('admin_abrechnungen.html',
                         gemeinschaften=gemeinschaften,
                         statistiken=statistiken)


@app.route('/admin/abrechnungen/<int:gemeinschaft_id>/erstellen', methods=['GET', 'POST'])
@admin_required
def abrechnungen_erstellen(gemeinschaft_id):
    """Erstellt Abrechnungen für alle Mitglieder einer Gemeinschaft"""
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        
        # Prüfe Berechtigung
        if session.get('admin_level', 0) < 2:
            cursor.execute(""" 
                SELECT COUNT(*) FROM gemeinschafts_admin
                WHERE benutzer_id = ? AND gemeinschaft_id = ?
            """, (session['benutzer_id'], gemeinschaft_id))
            if cursor.fetchone()[0] == 0:
                flash('Keine Berechtigung!', 'danger')
                return redirect(url_for('admin_abrechnungen'))
        
        if request.method == 'POST':
            zeitraum_von = request.form.get('zeitraum_von')
            zeitraum_bis = request.form.get('zeitraum_bis')
            
            if not zeitraum_von or not zeitraum_bis:
                flash('Bitte beide Datumsfelder ausfüllen!', 'warning')
                return redirect(request.url)
            
            # Erstelle Abrechnungszeitraum-String
            von_obj = datetime.strptime(zeitraum_von, '%Y-%m-%d')
            bis_obj = datetime.strptime(zeitraum_bis, '%Y-%m-%d')
            abrechnungszeitraum = f"{von_obj.strftime('%m/%Y')} - {bis_obj.strftime('%m/%Y')}"
            
            # Hole alle Mitglieder der Gemeinschaft
            cursor.execute(""" 
                SELECT DISTINCT b.id, b.name, b.vorname
                FROM benutzer b
                JOIN mitglied_gemeinschaft mg ON b.id = mg.mitglied_id
                WHERE mg.gemeinschaft_id = ?
                ORDER BY b.name
            """, (gemeinschaft_id,))
            mitglieder = cursor.fetchall()
            
            erstellt = 0
            uebersprungen = 0
            
            for mitglied in mitglieder:
                benutzer_id = mitglied[0]
                
                # Prüfe ob bereits Abrechnung für diesen Zeitraum existiert
                cursor.execute(""" 
                    SELECT COUNT(*) FROM mitglieder_abrechnungen
                    WHERE gemeinschaft_id = ? AND benutzer_id = ?
                    AND zeitraum_von = ? AND zeitraum_bis = ?
                """, (gemeinschaft_id, benutzer_id, zeitraum_von, zeitraum_bis))
                
                if cursor.fetchone()[0] > 0:
                    uebersprungen += 1
                    continue
                
                # Berechne Kosten für den Zeitraum (NUR Maschinen dieser Gemeinschaft!)
                # 1. Maschineneinsätze
                cursor.execute(""" 
                    SELECT COALESCE(SUM(me.kosten_berechnet), 0)
                    FROM maschineneinsaetze me
                    JOIN maschinen m ON me.maschine_id = m.id
                    WHERE me.benutzer_id = ? 
                    AND me.datum BETWEEN ? AND ?
                    AND m.gemeinschaft_id = ?
                """, (benutzer_id, zeitraum_von, zeitraum_bis, gemeinschaft_id))
                betrag_maschinen = cursor.fetchone()[0]
                
                # 2. Treibstoffkosten (nur für Maschinen mit treibstoff_berechnen = 1 UND dieser Gemeinschaft)
                cursor.execute(""" 
                    SELECT COALESCE(SUM(me.treibstoffkosten), 0)
                    FROM maschineneinsaetze me
                    JOIN maschinen m ON me.maschine_id = m.id
                    WHERE me.benutzer_id = ? 
                    AND me.datum BETWEEN ? AND ?
                    AND m.treibstoff_berechnen = 1
                    AND m.gemeinschaft_id = ?
                """, (benutzer_id, zeitraum_von, zeitraum_bis, gemeinschaft_id))
                betrag_treibstoff = cursor.fetchone()[0]
                
                betrag_gesamt = betrag_maschinen + betrag_treibstoff
                
                # Nur erstellen wenn Betrag > 0
                if betrag_gesamt > 0:
                    cursor.execute(""" 
                        INSERT INTO mitglieder_abrechnungen
                        (gemeinschaft_id, benutzer_id, abrechnungszeitraum,
                         zeitraum_von, zeitraum_bis, betrag_gesamt,
                         betrag_treibstoff, betrag_maschinen, betrag_sonstiges,
                         status, erstellt_von)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 'offen', ?)
                    """, (gemeinschaft_id, benutzer_id, abrechnungszeitraum,
                          zeitraum_von, zeitraum_bis, betrag_gesamt,
                          betrag_treibstoff, betrag_maschinen, session['benutzer_id']))
                    
                    abrechnung_id = cursor.lastrowid
                    
                    # Erstelle Buchung für diese Abrechnung
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
                        ) VALUES (?, ?, ?, ?, 'abrechnung', ?, 'abrechnung', ?, ?)
                    """, (
                        benutzer_id,
                        gemeinschaft_id,
                        zeitraum_bis,  # Buchungsdatum = Ende des Abrechnungszeitraums
                        -betrag_gesamt,  # Negativ = Mitglied schuldet der Gemeinschaft
                        f'Abrechnung #{abrechnung_id} für {abrechnungszeitraum}',
                        abrechnung_id,
                        session['benutzer_id']
                    ))
                    
                    # Aktualisiere Mitgliederkonto
                    cursor.execute(""" 
                        INSERT INTO mitglieder_konten (benutzer_id, gemeinschaft_id, saldo, saldo_vorjahr)
                        VALUES (?, ?, ?, 0)
                        ON CONFLICT(benutzer_id, gemeinschaft_id) 
                        DO UPDATE SET 
                            saldo = saldo + ?,
                            letzte_aktualisierung = CURRENT_TIMESTAMP
                    """, (benutzer_id, gemeinschaft_id, -betrag_gesamt, -betrag_gesamt))
                    
                    erstellt += 1
            
            db.connection.commit()
            
            # Detaillierte Rückmeldung
            if erstellt > 0:
                flash(f'✅ {erstellt} Abrechnung(en) erfolgreich erstellt', 'success')
            if uebersprungen > 0:
                flash(f'ℹ️ {uebersprungen} Abrechnung(en) bereits vorhanden (übersprungen)', 'info')
            if erstellt == 0 and uebersprungen == 0:
                flash(f'⚠️ Keine Maschineneinsätze im Zeitraum {zeitraum_von} bis {zeitraum_bis} gefunden. '
                      f'Bitte wählen Sie einen anderen Zeitraum.', 'warning')
            
            # Leite weiter zur Liste, auch wenn nichts erstellt wurde (damit User sieht was existiert)
            return redirect(url_for('abrechnungen_liste', gemeinschaft_id=gemeinschaft_id))
        
        # GET - Formular anzeigen
        cursor.execute("SELECT name FROM gemeinschaften WHERE id = ?", (gemeinschaft_id,))
        gemeinschaft_name = cursor.fetchone()[0]
        
        # Vorschlag für Zeitraum: Aktueller Monat (nicht letzter Monat!)
        # Da wir mitten im Monat sind, ist es wahrscheinlicher dass User aktuelle Einsätze abrechnen will
        heute = datetime.now()
        jahr = heute.year
        aktueller_monat = heute.month
        
        vorschlag_von = f"{jahr}-{aktueller_monat:02d}-01"
        
        # Letzter Tag des aktuellen Monats
        if aktueller_monat in [1, 3, 5, 7, 8, 10, 12]:
            letzter_tag = 31
        elif aktueller_monat in [4, 6, 9, 11]:
            letzter_tag = 30
        else:  # Februar
            if jahr % 4 == 0 and (jahr % 100 != 0 or jahr % 400 == 0):
                letzter_tag = 29
            else:
                letzter_tag = 28
        
        vorschlag_bis = f"{jahr}-{aktueller_monat:02d}-{letzter_tag}"
        
        # Hole Statistik über vorhandene Einsätze
        cursor.execute("""
            SELECT 
                MIN(datum) as erster_einsatz,
                MAX(datum) as letzter_einsatz,
                COUNT(*) as anzahl_einsaetze
            FROM maschineneinsaetze me
            JOIN mitglied_gemeinschaft mg ON me.benutzer_id = mg.mitglied_id
            WHERE mg.gemeinschaft_id = ?
        """, (gemeinschaft_id,))
        stats = cursor.fetchone()
        einsatz_info = {
            'erster': stats[0],
            'letzter': stats[1],
            'anzahl': stats[2]
        }
    
    return render_template('abrechnungen_erstellen.html',
                         gemeinschaft_id=gemeinschaft_id,
                         gemeinschaft_name=gemeinschaft_name,
                         vorschlag_von=vorschlag_von,
                         vorschlag_bis=vorschlag_bis,
                         einsatz_info=einsatz_info)


@app.route('/admin/abrechnungen/<int:gemeinschaft_id>/liste')
@admin_required
def abrechnungen_liste(gemeinschaft_id):
    """Liste aller Abrechnungen einer Gemeinschaft"""
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        
        # Prüfe Berechtigung
        if session.get('admin_level', 0) < 2:
            cursor.execute("""
                SELECT COUNT(*) FROM gemeinschafts_admin
                WHERE benutzer_id = ? AND gemeinschaft_id = ?
            """, (session['benutzer_id'], gemeinschaft_id))
            if cursor.fetchone()[0] == 0:
                flash('Keine Berechtigung!', 'danger')
                return redirect(url_for('admin_abrechnungen'))
        
        # Abrechnungen laden mit Zahlungsinformationen
        cursor.execute("""
            SELECT 
                ma.id, 
                ma.zeitraum_von,
                ma.zeitraum_bis,
                ma.betrag_maschinen,
                ma.betrag_treibstoff,
                ma.betrag_gesamt,
                ma.status,
                ma.erstellt_am,
                ma.bezahlt_am,
                ma.benutzer_id,
                b.name,
                b.vorname,
                b.email
            FROM mitglieder_abrechnungen ma
            JOIN benutzer b ON ma.benutzer_id = b.id
            WHERE ma.gemeinschaft_id = ?
            ORDER BY ma.erstellt_am DESC
        """, (gemeinschaft_id,))
        
        abrechnungen = []
        summe_maschinen = 0
        summe_treibstoff = 0
        
        for row in cursor.fetchall():
            betrag_maschinen = row[3] or 0
            betrag_treibstoff = row[4] or 0
            benutzer_id = row[9]
            
            # Hole Zahlungen für diese Abrechnung
            cursor.execute("""
                SELECT 
                    datum,
                    betrag,
                    beschreibung,
                    typ
                FROM buchungen
                WHERE benutzer_id = ?
                AND gemeinschaft_id = ?
                AND typ = 'einzahlung'
                AND datum >= ?
                ORDER BY datum DESC
                LIMIT 5
            """, (benutzer_id, gemeinschaft_id, row[1]))  # ab zeitraum_von
            
            zahlungen = []
            for z in cursor.fetchall():
                zahlungen.append({
                    'datum': z[0],
                    'betrag': z[1],
                    'beschreibung': z[2],
                    'typ': z[3]
                })
            
            abrechnungen.append({
                'id': row[0],
                'zeitraum_von': row[1],
                'zeitraum_bis': row[2],
                'betrag_maschinen': betrag_maschinen,
                'betrag_treibstoff': betrag_treibstoff,
                'betrag_gesamt': row[5],
                'status': row[6],
                'erstellt_am': row[7],
                'bezahlt_am': row[8],
                'mitglied_name': f"{row[11] or ''} {row[10]}".strip(),
                'mitglied_email': row[12],
                'zahlungen': zahlungen
            })
            
            summe_maschinen += betrag_maschinen
            summe_treibstoff += betrag_treibstoff
        
        cursor.execute("SELECT name FROM gemeinschaften WHERE id = ?", (gemeinschaft_id,))
        gemeinschaft_name = cursor.fetchone()[0]
    
    return render_template('abrechnungen_liste.html',
                         gemeinschaft_id=gemeinschaft_id,
                         gemeinschaft_name=gemeinschaft_name,
                         abrechnungen=abrechnungen,
                         summe_maschinen=summe_maschinen,
                         summe_treibstoff=summe_treibstoff)


@app.route('/admin/abrechnungen/<int:gemeinschaft_id>/csv-import', methods=['GET', 'POST'])
@admin_required
def admin_csv_import(gemeinschaft_id):
    """CSV-Import für Banktransaktionen mit konfigurierbarem Format"""
    import hashlib
    from io import StringIO
    from datetime import datetime as dt
    
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        
        # Prüfe Berechtigung
        if session.get('admin_level', 0) < 2:
            cursor.execute("""
                SELECT COUNT(*) FROM gemeinschafts_admin
                WHERE benutzer_id = ? AND gemeinschaft_id = ?
            """, (session['benutzer_id'], gemeinschaft_id))
            if cursor.fetchone()[0] == 0:
                flash('Keine Berechtigung für diese Gemeinschaft!', 'danger')
                return redirect(url_for('admin_abrechnungen'))
        
        # CSV-Konfiguration laden
        cursor.execute("""
            SELECT * FROM csv_import_konfiguration
            WHERE gemeinschaft_id = ?
        """, (gemeinschaft_id,))
        
        result = cursor.fetchone()
        if result:
            columns = [desc[0] for desc in cursor.description]
            config = dict(zip(columns, result))
        else:
            # Standard-Konfiguration erstellen
            cursor.execute("""
                INSERT INTO csv_import_konfiguration (gemeinschaft_id)
                VALUES (?)
            """, (gemeinschaft_id,))
            db.connection.commit()
            return redirect(request.url)
        
        if request.method == 'POST':
            # Konfiguration speichern
            cursor.execute("""
                UPDATE csv_import_konfiguration
                SET trennzeichen = ?,
                    kodierung = ?,
                    spalte_buchungsdatum = ?,
                    spalte_valutadatum = ?,
                    spalte_betrag = ?,
                    spalte_verwendungszweck = ?,
                    spalte_empfaenger = ?,
                    spalte_kontonummer = ?,
                    spalte_bic = ?,
                    dezimaltrennzeichen = ?,
                    tausendertrennzeichen = ?,
                    datumsformat = ?,
                    hat_kopfzeile = ?,
                    zeilen_ueberspringen = ?
                WHERE gemeinschaft_id = ?
            """, (
                request.form.get('trennzeichen'),
                request.form.get('kodierung'),
                request.form.get('spalte_buchungsdatum'),
                request.form.get('spalte_valutadatum'),
                request.form.get('spalte_betrag'),
                request.form.get('spalte_verwendungszweck'),
                request.form.get('spalte_empfaenger'),
                request.form.get('spalte_kontonummer'),
                request.form.get('spalte_bic'),
                request.form.get('dezimaltrennzeichen'),
                request.form.get('tausendertrennzeichen'),
                request.form.get('datumsformat'),
                1 if request.form.get('hat_kopfzeile') else 0,
                int(request.form.get('zeilen_ueberspringen', 0)),
                gemeinschaft_id
            ))
            
            db.connection.commit()
            flash('CSV-Konfiguration gespeichert!', 'success')
            return redirect(url_for('admin_csv_import', gemeinschaft_id=gemeinschaft_id))
        
        # Konfiguration laden
        cursor.execute("""
            SELECT * FROM csv_import_konfiguration
            WHERE gemeinschaft_id = ?
        """, (gemeinschaft_id,))
        
        result = cursor.fetchone()
        if result:
            columns = [desc[0] for desc in cursor.description]
            config = dict(zip(columns, result))
        else:
            # Standard-Konfiguration erstellen
            cursor.execute("""
                INSERT INTO csv_import_konfiguration (gemeinschaft_id)
                VALUES (?)
            """, (gemeinschaft_id,))
            db.connection.commit()
            return redirect(request.url)
        
        # Gemeinschaftsname laden
        cursor.execute("SELECT name FROM gemeinschaften WHERE id = ?", (gemeinschaft_id,))
        gemeinschaft_name = cursor.fetchone()[0]
    
    return render_template('admin_csv_import.html',
                         gemeinschaft_id=gemeinschaft_id,
                         gemeinschaft_name=gemeinschaft_name,
                         config=config)


@app.route('/admin/abrechnungen/<int:gemeinschaft_id>/transaktionen')
@admin_required
def admin_transaktionen(gemeinschaft_id):
    """Übersicht aller Transaktionen einer Gemeinschaft"""
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        
        # Prüfe Berechtigung
        if session.get('admin_level', 0) < 2:
            cursor.execute("""
                SELECT COUNT(*) FROM gemeinschafts_admin
                WHERE benutzer_id = ? AND gemeinschaft_id = ?
            """, (session['benutzer_id'], gemeinschaft_id))
            if cursor.fetchone()[0] == 0:
                flash('Keine Berechtigung für diese Gemeinschaft!', 'danger')
                return redirect(url_for('admin_abrechnungen'))
        
        # Filter-Parameter
        filter_typ = request.args.get('typ', 'alle')  # alle, eingaenge, ausgaenge, unzugeordnet
        
        # Transaktionen laden mit erweiterten Zuordnungsinfos
        query = """
            SELECT 
                t.*,
                b.name || ' ' || COALESCE(b.vorname, '') as benutzer_name,
                m.bezeichnung as maschine_name,
                g.name as gemeinschaft_name
            FROM bank_transaktionen t
            LEFT JOIN benutzer b ON t.benutzer_id = b.id
            LEFT JOIN maschinen m ON t.zuordnung_typ = 'maschine' AND t.zuordnung_id = m.id
            JOIN gemeinschaften g ON t.gemeinschaft_id = g.id
            WHERE t.gemeinschaft_id = ?
        """
        
        params = [gemeinschaft_id]
        
        if filter_typ == 'eingaenge':
            query += " AND t.betrag > 0"
        elif filter_typ == 'ausgaenge':
            query += " AND t.betrag < 0"
        elif filter_typ == 'unzugeordnet':
            query += " AND (t.zugeordnet = 0 OR t.zugeordnet IS NULL)"
        
        query += " ORDER BY t.buchungsdatum DESC, t.id DESC LIMIT 500"
        
        cursor.execute(query, params)
        
        columns = [desc[0] for desc in cursor.description]
        transaktionen = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Statistiken
        cursor.execute("""
            SELECT 
                COUNT(*) as anzahl_gesamt,
                COUNT(CASE WHEN zugeordnet = 1 THEN 1 END) as anzahl_zugeordnet,
                COALESCE(SUM(betrag), 0) as summe_gesamt,
                COALESCE(SUM(CASE WHEN zugeordnet = 1 THEN betrag ELSE 0 END), 0) as summe_zugeordnet,
                COALESCE(SUM(CASE WHEN betrag > 0 THEN betrag ELSE 0 END), 0) as summe_eingaenge,
                COALESCE(SUM(CASE WHEN betrag < 0 THEN betrag ELSE 0 END), 0) as summe_ausgaenge,
                COUNT(CASE WHEN betrag > 0 AND zugeordnet = 0 THEN 1 END) as unzugeordnete_eingaenge,
                COUNT(CASE WHEN betrag < 0 AND zugeordnet = 0 THEN 1 END) as unzugeordnete_ausgaenge
            FROM bank_transaktionen
            WHERE gemeinschaft_id = ?
        """, (gemeinschaft_id,))
        
        row = cursor.fetchone()
        
        # Anfangssaldo laden
        cursor.execute("""
            SELECT anfangssaldo_bank, anfangssaldo_datum
            FROM gemeinschaften
            WHERE id = ?
        """, (gemeinschaft_id,))
        saldo_row = cursor.fetchone()
        anfangssaldo = saldo_row[0] if saldo_row else 0.0
        anfangssaldo_datum = saldo_row[1] if saldo_row else None
        
        statistik = {
            'anzahl_gesamt': row[0],
            'anzahl_zugeordnet': row[1],
            'summe_gesamt': row[2],
            'summe_zugeordnet': row[3],
            'summe_eingaenge': row[4],
            'summe_ausgaenge': row[5],
            'unzugeordnete_eingaenge': row[6],
            'unzugeordnete_ausgaenge': row[7],
            'anfangssaldo': anfangssaldo,
            'anfangssaldo_datum': anfangssaldo_datum,
            'aktueller_saldo': anfangssaldo + row[2]
        }
        # Gemeinschaftsname laden
        cursor.execute("SELECT name FROM gemeinschaften WHERE id = ?", (gemeinschaft_id,))
        gemeinschaft_name = cursor.fetchone()[0]
        
        # Benutzer der Gemeinschaft laden (für Zuordnung)
        cursor.execute("""
            SELECT DISTINCT b.id, b.name, b.vorname
            FROM benutzer b
            JOIN mitglied_gemeinschaft mg ON b.id = mg.mitglied_id
            WHERE mg.gemeinschaft_id = ?
            ORDER BY b.name, b.vorname
        """, (gemeinschaft_id,))
        benutzer = [{'id': row[0], 'name': f"{row[1]} {row[2] or ''}"} for row in cursor.fetchall()]
        
        # Maschinen der Gemeinschaft laden
        cursor.execute("""
            SELECT id, bezeichnung
            FROM maschinen
            WHERE gemeinschaft_id = ?
            ORDER BY bezeichnung
        """, (gemeinschaft_id,))
        maschinen = [{'id': row[0], 'bezeichnung': row[1]} for row in cursor.fetchall()]
        
        # Import-Übersicht laden (für "Import löschen" Funktion)
        cursor.execute("""
            SELECT 
                date(importiert_am) as import_datum,
                importiert_von,
                COUNT(*) as anzahl,
                b.name || ' ' || COALESCE(b.vorname, '') as importiert_von_name
            FROM bank_transaktionen t
            LEFT JOIN benutzer b ON t.importiert_von = b.id
            WHERE t.gemeinschaft_id = ?
            GROUP BY date(importiert_am), importiert_von
            ORDER BY importiert_am DESC
        """, (gemeinschaft_id,))
        
        imports = []
        for row in cursor.fetchall():
            imports.append({
                'datum': row[0],
                'importiert_von_id': row[1],
                'anzahl': row[2],
                'importiert_von_name': row[3] or 'Unbekannt'
            })
    
    return render_template('admin_transaktionen.html',
                         gemeinschaft_id=gemeinschaft_id,
                         transaktionen=transaktionen,
                         statistik=statistik,
                         filter_typ=filter_typ,
                         benutzer=benutzer,
                         maschinen=maschinen,
                         imports=imports)


@app.route('/admin/abrechnungen/<int:gemeinschaft_id>/csv-konfiguration', methods=['GET', 'POST'])
@admin_required
def admin_csv_konfiguration(gemeinschaft_id):
    """CSV-Import-Format konfigurieren"""
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        
        # Prüfe Berechtigung
        if session.get('admin_level', 0) < 2:
            cursor.execute("""
                SELECT COUNT(*) FROM gemeinschafts_admin
                WHERE benutzer_id = ? AND gemeinschaft_id = ?
            """, (session['benutzer_id'], gemeinschaft_id))
            if cursor.fetchone()[0] == 0:
                flash('Keine Berechtigung für diese Gemeinschaft!', 'danger')
                return redirect(url_for('admin_abrechnungen'))
        
        if request.method == 'POST':
            # Konfiguration speichern
            cursor.execute("""
                UPDATE csv_import_konfiguration
                SET trennzeichen = ?,
                    kodierung = ?,
                    spalte_buchungsdatum = ?,
                    spalte_valutadatum = ?,
                    spalte_betrag = ?,
                    spalte_verwendungszweck = ?,
                    spalte_empfaenger = ?,
                    spalte_kontonummer = ?,
                    spalte_bic = ?,
                    dezimaltrennzeichen = ?,
                    tausendertrennzeichen = ?,
                    datumsformat = ?,
                    hat_kopfzeile = ?,
                    zeilen_ueberspringen = ?
                WHERE gemeinschaft_id = ?
            """, (
                request.form.get('trennzeichen'),
                request.form.get('kodierung'),
                request.form.get('spalte_buchungsdatum'),
                request.form.get('spalte_valutadatum'),
                request.form.get('spalte_betrag'),
                request.form.get('spalte_verwendungszweck'),
                request.form.get('spalte_empfaenger'),
                request.form.get('spalte_kontonummer'),
                request.form.get('spalte_bic'),
                request.form.get('dezimaltrennzeichen'),
                request.form.get('tausendertrennzeichen'),
                request.form.get('datumsformat'),
                1 if request.form.get('hat_kopfzeile') else 0,
                int(request.form.get('zeilen_ueberspringen', 0)),
                gemeinschaft_id
            ))
            
            db.connection.commit()
            flash('CSV-Konfiguration gespeichert!', 'success')
            return redirect(url_for('admin_csv_import', gemeinschaft_id=gemeinschaft_id))
        
        # Konfiguration laden
        cursor.execute("""
            SELECT * FROM csv_import_konfiguration
            WHERE gemeinschaft_id = ?
        """, (gemeinschaft_id,))
        
        result = cursor.fetchone()
        if result:
            columns = [desc[0] for desc in cursor.description]
            config = dict(zip(columns, result))
        else:
            # Standard-Konfiguration erstellen
            cursor.execute("""
                INSERT INTO csv_import_konfiguration (gemeinschaft_id)
                VALUES (?)
            """, (gemeinschaft_id,))
            db.connection.commit()
            return redirect(request.url)
        
        # Gemeinschaftsname laden
        cursor.execute("SELECT name FROM gemeinschaften WHERE id = ?", (gemeinschaft_id,))
        gemeinschaft_name = cursor.fetchone()[0]
    
    return render_template('admin_csv_konfiguration.html',
                         gemeinschaft_id=gemeinschaft_id,
                         gemeinschaft_name=gemeinschaft_name,
                         config=config)


@app.route('/admin/transaktion/<int:transaktion_id>/zuordnen', methods=['POST'])
@admin_required
def transaktion_zuordnen(transaktion_id):
    """Ordnet eine Transaktion einem Benutzer, einer Maschine oder Gemeinschaftskosten zu"""
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        
        # Transaktion laden
        cursor.execute("""
            SELECT gemeinschaft_id, betrag FROM bank_transaktionen
            WHERE id = ?
        """, (transaktion_id,))
        result = cursor.fetchone()
        if not result:
            flash('Transaktion nicht gefunden!', 'danger')
            return redirect(url_for('admin_abrechnungen'))
        
        gemeinschaft_id, betrag = result
        
        # Prüfe Berechtigung
        if session.get('admin_level', 0) < 2:
            cursor.execute("""
                SELECT COUNT(*) FROM gemeinschafts_admin
                WHERE benutzer_id = ? AND gemeinschaft_id = ?
            """, (session['benutzer_id'], gemeinschaft_id))
            if cursor.fetchone()[0] == 0:
                flash('Keine Berechtigung!', 'danger')
                return redirect(url_for('admin_transaktionen', gemeinschaft_id=gemeinschaft_id))
        
        zuordnung_typ = request.form.get('zuordnung_typ')
        
        if betrag > 0:  # EINGANG - Benutzer zuordnen
            benutzer_id = request.form.get('benutzer_id')
            if not benutzer_id:
                flash('Bitte Benutzer auswählen!', 'warning')
                return redirect(url_for('admin_transaktionen', gemeinschaft_id=gemeinschaft_id))
            
            # Update Transaktion
            cursor.execute("""
                UPDATE bank_transaktionen
                SET benutzer_id = ?, zugeordnet = 1, 
                    zuordnung_typ = 'benutzer', zuordnung_id = ?
                WHERE id = ?
            """, (benutzer_id, benutzer_id, transaktion_id))
            
            db.connection.commit()
            flash('✅ Eingang dem Benutzer zugeordnet', 'success')
            
        else:  # AUSGANG - Maschine oder Gemeinschaftskosten
            if zuordnung_typ == 'maschine':
                maschine_id = request.form.get('maschine_id')
                if not maschine_id:
                    flash('Bitte Maschine auswählen!', 'warning')
                    return redirect(url_for('admin_transaktionen', gemeinschaft_id=gemeinschaft_id))
                
                beschreibung = request.form.get('beschreibung', '')
                
                # Gemeinschaftskosten eintragen
                cursor.execute("""
                    INSERT INTO gemeinschafts_kosten
                    (gemeinschaft_id, transaktion_id, maschine_id, kategorie, betrag, datum, beschreibung, erstellt_von)
                    VALUES (?, ?, ?, 'maschine', ?, date('now'), ?, ?)
                """, (gemeinschaft_id, transaktion_id, maschine_id, abs(betrag), beschreibung, session['benutzer_id']))
                
                # Update Transaktion
                cursor.execute("""
                    UPDATE bank_transaktionen
                    SET zugeordnet = 1, zuordnung_typ = 'maschine', zuordnung_id = ?
                    WHERE id = ?
                """, (maschine_id, transaktion_id))
                
                db.connection.commit()
                flash('✅ Ausgang der Maschine zugeordnet', 'success')
                
            elif zuordnung_typ == 'gemeinschaft':
                kategorie = request.form.get('kategorie', 'sonstiges')
                beschreibung = request.form.get('beschreibung', '')
                
                # Gemeinschaftskosten eintragen
                cursor.execute("""
                    INSERT INTO gemeinschafts_kosten
                    (gemeinschaft_id, transaktion_id, kategorie, betrag, datum, beschreibung, erstellt_von)
                    VALUES (?, ?, ?, ?, date('now'), ?, ?)
                """, (gemeinschaft_id, transaktion_id, kategorie, abs(betrag), beschreibung, session['benutzer_id']))
                
                # Update Transaktion
                cursor.execute("""
                    UPDATE bank_transaktionen
                    SET zugeordnet = 1, zuordnung_typ = 'gemeinschaft', zuordnung_id = NULL
                    WHERE id = ?
                """, (transaktion_id,))
                
                db.connection.commit()
                flash('✅ Ausgang als Gemeinschaftskosten verbucht', 'success')
    
    return redirect(url_for('admin_transaktionen', gemeinschaft_id=gemeinschaft_id))


@app.route('/admin/transaktion/<int:transaktion_id>/zuordnung-aufheben', methods=['POST'])
@admin_required
def transaktion_zuordnung_aufheben(transaktion_id):
    """Hebt die Zuordnung einer Transaktion auf"""
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        
        # Transaktion laden
        cursor.execute("""
            SELECT gemeinschaft_id, zuordnung_typ, zuordnung_id
            FROM bank_transaktionen
            WHERE id = ?
        """, (transaktion_id,))
        result = cursor.fetchone()
        if not result:
            flash('Transaktion nicht gefunden!', 'danger')
            return redirect(url_for('admin_abrechnungen'))
        
        gemeinschaft_id, zuordnung_typ, zuordnung_id = result
        
        # Prüfe Berechtigung
        if session.get('admin_level', 0) < 2:
            cursor.execute("""
                SELECT COUNT(*) FROM gemeinschafts_admin
                WHERE benutzer_id = ? AND gemeinschaft_id = ?
            """, (session['benutzer_id'], gemeinschaft_id))
            if cursor.fetchone()[0] == 0:
                flash('Keine Berechtigung!', 'danger')
                return redirect(url_for('admin_transaktionen', gemeinschaft_id=gemeinschaft_id))
        
        # Zuordnung aufheben
        cursor.execute("""
            UPDATE bank_transaktionen
            SET zugeordnet = 0, zuordnung_typ = NULL, zuordnung_id = NULL, benutzer_id = NULL
            WHERE id = ?
        """, (transaktion_id,))
        
        # Gemeinschaftskosten löschen falls vorhanden
        if zuordnung_typ in ['maschine', 'gemeinschaft']:
            cursor.execute("""
                DELETE FROM gemeinschafts_kosten
                WHERE transaktion_id = ?
            """, (transaktion_id,))
        
        db.connection.commit()
        flash('✅ Zuordnung aufgehoben', 'info')
    
    return redirect(url_for('admin_transaktionen', gemeinschaft_id=gemeinschaft_id))


@app.route('/admin/transaktion/<int:transaktion_id>/loeschen', methods=['POST'])
@admin_required
def transaktion_loeschen(transaktion_id):
    """Löscht eine einzelne Transaktion"""
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        
        # Transaktion laden
        cursor.execute("""
            SELECT gemeinschaft_id, zuordnung_typ
            FROM bank_transaktionen
            WHERE id = ?
        """, (transaktion_id,))
        result = cursor.fetchone()
        if not result:
            flash('Transaktion nicht gefunden!', 'danger')
            return redirect(url_for('admin_abrechnungen'))
        
        gemeinschaft_id, zuordnung_typ = result
        
        # Prüfe Berechtigung
        if session.get('admin_level', 0) < 2:
            cursor.execute("""
                SELECT COUNT(*) FROM gemeinschafts_admin
                WHERE benutzer_id = ? AND gemeinschaft_id = ?
            """, (session['benutzer_id'], gemeinschaft_id))
            if cursor.fetchone()[0] == 0:
                flash('Keine Berechtigung!', 'danger')
                return redirect(url_for('admin_transaktionen', gemeinschaft_id=gemeinschaft_id))
        
        # Gemeinschaftskosten löschen falls vorhanden
        if zuordnung_typ in ['maschine', 'gemeinschaft']:
            cursor.execute("""
                DELETE FROM gemeinschafts_kosten
                WHERE transaktion_id = ?
            """, (transaktion_id,))
        
        # Transaktion löschen
        cursor.execute("""
            DELETE FROM bank_transaktionen
            WHERE id = ?
        """, (transaktion_id,))
        
        db.connection.commit()
        flash('✅ Transaktion gelöscht', 'success')
    
    return redirect(url_for('admin_transaktionen', gemeinschaft_id=gemeinschaft_id))


@app.route('/admin/abrechnungen/<int:gemeinschaft_id>/import-loeschen', methods=['POST'])
@admin_required
def import_loeschen(gemeinschaft_id):
    """Löscht alle Transaktionen eines bestimmten Imports"""
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        
        # Prüfe Berechtigung
        if session.get('admin_level', 0) < 2:
            cursor.execute("""
                SELECT COUNT(*) FROM gemeinschafts_admin
                WHERE benutzer_id = ? AND gemeinschaft_id = ?
            """, (session['benutzer_id'], gemeinschaft_id))
            if cursor.fetchone()[0] == 0:
                flash('Keine Berechtigung für diese Gemeinschaft!', 'danger')
                return redirect(url_for('admin_transaktionen', gemeinschaft_id=gemeinschaft_id))
        
        import_datum = request.form.get('import_datum')
        importiert_von = request.form.get('importiert_von')
        
        if not import_datum or not importiert_von:
            flash('Fehlende Parameter!', 'danger')
            return redirect(url_for('admin_transaktionen', gemeinschaft_id=gemeinschaft_id))
        
        # Zähle zu löschende Transaktionen
        cursor.execute("""
            SELECT COUNT(*) FROM bank_transaktionen
            WHERE gemeinschaft_id = ?
            AND date(importiert_am) = ?
            AND importiert_von = ?
        """, (gemeinschaft_id, import_datum, importiert_von))
        anzahl = cursor.fetchone()[0]
        
        if anzahl == 0:
            flash('Keine Transaktionen zum Löschen gefunden!', 'warning')
            return redirect(url_for('admin_transaktionen', gemeinschaft_id=gemeinschaft_id))
        
        # Lade IDs der zu löschenden Transaktionen
        cursor.execute("""
            SELECT id FROM bank_transaktionen
            WHERE gemeinschaft_id = ?
            AND date(importiert_am) = ?
            AND importiert_von = ?
        """, (gemeinschaft_id, import_datum, importiert_von))
        trans_ids = [row[0] for row in cursor.fetchall()]
        
        # Lösche zugehörige Gemeinschaftskosten
        if trans_ids:
            placeholders = ','.join('?' * len(trans_ids))
            cursor.execute(f"""
                DELETE FROM gemeinschafts_kosten
                WHERE transaktion_id IN ({placeholders})
            """, trans_ids)
        
        # Lösche Transaktionen
        cursor.execute("""
            DELETE FROM bank_transaktionen
            WHERE gemeinschaft_id = ?
            AND date(importiert_am) = ?
            AND importiert_von = ?
        """, (gemeinschaft_id, import_datum, importiert_von))
        
        db.connection.commit()
        flash(f'✅ {anzahl} Transaktionen des Imports vom {import_datum} gelöscht', 'success')
    
    return redirect(url_for('admin_transaktionen', gemeinschaft_id=gemeinschaft_id))


@app.route('/admin/abrechnungen/<int:gemeinschaft_id>/anfangssaldo', methods=['GET', 'POST'])
@admin_required
def anfangssaldo_bearbeiten(gemeinschaft_id):
    """Anfangssaldo für Gemeinschaft eingeben/bearbeiten"""
    with MaschinenDBContext(DB_PATH) as db:
        cursor = db.connection.cursor()
        
        # Prüfe Berechtigung
        if session.get('admin_level', 0) < 2:
            cursor.execute("""
                SELECT COUNT(*) FROM gemeinschafts_admin
                WHERE benutzer_id = ? AND gemeinschaft_id = ?
            """, (session['benutzer_id'], gemeinschaft_id))
            if cursor.fetchone()[0] == 0:
                flash('Keine Berechtigung!', 'danger')
                return redirect(url_for('admin_transaktionen', gemeinschaft_id=gemeinschaft_id))
        
        if request.method == 'POST':
            anfangssaldo = request.form.get('anfangssaldo', '0')
            anfangssaldo_datum = request.form.get('anfangssaldo_datum', None)
            
            try:
                anfangssaldo = float(anfangssaldo.replace(',', '.'))
            except ValueError:
                flash('Ungültiger Betrag!', 'danger')
                return redirect(request.url)
            
            # Update Gemeinschaft
            cursor.execute("""
                UPDATE gemeinschaften
                SET anfangssaldo_bank = ?, anfangssaldo_datum = ?
                WHERE id = ?
            """, (anfangssaldo, anfangssaldo_datum, gemeinschaft_id))
            
            db.connection.commit()
            flash(f'✅ Anfangssaldo auf {anfangssaldo:.2f} € gesetzt', 'success')
            return redirect(url_for('admin_transaktionen', gemeinschaft_id=gemeinschaft_id))
        
        # GET - Formular anzeigen
        cursor.execute("""
            SELECT name, anfangssaldo_bank, anfangssaldo_datum
            FROM gemeinschaften
            WHERE id = ?
        """, (gemeinschaft_id,))
        row = cursor.fetchone()
        
        gemeinschaft = {
            'id': gemeinschaft_id,
            'name': row[0],
            'anfangssaldo': row[1] or 0.0,
            'anfangssaldo_datum': row[2]
        }
    
    return render_template('anfangssaldo_bearbeiten.html', gemeinschaft=gemeinschaft)


if __name__ == "__main__":
    # Für Entwicklung: Flask-eigener Server (nicht für Produktion!)
    app.run(host="0.0.0.0", port=5000, debug=False)







