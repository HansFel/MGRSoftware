# -*- coding: utf-8 -*-
"""
Routes für Betriebe-Verwaltung
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime

from database import MaschinenDBContext
from utils.decorators import admin_required
from utils.training import get_current_db_path
from utils.sql_helpers import convert_sql

admin_betriebe_bp = Blueprint('admin_betriebe', __name__, url_prefix='/admin')


@admin_betriebe_bp.route('/betriebe')
@admin_required
def betriebe_liste():
    """Liste aller Betriebe"""
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
                return render_template('admin_betriebe.html', gemeinschaften=[], betriebe=[])

        gemeinschaften = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]

        # Ausgewählte Gemeinschaft
        gemeinschaft_id = request.args.get('gemeinschaft_id', type=int)
        if not gemeinschaft_id and gemeinschaften:
            gemeinschaft_id = gemeinschaften[0]['id']

        # Betriebe laden mit Anzahl Benutzer
        betriebe = []
        if gemeinschaft_id:
            sql = convert_sql("""
                SELECT b.*,
                       (SELECT COUNT(*) FROM benutzer WHERE betrieb_id = b.id) as anzahl_benutzer
                FROM betriebe b
                WHERE b.gemeinschaft_id = ?
                ORDER BY b.name
            """)
            cursor.execute(sql, (gemeinschaft_id,))
            columns = [desc[0] for desc in cursor.description]
            betriebe = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render_template('admin_betriebe.html',
                         gemeinschaften=gemeinschaften,
                         gemeinschaft_id=gemeinschaft_id,
                         betriebe=betriebe)


@admin_betriebe_bp.route('/betriebe/neu', methods=['GET', 'POST'])
@admin_required
def betrieb_neu():
    """Neuen Betrieb anlegen (nur Grunddaten, keine Gemeinschaft)"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            adresse = request.form.get('adresse', '').strip()
            telefon = request.form.get('telefon', '').strip()
            email = request.form.get('email', '').strip()
            iban = request.form.get('iban', '').strip()
            bic = request.form.get('bic', '').strip()
            bank_name = request.form.get('bank_name', '').strip()
            notizen = request.form.get('notizen', '').strip()

            if not name:
                flash('Bitte geben Sie einen Namen ein.', 'danger')
                return render_template('admin_betrieb_neu.html')

            # Betrieb ohne Gemeinschaft erstellen (gemeinschaft_id = NULL)
            sql = convert_sql("""
                INSERT INTO betriebe (name, adresse, telefon, email, iban, bic, bank_name, notizen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id
            """)
            cursor.execute(sql, (name, adresse, telefon, email, iban, bic, bank_name, notizen))
            betrieb_id = cursor.fetchone()[0]
            db.connection.commit()

            flash('Betrieb wurde erstellt. Bitte weisen Sie nun eine Gemeinschaft zu.', 'success')
            return redirect(url_for('admin_betriebe.betrieb_gemeinschaft', betrieb_id=betrieb_id))

    return render_template('admin_betrieb_neu.html')


