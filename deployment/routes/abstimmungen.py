# -*- coding: utf-8 -*-
"""
Benutzer - Abstimmungen und Anträge
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import MaschinenDBContext
from utils.decorators import login_required
from utils.training import get_current_db_path
from utils.sql_helpers import convert_sql

abstimmungen_bp = Blueprint('abstimmungen', __name__)


@abstimmungen_bp.route('/abstimmungen')
@login_required
def abstimmungen_liste():
    """Offene Abstimmungen anzeigen"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        # Gemeinschaften des Benutzers ermitteln
        sql = convert_sql("""
            SELECT gemeinschaft_id FROM mitglied_gemeinschaft
            WHERE mitglied_id = ?
        """)
        cursor.execute(sql, (session['benutzer_id'],))
        gemeinschaft_ids = [row[0] for row in cursor.fetchall()]

        if not gemeinschaft_ids:
            return render_template('abstimmungen.html',
                                 abstimmungen_offen=[],
                                 abstimmungen_abgeschlossen=[])

        # Offene Abstimmungen
        placeholders = ','.join(['?' for _ in gemeinschaft_ids])
        sql = convert_sql(f"""
            SELECT a.*, g.name as gemeinschaft_name,
                   (SELECT COUNT(*) FROM abstimmung_stimmen WHERE abstimmung_id = a.id) as stimmen_anzahl,
                   (SELECT 1 FROM abstimmung_stimmen WHERE abstimmung_id = a.id AND benutzer_id = ?) as hat_abgestimmt
            FROM abstimmungen a
            JOIN gemeinschaften g ON a.gemeinschaft_id = g.id
            WHERE a.status = 'offen'
            AND a.gemeinschaft_id IN ({placeholders})
            ORDER BY a.ablauf_datum ASC
        """)
        cursor.execute(sql, [session['benutzer_id']] + gemeinschaft_ids)
        columns = [desc[0] for desc in cursor.description]
        abstimmungen_offen = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Abgeschlossene Abstimmungen (letzte 10)
        sql = convert_sql(f"""
            SELECT a.*, g.name as gemeinschaft_name
            FROM abstimmungen a
            JOIN gemeinschaften g ON a.gemeinschaft_id = g.id
            WHERE a.status = 'abgeschlossen'
            AND a.gemeinschaft_id IN ({placeholders})
            ORDER BY a.erstellt_am DESC
            LIMIT 10
        """)
        cursor.execute(sql, gemeinschaft_ids)
        columns = [desc[0] for desc in cursor.description]
        abstimmungen_abgeschlossen = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render_template('abstimmungen.html',
                         abstimmungen_offen=abstimmungen_offen,
                         abstimmungen_abgeschlossen=abstimmungen_abgeschlossen)


