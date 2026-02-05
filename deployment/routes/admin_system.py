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
    """Alle Einsätze aller Betriebe"""
    db_path = get_current_db_path()
    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()
        sql = convert_sql("""
            SELECT e.id, e.datum,
                   bt.name as betrieb,
                   b.name || ', ' || COALESCE(b.vorname, '') AS benutzer,
                   m.bezeichnung AS maschine,
                   m.abrechnungsart,
                   m.preis_pro_einheit,
                   ez.bezeichnung AS einsatzzweck,
                   e.anfangstand, e.endstand, e.betriebsstunden,
                   e.treibstoffverbrauch, e.treibstoffkosten,
                   e.flaeche_menge, e.kosten_berechnet, e.anmerkungen
            FROM maschineneinsaetze e
            JOIN benutzer b ON e.benutzer_id = b.id
            LEFT JOIN betriebe bt ON b.betrieb_id = bt.id
            JOIN maschinen m ON e.maschine_id = m.id
            JOIN einsatzzwecke ez ON e.einsatzzweck_id = ez.id
            ORDER BY e.datum DESC, e.id DESC
        """)
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        einsaetze = [dict(zip(columns, row)) for row in cursor.fetchall()]
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

        # PostgreSQL verwendet STRING_AGG statt GROUP_CONCAT
        from utils.sql_helpers import USING_POSTGRESQL
        if USING_POSTGRESQL:
            sql = """
                SELECT b.*, STRING_AGG(g.name, ', ') as gemeinschaften
                FROM benutzer b
                LEFT JOIN gemeinschafts_admin ga ON b.id = ga.benutzer_id
                LEFT JOIN gemeinschaften g ON ga.gemeinschaft_id = g.id
                WHERE b.aktiv = true OR b.aktiv IS NULL
                GROUP BY b.id
                ORDER BY b.admin_level DESC, b.name
            """
        else:
            sql = """
                SELECT b.*, GROUP_CONCAT(g.name) as gemeinschaften
                FROM benutzer b
                LEFT JOIN gemeinschafts_admin ga ON b.id = ga.benutzer_id
                LEFT JOIN gemeinschaften g ON ga.gemeinschaft_id = g.id
                WHERE b.aktiv = true OR b.aktiv IS NULL
                GROUP BY b.id
                ORDER BY b.admin_level DESC, b.name
            """
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        benutzer = [dict(zip(columns, row)) for row in cursor.fetchall()]

        sql = convert_sql("SELECT * FROM gemeinschaften WHERE aktiv = true OR aktiv IS NULL ORDER BY name")
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

    benutzer_id = request.form.get('benutzer_id')
    admin_level = request.form.get('admin_level') or request.form.get('level')

    if not benutzer_id or admin_level is None:
        flash('Fehlende Formulardaten.', 'danger')
        return redirect(url_for('admin_system.admin_rollen'))

    benutzer_id = int(benutzer_id)
    admin_level = int(admin_level)

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

    benutzer_id_str = request.form.get('benutzer_id')
    gemeinschaft_id_str = request.form.get('gemeinschaft_id')

    print(f"[DEBUG] add-gemeinschaft: benutzer_id={benutzer_id_str}, gemeinschaft_id={gemeinschaft_id_str}")

    if not benutzer_id_str or not gemeinschaft_id_str:
        flash(f'Fehlende Daten: benutzer_id={benutzer_id_str}, gemeinschaft_id={gemeinschaft_id_str}', 'danger')
        return redirect(url_for('admin_system.admin_rollen'))

    try:
        benutzer_id = int(benutzer_id_str)
        gemeinschaft_id = int(gemeinschaft_id_str)
    except ValueError as e:
        flash(f'Ungültige Werte: {e}', 'danger')
        return redirect(url_for('admin_system.admin_rollen'))

    try:
        with MaschinenDBContext(db_path) as db:
            cursor = db.connection.cursor()

            # Direkt SQL ausführen
            from utils.sql_helpers import USING_POSTGRESQL
            from datetime import datetime

            if USING_POSTGRESQL:
                sql = """
                    INSERT INTO gemeinschafts_admin (benutzer_id, gemeinschaft_id, erstellt_am)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (benutzer_id, gemeinschaft_id) DO NOTHING
                """
                cursor.execute(sql, (benutzer_id, gemeinschaft_id, datetime.now()))
            else:
                sql = """
                    INSERT OR IGNORE INTO gemeinschafts_admin (benutzer_id, gemeinschaft_id, erstellt_am)
                    VALUES (?, ?, ?)
                """
                cursor.execute(sql, (benutzer_id, gemeinschaft_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

            db.connection.commit()

            # Prüfen ob eingefügt wurde
            if USING_POSTGRESQL:
                cursor.execute("SELECT COUNT(*) FROM gemeinschafts_admin WHERE benutzer_id = %s AND gemeinschaft_id = %s",
                              (benutzer_id, gemeinschaft_id))
            else:
                cursor.execute("SELECT COUNT(*) FROM gemeinschafts_admin WHERE benutzer_id = ? AND gemeinschaft_id = ?",
                              (benutzer_id, gemeinschaft_id))

            count = cursor.fetchone()[0]
            print(f"[DEBUG] Nach INSERT: {count} Einträge gefunden")

            if count > 0:
                flash(f'Gemeinschafts-Admin-Rechte hinzugefügt! (Benutzer {benutzer_id} -> Gemeinschaft {gemeinschaft_id})', 'success')
            else:
                flash(f'Eintrag existierte bereits oder konnte nicht erstellt werden.', 'warning')

    except Exception as e:
        import traceback
        print(f"[ERROR] add-gemeinschaft: {e}")
        print(traceback.format_exc())
        flash(f'Fehler beim Speichern: {e}', 'danger')

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


@admin_system_bp.route('/rollen/set-rolle', methods=['POST'])
@hauptadmin_required
def admin_rollen_set_rolle():
    """Vorstandsrolle setzen (Obmann, Kassier, Schriftführer, Kassaprüfer)"""
    db_path = get_current_db_path()

    benutzer_id = request.form.get('benutzer_id')
    rolle = request.form.get('rolle')

    if not benutzer_id:
        flash('Fehlende Formulardaten.', 'danger')
        return redirect(url_for('admin_system.admin_rollen'))

    benutzer_id = int(benutzer_id)

    # Leere Rolle als NULL speichern
    if rolle == '' or rolle == 'keine':
        rolle = None

    with MaschinenDBContext(db_path) as db:
        cursor = db.connection.cursor()

        sql = convert_sql("""
            UPDATE benutzer
            SET rolle = ?
            WHERE id = ?
        """)
        cursor.execute(sql, (rolle, benutzer_id))
        db.connection.commit()

    rollen_namen = {
        'obmann': 'Obmann',
        'kassier': 'Kassier',
        'schriftfuehrer': 'Schriftführer',
        'kassaprufer1': 'Kassaprüfer 1',
        'kassaprufer2': 'Kassaprüfer 2',
        None: 'Keine Rolle'
    }
    flash(f'Rolle wurde auf "{rollen_namen.get(rolle, rolle)}" gesetzt.', 'success')
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
                    m.treibstoffverbrauch as treibstoff_liter,
                    m.treibstoffkosten as treibstoff_preis,
                    m.treibstoffkosten,
                    m.kosten_berechnet as maschinenkosten,
                    (COALESCE(m.treibstoffkosten, 0) + COALESCE(m.kosten_berechnet, 0)) as gesamtkosten,
                    m.anfangstand,
                    m.endstand,
                    m.anmerkungen as bemerkung
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
                '/usr/bin/pg_dump',
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
                    '/usr/bin/pg_dump', '-h', PG_HOST, '-p', str(PG_PORT),
                    '-U', PG_USER, '-d', PG_DATABASE, '-f', backup_current
                ], env=env, check=True)

                result = subprocess.run([
                    '/usr/bin/psql', '-h', PG_HOST, '-p', str(PG_PORT),
                    '-U', PG_USER, '-d', PG_DATABASE, '-f', temp_upload_path
                ], env=env, capture_output=True, text=True)

                os.remove(temp_upload_path)

                if result.returncode != 0:
                    raise Exception(f"psql Fehler: {result.stderr}")

                # Schema-Migration nach Restore durchführen
                from utils.schema_migration import run_migrations_with_report
                migration_report = run_migrations_with_report()

                flash(f'Datenbank erfolgreich wiederhergestellt! Backup erstellt: {os.path.basename(backup_current)}', 'success')

                if migration_report['tables_added']:
                    flash(f"Fehlende Tabellen hinzugefügt: {', '.join(migration_report['tables_added'])}", 'info')
                if migration_report['columns_added']:
                    flash(f"Fehlende Spalten hinzugefügt: {', '.join(migration_report['columns_added'])}", 'info')
                if migration_report['errors']:
                    flash(f"Migration-Fehler: {', '.join(migration_report['errors'])}", 'warning')

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

                # Schema-Migration nach Restore durchführen
                from utils.schema_migration import run_migrations_with_report
                migration_report = run_migrations_with_report()

                flash(f'Datenbank erfolgreich wiederhergestellt! Alte Datenbank gesichert als: {os.path.basename(backup_current)}', 'success')

                if migration_report['tables_added']:
                    flash(f"Fehlende Tabellen hinzugefügt: {', '.join(migration_report['tables_added'])}", 'info')
                if migration_report['columns_added']:
                    flash(f"Fehlende Spalten hinzugefügt: {', '.join(migration_report['columns_added'])}", 'info')
                if migration_report['errors']:
                    flash(f"Migration-Fehler: {', '.join(migration_report['errors'])}", 'warning')

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


