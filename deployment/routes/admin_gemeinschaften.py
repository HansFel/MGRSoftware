# -*- coding: utf-8 -*-
"""
Admin - Gemeinschaften-Verwaltung
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import MaschinenDBContext
from utils.decorators import admin_required
from utils.training import get_current_db_path
from utils.sql_helpers import convert_sql

admin_gemeinschaften_bp = Blueprint('admin_gemeinschaften', __name__, url_prefix='/admin')


@admin_gemeinschaften_bp.route('/gemeinschaften')
@admin_required
def admin_gemeinschaften():
    """Gemeinschaften verwalten"""
    db_path = get_current_db_path()
    with MaschinenDBContext(db_path) as db:
        cursor = db.cursor
        sql = convert_sql("SELECT * FROM gemeinschaften_uebersicht ORDER BY name")
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        gemeinschaften = [dict(zip(columns, row)) for row in cursor.fetchall()]
    return render_template('admin_gemeinschaften.html', gemeinschaften=gemeinschaften)


@admin_gemeinschaften_bp.route('/gemeinschaften/neu', methods=['GET', 'POST'])
@admin_required
def admin_gemeinschaften_neu():
    """Neue Gemeinschaft"""
    db_path = get_current_db_path()
    if request.method == 'POST':
        with MaschinenDBContext(db_path) as db:
            cursor = db.cursor
            sql = convert_sql("""
                INSERT INTO gemeinschaften (name, beschreibung, aktiv)
                VALUES (?, ?, ?)
            """)
            cursor.execute(sql, (
                request.form['name'],
                request.form.get('beschreibung'),
                1 if request.form.get('aktiv') else 0
            ))
            db.connection.commit()
        flash('Gemeinschaft erfolgreich angelegt!', 'success')
        return redirect(url_for('admin_gemeinschaften.admin_gemeinschaften'))
    return render_template('admin_gemeinschaften_form.html', gemeinschaft=None)


@admin_gemeinschaften_bp.route('/gemeinschaften/<int:gemeinschaft_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_gemeinschaften_edit(gemeinschaft_id):
    """Gemeinschaft bearbeiten"""
    db_path = get_current_db_path()
    with MaschinenDBContext(db_path) as db:
        cursor = db.cursor

        if request.method == 'POST':
            sql = convert_sql("""
                UPDATE gemeinschaften
                SET name = ?,
                    beschreibung = ?,
                    adresse = ?,
                    telefon = ?,
                    email = ?,
                    aktiv = ?,
                    bank_name = ?,
                    bank_iban = ?,
                    bank_bic = ?,
                    bank_kontoinhaber = ?
                WHERE id = ?
            """)
            cursor.execute(sql, (
                request.form['name'],
                request.form.get('beschreibung'),
                request.form.get('adresse'),
                request.form.get('telefon'),
                request.form.get('email'),
                1 if request.form.get('aktiv') else 0,
                request.form.get('bank_name'),
                request.form.get('bank_iban'),
                request.form.get('bank_bic'),
                request.form.get('bank_kontoinhaber'),
                gemeinschaft_id
            ))
            db.connection.commit()
            flash('Gemeinschaft erfolgreich aktualisiert!', 'success')
            return redirect(url_for('admin_gemeinschaften.admin_gemeinschaften'))

        sql = convert_sql("SELECT * FROM gemeinschaften WHERE id = ?")
        cursor.execute(sql, (gemeinschaft_id,))
        columns = [desc[0] for desc in cursor.description]
        gemeinschaft = dict(zip(columns, cursor.fetchone()))

    return render_template('admin_gemeinschaften_form.html', gemeinschaft=gemeinschaft)


@admin_gemeinschaften_bp.route('/gemeinschaften/<int:gemeinschaft_id>/mitglieder', methods=['GET', 'POST'])
@admin_required
def admin_gemeinschaften_mitglieder(gemeinschaft_id):
    """Mitglieder einer Gemeinschaft verwalten"""
    db_path = get_current_db_path()
    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("SELECT * FROM gemeinschaften WHERE id = ?")
        cursor.execute(sql, (gemeinschaft_id,))
        columns = [desc[0] for desc in cursor.description]
        gemeinschaft = dict(zip(columns, cursor.fetchone()))

        if request.method == 'POST':
            action = request.form.get('action')
            benutzer_id = int(request.form.get('benutzer_id'))

            if action == 'hinzufuegen':
                sql = convert_sql("""
                    INSERT INTO mitglied_gemeinschaft (mitglied_id, gemeinschaft_id)
                    VALUES (?, ?)
                    ON CONFLICT DO NOTHING
                """)
                cursor.execute(sql, (benutzer_id, gemeinschaft_id))
                flash('Mitglied hinzugefügt!', 'success')
            elif action == 'entfernen':
                sql = convert_sql("""
                    DELETE FROM mitglied_gemeinschaft
                    WHERE mitglied_id = ? AND gemeinschaft_id = ?
                """)
                cursor.execute(sql, (benutzer_id, gemeinschaft_id))
                flash('Mitglied entfernt!', 'success')

            db.connection.commit()
            return redirect(url_for('admin_gemeinschaften.admin_gemeinschaften_mitglieder',
                                   gemeinschaft_id=gemeinschaft_id))

        # Mitglieder laden
        sql = convert_sql("""
            SELECT b.*, mg.beigetreten_am
            FROM benutzer b
            JOIN mitglied_gemeinschaft mg ON b.id = mg.mitglied_id
            WHERE mg.gemeinschaft_id = ?
            ORDER BY b.name
        """)
        cursor.execute(sql, (gemeinschaft_id,))
        columns = [desc[0] for desc in cursor.description]
        mitglieder = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Alle Benutzer (für Hinzufügen)
        sql = convert_sql("""
            SELECT b.* FROM benutzer b
            WHERE b.aktiv = true
            AND b.id NOT IN (
                SELECT mitglied_id FROM mitglied_gemeinschaft
                WHERE gemeinschaft_id = ?
            )
            ORDER BY b.name
        """)
        cursor.execute(sql, (gemeinschaft_id,))
        columns = [desc[0] for desc in cursor.description]
        verfuegbare_benutzer = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render_template('admin_gemeinschaften_mitglieder.html',
                         gemeinschaft=gemeinschaft,
                         mitglieder=mitglieder,
                         verfuegbare_benutzer=verfuegbare_benutzer)


@admin_gemeinschaften_bp.route('/gemeinschaften/<int:gemeinschaft_id>/abrechnung')
@admin_required
def admin_gemeinschaften_abrechnung(gemeinschaft_id):
    """Abrechnungsübersicht einer Gemeinschaft"""
    db_path = get_current_db_path()
    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("SELECT * FROM gemeinschaften WHERE id = ?")
        cursor.execute(sql, (gemeinschaft_id,))
        columns = [desc[0] for desc in cursor.description]
        gemeinschaft = dict(zip(columns, cursor.fetchone()))

        # Einsätze nach Mitglied
        sql = convert_sql("""
            SELECT
                b.id,
                b.vorname || ' ' || b.name as mitglied_name,
                COUNT(e.id) as anzahl_einsaetze,
                SUM(e.endstand - e.anfangstand) as betriebsstunden,
                SUM(
                    CASE
                        WHEN m.abrechnungsart = 'stunden' THEN (e.endstand - e.anfangstand) * COALESCE(m.preis_pro_einheit, 0)
                        ELSE COALESCE(e.flaeche_menge, 0) * COALESCE(m.preis_pro_einheit, 0)
                    END
                ) as maschinenkosten,
                SUM(COALESCE(e.treibstoffkosten, 0)) as treibstoffkosten
            FROM maschineneinsaetze e
            JOIN maschinen m ON e.maschine_id = m.id
            JOIN benutzer b ON e.benutzer_id = b.id
            WHERE m.gemeinschaft_id = ?
            GROUP BY b.id, b.vorname, b.name
            ORDER BY maschinenkosten DESC
        """)
        cursor.execute(sql, (gemeinschaft_id,))
        columns = [desc[0] for desc in cursor.description]
        mitglieder_kosten = [dict(zip(columns, row)) for row in cursor.fetchall()]

        for m in mitglieder_kosten:
            m['gesamt'] = (m['maschinenkosten'] or 0) + (m['treibstoffkosten'] or 0)

    return render_template('admin_gemeinschaften_abrechnung.html',
                         gemeinschaft=gemeinschaft,
                         mitglieder_kosten=mitglieder_kosten)
