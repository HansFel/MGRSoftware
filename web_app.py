"""
Flask-Webanwendung für Maschinengemeinschaft
Ermöglicht Benutzern den Zugriff von extern (z.B. Mobiltelefon)
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify, make_response
from database import MaschinenDBContext
from datetime import datetime
import os
import json
import csv
from io import StringIO, BytesIO
from functools import wraps
import zipfile

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))  # Für Session-Management

DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.dirname(__file__), "maschinengemeinschaft.db"))


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
    """Decorator für Admin-Routen"""
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


@app.route('/')
def index():
    """Startseite - Weiterleitung"""
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
    
    return render_template('dashboard.html', 
                         statistik=statistik,
                         einsaetze=letzte_einsaetze,
                         schulden_nach_gemeinschaft=schulden_nach_gemeinschaft,
                         reservierungen=reservierungen)


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
    
    return render_template('neuer_einsatz.html',
                         maschinen=maschinen,
                         einsatzzwecke=einsatzzwecke,
                         heute=datetime.now().strftime('%Y-%m-%d'),
                         treibstoffkosten_preis=treibstoffkosten_preis)


@app.route('/meine-einsaetze')
@login_required
def meine_einsaetze():
    """Liste aller eigenen Einsätze"""
    with MaschinenDBContext(DB_PATH) as db:
        einsaetze = db.get_einsaetze_by_benutzer(session['benutzer_id'])
        
        # Summen berechnen
        summe_treibstoff = sum(e.get('treibstoffkosten', 0) or 0 for e in einsaetze)
        summe_maschine = sum(e.get('kosten_berechnet', 0) or 0 for e in einsaetze)
        summe_gesamt = summe_treibstoff + summe_maschine
    
    return render_template('meine_einsaetze.html', 
                         einsaetze=einsaetze,
                         summe_treibstoff=summe_treibstoff,
                         summe_maschine=summe_maschine,
                         summe_gesamt=summe_gesamt)


@app.route('/maschine/<int:maschine_id>/reservieren', methods=['GET', 'POST'])
@login_required
def maschine_reservieren(maschine_id):
    """Maschine reservieren"""
    from datetime import datetime, timedelta
    
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
        
        # Prüfen ob Reservierung dem Benutzer gehört
        cursor.execute("""
            SELECT maschine_id FROM maschinen_reservierungen
            WHERE id = ? AND benutzer_id = ?
        """, (reservierung_id, session['benutzer_id']))
        
        result = cursor.fetchone()
        if not result:
            flash('Reservierung nicht gefunden oder keine Berechtigung!', 'danger')
            return redirect(url_for('dashboard'))
        
        maschine_id = result[0]
        
        # Status auf 'storniert' setzen
        cursor.execute("""
            UPDATE maschinen_reservierungen
            SET status = 'storniert', geaendert_am = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (reservierung_id,))
        
        db.connection.commit()
        flash('Reservierung wurde storniert.', 'success')
        
    return redirect(url_for('maschine_reservieren', maschine_id=maschine_id))


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
    for e in einsaetze:
        writer.writerow([
            e['datum'],
            e['benutzer'],
            e['maschine'],
            e['einsatzzweck'],
            e.get('abrechnungsart', 'stunden'),
            f"{e.get('preis_pro_einheit', 0):.2f}",
            f"{e['anfangstand']:.1f}",
            f"{e['endstand']:.1f}",
            f"{e['betriebsstunden']:.1f}",
            f"{e['treibstoffverbrauch']:.1f}" if e['treibstoffverbrauch'] else '',
            f"{e.get('treibstoffkosten', 0):.2f}" if e.get('treibstoffkosten') else '',
            f"{e.get('flaeche_menge', 0):.1f}" if e.get('flaeche_menge') else '',
            f"{e.get('kosten_berechnet', 0):.2f}" if e.get('kosten_berechnet') else '',
            e.get('anmerkungen', '')
        ])
    
    # BytesIO für send_file
    csv_bytes = BytesIO(csv_buffer.getvalue().encode('utf-8-sig'))
    csv_bytes.seek(0)
    
    filename = f'meine_einsaetze_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    return send_file(
        csv_bytes,
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )


@app.route('/api/maschine/<int:maschine_id>')
@login_required
def api_maschine_details(maschine_id):
    """API-Endpunkt für Maschinen-Details (für AJAX)"""
    with MaschinenDBContext(DB_PATH) as db:
        maschine = db.get_maschine(maschine_id)
    
    if maschine:
        return {
            'success': True,
            'stundenzaehler': maschine['stundenzaehler_aktuell']
        }
    return {'success': False}, 404