# ============================================================================
# BENUTZER-IMPERSONATION (nur im Übungsmodus)
# ============================================================================

@admin_system_bp.route('/training/benutzer-wechseln')
@admin_required
def admin_training_benutzer_wechseln():
    """Liste der Benutzer zum Wechseln (Impersonation) im Übungsmodus"""
    from utils.training import is_training_mode

    if not is_training_mode():
        flash('Benutzer-Wechsel ist nur im Übungsmodus verfügbar!', 'warning')
        return redirect(url_for('admin_system.admin_dashboard'))

    db_path = get_current_db_path()
    with MaschinenDBContext(db_path) as db:
        benutzer = db.get_all_benutzer(nur_aktive=True)

    # Aktuellen Benutzer markieren
    current_id = session.get('benutzer_id')
    original_id = session.get('original_admin_id')

    return render_template('admin_training_benutzer_wechseln.html',
                         benutzer=benutzer,
                         current_id=current_id,
                         original_id=original_id,
                         is_impersonating=original_id is not None)


@admin_system_bp.route('/training/als-benutzer/<int:user_id>', methods=['POST'])
@admin_required
def admin_training_als_benutzer(user_id):
    """Wechselt zur Ansicht eines bestimmten Benutzers (Impersonation)"""
    from utils.training import is_training_mode

    if not is_training_mode():
        flash('Benutzer-Wechsel ist nur im Übungsmodus verfügbar!', 'warning')
        return redirect(url_for('admin_system.admin_dashboard'))

    db_path = get_current_db_path()
    with MaschinenDBContext(db_path) as db:
        benutzer = db.get_benutzer(user_id)
        if not benutzer:
            flash('Benutzer nicht gefunden!', 'danger')
            return redirect(url_for('admin_system.admin_training_benutzer_wechseln'))

        # Original-Admin-Daten speichern (nur beim ersten Wechsel)
        if 'original_admin_id' not in session:
            session['original_admin_id'] = session['benutzer_id']
            session['original_admin_name'] = session['benutzer_name']
            session['original_is_admin'] = session['is_admin']
            session['original_admin_level'] = session['admin_level']
            session['original_gemeinschafts_admin_ids'] = session.get('gemeinschafts_admin_ids', [])

        # Session mit neuen Benutzer-Daten aktualisieren
        session['benutzer_id'] = benutzer['id']
        session['benutzer_name'] = f"{benutzer['name']}, {benutzer['vorname']}"
        session['is_admin'] = bool(benutzer.get('is_admin', False))
        session['admin_level'] = benutzer.get('admin_level', 0)

        # Gemeinschaften des neuen Benutzers laden
        cursor = db.connection.cursor()
        sql = convert_sql("""
            SELECT g.id, g.name
            FROM gemeinschaften g
            JOIN mitglied_gemeinschaft mg ON g.id = mg.gemeinschaft_id
            WHERE mg.mitglied_id = ? AND g.aktiv = true
            ORDER BY g.name
        """)
        cursor.execute(sql, (user_id,))
        gemeinschaften = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
        session['gemeinschaften'] = gemeinschaften

        flash(f'Sie sehen jetzt die Ansicht von: {benutzer["vorname"]} {benutzer["name"]}', 'info')

    return redirect(url_for('dashboard.dashboard'))


