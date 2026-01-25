# -*- coding: utf-8 -*-
"""
Admin - System, Dashboard, Backup, Export, Rollen
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import MaschinenDBContext
from utils.decorators import admin_required, hauptadmin_required
from utils.training import get_current_db_path
from utils.sql_helpers import convert_sql, db_execute

admin_system_bp = Blueprint('admin_system', __name__, url_prefix='/admin')


@admin_system_bp.route('')
@admin_required
def admin_dashboard():
    """Admin-Dashboard"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        alle_einsaetze = db.get_all_einsaetze(limit=50)
        benutzer = db.get_all_benutzer()
        maschinen = db.get_all_maschinen()

        cursor = db.cursor
        sql = convert_sql("""
            SELECT
                COUNT(*) as gesamt_einsaetze,
                SUM(betriebsstunden) as gesamt_stunden,
                SUM(treibstoffverbrauch) as gesamt_treibstoff
            FROM maschineneinsaetze
        """)
        cursor.execute(sql)
        gesamt_stats = dict(cursor.fetchone())

        backup_warnung = False
        einsaetze_seit_backup = 0
        letztes_backup = None
        offene_bestaetigung = None

        sql = convert_sql("SELECT backup_schwellwert FROM benutzer WHERE id = ?")
        cursor.execute(sql, (session['benutzer_id'],))
        schwellwert_row = cursor.fetchone()
        BACKUP_SCHWELLWERT = schwellwert_row[0] if schwellwert_row and schwellwert_row[0] else 50

        db_execute(cursor, """
            SELECT b.id, b.admin_id, b.zeitpunkt, b.bemerkung,
                   u.name, u.vorname
            FROM backup_bestaetigung b
            JOIN benutzer u ON b.admin_id = u.id
            WHERE b.status = 'wartend'
            AND datetime(b.zeitpunkt, '+24 hours') > datetime('now')
            ORDER BY b.zeitpunkt DESC
            LIMIT 1
        """)
        offene_row = cursor.fetchone()
        if offene_row:
            offene_bestaetigung = {
                'id': offene_row[0],
                'admin_id': offene_row[1],
                'zeitpunkt': offene_row[2],
                'bemerkung': offene_row[3],
                'admin_name': f"{offene_row[5]} {offene_row[4]}",
                'ist_eigene': offene_row[1] == session['benutzer_id']
            }

        sql = convert_sql("""
            SELECT letztes_backup, einsaetze_bei_backup
            FROM backup_tracking
            ORDER BY letztes_backup DESC
            LIMIT 1
        """)
        cursor.execute(sql)
        backup_row = cursor.fetchone()

        if backup_row:
            letztes_backup = backup_row[0]
            einsaetze_bei_letztem_backup = backup_row[1]
            aktuelle_einsaetze = gesamt_stats.get('gesamt_einsaetze', 0) or 0
            einsaetze_seit_backup = aktuelle_einsaetze - einsaetze_bei_letztem_backup

            if einsaetze_seit_backup >= BACKUP_SCHWELLWERT:
                backup_warnung = True

    return render_template('admin_dashboard.html',
                         einsaetze=alle_einsaetze,
                         benutzer=benutzer,
                         maschinen=maschinen,
                         stats=gesamt_stats,
                         backup_warnung=backup_warnung,
                         einsaetze_seit_backup=einsaetze_seit_backup,
                         letztes_backup=letztes_backup,
                         backup_schwellwert=BACKUP_SCHWELLWERT,
                         offene_bestaetigung=offene_bestaetigung)


@admin_system_bp.route('/alle-einsaetze')
@admin_required
def admin_alle_einsaetze():
    """Alle Einsätze aller Benutzer"""
    db_path = get_current_db_path()
    with MaschinenDBContext(db_path) as db:
        einsaetze = db.get_all_einsaetze()
    return render_template('admin_alle_einsaetze.html', einsaetze=einsaetze)


