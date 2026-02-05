# -*- coding: utf-8 -*-
"""
Admin - Abstimmungen verwalten (Schriftführer)
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import MaschinenDBContext
from utils.decorators import admin_required, schriftfuehrer_required
from utils.training import get_current_db_path
from utils.sql_helpers import convert_sql

admin_abstimmungen_bp = Blueprint('admin_abstimmungen', __name__, url_prefix='/admin/abstimmungen')


@admin_abstimmungen_bp.route('')
@admin_required
def abstimmungen_liste():
    """Liste aller Abstimmungen"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("""
            SELECT a.*, g.name as gemeinschaft_name,
                   b.name || ', ' || b.vorname as erstellt_von_name
            FROM abstimmungen a
            JOIN gemeinschaften g ON a.gemeinschaft_id = g.id
            JOIN benutzer b ON a.erstellt_von = b.id
            ORDER BY a.erstellt_am DESC
        """)
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        abstimmungen = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Gemeinschaften für Dropdown
        sql = convert_sql("SELECT id, name FROM gemeinschaften WHERE aktiv = true ORDER BY name")
        cursor.execute(sql)
        gemeinschaften = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]

    return render_template('admin_abstimmungen.html',
                         abstimmungen=abstimmungen,
                         gemeinschaften=gemeinschaften)


@admin_abstimmungen_bp.route('/neu', methods=['GET', 'POST'])
@admin_required
def abstimmung_neu():
    """Neue Abstimmung erstellen"""
    db_path = get_current_db_path()

    if request.method == 'POST':
        gemeinschaft_id = request.form.get('gemeinschaft_id')
        titel = request.form.get('titel')
        beschreibung = request.form.get('beschreibung')
        ablauf_datum = request.form.get('ablauf_datum')
        geheim = request.form.get('geheim') == 'on'

        if not gemeinschaft_id or not titel or not ablauf_datum:
            flash('Bitte alle Pflichtfelder ausfüllen.', 'danger')
            return redirect(url_for('admin_abstimmungen.abstimmung_neu'))

        with MaschinenDBContext(db_path) as db:
            cursor = db.connection.cursor()

            sql = convert_sql("""
                INSERT INTO abstimmungen
                (gemeinschaft_id, titel, beschreibung, ablauf_datum, erstellt_von, geheim)
                VALUES (?, ?, ?, ?, ?, ?)
            """)
            cursor.execute(sql, (
                gemeinschaft_id,
                titel,
                beschreibung,
                ablauf_datum,
                session['benutzer_id'],
                geheim
            ))
            db.connection.commit()

        flash('Abstimmung wurde erstellt.', 'success')
        return redirect(url_for('admin_abstimmungen.abstimmungen_liste'))

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()
        sql = convert_sql("SELECT id, name FROM gemeinschaften WHERE aktiv = true ORDER BY name")
        cursor.execute(sql)
        gemeinschaften = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]

    return render_template('admin_abstimmung_form.html',
                         abstimmung=None,
                         gemeinschaften=gemeinschaften)


@admin_abstimmungen_bp.route('/<int:id>')
@admin_required
def abstimmung_detail(id):
    """Abstimmung anzeigen mit Ergebnis"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("""
            SELECT a.*, g.name as gemeinschaft_name,
                   b.name || ', ' || b.vorname as erstellt_von_name
            FROM abstimmungen a
            JOIN gemeinschaften g ON a.gemeinschaft_id = g.id
            JOIN benutzer b ON a.erstellt_von = b.id
            WHERE a.id = ?
        """)
        cursor.execute(sql, (id,))
        row = cursor.fetchone()
        if not row:
            flash('Abstimmung nicht gefunden.', 'danger')
            return redirect(url_for('admin_abstimmungen.abstimmungen_liste'))

        columns = [desc[0] for desc in cursor.description]
        abstimmung = dict(zip(columns, row))

        # Stimmen laden (nur wenn nicht geheim oder abgeschlossen)
        stimmen = []
        if not abstimmung['geheim'] or abstimmung['status'] == 'abgeschlossen':
            sql = convert_sql("""
                SELECT s.*, b.name || ', ' || b.vorname as benutzer_name
                FROM abstimmung_stimmen s
                JOIN benutzer b ON s.benutzer_id = b.id
                WHERE s.abstimmung_id = ?
                ORDER BY s.abgegeben_am
            """)
            cursor.execute(sql, (id,))
            columns = [desc[0] for desc in cursor.description]
            stimmen = [dict(zip(columns, row)) for row in cursor.fetchall()]

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

    return render_template('admin_abstimmung_detail.html',
                         abstimmung=abstimmung,
                         stimmen=stimmen,
                         statistik=statistik)


@admin_abstimmungen_bp.route('/<int:id>/bearbeiten', methods=['GET', 'POST'])
@admin_required
def abstimmung_bearbeiten(id):
    """Abstimmung bearbeiten"""
    db_path = get_current_db_path()

    if request.method == 'POST':
        titel = request.form.get('titel')
        beschreibung = request.form.get('beschreibung')
        ablauf_datum = request.form.get('ablauf_datum')
        geheim = request.form.get('geheim') == 'on'

        with MaschinenDBContext(db_path) as db:
            cursor = db.connection.cursor()

            sql = convert_sql("""
                UPDATE abstimmungen
                SET titel = ?, beschreibung = ?, ablauf_datum = ?, geheim = ?
                WHERE id = ?
            """)
            cursor.execute(sql, (titel, beschreibung, ablauf_datum, geheim, id))
            db.connection.commit()

        flash('Abstimmung wurde aktualisiert.', 'success')
        return redirect(url_for('admin_abstimmungen.abstimmung_detail', id=id))

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("SELECT * FROM abstimmungen WHERE id = ?")
        cursor.execute(sql, (id,))
        row = cursor.fetchone()
        if not row:
            flash('Abstimmung nicht gefunden.', 'danger')
            return redirect(url_for('admin_abstimmungen.abstimmungen_liste'))

        columns = [desc[0] for desc in cursor.description]
        abstimmung = dict(zip(columns, row))

        sql = convert_sql("SELECT id, name FROM gemeinschaften WHERE aktiv = true ORDER BY name")
        cursor.execute(sql)
        gemeinschaften = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]

    return render_template('admin_abstimmung_form.html',
                         abstimmung=abstimmung,
                         gemeinschaften=gemeinschaften)


@admin_abstimmungen_bp.route('/<int:id>/abschliessen', methods=['POST'])
@admin_required
def abstimmung_abschliessen(id):
    """Abstimmung abschließen"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        # Ergebnis berechnen
        sql = convert_sql("""
            SELECT stimme, COUNT(*) as anzahl
            FROM abstimmung_stimmen
            WHERE abstimmung_id = ?
            GROUP BY stimme
        """)
        cursor.execute(sql, (id,))
        ergebnis = {'ja': 0, 'nein': 0, 'enthaltung': 0}
        for row in cursor.fetchall():
            ergebnis[row[0]] = row[1]

        # Abstimmung abschließen mit Ergebnis
        sql = convert_sql("""
            UPDATE abstimmungen
            SET status = 'abgeschlossen',
                ergebnis_ja = ?,
                ergebnis_nein = ?,
                ergebnis_enthaltung = ?
            WHERE id = ?
        """)
        cursor.execute(sql, (ergebnis['ja'], ergebnis['nein'], ergebnis['enthaltung'], id))
        db.connection.commit()

    flash('Abstimmung wurde abgeschlossen.', 'success')
    return redirect(url_for('admin_abstimmungen.abstimmung_detail', id=id))


@admin_abstimmungen_bp.route('/<int:id>/loeschen', methods=['POST'])
@admin_required
def abstimmung_loeschen(id):
    """Abstimmung löschen"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        # Erst Stimmen löschen
        sql = convert_sql("DELETE FROM abstimmung_stimmen WHERE abstimmung_id = ?")
        cursor.execute(sql, (id,))

        # Dann Abstimmung löschen
        sql = convert_sql("DELETE FROM abstimmungen WHERE id = ?")
        cursor.execute(sql, (id,))
        db.connection.commit()

    flash('Abstimmung wurde gelöscht.', 'success')
    return redirect(url_for('admin_abstimmungen.abstimmungen_liste'))
