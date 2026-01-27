# -*- coding: utf-8 -*-
"""
Reservierungen - Maschinen reservieren, Kalender, Übersichten
"""

from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import MaschinenDBContext
from utils.decorators import login_required
from utils.training import get_current_db_path
from utils.sql_helpers import convert_sql

reservierungen_bp = Blueprint('reservierungen', __name__)


@reservierungen_bp.route('/maschine/<int:maschine_id>/reservieren', methods=['GET', 'POST'])
@login_required
def maschine_reservieren(maschine_id):
    """Maschine reservieren"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()
        maschine = db.get_maschine_by_id(maschine_id)

        if request.method == 'POST':
            datum = request.form.get('datum')
            uhrzeit_von = request.form.get('uhrzeit_von')
            nutzungsdauer = float(request.form.get('nutzungsdauer'))
            uhrzeit_bis = request.form.get('uhrzeit_bis')
            zweck = request.form.get('zweck')
            bemerkung = request.form.get('bemerkung')

            sql = convert_sql("""
                SELECT COUNT(*) FROM maschinen_reservierungen
                WHERE maschine_id = ?
                  AND datum = ?
                  AND status = 'aktiv'
                  AND (
                    (uhrzeit_von <= ? AND uhrzeit_bis > ?)
                    OR (uhrzeit_von < ? AND uhrzeit_bis >= ?)
                    OR (uhrzeit_von >= ? AND uhrzeit_bis <= ?)
                  )
            """)
            cursor.execute(sql, (maschine_id, datum, uhrzeit_von, uhrzeit_von,
                                uhrzeit_bis, uhrzeit_bis, uhrzeit_von, uhrzeit_bis))

            if cursor.fetchone()[0] > 0:
                flash('Der gewählte Zeitraum überschneidet sich mit einer bestehenden Reservierung!', 'danger')
                return redirect(url_for('reservierungen.maschine_reservieren', maschine_id=maschine_id))

            sql = convert_sql("""
                INSERT INTO maschinen_reservierungen
                (maschine_id, benutzer_id, datum, uhrzeit_von, uhrzeit_bis, nutzungsdauer_stunden, zweck, bemerkung)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """)
            cursor.execute(sql, (maschine_id, session['benutzer_id'], datum,
                                uhrzeit_von, uhrzeit_bis, nutzungsdauer, zweck, bemerkung))

            db.connection.commit()
            flash(f'Maschine "{maschine["bezeichnung"]}" wurde erfolgreich für {datum} reserviert!', 'success')
            return redirect(url_for('dashboard.dashboard'))

        einsatzzwecke = db.get_all_einsatzzwecke()

        sql = convert_sql("""
            SELECT r.*, b.name || ' ' || COALESCE(b.vorname, '') as benutzer_name
            FROM maschinen_reservierungen r
            JOIN benutzer b ON r.benutzer_id = b.id
            WHERE r.maschine_id = ?
              AND r.datum >= date('now')
              AND r.status = 'aktiv'
            ORDER BY r.datum, r.uhrzeit_von
        """)
        cursor.execute(sql, (maschine_id,))

        columns = [desc[0] for desc in cursor.description]
        reservierungen = [dict(zip(columns, row)) for row in cursor.fetchall()]

        sql = convert_sql("""
            SELECT * FROM maschinen_reservierungen
            WHERE maschine_id = ?
              AND benutzer_id = ?
              AND datum >= date('now')
              AND status = 'aktiv'
            ORDER BY datum, uhrzeit_von
        """)
        cursor.execute(sql, (maschine_id, session['benutzer_id']))

        columns = [desc[0] for desc in cursor.description]
        meine_reservierungen = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render_template('maschine_reservieren.html',
                         maschine=maschine,
                         einsatzzwecke=einsatzzwecke,
                         reservierungen=reservierungen,
                         meine_reservierungen=meine_reservierungen,
                         heute=datetime.now().strftime('%Y-%m-%d'))


@reservierungen_bp.route('/reservierungen-kalender')
@login_required
def reservierungen_kalender():
    """Kalenderansicht aller Reservierungen"""
    db_path = get_current_db_path()
    maschine_id = request.args.get('maschine_id', type=int)

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()
        maschinen = db.get_all_maschinen()

        heute = datetime.now()
        bis_datum = (heute + timedelta(days=30)).strftime('%Y-%m-%d')

        if maschine_id:
            sql = convert_sql("""
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
            """)
            cursor.execute(sql, (maschine_id, bis_datum))
        else:
            sql = convert_sql("""
                SELECT r.*, m.bezeichnung as maschine_bezeichnung,
                       b.name || ' ' || COALESCE(b.vorname, '') as benutzer_name
                FROM maschinen_reservierungen r
                JOIN maschinen m ON r.maschine_id = m.id
                JOIN benutzer b ON r.benutzer_id = b.id
                WHERE r.datum >= date('now')
                  AND r.datum <= ?
                  AND r.status = 'aktiv'
                ORDER BY r.datum, m.bezeichnung, r.uhrzeit_von
            """)
            cursor.execute(sql, (bis_datum,))

        columns = [desc[0] for desc in cursor.description]
        reservierungen = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render_template('reservierungen_kalender.html',
                         reservierungen=reservierungen,
                         maschinen=maschinen,
                         selected_maschine_id=maschine_id,
                         heute=heute.strftime('%Y-%m-%d'))


@reservierungen_bp.route('/reservierungen-balken')
@login_required
def reservierungen_balken():
    """Balkendiagramm-Ansicht der Reservierungen"""
    db_path = get_current_db_path()
    tage = int(request.args.get('tage', 10))
    start_datum = request.args.get('start_datum')

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()
        maschinen = db.get_all_maschinen()

        if start_datum:
            start = datetime.strptime(start_datum, '%Y-%m-%d')
        else:
            start = datetime.now() - timedelta(days=1)

        ende = start + timedelta(days=tage)

        sql = convert_sql("""
            SELECT r.*, m.bezeichnung as maschine_bezeichnung,
                   b.name || ' ' || COALESCE(b.vorname, '') as benutzer_name
            FROM maschinen_reservierungen r
            JOIN maschinen m ON r.maschine_id = m.id
            JOIN benutzer b ON r.benutzer_id = b.id
            WHERE r.datum >= ?
              AND r.datum < ?
              AND r.status = 'aktiv'
            ORDER BY m.bezeichnung, r.datum, r.uhrzeit_von
        """)
        cursor.execute(sql, (start.strftime('%Y-%m-%d'), ende.strftime('%Y-%m-%d')))

        columns = [desc[0] for desc in cursor.description]
        reservierungen = [dict(zip(columns, row)) for row in cursor.fetchall()]

    tage_liste = []
    for i in range(tage):
        tag = start + timedelta(days=i)
        tage_liste.append({
            'datum': tag.date() if hasattr(tag, 'date') else tag,
            'datum_str': tag.strftime('%Y-%m-%d'),
            'tag': tag.strftime('%d.%m'),
            'wochentag': ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'][tag.weekday()]
        })

    return render_template('reservierungen_balken.html',
                         reservierungen=reservierungen,
                         maschinen=maschinen,
                         tage_liste=tage_liste,
                         start_datum=start.strftime('%Y-%m-%d'),
                         tage_anzahl=tage)


@reservierungen_bp.route('/meine-reservierungen')
@login_required
def meine_reservierungen():
    """Übersicht aller eigenen Reservierungen"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("""
            SELECT r.*, m.bezeichnung as maschine_bezeichnung
            FROM maschinen_reservierungen r
            JOIN maschinen m ON r.maschine_id = m.id
            WHERE r.benutzer_id = ?
              AND r.status = 'aktiv'
            ORDER BY r.datum, r.uhrzeit_von
        """)
        cursor.execute(sql, (session['benutzer_id'],))

        columns = [desc[0] for desc in cursor.description]
        reservierungen = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render_template('meine_reservierungen.html',
                         reservierungen=reservierungen,
                         today=datetime.now().date())


@reservierungen_bp.route('/reservierung/<int:reservierung_id>/stornieren', methods=['POST'])
@login_required
def reservierung_stornieren(reservierung_id):
    """Reservierung stornieren"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("""
            SELECT r.*, m.bezeichnung as maschine_bezeichnung,
                   b.name || ' ' || COALESCE(b.vorname, '') as benutzer_name
            FROM maschinen_reservierungen r
            JOIN maschinen m ON r.maschine_id = m.id
            JOIN benutzer b ON r.benutzer_id = b.id
            WHERE r.id = ? AND r.benutzer_id = ?
        """)
        cursor.execute(sql, (reservierung_id, session['benutzer_id']))

        result = cursor.fetchone()
        if not result:
            flash('Reservierung nicht gefunden oder keine Berechtigung!', 'danger')
            return redirect(url_for('dashboard.dashboard'))

        columns = [desc[0] for desc in cursor.description]
        reservierung = dict(zip(columns, result))
        maschine_id = reservierung['maschine_id']

        sql = convert_sql("""
            INSERT INTO reservierungen_geloescht
            (reservierung_id, maschine_id, maschine_bezeichnung, benutzer_id,
             benutzer_name, datum, uhrzeit_von, uhrzeit_bis, nutzungsdauer_stunden,
             zweck, bemerkung, erstellt_am, geloescht_von, grund)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)
        cursor.execute(sql, (
            reservierung_id, reservierung['maschine_id'],
            reservierung['maschine_bezeichnung'], reservierung['benutzer_id'],
            reservierung['benutzer_name'], reservierung['datum'],
            reservierung['uhrzeit_von'], reservierung['uhrzeit_bis'],
            reservierung.get('nutzungsdauer_stunden'), reservierung.get('zweck'),
            reservierung.get('bemerkung'), reservierung['erstellt_am'],
            session['benutzer_id'], 'Benutzer-Stornierung'
        ))

        sql = convert_sql("""
            UPDATE maschinen_reservierungen
            SET status = 'storniert', geaendert_am = CURRENT_TIMESTAMP
            WHERE id = ?
        """)
        cursor.execute(sql, (reservierung_id,))

        db.connection.commit()
        flash('Reservierung wurde storniert und archiviert.', 'success')

    return redirect(url_for('reservierungen.maschine_reservieren', maschine_id=maschine_id))