@admin_system_bp.route('/stornierte-einsaetze')
@admin_required
def admin_stornierte_einsaetze():
    """Alle stornierten Einsätze"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("""
            SELECT s.*, m.bezeichnung as maschine_name,
                   b.name as benutzer_name, b.vorname as benutzer_vorname,
                   sv.name as storniert_von_name, sv.vorname as storniert_von_vorname,
                   ez.bezeichnung as einsatzzweck_name
            FROM maschineneinsaetze_storniert s
            JOIN maschinen m ON s.maschine_id = m.id
            JOIN benutzer b ON s.benutzer_id = b.id
            JOIN benutzer sv ON s.storniert_von = sv.id
            LEFT JOIN einsatzzwecke ez ON s.einsatzzweck_id = ez.id
            ORDER BY s.storniert_am DESC
        """)
        cursor.execute(sql)

        columns = [desc[0] for desc in cursor.description]
        stornierte_einsaetze = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render_template('admin_stornierte_einsaetze.html',
                         stornierte_einsaetze=stornierte_einsaetze)


@admin_system_bp.route('/backup-bestaetigen', methods=['POST'])
@admin_required
def admin_backup_bestaetigen():
    """Backup-Durchführung bestätigen"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        bemerkung = request.form.get('bemerkung', '')

        db_execute(cursor, """
            SELECT * FROM backup_bestaetigung
            WHERE status = 'wartend'
            AND datetime(zeitpunkt, '+24 hours') > datetime('now')
            ORDER BY zeitpunkt DESC
            LIMIT 1
        """)
        offene_bestaetigung = cursor.fetchone()

        if offene_bestaetigung:
            if offene_bestaetigung[1] == session['benutzer_id']:
                flash('Sie haben bereits eine Bestätigung abgegeben.', 'warning')
                return redirect(url_for('admin_system.admin_dashboard'))

            sql = convert_sql('SELECT COUNT(*) FROM maschineneinsaetze')
            cursor.execute(sql)
            anzahl_einsaetze = cursor.fetchone()[0]

            sql = convert_sql("""
                INSERT INTO backup_tracking
                (letztes_backup, einsaetze_bei_backup, durchgefuehrt_von, bemerkung)
                VALUES (?, ?, ?, ?)
            """)
            cursor.execute(sql, (
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                anzahl_einsaetze,
                f"{offene_bestaetigung[1]}, {session['benutzer_id']}",
                f"Admin 1: {offene_bestaetigung[3] or 'keine'} | Admin 2: {bemerkung or 'keine'}"
            ))

            sql = convert_sql("""
                UPDATE backup_bestaetigung
                SET status = 'abgeschlossen'
                WHERE id = ?
            """)
            cursor.execute(sql, (offene_bestaetigung[0],))

            db.connection.commit()
            flash('Backup-Durchführung wurde von zwei Administratoren bestätigt.', 'success')
        else:
            sql = convert_sql("""
                INSERT INTO backup_bestaetigung
                (admin_id, zeitpunkt, bemerkung, status)
                VALUES (?, ?, ?, 'wartend')
            """)
            cursor.execute(sql, (
                session['benutzer_id'],
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                bemerkung
            ))

            db.connection.commit()
            flash('Ihre Bestätigung wurde gespeichert. Ein zweiter Administrator muss bestätigen.', 'info')

    return redirect(url_for('admin_system.admin_dashboard'))


@admin_system_bp.route('/rollen')
@hauptadmin_required
def admin_rollen():
    """Rollenverwaltung"""
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("""
            SELECT b.*, GROUP_CONCAT(g.name) as gemeinschaften_admin
            FROM benutzer b
            LEFT JOIN gemeinschafts_admin ga ON b.id = ga.benutzer_id
            LEFT JOIN gemeinschaften g ON ga.gemeinschaft_id = g.id
            WHERE b.aktiv = true
            GROUP BY b.id
            ORDER BY b.admin_level DESC, b.name
        """)
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        benutzer = [dict(zip(columns, row)) for row in cursor.fetchall()]

        sql = convert_sql("SELECT * FROM gemeinschaften WHERE aktiv = true ORDER BY name")
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        gemeinschaften = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render_template('admin_rollen.html',
                         benutzer=benutzer,
                         gemeinschaften=gemeinschaften)


