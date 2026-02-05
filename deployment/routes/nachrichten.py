# -*- coding: utf-8 -*-
"""
Nachrichten - Gemeinschafts-Nachrichten
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import MaschinenDBContext
from utils.decorators import login_required
from utils.training import get_current_db_path
from utils.sql_helpers import convert_sql, db_execute

nachrichten_bp = Blueprint('nachrichten', __name__)


@nachrichten_bp.route('/nachrichten')
@login_required
def nachrichten():
    """Nachrichten der eigenen Gemeinschaften anzeigen"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("""
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
        """)
        cursor.execute(sql, (session['benutzer_id'], session['benutzer_id']))

        columns = [desc[0] for desc in cursor.description]
        nachrichten_list = [dict(zip(columns, row)) for row in cursor.fetchall()]

        ungelesen = sum(1 for n in nachrichten_list if not n['gelesen'])

    return render_template('nachrichten.html',
                         nachrichten=nachrichten_list,
                         ungelesen=ungelesen)


@nachrichten_bp.route('/nachricht/<int:nachricht_id>/lesen')
@login_required
def nachricht_lesen(nachricht_id):
    """Nachricht als gelesen markieren"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("""
            SELECT n.* FROM gemeinschafts_nachrichten n
            JOIN mitglied_gemeinschaft mg ON n.gemeinschaft_id = mg.gemeinschaft_id
            WHERE n.id = ? AND mg.mitglied_id = ?
        """)
        cursor.execute(sql, (nachricht_id, session['benutzer_id']))

        if cursor.fetchone():
            db_execute(cursor, """
                INSERT OR IGNORE INTO nachricht_gelesen (nachricht_id, benutzer_id, gelesen_am)
                VALUES (?, ?, ?)
            """, (nachricht_id, session['benutzer_id'], datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            db.connection.commit()

    return redirect(url_for('nachrichten.nachrichten'))


@nachrichten_bp.route('/nachricht/neu', methods=['GET', 'POST'])
@login_required
def nachricht_neu():
    """Neue Nachricht an Gemeinschaft senden"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        if request.method == 'POST':
            gemeinschaft_id = int(request.form.get('gemeinschaft_id'))
            betreff = request.form.get('betreff')
            nachricht = request.form.get('nachricht')

            sql = convert_sql("""
                SELECT COUNT(*) FROM mitglied_gemeinschaft
                WHERE gemeinschaft_id = ? AND mitglied_id = ?
            """)
            cursor.execute(sql, (gemeinschaft_id, session['benutzer_id']))

            if cursor.fetchone()[0] > 0:
                sql = convert_sql("""
                    INSERT INTO gemeinschafts_nachrichten
                    (gemeinschaft_id, absender_id, betreff, inhalt, erstellt_am)
                    VALUES (?, ?, ?, ?, ?)
                """)
                cursor.execute(sql, (gemeinschaft_id, session['benutzer_id'], betreff, nachricht,
                              datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                db.connection.commit()

                flash('Nachricht wurde an alle Mitglieder der Gemeinschaft gesendet!', 'success')
                return redirect(url_for('nachrichten.nachrichten'))
            else:
                flash('Sie sind nicht Mitglied dieser Gemeinschaft.', 'danger')

        sql = convert_sql("""
            SELECT DISTINCT g.* FROM gemeinschaften g
            JOIN mitglied_gemeinschaft mg ON g.id = mg.gemeinschaft_id
            WHERE mg.mitglied_id = ? AND g.aktiv = true
            ORDER BY g.name
        """)
        cursor.execute(sql, (session['benutzer_id'],))

        columns = [desc[0] for desc in cursor.description]
        gemeinschaften = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render_template('nachricht_neu.html', gemeinschaften=gemeinschaften)
