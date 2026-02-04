# -*- coding: utf-8 -*-
"""
Routes für Schriftführer-Funktionen (Protokolle, Abstimmungen, Wahlen)
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime

from database import MaschinenDBContext
from utils.decorators import admin_required
from utils.training import get_current_db_path
from utils.sql_helpers import convert_sql

admin_schriftfuehrer_bp = Blueprint('admin_schriftfuehrer', __name__, url_prefix='/admin')


# ==================== PROTOKOLLE ====================

@admin_schriftfuehrer_bp.route('/protokolle')
@admin_required
def protokolle_liste():
    """Liste aller Protokolle"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        # Gemeinschaften laden (je nach Admin-Level)
        if session.get('admin_level', 0) >= 2:
            sql = convert_sql("SELECT id, name FROM gemeinschaften WHERE aktiv = true OR aktiv IS NULL ORDER BY name")
            cursor.execute(sql)
        else:
            gemeinschafts_ids = session.get('gemeinschafts_admin_ids', [])
            if gemeinschafts_ids:
                placeholders = ','.join(['?' for _ in gemeinschafts_ids])
                sql = convert_sql(f"SELECT id, name FROM gemeinschaften WHERE id IN ({placeholders}) ORDER BY name")
                cursor.execute(sql, gemeinschafts_ids)
            else:
                return render_template('admin_protokolle.html', gemeinschaften=[], protokolle=[])

        gemeinschaften = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]

        # Ausgewählte Gemeinschaft
        gemeinschaft_id = request.args.get('gemeinschaft_id', type=int)
        if not gemeinschaft_id and gemeinschaften:
            gemeinschaft_id = gemeinschaften[0]['id']

        # Protokolle laden
        protokolle = []
        if gemeinschaft_id:
            sql = convert_sql("""
                SELECT p.*, b.vorname || ' ' || b.name as erstellt_von_name
                FROM protokolle p
                LEFT JOIN benutzer b ON p.erstellt_von = b.id
                WHERE p.gemeinschaft_id = ?
                ORDER BY p.datum DESC, p.id DESC
            """)
            cursor.execute(sql, (gemeinschaft_id,))
            columns = [desc[0] for desc in cursor.description]
            protokolle = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render_template('admin_protokolle.html',
                         gemeinschaften=gemeinschaften,
                         gemeinschaft_id=gemeinschaft_id,
                         protokolle=protokolle)


@admin_schriftfuehrer_bp.route('/protokolle/neu', methods=['GET', 'POST'])
@admin_required
def protokoll_neu():
    """Neues Protokoll anlegen"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        # Gemeinschaften laden
        if session.get('admin_level', 0) >= 2:
            sql = convert_sql("SELECT id, name FROM gemeinschaften WHERE aktiv = true OR aktiv IS NULL ORDER BY name")
            cursor.execute(sql)
        else:
            gemeinschafts_ids = session.get('gemeinschafts_admin_ids', [])
            if gemeinschafts_ids:
                placeholders = ','.join(['?' for _ in gemeinschafts_ids])
                sql = convert_sql(f"SELECT id, name FROM gemeinschaften WHERE id IN ({placeholders}) ORDER BY name")
                cursor.execute(sql, gemeinschafts_ids)
            else:
                flash('Keine Gemeinschaft zugewiesen.', 'warning')
                return redirect(url_for('admin_schriftfuehrer.protokolle_liste'))

        gemeinschaften = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]

        if request.method == 'POST':
            gemeinschaft_id = request.form.get('gemeinschaft_id', type=int)
            titel = request.form.get('titel', '').strip()
            datum = request.form.get('datum')
            inhalt = request.form.get('inhalt', '').strip()

            if not titel:
                flash('Bitte geben Sie einen Titel ein.', 'danger')
                return render_template('admin_protokoll_form.html',
                                     gemeinschaften=gemeinschaften,
                                     protokoll=None,
                                     heute=datetime.now().strftime('%Y-%m-%d'))

            sql = convert_sql("""
                INSERT INTO protokolle (gemeinschaft_id, titel, datum, inhalt, erstellt_von)
                VALUES (?, ?, ?, ?, ?)
                RETURNING id
            """)
            cursor.execute(sql, (gemeinschaft_id, titel, datum, inhalt, session['benutzer_id']))
            protokoll_id = cursor.fetchone()[0]
            db.connection.commit()

            flash('Protokoll wurde erstellt.', 'success')
            return redirect(url_for('admin_schriftfuehrer.protokoll_bearbeiten', protokoll_id=protokoll_id))

    return render_template('admin_protokoll_form.html',
                         gemeinschaften=gemeinschaften,
                         protokoll=None,
                         heute=datetime.now().strftime('%Y-%m-%d'))


@admin_schriftfuehrer_bp.route('/protokolle/<int:protokoll_id>/bearbeiten', methods=['GET', 'POST'])
@admin_required
def protokoll_bearbeiten(protokoll_id):
    """Protokoll bearbeiten"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        # Protokoll laden
        sql = convert_sql("SELECT * FROM protokolle WHERE id = ?")
        cursor.execute(sql, (protokoll_id,))
        columns = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()

        if not row:
            flash('Protokoll nicht gefunden.', 'danger')
            return redirect(url_for('admin_schriftfuehrer.protokolle_liste'))

        protokoll = dict(zip(columns, row))

        # Prüfen ob bereits abgeschlossen
        if protokoll['status'] == 'abgeschlossen':
            flash('Abgeschlossene Protokolle können nicht bearbeitet werden.', 'warning')
            return redirect(url_for('admin_schriftfuehrer.protokoll_ansehen', protokoll_id=protokoll_id))

        # Gemeinschaften laden
        sql = convert_sql("SELECT id, name FROM gemeinschaften WHERE aktiv = true OR aktiv IS NULL ORDER BY name")
        cursor.execute(sql)
        gemeinschaften = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]

        if request.method == 'POST':
            titel = request.form.get('titel', '').strip()
            datum = request.form.get('datum')
            inhalt = request.form.get('inhalt', '').strip()

            if not titel:
                flash('Bitte geben Sie einen Titel ein.', 'danger')
                return render_template('admin_protokoll_form.html',
                                     gemeinschaften=gemeinschaften,
                                     protokoll=protokoll,
                                     heute=datetime.now().strftime('%Y-%m-%d'))

            sql = convert_sql("""
                UPDATE protokolle
                SET titel = ?, datum = ?, inhalt = ?
                WHERE id = ?
            """)
            cursor.execute(sql, (titel, datum, inhalt, protokoll_id))
            db.connection.commit()

            flash('Protokoll wurde gespeichert.', 'success')
            return redirect(url_for('admin_schriftfuehrer.protokoll_bearbeiten', protokoll_id=protokoll_id))

    return render_template('admin_protokoll_form.html',
                         gemeinschaften=gemeinschaften,
                         protokoll=protokoll,
                         heute=datetime.now().strftime('%Y-%m-%d'))