@admin_system_bp.route('/rollen/set-level', methods=['POST'])
@hauptadmin_required
def admin_rollen_set_level():
    """Admin-Level setzen"""
    db_path = get_current_db_path()
    benutzer_id = int(request.form['benutzer_id'])
    admin_level = int(request.form['admin_level'])

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        is_admin = admin_level > 0
        sql = convert_sql("""
            UPDATE benutzer
            SET admin_level = ?, is_admin = ?
            WHERE id = ?
        """)
        cursor.execute(sql, (admin_level, is_admin, benutzer_id))
        db.connection.commit()

    flash('Admin-Level wurde aktualisiert.', 'success')
    return redirect(url_for('admin_system.admin_rollen'))


@admin_system_bp.route('/rollen/add-gemeinschaft', methods=['POST'])
@hauptadmin_required
def admin_rollen_add_gemeinschaft():
    """Gemeinschafts-Admin-Rechte hinzufügen"""
    db_path = get_current_db_path()
    benutzer_id = int(request.form.get('benutzer_id'))
    gemeinschaft_id = int(request.form.get('gemeinschaft_id'))

    with MaschinenDBContext(db_path) as db:
        db.add_gemeinschafts_admin(benutzer_id, gemeinschaft_id)
        flash('Gemeinschafts-Admin-Rechte hinzugefügt!', 'success')

    return redirect(url_for('admin_system.admin_rollen'))


@admin_system_bp.route('/rollen/remove-gemeinschaft', methods=['POST'])
@hauptadmin_required
def admin_rollen_remove_gemeinschaft():
    """Gemeinschafts-Admin-Rechte entfernen"""
    db_path = get_current_db_path()
    benutzer_id = int(request.form.get('benutzer_id'))
    gemeinschaft_id = int(request.form.get('gemeinschaft_id'))

    with MaschinenDBContext(db_path) as db:
        db.remove_gemeinschafts_admin(benutzer_id, gemeinschaft_id)
        flash('Gemeinschafts-Admin-Rechte entfernt!', 'success')

    return redirect(url_for('admin_system.admin_rollen'))


@admin_system_bp.route('/export/json')
@admin_required
def admin_export_json():
    """Alle Daten als JSON exportieren"""
    import json
    from io import BytesIO
    from flask import send_file

    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        data = {
            'export_datum': datetime.now().isoformat(),
            'benutzer': db.get_all_benutzer(nur_aktive=False),
            'maschinen': db.get_all_maschinen(nur_aktive=False),
            'einsatzzwecke': db.get_all_einsatzzwecke(nur_aktive=False),
            'einsaetze': db.get_all_einsaetze()
        }

    json_str = json.dumps(data, indent=2, ensure_ascii=False, default=str)
    json_bytes = BytesIO(json_str.encode('utf-8'))
    json_bytes.seek(0)

    filename = f'maschinengemeinschaft_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    return send_file(
        json_bytes,
        mimetype='application/json',
        as_attachment=True,
        download_name=filename
    )


@admin_system_bp.route('/export/csv')
@admin_required
def admin_export_csv():
    """Alle Daten als CSV-ZIP exportieren"""
    import csv
    import zipfile
    from io import BytesIO, StringIO
    from flask import send_file

    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        benutzer = db.get_all_benutzer(nur_aktive=False)
        maschinen = db.get_all_maschinen(nur_aktive=False)
        einsatzzwecke = db.get_all_einsatzzwecke(nur_aktive=False)
        einsaetze = db.get_all_einsaetze()

    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        if benutzer:
            csv_buffer = StringIO()
            writer = csv.DictWriter(csv_buffer, fieldnames=benutzer[0].keys())
            writer.writeheader()
            writer.writerows(benutzer)
            zip_file.writestr('benutzer.csv', csv_buffer.getvalue())

        if maschinen:
            csv_buffer = StringIO()
            writer = csv.DictWriter(csv_buffer, fieldnames=maschinen[0].keys())
            writer.writeheader()
            writer.writerows(maschinen)
            zip_file.writestr('maschinen.csv', csv_buffer.getvalue())

        if einsatzzwecke:
            csv_buffer = StringIO()
            writer = csv.DictWriter(csv_buffer, fieldnames=einsatzzwecke[0].keys())
            writer.writeheader()
            writer.writerows(einsatzzwecke)
            zip_file.writestr('einsatzzwecke.csv', csv_buffer.getvalue())

        if einsaetze:
            csv_buffer = StringIO()
            writer = csv.DictWriter(csv_buffer, fieldnames=einsaetze[0].keys())
            writer.writeheader()
            writer.writerows(einsaetze)
            zip_file.writestr('einsaetze.csv', csv_buffer.getvalue())

    zip_buffer.seek(0)
    filename = f'maschinengemeinschaft_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'

    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=filename
    )