@reservierungen_bp.route('/geloeschte-reservierungen')
@login_required
def geloeschte_reservierungen():
    """Übersicht aller gelöschten/stornierten Reservierungen"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("""
            SELECT * FROM reservierungen_geloescht
            WHERE benutzer_id = ?
            ORDER BY geloescht_am DESC
            LIMIT 100
        """)
        cursor.execute(sql, (session['benutzer_id'],))

        columns = [desc[0] for desc in cursor.description]
        geloeschte = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render_template('geloeschte_reservierungen.html',
                         geloeschte=geloeschte,
                         today=datetime.now().strftime('%Y-%m-%d'))


@reservierungen_bp.route('/abgelaufene-reservierungen')
@login_required
def abgelaufene_reservierungen():
    """Übersicht aller abgelaufenen Reservierungen"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("""
            SELECT * FROM reservierungen_abgelaufen
            WHERE benutzer_id = ?
            ORDER BY abgelaufen_am DESC
            LIMIT 100
        """)
        cursor.execute(sql, (session['benutzer_id'],))

        columns = [desc[0] for desc in cursor.description]
        abgelaufene = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render_template('abgelaufene_reservierungen.html',
                         abgelaufene=abgelaufene,
                         today=datetime.now().strftime('%Y-%m-%d'))