@admin_system_bp.route('/training/zurueck-zum-admin', methods=['POST'])
def admin_training_zurueck():
    """Wechselt zurück zum Original-Admin"""
    from utils.training import is_training_mode

    if not is_training_mode():
        flash('Diese Funktion ist nur im Übungsmodus verfügbar!', 'warning')
        return redirect(url_for('dashboard.dashboard'))

    if 'original_admin_id' not in session:
        flash('Kein Original-Admin gespeichert!', 'warning')
        return redirect(url_for('dashboard.dashboard'))

    db_path = get_current_db_path()
    with MaschinenDBContext(db_path) as db:
        # Original-Admin-Daten wiederherstellen
        session['benutzer_id'] = session['original_admin_id']
        session['benutzer_name'] = session['original_admin_name']
        session['is_admin'] = session['original_is_admin']
        session['admin_level'] = session['original_admin_level']
        session['gemeinschafts_admin_ids'] = session.get('original_gemeinschafts_admin_ids', [])

        # Gemeinschaften des Admins laden
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
        session['gemeinschaften'] = gemeinschaften

        # Original-Daten aus Session entfernen
        del session['original_admin_id']
        del session['original_admin_name']
        del session['original_is_admin']
        del session['original_admin_level']
        if 'original_gemeinschafts_admin_ids' in session:
            del session['original_gemeinschafts_admin_ids']

        flash('Sie sind wieder als Administrator angemeldet.', 'success')

    return redirect(url_for('admin_system.admin_dashboard'))