@admin_system_bp.route('/export/alle-einsaetze-csv')
@admin_required
def admin_export_alle_einsaetze_csv():
    """Exportiert alle Einsätze als CSV für Jahresabschluss"""
    import csv
    from io import StringIO
    from flask import make_response

    db_path = get_current_db_path()

    try:
        with MaschinenDBContext(db_path) as db:
            cursor = db.cursor
            sql = convert_sql("""
                SELECT
                    m.datum,
                    b.name as benutzer,
                    ma.bezeichnung as maschine,
                    ez.bezeichnung as einsatzzweck,
                    ma.abrechnungsart,
                    ma.preis_pro_einheit,
                    m.flaeche_menge,
                    m.treibstoff_liter,
                    m.treibstoff_preis,
                    m.treibstoffkosten,
                    m.kosten_berechnet as maschinenkosten,
                    (COALESCE(m.treibstoffkosten, 0) + COALESCE(m.kosten_berechnet, 0)) as gesamtkosten,
                    m.anfangstand,
                    m.endstand,
                    m.bemerkung
                FROM maschineneinsaetze m
                JOIN benutzer b ON m.benutzer_id = b.id
                JOIN maschinen ma ON m.maschine_id = ma.id
                LEFT JOIN einsatzzwecke ez ON m.einsatzzweck_id = ez.id
                ORDER BY m.datum DESC, m.id DESC
            """)
            cursor.execute(sql)

            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

        output = StringIO()
        writer = csv.writer(output, delimiter=';')

        writer.writerow(columns)

        for row in rows:
            writer.writerow(row)

        writer.writerow([])
        writer.writerow(['GESAMT', '', '', '', '', '', '', '', '',
                        sum(r[9] or 0 for r in rows),
                        sum(r[10] or 0 for r in rows),
                        sum(r[11] or 0 for r in rows),
                        '', '', ''])

        output.seek(0)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        response = make_response(output.getvalue().encode('utf-8-sig'))
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=alle_einsaetze_{timestamp}.csv'

        return response

    except Exception as e:
        flash(f'Fehler beim Exportieren: {str(e)}', 'danger')
        return redirect(url_for('admin_system.admin_dashboard'))


@admin_system_bp.route('/backup/database')
@admin_required
def admin_backup_database():
    """Komplette SQLite-Datenbank herunterladen"""
    import os
    from flask import send_file

    db_path = get_current_db_path()

    if not os.path.exists(db_path):
        flash('Datenbankdatei nicht gefunden!', 'danger')
        return redirect(url_for('admin_system.admin_dashboard'))

    filename = f'maschinengemeinschaft_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    return send_file(
        db_path,
        mimetype='application/x-sqlite3',
        as_attachment=True,
        download_name=filename
    )


