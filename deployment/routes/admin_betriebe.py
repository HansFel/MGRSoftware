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

        # Alle Betriebe laden mit Anzahl Benutzer und zugewiesenen Gemeinschaften
        sql = convert_sql("""
            SELECT b.*,
                   (SELECT COUNT(*) FROM benutzer_betriebe WHERE betrieb_id = b.id) as anzahl_benutzer,
                   (SELECT string_agg(g.name, ', ') FROM betriebe_gemeinschaften bg
                    JOIN gemeinschaften g ON bg.gemeinschaft_id = g.id
                    WHERE bg.betrieb_id = b.id) as gemeinschaften_namen
            FROM betriebe b
            ORDER BY b.name
        """)
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        betriebe = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render_template('admin_betriebe.html', betriebe=betriebe)


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
            return redirect(url_for('admin_betriebe.betrieb_gemeinschaften', betrieb_id=betrieb_id))

    return render_template('admin_betrieb_neu.html')


@admin_betriebe_bp.route('/betriebe/<int:betrieb_id>/gemeinschaften', methods=['GET', 'POST'])
@admin_required
def betrieb_gemeinschaften(betrieb_id):
    """Gemeinschaften einem Betrieb zuweisen (mehrere möglich)"""
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

        # Alle Gemeinschaften laden
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

        # Bereits zugewiesene Gemeinschaften laden
        sql = convert_sql("SELECT gemeinschaft_id FROM betriebe_gemeinschaften WHERE betrieb_id = ?")
        cursor.execute(sql, (betrieb_id,))
        zugewiesene_ids = [row[0] for row in cursor.fetchall()]

        if request.method == 'POST':
            # Ausgewählte Gemeinschaften aus Form holen
            neue_ids = request.form.getlist('gemeinschaft_ids', type=int)

            # Alte Zuweisungen löschen
            sql = convert_sql("DELETE FROM betriebe_gemeinschaften WHERE betrieb_id = ?")
            cursor.execute(sql, (betrieb_id,))

            # Neue Zuweisungen einfügen
            for gid in neue_ids:
                sql = convert_sql("INSERT INTO betriebe_gemeinschaften (betrieb_id, gemeinschaft_id) VALUES (?, ?)")
                cursor.execute(sql, (betrieb_id, gid))

            db.connection.commit()

            flash(f'{len(neue_ids)} Gemeinschaft(en) zugewiesen.', 'success')
            return redirect(url_for('admin_betriebe.betrieb_bearbeiten', betrieb_id=betrieb_id))

    return render_template('admin_betrieb_gemeinschaften.html',
                         betrieb=betrieb,
                         gemeinschaften=gemeinschaften,
                         zugewiesene_ids=zugewiesene_ids)


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

        # Prüfen ob Gemeinschaft zugewiesen (über Verknüpfungstabelle)
        sql = convert_sql("SELECT COUNT(*) FROM betriebe_gemeinschaften WHERE betrieb_id = ?")
        cursor.execute(sql, (betrieb_id,))
        if cursor.fetchone()[0] == 0:
            flash('Bitte weisen Sie zuerst eine Gemeinschaft zu.', 'warning')
            return redirect(url_for('admin_betriebe.betrieb_gemeinschaften', betrieb_id=betrieb_id))

        # Gemeinschaften laden
        sql = convert_sql("SELECT id, name FROM gemeinschaften WHERE aktiv = true OR aktiv IS NULL ORDER BY name")
        cursor.execute(sql)
        gemeinschaften = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]

        # Benutzer des Betriebs laden (über benutzer_betriebe)
        sql = convert_sql("""
            SELECT u.id, u.vorname, u.name, u.email
            FROM benutzer u
            JOIN benutzer_betriebe bb ON u.id = bb.benutzer_id
            WHERE bb.betrieb_id = ?
            ORDER BY u.name, u.vorname
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
                # Benutzer über benutzer_betriebe zuordnen
                sql = convert_sql("""
                    INSERT INTO benutzer_betriebe (benutzer_id, betrieb_id)
                    VALUES (?, ?)
                    ON CONFLICT (benutzer_id, betrieb_id) DO NOTHING
                """)
                cursor.execute(sql, (benutzer_id, betrieb_id))
                db.connection.commit()
                flash('Benutzer wurde dem Betrieb zugeordnet.', 'success')

            elif action == 'remove' and benutzer_id:
                # Benutzer aus benutzer_betriebe entfernen
                sql = convert_sql("DELETE FROM benutzer_betriebe WHERE benutzer_id = ? AND betrieb_id = ?")
                cursor.execute(sql, (benutzer_id, betrieb_id))
                db.connection.commit()
                flash('Benutzer wurde vom Betrieb entfernt.', 'success')

        # Benutzer des Betriebs laden (über benutzer_betriebe)
        sql = convert_sql("""
            SELECT u.id, u.vorname, u.name, u.email
            FROM benutzer u
            JOIN benutzer_betriebe bb ON u.id = bb.benutzer_id
            WHERE bb.betrieb_id = ?
            ORDER BY u.name, u.vorname
        """)
        cursor.execute(sql, (betrieb_id,))
        benutzer_im_betrieb = [{'id': row[0], 'vorname': row[1], 'name': row[2], 'email': row[3]} for row in cursor.fetchall()]

        # Verfügbare Benutzer (alle aktiven Benutzer, KEINE Admins, nicht bereits im aktuellen Betrieb)
        sql = convert_sql("""
            SELECT DISTINCT u.id, u.vorname, u.name, u.email
            FROM benutzer u
            WHERE u.id NOT IN (SELECT benutzer_id FROM benutzer_betriebe WHERE betrieb_id = ?)
            AND COALESCE(u.aktiv, true) = true
            AND COALESCE(u.nur_training, false) = false
            AND COALESCE(u.is_admin, false) = false
            AND COALESCE(u.admin_level, 0) = 0
            AND u.username NOT LIKE 'S-%%'
            ORDER BY u.name, u.vorname
        """)
        cursor.execute(sql, (betrieb_id,))
        verfuegbare_benutzer = [{'id': row[0], 'vorname': row[1], 'name': row[2], 'email': row[3]} for row in cursor.fetchall()]

    return render_template('admin_betrieb_benutzer.html',
                         betrieb=betrieb,
                         benutzer_im_betrieb=benutzer_im_betrieb,
                         verfuegbare_benutzer=verfuegbare_benutzer)


@admin_betriebe_bp.route('/betriebe/<int:betrieb_id>/loeschen', methods=['POST'])
@admin_required
def betrieb_loeschen(betrieb_id):
    """Betrieb löschen (nur wenn keine Abhängigkeiten)"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        # Prüfen ob Benutzer zugeordnet sind (über benutzer_betriebe)
        sql = convert_sql("SELECT COUNT(*) FROM benutzer_betriebe WHERE betrieb_id = ?")
        cursor.execute(sql, (betrieb_id,))
        if cursor.fetchone()[0] > 0:
            flash('Betrieb kann nicht gelöscht werden - Benutzer zugeordnet.', 'danger')
            return redirect(url_for('admin_betriebe.betrieb_bearbeiten', betrieb_id=betrieb_id))

        # Prüfen ob Mitgliederkonten existieren
        sql = convert_sql("SELECT COUNT(*) FROM mitglieder_konten WHERE betrieb_id = ?")
        cursor.execute(sql, (betrieb_id,))
        if cursor.fetchone()[0] > 0:
            flash('Betrieb kann nicht gelöscht werden - Mitgliederkonto vorhanden.', 'danger')
            return redirect(url_for('admin_betriebe.betrieb_bearbeiten', betrieb_id=betrieb_id))

        # Prüfen ob Abrechnungen existieren
        sql = convert_sql("SELECT COUNT(*) FROM mitglieder_abrechnungen WHERE betrieb_id = ?")
        cursor.execute(sql, (betrieb_id,))
        if cursor.fetchone()[0] > 0:
            flash('Betrieb kann nicht gelöscht werden - Abrechnungen vorhanden.', 'danger')
            return redirect(url_for('admin_betriebe.betrieb_bearbeiten', betrieb_id=betrieb_id))

        # Prüfen ob Buchungen existieren
        sql = convert_sql("SELECT COUNT(*) FROM buchungen WHERE betrieb_id = ?")
        cursor.execute(sql, (betrieb_id,))
        if cursor.fetchone()[0] > 0:
            flash('Betrieb kann nicht gelöscht werden - Buchungen vorhanden.', 'danger')
            return redirect(url_for('admin_betriebe.betrieb_bearbeiten', betrieb_id=betrieb_id))

        # Betrieb löschen
        sql = convert_sql("DELETE FROM betriebe WHERE id = ?")
        cursor.execute(sql, (betrieb_id,))
        db.connection.commit()

        flash('Betrieb wurde gelöscht.', 'success')

    return redirect(url_for('admin_betriebe.betriebe_liste'))