# ============================================================================
# REPLICATION-VERWALTUNG
# ============================================================================

@admin_system_bp.route('/replication')
@hauptadmin_required
def admin_replication():
    """Replication-Konfiguration und Status"""
    from database import USING_POSTGRESQL, PG_HOST, PG_PORT, PG_DATABASE, PG_USER

    if not USING_POSTGRESQL:
        flash('Replication ist nur mit PostgreSQL verfügbar!', 'warning')
        return redirect(url_for('admin_system.admin_dashboard'))

    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.cursor

        # Replication-Konfiguration laden
        cursor.execute("SELECT * FROM replication_config WHERE id = 1")
        config_row = cursor.fetchone()

        config = None
        if config_row:
            config = {
                'standby_host': config_row[1],
                'standby_port': config_row[2] or 5432,
                'standby_user': config_row[3] or 'replicator',
                'replication_slot': config_row[4] or 'mgr_slot',
                'aktiv': config_row[5],
                'sync_modus': config_row[6] or 'async',
                'letzter_status': config_row[7],
                'letzter_check': config_row[8]
            }

        # Replication-Status von PostgreSQL abfragen
        replication_status = None
        try:
            cursor.execute("""
                SELECT client_addr, state, sent_lsn, write_lsn, flush_lsn, replay_lsn,
                       sync_state, reply_time
                FROM pg_stat_replication
            """)
            rows = cursor.fetchall()
            if rows:
                replication_status = []
                for row in rows:
                    replication_status.append({
                        'client_addr': row[0],
                        'state': row[1],
                        'sent_lsn': row[2],
                        'write_lsn': row[3],
                        'flush_lsn': row[4],
                        'replay_lsn': row[5],
                        'sync_state': row[6],
                        'reply_time': row[7]
                    })
        except Exception as e:
            flash(f'Fehler beim Abrufen des Replication-Status: {str(e)}', 'warning')

        # Replication-Slots abfragen
        replication_slots = []
        try:
            cursor.execute("""
                SELECT slot_name, slot_type, active, restart_lsn
                FROM pg_replication_slots
            """)
            for row in cursor.fetchall():
                replication_slots.append({
                    'slot_name': row[0],
                    'slot_type': row[1],
                    'active': row[2],
                    'restart_lsn': row[3]
                })
        except Exception as e:
            pass

        # Replication-Log laden
        cursor.execute("""
            SELECT l.zeitpunkt, l.aktion, l.status, l.details, b.name, b.vorname
            FROM replication_log l
            LEFT JOIN benutzer b ON l.ausgefuehrt_von = b.id
            ORDER BY l.zeitpunkt DESC
            LIMIT 50
        """)
        log_entries = []
        for row in cursor.fetchall():
            log_entries.append({
                'zeitpunkt': row[0],
                'aktion': row[1],
                'status': row[2],
                'details': row[3],
                'benutzer': f"{row[4]}, {row[5]}" if row[4] else 'System'
            })

        return render_template('admin_replication.html',
                               config=config,
                               replication_status=replication_status,
                               replication_slots=replication_slots,
                               log_entries=log_entries,
                               pg_host=PG_HOST,
                               pg_port=PG_PORT,
                               pg_database=PG_DATABASE)