@admin_system_bp.route('/backup')
@admin_required
def admin_database_backup():
    """Erstellt ein Backup der Datenbank als Download"""
    import os
    import shutil
    import tempfile
    import subprocess
    from flask import send_file
    from database import USING_POSTGRESQL

    db_path = get_current_db_path()

    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if USING_POSTGRESQL:
            from database import PG_HOST, PG_PORT, PG_DATABASE, PG_USER, PG_PASSWORD

            backup_filename = f"maschinengemeinschaft_backup_{timestamp}.sql"
            temp_dir = tempfile.gettempdir()
            temp_backup_path = os.path.join(temp_dir, backup_filename)

            env = os.environ.copy()
            env['PGPASSWORD'] = PG_PASSWORD

            result = subprocess.run([
                'pg_dump',
                '-h', PG_HOST,
                '-p', str(PG_PORT),
                '-U', PG_USER,
                '-d', PG_DATABASE,
                '-f', temp_backup_path
            ], env=env, capture_output=True, text=True)

            if result.returncode != 0:
                raise Exception(f"pg_dump Fehler: {result.stderr}")

            mimetype = 'application/sql'
        else:
            backup_filename = f"maschinengemeinschaft_backup_{timestamp}.db"
            temp_dir = tempfile.gettempdir()
            temp_backup_path = os.path.join(temp_dir, backup_filename)
            shutil.copy2(db_path, temp_backup_path)
            mimetype = 'application/x-sqlite3'

        return send_file(
            temp_backup_path,
            as_attachment=True,
            download_name=backup_filename,
            mimetype=mimetype
        )
    except Exception as e:
        flash(f'Fehler beim Erstellen des Backups: {str(e)}', 'danger')
        return redirect(url_for('admin_system.admin_dashboard'))


@admin_system_bp.route('/restore', methods=['GET', 'POST'])
@hauptadmin_required
def admin_database_restore():
    """Datenbank-Wiederherstellung (nur Haupt-Administratoren)"""
    import os
    import shutil
    import tempfile
    import subprocess
    from database import USING_POSTGRESQL

    db_path = get_current_db_path()

    if request.method == 'POST':
        if 'backup_file' not in request.files:
            flash('Keine Datei ausgewählt!', 'danger')
            return redirect(url_for('admin_system.admin_database_restore'))

        backup_file = request.files['backup_file']

        if backup_file.filename == '':
            flash('Keine Datei ausgewählt!', 'danger')
            return redirect(url_for('admin_system.admin_database_restore'))

        if USING_POSTGRESQL:
            if not backup_file.filename.endswith('.sql'):
                flash('Ungültiges Dateiformat! Nur .sql Dateien sind erlaubt.', 'danger')
                return redirect(url_for('admin_system.admin_database_restore'))

            try:
                from database import PG_HOST, PG_PORT, PG_DATABASE, PG_USER, PG_PASSWORD

                temp_dir = tempfile.gettempdir()
                temp_upload_path = os.path.join(temp_dir, 'temp_restore.sql')
                backup_file.save(temp_upload_path)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_current = os.path.join(temp_dir, f"backup_before_restore_{timestamp}.sql")

                env = os.environ.copy()
                env['PGPASSWORD'] = PG_PASSWORD

                subprocess.run([
                    'pg_dump', '-h', PG_HOST, '-p', str(PG_PORT),
                    '-U', PG_USER, '-d', PG_DATABASE, '-f', backup_current
                ], env=env, check=True)

                result = subprocess.run([
                    'psql', '-h', PG_HOST, '-p', str(PG_PORT),
                    '-U', PG_USER, '-d', PG_DATABASE, '-f', temp_upload_path
                ], env=env, capture_output=True, text=True)

                os.remove(temp_upload_path)

                if result.returncode != 0:
                    raise Exception(f"psql Fehler: {result.stderr}")

                flash(f'Datenbank erfolgreich wiederhergestellt! Backup erstellt: {os.path.basename(backup_current)}', 'success')
                flash('WICHTIG: Bitte starten Sie die Anwendung neu!', 'warning')

                return redirect(url_for('admin_system.admin_dashboard'))

            except Exception as e:
                flash(f'Fehler bei der Wiederherstellung: {str(e)}', 'danger')
                return redirect(url_for('admin_system.admin_database_restore'))
        else:
            if not backup_file.filename.endswith('.db'):
                flash('Ungültiges Dateiformat! Nur .db Dateien sind erlaubt.', 'danger')
                return redirect(url_for('admin_system.admin_database_restore'))

            try:
                temp_dir = tempfile.gettempdir()
                temp_upload_path = os.path.join(temp_dir, 'temp_restore.db')
                backup_file.save(temp_upload_path)

                try:
                    import sqlite3
                    test_conn = sqlite3.connect(temp_upload_path)
                    test_cursor = test_conn.cursor()
                    test_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = test_cursor.fetchall()
                    test_conn.close()

                    if not tables:
                        raise Exception("Keine Tabellen in der Datenbank gefunden")
                except Exception as e:
                    os.remove(temp_upload_path)
                    flash(f'Ungültige Datenbank-Datei: {str(e)}', 'danger')
                    return redirect(url_for('admin_system.admin_database_restore'))

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_current = f"{db_path}.backup_{timestamp}"
                shutil.copy2(db_path, backup_current)

                shutil.copy2(temp_upload_path, db_path)
                os.remove(temp_upload_path)

                flash(f'Datenbank erfolgreich wiederhergestellt! Alte Datenbank gesichert als: {os.path.basename(backup_current)}', 'success')
                flash('WICHTIG: Bitte starten Sie die Anwendung neu!', 'warning')

                return redirect(url_for('admin_system.admin_dashboard'))

            except Exception as e:
                flash(f'Fehler bei der Wiederherstellung: {str(e)}', 'danger')
                return redirect(url_for('admin_system.admin_database_restore'))

    file_extension = '.sql' if USING_POSTGRESQL else '.db'
    return render_template('admin_restore.html', file_extension=file_extension)