@app.route('/passwort-aendern', methods=['GET', 'POST'])
@login_required
def passwort_aendern():
    """Passwort und Einstellungen ändern"""
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        
        if form_type == 'passwort':
            # Passwort ändern
            altes_passwort = request.form.get('altes_passwort')
            neues_passwort = request.form.get('neues_passwort')
            neues_passwort_wdh = request.form.get('neues_passwort_wdh')
            
            if neues_passwort != neues_passwort_wdh:
                flash('Die Passwörter stimmen nicht überein!', 'danger')
                return redirect(url_for('passwort_aendern'))
            
            with MaschinenDBContext(DB_PATH) as db:
                # Altes Passwort überprüfen
                benutzer = db.get_benutzer(session['benutzer_id'])
                if not db.verify_login(benutzer['username'], altes_passwort):
                    flash('Altes Passwort ist falsch!', 'danger')
                    return redirect(url_for('passwort_aendern'))
                
                # Neues Passwort setzen
                db.update_password(session['benutzer_id'], neues_passwort)
                flash('Passwort wurde erfolgreich geändert!', 'success')
                return redirect(url_for('dashboard'))
        
        elif form_type == 'treibstoff':
            # Treibstoffkosten ändern
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
                flash('Ungültiger Preis!', 'danger')
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
    
    return render_template('admin_dashboard.html',
                         einsaetze=alle_einsaetze,
                         benutzer=benutzer,
                         maschinen=maschinen,
                         stats=gesamt_stats)


@app.route('/admin/alle-einsaetze')
@admin_required
def admin_alle_einsaetze():
    """Alle Einsätze aller Benutzer"""
    with MaschinenDBContext(DB_PATH) as db:
        einsaetze = db.get_all_einsaetze()
    
    return render_template('admin_alle_einsaetze.html', einsaetze=einsaetze)


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
            # Passwort nur ändern wenn angegeben
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
    """Benutzer löschen"""
    with MaschinenDBContext(DB_PATH) as db:
        benutzer = db.get_benutzer_by_id(benutzer_id)
        # Hard delete: tatsächlich aus Datenbank löschen
        db.delete_benutzer(benutzer_id, soft_delete=False)
    flash(f'Benutzer {benutzer["name"]} wurde gelöscht.', 'success')
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
    """Rentabilitätsbericht für eine Maschine"""
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
        
        # Alter berechnen
        alter_jahre = 0
        if anschaffungsdatum:
            try:
                datum = datetime.strptime(anschaffungsdatum, '%Y-%m-%d')
                alter_jahre = (datetime.now() - datum).days / 365.25
            except:
                alter_jahre = 0
        
        abschreibung_bisher = min(abschreibung_pro_jahr * alter_jahre, anschaffungspreis)
        restwert = max(anschaffungspreis - abschreibung_bisher, 0)
        
        # Rentabilität
        deckungsbeitrag = einnahmen - abschreibung_bisher
        rentabilitaet_prozent = (deckungsbeitrag / anschaffungspreis * 100) if anschaffungspreis > 0 else 0
        
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
        
        # Gesamtaufwendungen berechnen
        aufwendungen_gesamt = sum(
            a['wartungskosten'] + a['reparaturkosten'] + a['versicherung'] + 
            a['steuern'] + a['sonstige_kosten']
            for a in alle_aufwendungen
        )
        
        # Aufwendungen zu einsaetze_pro_jahr hinzufügen
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
        
        # Rentabilität neu berechnen (Einnahmen - Abschreibung - Aufwendungen)
        deckungsbeitrag = einnahmen - abschreibung_bisher - aufwendungen_gesamt
        rentabilitaet_prozent = (deckungsbeitrag / anschaffungspreis * 100) if anschaffungspreis > 0 else 0
        
        rentabilitaet = {
            'anzahl_einsaetze': anzahl_einsaetze,
            'betriebsstunden': betriebsstunden,
            'einnahmen_gesamt': einnahmen,
            'aufwendungen_gesamt': aufwendungen_gesamt,
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
                         einsaetze_pro_jahr=einsaetze_pro_jahr)