@admin_betriebe_bp.route('/betriebe/<int:betrieb_id>/gemeinschaft', methods=['GET', 'POST'])
@admin_required
def betrieb_gemeinschaft(betrieb_id):
    """Gemeinschaft einem Betrieb zuweisen"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        # Betrieb laden
        sql = convert_sql("SELECT * FROM betriebe WHERE id = ?")
        cursor.execute(sql, (betrieb_id,))
        columns = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()

        if not row:
            flash('Betrieb nicht gefunden.', 'danger')
            return redirect(url_for('admin_betriebe.betriebe_liste'))

        betrieb = dict(zip(columns, row))

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
                flash('Keine Gemeinschaft verfügbar.', 'warning')
                return redirect(url_for('admin_betriebe.betriebe_liste'))

        gemeinschaften = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]

        if request.method == 'POST':
            gemeinschaft_id = request.form.get('gemeinschaft_id', type=int)

            if not gemeinschaft_id:
                flash('Bitte wählen Sie eine Gemeinschaft.', 'danger')
            else:
                sql = convert_sql("UPDATE betriebe SET gemeinschaft_id = ? WHERE id = ?")
                cursor.execute(sql, (gemeinschaft_id, betrieb_id))
                db.connection.commit()

                flash('Gemeinschaft wurde zugewiesen.', 'success')
                return redirect(url_for('admin_betriebe.betrieb_bearbeiten', betrieb_id=betrieb_id))

    return render_template('admin_betrieb_gemeinschaft.html',
                         betrieb=betrieb,
                         gemeinschaften=gemeinschaften)


@admin_betriebe_bp.route('/betriebe/<int:betrieb_id>/bearbeiten', methods=['GET', 'POST'])
@admin_required
def betrieb_bearbeiten(betrieb_id):
    """Betrieb bearbeiten"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        # Betrieb laden
        sql = convert_sql("SELECT * FROM betriebe WHERE id = ?")
        cursor.execute(sql, (betrieb_id,))
        columns = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()

        if not row:
            flash('Betrieb nicht gefunden.', 'danger')
            return redirect(url_for('admin_betriebe.betriebe_liste'))

        betrieb = dict(zip(columns, row))

        # Prüfen ob Gemeinschaft zugewiesen
        if not betrieb.get('gemeinschaft_id'):
            flash('Bitte weisen Sie zuerst eine Gemeinschaft zu.', 'warning')
            return redirect(url_for('admin_betriebe.betrieb_gemeinschaft', betrieb_id=betrieb_id))

        # Gemeinschaften laden
        sql = convert_sql("SELECT id, name FROM gemeinschaften WHERE aktiv = true OR aktiv IS NULL ORDER BY name")
        cursor.execute(sql)
        gemeinschaften = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]

        # Benutzer des Betriebs laden (für Kontaktperson-Auswahl)
        sql = convert_sql("""
            SELECT id, vorname, name, email
            FROM benutzer
            WHERE betrieb_id = ?
            ORDER BY name, vorname
        """)
        cursor.execute(sql, (betrieb_id,))
        benutzer = [{'id': row[0], 'vorname': row[1], 'name': row[2], 'email': row[3]} for row in cursor.fetchall()]

        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            adresse = request.form.get('adresse', '').strip()
            kontaktperson_id = request.form.get('kontaktperson_id', type=int)
            telefon = request.form.get('telefon', '').strip()
            email = request.form.get('email', '').strip()
            iban = request.form.get('iban', '').strip()
            bic = request.form.get('bic', '').strip()
            bank_name = request.form.get('bank_name', '').strip()
            notizen = request.form.get('notizen', '').strip()
            aktiv = request.form.get('aktiv') == 'on'

            if not name:
                flash('Bitte geben Sie einen Namen ein.', 'danger')
                return render_template('admin_betrieb_form.html',
                                     gemeinschaften=gemeinschaften,
                                     betrieb=betrieb,
                                     benutzer=benutzer)

            # Kontaktperson-Name ermitteln
            kontaktperson = ''
            if kontaktperson_id:
                for b in benutzer:
                    if b['id'] == kontaktperson_id:
                        kontaktperson = f"{b['vorname']} {b['name']}".strip()
                        break

            sql = convert_sql("""
                UPDATE betriebe
                SET name = ?, adresse = ?, kontaktperson = ?, telefon = ?, email = ?,
                    iban = ?, bic = ?, bank_name = ?, notizen = ?, aktiv = ?
                WHERE id = ?
            """)
            cursor.execute(sql, (name, adresse, kontaktperson, telefon, email, iban, bic, bank_name, notizen, aktiv, betrieb_id))
            db.connection.commit()

            flash('Betrieb wurde gespeichert.', 'success')
            return redirect(url_for('admin_betriebe.betrieb_bearbeiten', betrieb_id=betrieb_id))

    return render_template('admin_betrieb_form.html',
                         gemeinschaften=gemeinschaften,
                         betrieb=betrieb,
                         benutzer=benutzer)