@admin_system_bp.route('/einsaetze/loeschen', methods=['GET', 'POST'])
@admin_required
def admin_einsaetze_loeschen():
    """Einsätze nach Zeitraum löschen"""
    db_path = get_current_db_path()

    if request.method == 'POST':
        von_datum = request.form.get('von_datum')
        bis_datum = request.form.get('bis_datum')
        bestaetigung = request.form.get('bestaetigung')

        if bestaetigung != 'LOESCHEN':
            flash('Bestätigung nicht korrekt. Bitte "LOESCHEN" eingeben.', 'danger')
            return redirect(url_for('admin_system.admin_einsaetze_loeschen'))

        try:
            with MaschinenDBContext(db_path) as db:
                cursor = db.cursor
                sql = convert_sql("""
                    SELECT COUNT(*) FROM maschineneinsaetze
                    WHERE datum BETWEEN ? AND ?
                """)
                cursor.execute(sql, (von_datum, bis_datum))
                anzahl = cursor.fetchone()[0]

                if anzahl == 0:
                    flash('Keine Einsätze im angegebenen Zeitraum gefunden.', 'warning')
                    return redirect(url_for('admin_system.admin_einsaetze_loeschen'))

                sql = convert_sql("""
                    DELETE FROM maschineneinsaetze
                    WHERE datum BETWEEN ? AND ?
                """)
                cursor.execute(sql, (von_datum, bis_datum))
                db.connection.commit()

                flash(f'{anzahl} Einsätze erfolgreich gelöscht!', 'success')
                return redirect(url_for('admin_system.admin_dashboard'))

        except Exception as e:
            flash(f'Fehler beim Löschen: {str(e)}', 'danger')
            return redirect(url_for('admin_system.admin_einsaetze_loeschen'))

    with MaschinenDBContext(db_path) as db:
        cursor = db.cursor
        sql = convert_sql("""
            SELECT MIN(datum) as min_datum, MAX(datum) as max_datum, COUNT(*) as anzahl
            FROM maschineneinsaetze
        """)
        cursor.execute(sql)
        zeitraum = cursor.fetchone()

    return render_template('admin_einsaetze_loeschen.html', zeitraum=zeitraum)


@admin_system_bp.route('/training-rechte')
@admin_required
def admin_training_rechte():
    """Verwaltet Trainings-Zugriffsrechte für Benutzer"""
    from utils.training import get_available_training_dbs, DB_PATH_PRODUCTION

    with MaschinenDBContext(DB_PATH_PRODUCTION) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("""
            SELECT id, name, vorname, username, is_admin, admin_level,
                   COALESCE(nur_training, FALSE) as nur_training, aktiv
            FROM benutzer
            WHERE id != 1
            ORDER BY name, vorname
        """)
        cursor.execute(sql)

        columns = [desc[0] for desc in cursor.description]
        benutzer = [dict(zip(columns, row)) for row in cursor.fetchall()]

    training_dbs = get_available_training_dbs()

    return render_template('admin_training_rechte.html',
                         benutzer=benutzer,
                         training_dbs=training_dbs)