@app.route('/admin/maschinen/<int:maschine_id>/rentabilitaet/pdf')
@admin_required
def admin_maschinen_rentabilitaet_pdf(maschine_id):
    """Rentabilitätsbericht als PDF exportieren"""
    from datetime import datetime
    from io import BytesIO
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    
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
        
        alter_jahre = 0
        if anschaffungsdatum:
            try:
                datum = datetime.strptime(anschaffungsdatum, '%Y-%m-%d')
                alter_jahre = (datetime.now() - datum).days / 365.25
            except:
                alter_jahre = 0
        
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
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Titel
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, spaceAfter=30)
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
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
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
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
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
        ['Abschreibung pro Jahr:', f"{abschreibung_pro_jahr:.2f} €"],
        ['Alter der Maschine:', f"{alter_jahre:.1f} Jahre"],
        ['Abschreibung bisher:', f"{abschreibung_bisher:.2f} €"],
    ]
    
    abschreibung_table = Table(abschreibung_data, colWidths=[10*cm, 7*cm])
    abschreibung_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
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
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
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
    """Jährliche Aufwendungen für eine Maschine verwalten"""
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
            flash(f'Aufwendungen für {jahr} gespeichert.', 'success')
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
        
        # Historische Aufwendungen laden (außer aktuelles Jahr)
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
    # Einfach zurück zur Hauptseite mit dem Jahr als vorbefülltes Formular
    # (könnte später erweitert werden)
    return redirect(url_for('admin_maschinen_aufwendungen', maschine_id=maschine_id))


@app.route('/admin/maschinen/neu', methods=['GET', 'POST'])
@admin_required
def admin_maschinen_neu():
    """Neue Maschine anlegen"""
    with MaschinenDBContext(DB_PATH) as db:
        if request.method == 'POST':
            db.add_maschine(
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
            flash('Maschine erfolgreich angelegt!', 'success')
            return redirect(url_for('admin_maschinen'))
        
        # Hole Gemeinschaften für Dropdown
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
            flash('Maschine erfolgreich aktualisiert!', 'success')
            return redirect(url_for('admin_maschinen'))
        
        maschine = db.get_maschine_by_id(maschine_id)
        
        # Hole Gemeinschaften für Dropdown
        cursor = db.cursor
        cursor.execute("SELECT id, name FROM gemeinschaften WHERE aktiv = 1 ORDER BY name")
        gemeinschaften = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
        
    return render_template('admin_maschinen_form.html', maschine=maschine, gemeinschaften=gemeinschaften)


@app.route('/admin/maschinen/<int:maschine_id>/delete', methods=['POST'])
@admin_required
def admin_maschinen_delete(maschine_id):
    """Maschine löschen"""
    with MaschinenDBContext(DB_PATH) as db:
        maschine = db.get_maschine_by_id(maschine_id)
        db.delete_maschine(maschine_id)
    flash(f'Maschine {maschine["bezeichnung"]} wurde gelöscht.', 'success')
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
    """Einsatzzweck löschen"""
    with MaschinenDBContext(DB_PATH) as db:
        einsatzzweck = db.get_einsatzzweck_by_id(einsatzzweck_id)
        db.delete_einsatzzweck(einsatzzweck_id, soft_delete=False)
    flash(f'Einsatzzweck {einsatzzweck["bezeichnung"]} wurde gelöscht.', 'success')
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
                SET name = ?, beschreibung = ?, aktiv = ?
                WHERE id = ?
            """, (
                request.form['name'],
                request.form.get('beschreibung'),
                1 if request.form.get('aktiv') else 0,
                gemeinschaft_id
            ))
            db.connection.commit()
            flash('Gemeinschaft erfolgreich aktualisiert!', 'success')
            return redirect(url_for('admin_gemeinschaften'))
        
        cursor.execute("SELECT * FROM gemeinschaften WHERE id = ?", (gemeinschaft_id,))
        columns = [desc[0] for desc in cursor.description]
        gemeinschaft = dict(zip(columns, cursor.fetchone()))
    
    return render_template('admin_gemeinschaften_form.html', gemeinschaft=gemeinschaft)


@app.route('/admin/gemeinschaften/<int:gemeinschaft_id>/abrechnung')
@admin_required
def admin_gemeinschaften_abrechnung(gemeinschaft_id):
    """Abrechnung für eine Gemeinschaft"""
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
                ) as maschinenkosten
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
        
        # Abrechnung pro Mitglied (nur Maschinenkosten für CSV)
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
    
    # CSV erstellen
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    
    # Header
    writer.writerow([f'Abrechnung: {gemeinschaft["name"]}'])
    writer.writerow([f'Erstellt am: {datetime.now().strftime("%d.%m.%Y %H:%M")}'])
    writer.writerow([])
    writer.writerow(['Name', 'Vorname', 'Anzahl Einsätze', 'Betriebsstunden', 
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
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename=abrechnung_{gemeinschaft['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv"
    response.headers["Content-type"] = "text/csv; charset=utf-8"
    
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
                flash(f'{len(mitglieder)} Mitglied(er) hinzugefügt!', 'success')
                
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
        
        # Verfügbare Benutzer (noch nicht in Gemeinschaft)
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
        writer.writerow(['SUMMEN', '', '', '', '', '', '', '', '',
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


if __name__ == '__main__':
    # Für Entwicklung
    app.run(host='0.0.0.0', port=5000, debug=True)