@abstimmungen_bp.route('/abstimmungen/<int:id>')
@login_required
def abstimmung_detail(id):
    """Abstimmung Details und Stimmabgabe"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("""
            SELECT a.*, g.name as gemeinschaft_name
            FROM abstimmungen a
            JOIN gemeinschaften g ON a.gemeinschaft_id = g.id
            WHERE a.id = ?
        """)
        cursor.execute(sql, (id,))
        row = cursor.fetchone()
        if not row:
            flash('Abstimmung nicht gefunden.', 'danger')
            return redirect(url_for('abstimmungen.abstimmungen_liste'))

        columns = [desc[0] for desc in cursor.description]
        abstimmung = dict(zip(columns, row))

        # Prüfen ob Benutzer Mitglied der Gemeinschaft ist
        sql = convert_sql("""
            SELECT 1 FROM mitglied_gemeinschaft
            WHERE mitglied_id = ? AND gemeinschaft_id = ?
        """)
        cursor.execute(sql, (session['benutzer_id'], abstimmung['gemeinschaft_id']))
        if not cursor.fetchone():
            flash('Sie sind nicht berechtigt, an dieser Abstimmung teilzunehmen.', 'danger')
            return redirect(url_for('abstimmungen.abstimmungen_liste'))

        # Hat der Benutzer bereits abgestimmt?
        sql = convert_sql("""
            SELECT stimme FROM abstimmung_stimmen
            WHERE abstimmung_id = ? AND benutzer_id = ?
        """)
        cursor.execute(sql, (id, session['benutzer_id']))
        eigene_stimme_row = cursor.fetchone()
        eigene_stimme = eigene_stimme_row[0] if eigene_stimme_row else None

        # Statistik berechnen
        sql = convert_sql("""
            SELECT stimme, COUNT(*) as anzahl
            FROM abstimmung_stimmen
            WHERE abstimmung_id = ?
            GROUP BY stimme
        """)
        cursor.execute(sql, (id,))
        statistik = {'ja': 0, 'nein': 0, 'enthaltung': 0}
        for row in cursor.fetchall():
            statistik[row[0]] = row[1]

    return render_template('abstimmung_stimmen.html',
                         abstimmung=abstimmung,
                         eigene_stimme=eigene_stimme,
                         statistik=statistik)


@abstimmungen_bp.route('/abstimmungen/<int:id>/stimmen', methods=['POST'])
@login_required
def abstimmung_stimme_abgeben(id):
    """Stimme abgeben"""
    db_path = get_current_db_path()

    stimme = request.form.get('stimme')
    if stimme not in ['ja', 'nein', 'enthaltung']:
        flash('Ungültige Stimme.', 'danger')
        return redirect(url_for('abstimmungen.abstimmung_detail', id=id))

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        # Prüfen ob Abstimmung noch offen
        sql = convert_sql("SELECT status, gemeinschaft_id FROM abstimmungen WHERE id = ?")
        cursor.execute(sql, (id,))
        row = cursor.fetchone()
        if not row:
            flash('Abstimmung nicht gefunden.', 'danger')
            return redirect(url_for('abstimmungen.abstimmungen_liste'))

        if row[0] != 'offen':
            flash('Diese Abstimmung ist bereits abgeschlossen.', 'warning')
            return redirect(url_for('abstimmungen.abstimmung_detail', id=id))

        # Prüfen ob Benutzer Mitglied ist
        sql = convert_sql("""
            SELECT 1 FROM mitglied_gemeinschaft
            WHERE mitglied_id = ? AND gemeinschaft_id = ?
        """)
        cursor.execute(sql, (session['benutzer_id'], row[1]))
        if not cursor.fetchone():
            flash('Sie sind nicht berechtigt, an dieser Abstimmung teilzunehmen.', 'danger')
            return redirect(url_for('abstimmungen.abstimmungen_liste'))

        # Prüfen ob bereits abgestimmt
        sql = convert_sql("""
            SELECT 1 FROM abstimmung_stimmen
            WHERE abstimmung_id = ? AND benutzer_id = ?
        """)
        cursor.execute(sql, (id, session['benutzer_id']))
        if cursor.fetchone():
            # Stimme aktualisieren
            sql = convert_sql("""
                UPDATE abstimmung_stimmen
                SET stimme = ?, abgegeben_am = ?
                WHERE abstimmung_id = ? AND benutzer_id = ?
            """)
            cursor.execute(sql, (
                stimme,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                id,
                session['benutzer_id']
            ))
            flash('Ihre Stimme wurde geändert.', 'success')
        else:
            # Neue Stimme einfügen
            sql = convert_sql("""
                INSERT INTO abstimmung_stimmen (abstimmung_id, benutzer_id, stimme)
                VALUES (?, ?, ?)
            """)
            cursor.execute(sql, (id, session['benutzer_id'], stimme))
            flash('Ihre Stimme wurde erfolgreich abgegeben.', 'success')

        db.connection.commit()

    return redirect(url_for('abstimmungen.abstimmung_detail', id=id))


@abstimmungen_bp.route('/antrag-stellen', methods=['GET', 'POST'])
@login_required
def antrag_stellen():
    """Neuen Antrag einreichen"""
    db_path = get_current_db_path()

    if request.method == 'POST':
        gemeinschaft_id = request.form.get('gemeinschaft_id')
        titel = request.form.get('titel')
        beschreibung = request.form.get('beschreibung')

        if not gemeinschaft_id or not titel:
            flash('Bitte alle Pflichtfelder ausfüllen.', 'danger')
            return redirect(url_for('abstimmungen.antrag_stellen'))

        with MaschinenDBContext(db_path) as db:
            cursor = db.connection.cursor()

            # Prüfen ob Benutzer Mitglied ist
            sql = convert_sql("""
                SELECT 1 FROM mitglied_gemeinschaft
                WHERE mitglied_id = ? AND gemeinschaft_id = ?
            """)
            cursor.execute(sql, (session['benutzer_id'], gemeinschaft_id))
            if not cursor.fetchone():
                flash('Sie sind nicht Mitglied dieser Gemeinschaft.', 'danger')
                return redirect(url_for('abstimmungen.antrag_stellen'))

            sql = convert_sql("""
                INSERT INTO antraege (gemeinschaft_id, titel, beschreibung, benutzer_id)
                VALUES (?, ?, ?, ?)
            """)
            cursor.execute(sql, (gemeinschaft_id, titel, beschreibung, session['benutzer_id']))
            db.connection.commit()

        flash('Ihr Antrag wurde erfolgreich eingereicht.', 'success')
        return redirect(url_for('abstimmungen.meine_antraege'))

    # Gemeinschaften des Benutzers
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

    return render_template('antrag_stellen.html', gemeinschaften=gemeinschaften)


@abstimmungen_bp.route('/meine-antraege')
@login_required
def meine_antraege():
    """Eigene Anträge anzeigen"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("""
            SELECT a.*, g.name as gemeinschaft_name,
                   bb.name || ', ' || bb.vorname as bearbeiter_name
            FROM antraege a
            JOIN gemeinschaften g ON a.gemeinschaft_id = g.id
            LEFT JOIN benutzer bb ON a.bearbeitet_von = bb.id
            WHERE a.benutzer_id = ?
            ORDER BY a.erstellt_am DESC
        """)
        cursor.execute(sql, (session['benutzer_id'],))
        columns = [desc[0] for desc in cursor.description]
        antraege = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render_template('meine_antraege.html', antraege=antraege)