@admin_system_bp.route('/training-rechte/update', methods=['POST'])
@admin_required
def admin_training_rechte_update():
    """Aktualisiert Trainings-Zugriffsrechte eines Benutzers"""
    from utils.training import DB_PATH_PRODUCTION

    benutzer_id = request.form.get('benutzer_id', type=int)
    nur_training = request.form.get('nur_training', '0') == '1'

    if not benutzer_id:
        flash('Ungültiger Benutzer!', 'danger')
        return redirect(url_for('admin_system.admin_training_rechte'))

    with MaschinenDBContext(DB_PATH_PRODUCTION) as db:
        cursor = db.connection.cursor()

        cursor.execute("PRAGMA table_info(benutzer)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'nur_training' not in columns:
            cursor.execute("ALTER TABLE benutzer ADD COLUMN nur_training BOOLEAN DEFAULT 0")

        sql = convert_sql("UPDATE benutzer SET nur_training = ? WHERE id = ?")
        cursor.execute(sql, (True if nur_training else False, benutzer_id))

        db.connection.commit()

        sql = convert_sql("SELECT name, vorname FROM benutzer WHERE id = ?")
        cursor.execute(sql, (benutzer_id,))
        row = cursor.fetchone()
        name = f"{row[1]} {row[0]}" if row else "Benutzer"

    if nur_training:
        flash(f'{name}: Nur Übungsmodus erlaubt', 'info')
    else:
        flash(f'{name}: Vollzugriff (Produktion + Übung) erlaubt', 'success')

    return redirect(url_for('admin_system.admin_training_rechte'))


@admin_system_bp.route('/training-datenbanken')
@hauptadmin_required
def admin_training_datenbanken():
    """Übersicht und Verwaltung der Trainingsdatenbanken"""
    import os
    from utils.training import TRAINING_DATABASES, TRAINING_DB_DIR

    training_dbs = []

    for key, config in TRAINING_DATABASES.items():
        path = os.path.join(TRAINING_DB_DIR, config['file'])
        db_info = {
            'key': key,
            'name': config['name'],
            'description': config['description'],
            'level': config['level'],
            'file': config['file'],
            'exists': os.path.exists(path),
            'size_kb': 0,
            'users': 0,
            'einsaetze': 0
        }

        if db_info['exists']:
            db_info['size_kb'] = round(os.path.getsize(path) / 1024, 1)
            try:
                with MaschinenDBContext(path) as db:
                    cursor = db.connection.cursor()
                    cursor.execute("SELECT COUNT(*) FROM benutzer WHERE aktiv = true")
                    db_info['users'] = cursor.fetchone()[0]
                    cursor.execute("SELECT COUNT(*) FROM maschineneinsaetze")
                    db_info['einsaetze'] = cursor.fetchone()[0]
            except:
                pass

        training_dbs.append(db_info)

    return render_template('admin_training_datenbanken.html', training_dbs=training_dbs)


@admin_system_bp.route('/training-datenbanken/neu-erstellen', methods=['POST'])
@hauptadmin_required
def admin_training_db_erstellen():
    """Erstellt Trainingsdatenbanken neu"""
    import os
    import subprocess

    script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'create_training_databases.py')

    if os.path.exists(script_path):
        try:
            result = subprocess.run(
                ['python', script_path],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                flash('Trainingsdatenbanken wurden neu erstellt!', 'success')
            else:
                flash(f'Fehler: {result.stderr}', 'danger')
        except Exception as e:
            flash(f'Fehler beim Erstellen: {str(e)}', 'danger')
    else:
        flash('Script nicht gefunden!', 'danger')

    return redirect(url_for('admin_system.admin_training_datenbanken'))
