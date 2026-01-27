# -*- coding: utf-8 -*-
"""
Authentifizierung - Login, Logout, Passwort ändern
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import MaschinenDBContext
from utils.decorators import login_required
from utils.training import get_current_db_path, TRAINING_DATABASES, get_available_training_dbs, can_access_production
from utils.sql_helpers import convert_sql

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login-Seite"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        db_path = get_current_db_path()
        with MaschinenDBContext(db_path) as db:
            benutzer = db.verify_login(username, password)

            if benutzer:
                session['benutzer_id'] = benutzer['id']
                session['benutzer_name'] = f"{benutzer['name']}, {benutzer['vorname']}"
                session['is_admin'] = bool(benutzer.get('is_admin', False))
                session['admin_level'] = benutzer.get('admin_level', 0)

                # Trainings-Modus Einstellung laden
                nur_training = benutzer.get('nur_training', 0)
                session['nur_training'] = bool(nur_training)

                # Wenn nur Training erlaubt, direkt auf Training-DB setzen
                if nur_training and not session['is_admin']:
                    session['current_database'] = 'uebung_anfaenger'
                else:
                    session['current_database'] = 'produktion'

                # Gemeinschafts-Admin Zuordnungen laden
                if session['admin_level'] == 1:
                    gemeinschafts_ids = db.get_gemeinschafts_admin_ids(benutzer['id'])
                    session['gemeinschafts_admin_ids'] = gemeinschafts_ids
                else:
                    session['gemeinschafts_admin_ids'] = []

                # Lade Gemeinschaften des Benutzers für das Menü
                cursor = db.connection.cursor()
                sql = convert_sql("""
                    SELECT g.id, g.name
                    FROM gemeinschaften g
                    JOIN mitglied_gemeinschaft mg ON g.id = mg.gemeinschaft_id
                    WHERE mg.mitglied_id = ? AND g.aktiv = true
                    ORDER BY g.name
                """)
                cursor.execute(sql, (benutzer['id'],))
                gemeinschaften = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
                session['gemeinschaften'] = gemeinschaften

                # Begrüßung mit Info über Datenbank-Modus
                if nur_training and not session['is_admin']:
                    flash(f"Willkommen, {benutzer['vorname']}! (Übungsmodus)", 'info')
                else:
                    flash(f"Willkommen, {benutzer['vorname']}!", 'success')

                if session['is_admin']:
                    return redirect(url_for('admin_system.admin_dashboard'))
                return redirect(url_for('dashboard.dashboard'))
            else:
                flash('Ungültiger Benutzername oder Passwort.', 'danger')

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    """Logout"""
    session.clear()
    flash('Sie wurden abgemeldet.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/datenbank-auswahl')
@login_required
def datenbank_auswahl():
    """Seite zur Auswahl der Datenbank (Produktion oder Training)"""
    training_dbs = get_available_training_dbs()
    current_db = session.get('current_database', 'produktion')
    allow_production = can_access_production()

    return render_template('datenbank_auswahl.html',
                         training_dbs=training_dbs,
                         current_db=current_db,
                         allow_production=allow_production)


@auth_bp.route('/datenbank-wechseln', methods=['POST'])
@login_required
def datenbank_wechseln():
    """Wechselt die aktive Datenbank"""
    target_db = request.form.get('database', 'produktion')

    if target_db == 'produktion':
        if not can_access_production():
            flash('Sie haben keinen Zugriff auf die Produktionsdatenbank.', 'danger')
            return redirect(url_for('auth.datenbank_auswahl'))
        session['current_database'] = 'produktion'
        flash('Gewechselt zur Produktionsdatenbank.', 'success')
    elif target_db in TRAINING_DATABASES:
        session['current_database'] = target_db
        db_name = TRAINING_DATABASES[target_db]['name']
        flash(f'Gewechselt zu: {db_name}', 'info')
    else:
        flash('Ungültige Datenbank ausgewählt.', 'danger')

    # Gemeinschaften für neue DB laden
    db_path = get_current_db_path()
    try:
        with MaschinenDBContext(db_path) as db:
            cursor = db.connection.cursor()
            sql = convert_sql("""
                SELECT g.id, g.name
                FROM gemeinschaften g
                JOIN mitglied_gemeinschaft mg ON g.id = mg.gemeinschaft_id
                WHERE mg.mitglied_id = ? AND g.aktiv = true
                ORDER BY g.name
            """)
            cursor.execute(sql, (session['benutzer_id'],))
            gemeinschaften = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
            session['gemeinschaften'] = gemeinschaften
    except:
        session['gemeinschaften'] = []

    return redirect(url_for('dashboard.dashboard'))


@auth_bp.route('/passwort-aendern', methods=['GET', 'POST'])
@login_required
def passwort_aendern():
    """Passwort ändern"""
    if request.method == 'POST':
        altes_passwort = request.form.get('altes_passwort')
        neues_passwort = request.form.get('neues_passwort')
        passwort_bestaetigung = request.form.get('passwort_bestaetigung')

        if neues_passwort != passwort_bestaetigung:
            flash('Die neuen Passwörter stimmen nicht überein!', 'danger')
            return redirect(url_for('auth.passwort_aendern'))

        if len(neues_passwort) < 4:
            flash('Das Passwort muss mindestens 4 Zeichen lang sein!', 'danger')
            return redirect(url_for('auth.passwort_aendern'))

        db_path = get_current_db_path()
        with MaschinenDBContext(db_path) as db:
            # Altes Passwort überprüfen
            benutzer = db.get_benutzer(session['benutzer_id'])
            if not benutzer:
                flash('Benutzer nicht gefunden!', 'danger')
                return redirect(url_for('auth.passwort_aendern'))

            # Hash des alten Passworts prüfen
            import hashlib
            altes_hash = hashlib.sha256(altes_passwort.encode('utf-8')).hexdigest()
            if altes_hash != benutzer.get('password_hash'):
                flash('Das alte Passwort ist falsch!', 'danger')
                return redirect(url_for('auth.passwort_aendern'))

            # Neues Passwort setzen
            db.update_password(session['benutzer_id'], neues_passwort)
            flash('Passwort wurde erfolgreich geändert!', 'success')
            return redirect(url_for('dashboard.dashboard'))

    # GET: Benutzer laden für Einstellungsanzeige
    db_path = get_current_db_path()
    with MaschinenDBContext(db_path) as db:
        benutzer = db.get_benutzer(session['benutzer_id'])

    return render_template('passwort_aendern.html', benutzer=benutzer)