@admin_schriftfuehrer_bp.route('/protokolle/<int:protokoll_id>')
@admin_required
def protokoll_ansehen(protokoll_id):
    """Protokoll ansehen"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("""
            SELECT p.*,
                   b1.vorname || ' ' || b1.name as erstellt_von_name,
                   b2.vorname || ' ' || b2.name as abgeschlossen_von_name,
                   g.name as gemeinschaft_name
            FROM protokolle p
            LEFT JOIN benutzer b1 ON p.erstellt_von = b1.id
            LEFT JOIN benutzer b2 ON p.abgeschlossen_von = b2.id
            LEFT JOIN gemeinschaften g ON p.gemeinschaft_id = g.id
            WHERE p.id = ?
        """)
        cursor.execute(sql, (protokoll_id,))
        columns = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()

        if not row:
            flash('Protokoll nicht gefunden.', 'danger')
            return redirect(url_for('admin_schriftfuehrer.protokolle_liste'))

        protokoll = dict(zip(columns, row))

    return render_template('admin_protokoll_ansehen.html', protokoll=protokoll)


@admin_schriftfuehrer_bp.route('/protokolle/<int:protokoll_id>/abschliessen', methods=['POST'])
@admin_required
def protokoll_abschliessen(protokoll_id):
    """Protokoll abschließen"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("""
            UPDATE protokolle
            SET status = 'abgeschlossen',
                abgeschlossen_am = CURRENT_TIMESTAMP,
                abgeschlossen_von = ?
            WHERE id = ? AND status = 'entwurf'
        """)
        cursor.execute(sql, (session['benutzer_id'], protokoll_id))
        db.connection.commit()

        if cursor.rowcount > 0:
            flash('Protokoll wurde abgeschlossen.', 'success')
        else:
            flash('Protokoll konnte nicht abgeschlossen werden.', 'warning')

    return redirect(url_for('admin_schriftfuehrer.protokoll_ansehen', protokoll_id=protokoll_id))


@admin_schriftfuehrer_bp.route('/protokolle/<int:protokoll_id>/loeschen', methods=['POST'])
@admin_required
def protokoll_loeschen(protokoll_id):
    """Protokoll löschen (nur Entwürfe)"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        # Nur Entwürfe können gelöscht werden
        sql = convert_sql("DELETE FROM protokolle WHERE id = ? AND status = 'entwurf'")
        cursor.execute(sql, (protokoll_id,))
        db.connection.commit()

        if cursor.rowcount > 0:
            flash('Protokoll wurde gelöscht.', 'success')
        else:
            flash('Abgeschlossene Protokolle können nicht gelöscht werden.', 'warning')

    return redirect(url_for('admin_schriftfuehrer.protokolle_liste'))