@admin_system_bp.route('/replication/config', methods=['POST'])
@hauptadmin_required
def admin_replication_config():
    """Replication-Konfiguration speichern"""
    from database import USING_POSTGRESQL

    if not USING_POSTGRESQL:
        flash('Replication ist nur mit PostgreSQL verfügbar!', 'warning')
        return redirect(url_for('admin_system.admin_dashboard'))

    standby_host = request.form.get('standby_host', '').strip()
    standby_port = request.form.get('standby_port', '5432')
    standby_user = request.form.get('standby_user', 'replicator')
    replication_slot = request.form.get('replication_slot', 'mgr_slot')
    sync_modus = request.form.get('sync_modus', 'async')

    if not standby_host:
        flash('Standby-Host ist erforderlich!', 'danger')
        return redirect(url_for('admin_system.admin_replication'))

    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.cursor

        cursor.execute("""
            UPDATE replication_config
            SET standby_host = %s,
                standby_port = %s,
                standby_user = %s,
                replication_slot = %s,
                sync_modus = %s,
                geaendert_am = NOW()
            WHERE id = 1
        """, (standby_host, int(standby_port), standby_user, replication_slot, sync_modus))

        # Log-Eintrag
        cursor.execute("""
            INSERT INTO replication_log (aktion, status, details, ausgefuehrt_von)
            VALUES ('Konfiguration geändert', 'erfolg', %s, %s)
        """, (f"Host: {standby_host}:{standby_port}, Slot: {replication_slot}", session['benutzer_id']))

        db.connection.commit()
        flash('Replication-Konfiguration gespeichert!', 'success')

    return redirect(url_for('admin_system.admin_replication'))


