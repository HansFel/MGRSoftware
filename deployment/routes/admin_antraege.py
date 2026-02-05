# -*- coding: utf-8 -*-
"""
Admin - Anträge verwalten (Schriftführer)
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import MaschinenDBContext
from utils.decorators import admin_required
from utils.training import get_current_db_path
from utils.sql_helpers import convert_sql

admin_antraege_bp = Blueprint('admin_antraege', __name__, url_prefix='/admin/antraege')


@admin_antraege_bp.route('')
@admin_required
def antraege_liste():
    """Liste aller Anträge"""
    db_path = get_current_db_path()

    status_filter = request.args.get('status', '')

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        if status_filter:
            sql = convert_sql("""
                SELECT a.*, g.name as gemeinschaft_name,
                       b.name || ', ' || b.vorname as antragsteller,
                       bb.name || ', ' || bb.vorname as bearbeiter_name
                FROM antraege a
                JOIN gemeinschaften g ON a.gemeinschaft_id = g.id
                JOIN benutzer b ON a.benutzer_id = b.id
                LEFT JOIN benutzer bb ON a.bearbeitet_von = bb.id
                WHERE a.status = ?
                ORDER BY a.erstellt_am DESC
            """)
            cursor.execute(sql, (status_filter,))
        else:
            sql = convert_sql("""
                SELECT a.*, g.name as gemeinschaft_name,
                       b.name || ', ' || b.vorname as antragsteller,
                       bb.name || ', ' || bb.vorname as bearbeiter_name
                FROM antraege a
                JOIN gemeinschaften g ON a.gemeinschaft_id = g.id
                JOIN benutzer b ON a.benutzer_id = b.id
                LEFT JOIN benutzer bb ON a.bearbeitet_von = bb.id
                ORDER BY a.erstellt_am DESC
            """)
            cursor.execute(sql)

        columns = [desc[0] for desc in cursor.description]
        antraege = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Statistik
        sql = convert_sql("""
            SELECT status, COUNT(*) as anzahl
            FROM antraege
            GROUP BY status
        """)
        cursor.execute(sql)
        statistik = {'eingereicht': 0, 'angenommen': 0, 'abgelehnt': 0}
        for row in cursor.fetchall():
            statistik[row[0]] = row[1]

    return render_template('admin_antraege.html',
                         antraege=antraege,
                         statistik=statistik,
                         status_filter=status_filter)


@admin_antraege_bp.route('/<int:id>')
@admin_required
def antrag_detail(id):
    """Antrag anzeigen"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("""
            SELECT a.*, g.name as gemeinschaft_name,
                   b.name || ', ' || b.vorname as antragsteller,
                   bb.name || ', ' || bb.vorname as bearbeiter_name
            FROM antraege a
            JOIN gemeinschaften g ON a.gemeinschaft_id = g.id
            JOIN benutzer b ON a.benutzer_id = b.id
            LEFT JOIN benutzer bb ON a.bearbeitet_von = bb.id
            WHERE a.id = ?
        """)
        cursor.execute(sql, (id,))
        row = cursor.fetchone()
        if not row:
            flash('Antrag nicht gefunden.', 'danger')
            return redirect(url_for('admin_antraege.antraege_liste'))

        columns = [desc[0] for desc in cursor.description]
        antrag = dict(zip(columns, row))

    return render_template('admin_antrag_detail.html', antrag=antrag)


@admin_antraege_bp.route('/<int:id>/status', methods=['POST'])
@admin_required
def antrag_status(id):
    """Status ändern (annehmen/ablehnen)"""
    db_path = get_current_db_path()

    neuer_status = request.form.get('status')
    bemerkung = request.form.get('bemerkung', '')

    if neuer_status not in ['angenommen', 'abgelehnt']:
        flash('Ungültiger Status.', 'danger')
        return redirect(url_for('admin_antraege.antrag_detail', id=id))

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("""
            UPDATE antraege
            SET status = ?,
                bearbeitet_am = ?,
                bearbeitet_von = ?,
                bemerkung = ?
            WHERE id = ?
        """)
        cursor.execute(sql, (
            neuer_status,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            session['benutzer_id'],
            bemerkung,
            id
        ))
        db.connection.commit()

    if neuer_status == 'angenommen':
        flash('Antrag wurde angenommen.', 'success')
    else:
        flash('Antrag wurde abgelehnt.', 'warning')

    return redirect(url_for('admin_antraege.antrag_detail', id=id))


@admin_antraege_bp.route('/<int:id>/loeschen', methods=['POST'])
@admin_required
def antrag_loeschen(id):
    """Antrag löschen"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("DELETE FROM antraege WHERE id = ?")
        cursor.execute(sql, (id,))
        db.connection.commit()

    flash('Antrag wurde gelöscht.', 'success')
    return redirect(url_for('admin_antraege.antraege_liste'))