@admin_betriebe_bp.route('/betriebe/<int:betrieb_id>/benutzer', methods=['GET', 'POST'])
@admin_required
def betrieb_benutzer(betrieb_id):
    """Benutzer einem Betrieb zuordnen"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        # Betrieb laden
        sql = convert_sql("SELECT * FROM betriebe WHERE id = ?")
        cursor.execute(sql, (betrieb_id,))
        columns = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()

        if not row:
            flash('Betrieb nicht gefunden.', 'danger')
            return redirect(url_for('admin_betriebe.betriebe_liste'))

        betrieb = dict(zip(columns, row))

        if request.method == 'POST':
            action = request.form.get('action')
            benutzer_id = request.form.get('benutzer_id', type=int)

            if action == 'add' and benutzer_id:
                sql = convert_sql("UPDATE benutzer SET betrieb_id = ? WHERE id = ?")
                cursor.execute(sql, (betrieb_id, benutzer_id))
                db.connection.commit()
                flash('Benutzer wurde dem Betrieb zugeordnet.', 'success')

            elif action == 'remove' and benutzer_id:
                # Benutzer braucht einen eigenen Betrieb
                # Erstelle neuen Betrieb für den Benutzer
                sql = convert_sql("SELECT vorname, name FROM benutzer WHERE id = ?")
                cursor.execute(sql, (benutzer_id,))
                user_row = cursor.fetchone()
                if user_row:
                    new_name = f"{user_row[0]} {user_row[1]}".strip() if user_row[0] else user_row[1]
                    sql = convert_sql("""
                        INSERT INTO betriebe (gemeinschaft_id, name, kontaktperson)
                        VALUES (?, ?, ?)
                        RETURNING id
                    """)
                    cursor.execute(sql, (betrieb['gemeinschaft_id'], new_name, new_name))
                    new_betrieb_id = cursor.fetchone()[0]

                    sql = convert_sql("UPDATE benutzer SET betrieb_id = ? WHERE id = ?")
                    cursor.execute(sql, (new_betrieb_id, benutzer_id))
                    db.connection.commit()
                    flash(f'Benutzer wurde entfernt und neuer Betrieb "{new_name}" erstellt.', 'success')

        # Benutzer des Betriebs laden
        sql = convert_sql("""
            SELECT id, vorname, name, email
            FROM benutzer
            WHERE betrieb_id = ?
            ORDER BY name, vorname
        """)
        cursor.execute(sql, (betrieb_id,))
        benutzer_im_betrieb = [{'id': row[0], 'vorname': row[1], 'name': row[2], 'email': row[3]} for row in cursor.fetchall()]

        # Verfügbare Benutzer (ohne Betrieb oder in anderen Betrieben der gleichen Gemeinschaft)
        sql = convert_sql("""
            SELECT DISTINCT b.id, b.vorname, b.name, b.email, bt.name as betrieb_name
            FROM benutzer b
            JOIN benutzer_gemeinschaften bg ON b.id = bg.benutzer_id
            LEFT JOIN betriebe bt ON b.betrieb_id = bt.id
            WHERE bg.gemeinschaft_id = ?
            AND (b.betrieb_id IS NULL OR b.betrieb_id != ?)
            AND (b.aktiv = true OR b.aktiv IS NULL)
            ORDER BY b.name, b.vorname
        """)
        cursor.execute(sql, (betrieb['gemeinschaft_id'], betrieb_id))
        verfuegbare_benutzer = [{'id': row[0], 'vorname': row[1], 'name': row[2], 'email': row[3], 'betrieb_name': row[4]} for row in cursor.fetchall()]

    return render_template('admin_betrieb_benutzer.html',
                         betrieb=betrieb,
                         benutzer_im_betrieb=benutzer_im_betrieb,
                         verfuegbare_benutzer=verfuegbare_benutzer)


@admin_betriebe_bp.route('/betriebe/<int:betrieb_id>/loeschen', methods=['POST'])
@admin_required
def betrieb_loeschen(betrieb_id):
    """Betrieb löschen (nur wenn keine Benutzer zugeordnet)"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        # Prüfen ob Benutzer zugeordnet sind
        sql = convert_sql("SELECT COUNT(*) FROM benutzer WHERE betrieb_id = ?")
        cursor.execute(sql, (betrieb_id,))
        count = cursor.fetchone()[0]

        if count > 0:
            flash(f'Betrieb kann nicht gelöscht werden - {count} Benutzer zugeordnet.', 'danger')
            return redirect(url_for('admin_betriebe.betrieb_bearbeiten', betrieb_id=betrieb_id))

        # Betrieb löschen
        sql = convert_sql("DELETE FROM betriebe WHERE id = ?")
        cursor.execute(sql, (betrieb_id,))
        db.connection.commit()

        flash('Betrieb wurde gelöscht.', 'success')

    return redirect(url_for('admin_betriebe.betriebe_liste'))