@admin_system_bp.route('/replication/toggle', methods=['POST'])
@hauptadmin_required
def admin_replication_toggle():
    """Replication ein-/ausschalten"""
    from database import USING_POSTGRESQL
    import subprocess

    if not USING_POSTGRESQL:
        flash('Replication ist nur mit PostgreSQL verfügbar!', 'warning')
        return redirect(url_for('admin_system.admin_dashboard'))

    action = request.form.get('action')
    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.cursor

        # Aktuelle Konfiguration laden
        cursor.execute("SELECT standby_host, replication_slot, aktiv FROM replication_config WHERE id = 1")
        config = cursor.fetchone()

        if not config or not config[0]:
            flash('Bitte zuerst Standby-Host konfigurieren!', 'danger')
            return redirect(url_for('admin_system.admin_replication'))

        standby_host = config[0]
        replication_slot = config[1] or 'mgr_slot'
        ist_aktiv = config[2]

        try:
            if action == 'activate':
                if ist_aktiv:
                    flash('Replication ist bereits aktiv!', 'info')
                    return redirect(url_for('admin_system.admin_replication'))

                # Replication-Slot erstellen (falls nicht vorhanden)
                try:
                    cursor.execute(f"SELECT pg_create_physical_replication_slot('{replication_slot}')")
                except Exception:
                    pass  # Slot existiert bereits

                # Status aktualisieren
                cursor.execute("""
                    UPDATE replication_config
                    SET aktiv = TRUE, letzter_status = 'Aktiviert', letzter_check = NOW()
                    WHERE id = 1
                """)

                cursor.execute("""
                    INSERT INTO replication_log (aktion, status, details, ausgefuehrt_von)
                    VALUES ('Replication aktiviert', 'erfolg', %s, %s)
                """, (f"Slot: {replication_slot}", session['benutzer_id']))

                db.connection.commit()
                flash('Replication wurde aktiviert! Bitte Standby-Server konfigurieren.', 'success')

            elif action == 'deactivate':
                if not ist_aktiv:
                    flash('Replication ist bereits deaktiviert!', 'info')
                    return redirect(url_for('admin_system.admin_replication'))

                # Status aktualisieren
                cursor.execute("""
                    UPDATE replication_config
                    SET aktiv = FALSE, letzter_status = 'Deaktiviert', letzter_check = NOW()
                    WHERE id = 1
                """)

                cursor.execute("""
                    INSERT INTO replication_log (aktion, status, details, ausgefuehrt_von)
                    VALUES ('Replication deaktiviert', 'erfolg', NULL, %s)
                """, (session['benutzer_id'],))

                db.connection.commit()
                flash('Replication wurde deaktiviert!', 'success')

        except Exception as e:
            cursor.execute("""
                INSERT INTO replication_log (aktion, status, details, ausgefuehrt_von)
                VALUES (%s, 'fehler', %s, %s)
            """, (f"Replication {action}", str(e), session['benutzer_id']))
            db.connection.commit()
            flash(f'Fehler: {str(e)}', 'danger')

    return redirect(url_for('admin_system.admin_replication'))


@admin_system_bp.route('/replication/test', methods=['POST'])
@hauptadmin_required
def admin_replication_test():
    """Verbindung zum Standby-Server testen"""
    from database import USING_POSTGRESQL
    import subprocess

    if not USING_POSTGRESQL:
        flash('Replication ist nur mit PostgreSQL verfügbar!', 'warning')
        return redirect(url_for('admin_system.admin_dashboard'))

    db_path = get_current_db_path()

    with MaschinenDBContext(db_path) as db:
        cursor = db.cursor

        cursor.execute("SELECT standby_host, standby_port FROM replication_config WHERE id = 1")
        config = cursor.fetchone()

        if not config or not config[0]:
            flash('Bitte zuerst Standby-Host konfigurieren!', 'danger')
            return redirect(url_for('admin_system.admin_replication'))

        standby_host = config[0]
        standby_port = config[1] or 5432

        try:
            # Ping-Test
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '2', standby_host],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                cursor.execute("""
                    UPDATE replication_config
                    SET letzter_status = 'Erreichbar', letzter_check = NOW()
                    WHERE id = 1
                """)
                cursor.execute("""
                    INSERT INTO replication_log (aktion, status, details, ausgefuehrt_von)
                    VALUES ('Verbindungstest', 'erfolg', %s, %s)
                """, (f"Host {standby_host} erreichbar", session['benutzer_id']))
                db.connection.commit()
                flash(f'Standby-Server {standby_host} ist erreichbar!', 'success')
            else:
                cursor.execute("""
                    UPDATE replication_config
                    SET letzter_status = 'Nicht erreichbar', letzter_check = NOW()
                    WHERE id = 1
                """)
                cursor.execute("""
                    INSERT INTO replication_log (aktion, status, details, ausgefuehrt_von)
                    VALUES ('Verbindungstest', 'fehler', %s, %s)
                """, (f"Host {standby_host} nicht erreichbar", session['benutzer_id']))
                db.connection.commit()
                flash(f'Standby-Server {standby_host} ist NICHT erreichbar!', 'danger')

        except Exception as e:
            flash(f'Fehler beim Verbindungstest: {str(e)}', 'danger')

    return redirect(url_for('admin_system.admin_replication'))
