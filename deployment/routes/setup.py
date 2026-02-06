# -*- coding: utf-8 -*-
"""
Notfall-Setup-Route mit Token-Authentifizierung und Zwei-Personen-Regel

Ermöglicht:
- Erstinbetriebnahme ohne bestehende Datenbank
- Notfall-Wiederherstellung eines Backups (erfordert 2 Admins)
- Schema-Initialisierung

Zugriff nur mit SETUP_TOKEN aus Umgebungsvariablen.
Kritische Aktionen (Backup-Restore) erfordern Bestätigung durch zweiten Admin.
"""

import os
import tempfile
import subprocess
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response

setup_bp = Blueprint('setup', __name__, url_prefix='/setup')

# Token aus Umgebungsvariablen
SETUP_TOKEN = os.environ.get('SETUP_TOKEN', '')
SETUP_TOKEN_ADMIN1 = os.environ.get('SETUP_TOKEN_ADMIN1', '')
SETUP_TOKEN_ADMIN2 = os.environ.get('SETUP_TOKEN_ADMIN2', '')

# Speicher für ausstehende Bestätigungsanfragen
# Format: {code: {'file_path': ..., 'filename': ..., 'admin1': ..., 'created': ..., 'action': ...}}
pending_requests = {}

# Gültigkeitsdauer für Anfragen (30 Minuten)
REQUEST_TIMEOUT_MINUTES = 30


def cleanup_expired_requests():
    """Entfernt abgelaufene Anfragen"""
    now = datetime.now()
    expired = [code for code, req in pending_requests.items()
               if now - req['created'] > timedelta(minutes=REQUEST_TIMEOUT_MINUTES)]
    for code in expired:
        # Temporäre Datei löschen falls vorhanden
        if 'file_path' in pending_requests[code] and os.path.exists(pending_requests[code]['file_path']):
            try:
                os.remove(pending_requests[code]['file_path'])
            except:
                pass
        del pending_requests[code]


def get_admin_role(token):
    """Gibt die Admin-Rolle zurück (1, 2 oder None)"""
    if SETUP_TOKEN_ADMIN1 and token == SETUP_TOKEN_ADMIN1:
        return 1
    if SETUP_TOKEN_ADMIN2 and token == SETUP_TOKEN_ADMIN2:
        return 2
    return None


def is_two_person_mode():
    """Prüft ob Zwei-Personen-Modus aktiv ist (beide Admin-Tokens konfiguriert)"""
    return bool(SETUP_TOKEN_ADMIN1 and SETUP_TOKEN_ADMIN2)


def token_required(f):
    """Decorator: Prüft ob gültiger Setup-Token übergeben wurde"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.args.get('token') or request.form.get('token')

        # Zwei-Personen-Modus: Beide Admin-Tokens akzeptieren
        if is_two_person_mode():
            if token in [SETUP_TOKEN_ADMIN1, SETUP_TOKEN_ADMIN2]:
                return f(*args, **kwargs)
            return Response(
                "Ungültiger Token. Zugriff verweigert. (Zwei-Personen-Modus aktiv)",
                status=403,
                mimetype='text/plain'
            )

        # Einfacher Modus: Nur SETUP_TOKEN
        if not SETUP_TOKEN:
            return Response(
                "SETUP_TOKEN nicht konfiguriert. Bitte in .env setzen.",
                status=503,
                mimetype='text/plain'
            )

        if not token or token != SETUP_TOKEN:
            return Response(
                "Ungültiger oder fehlender Token. Zugriff verweigert.",
                status=403,
                mimetype='text/plain'
            )

        return f(*args, **kwargs)
    return decorated_function


@setup_bp.route('/')
@token_required
def setup_index():
    """Setup-Übersicht"""
    from database import USING_POSTGRESQL

    cleanup_expired_requests()

    token = request.args.get('token')
    admin_role = get_admin_role(token) if is_two_person_mode() else None

    # Datenbankstatus prüfen
    db_status = {
        'type': 'PostgreSQL' if USING_POSTGRESQL else 'SQLite',
        'connected': False,
        'tables': 0,
        'has_users': False
    }

    try:
        if USING_POSTGRESQL:
            from database import PG_HOST, PG_PORT, PG_DATABASE, PG_USER, PG_PASSWORD
            import psycopg2

            conn = psycopg2.connect(
                host=PG_HOST,
                port=PG_PORT,
                database=PG_DATABASE,
                user=PG_USER,
                password=PG_PASSWORD
            )
            cursor = conn.cursor()
            db_status['connected'] = True

            # Tabellen zählen
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
            db_status['tables'] = cursor.fetchone()[0]

            # Benutzer prüfen
            if db_status['tables'] > 0:
                try:
                    cursor.execute("SELECT COUNT(*) FROM benutzer")
                    db_status['has_users'] = cursor.fetchone()[0] > 0
                except:
                    pass

            conn.close()
    except Exception as e:
        db_status['error'] = str(e)

    # Ausstehende Anfragen für diesen Admin
    my_pending = []
    waiting_for_me = []

    if is_two_person_mode() and admin_role:
        for code, req in pending_requests.items():
            if req.get('admin1') == admin_role:
                my_pending.append({'code': code, **req})
            elif req.get('admin1') != admin_role:
                waiting_for_me.append({'code': code, **req})

    return render_template('setup_index.html',
                          db_status=db_status,
                          token=token,
                          two_person_mode=is_two_person_mode(),
                          admin_role=admin_role,
                          my_pending=my_pending,
                          waiting_for_me=waiting_for_me)


@setup_bp.route('/init-schema', methods=['POST'])
@token_required
def init_schema():
    """Datenbank-Schema initialisieren"""
    from database import USING_POSTGRESQL

    try:
        if USING_POSTGRESQL:
            from database import PG_HOST, PG_PORT, PG_DATABASE, PG_USER, PG_PASSWORD
            import psycopg2

            # Schema-Datei lesen
            schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schema_postgresql.sql')

            if not os.path.exists(schema_path):
                flash(f'Schema-Datei nicht gefunden: {schema_path}', 'danger')
                return redirect(url_for('setup.setup_index', token=request.form.get('token')))

            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()

            conn = psycopg2.connect(
                host=PG_HOST,
                port=PG_PORT,
                database=PG_DATABASE,
                user=PG_USER,
                password=PG_PASSWORD
            )
            cursor = conn.cursor()

            # Schema ausführen
            cursor.execute(schema_sql)
            conn.commit()
            conn.close()

            # Schema-Migration ausführen
            try:
                from utils.schema_migration import run_migrations_with_report
                migration_report = run_migrations_with_report()

                if migration_report.get('tables_added'):
                    flash(f"Zusätzliche Tabellen: {', '.join(migration_report['tables_added'])}", 'info')
            except Exception as e:
                flash(f'Migration-Hinweis: {str(e)}', 'warning')

            flash('Datenbank-Schema erfolgreich initialisiert!', 'success')
        else:
            flash('SQLite-Initialisierung nicht implementiert', 'warning')

    except Exception as e:
        flash(f'Fehler bei Schema-Initialisierung: {str(e)}', 'danger')

    return redirect(url_for('setup.setup_index', token=request.form.get('token')))


@setup_bp.route('/restore', methods=['GET', 'POST'])
@token_required
def restore_backup():
    """Backup wiederherstellen - Schritt 1: Anfrage erstellen (erfordert Bestätigung)"""
    from database import USING_POSTGRESQL

    cleanup_expired_requests()

    token = request.args.get('token') or request.form.get('token')
    admin_role = get_admin_role(token) if is_two_person_mode() else None

    if request.method == 'POST':
        if 'backup_file' not in request.files:
            flash('Keine Datei ausgewählt!', 'danger')
            return redirect(url_for('setup.restore_backup', token=token))

        backup_file = request.files['backup_file']

        if backup_file.filename == '':
            flash('Keine Datei ausgewählt!', 'danger')
            return redirect(url_for('setup.restore_backup', token=token))

        if not backup_file.filename.endswith('.sql'):
            flash('Ungültiges Dateiformat! Nur .sql Dateien erlaubt.', 'danger')
            return redirect(url_for('setup.restore_backup', token=token))

        # Zwei-Personen-Modus: Anfrage erstellen
        if is_two_person_mode():
            # Temporäre Datei speichern
            temp_dir = tempfile.gettempdir()
            confirmation_code = secrets.token_hex(8).upper()
            temp_path = os.path.join(temp_dir, f'restore_{confirmation_code}.sql')
            backup_file.save(temp_path)

            # Anfrage speichern
            pending_requests[confirmation_code] = {
                'file_path': temp_path,
                'filename': backup_file.filename,
                'admin1': admin_role,
                'created': datetime.now(),
                'action': 'restore'
            }

            flash(f'Restore-Anfrage erstellt! Bestätigungs-Code: {confirmation_code}', 'success')
            flash(f'Der zweite Administrator muss diesen Code bestätigen (gültig für {REQUEST_TIMEOUT_MINUTES} Minuten).', 'info')
            return redirect(url_for('setup.setup_index', token=token))

        # Einfacher Modus: Direkt ausführen
        try:
            if USING_POSTGRESQL:
                from database import PG_HOST, PG_PORT, PG_DATABASE, PG_USER, PG_PASSWORD

                # Temporäre Datei speichern
                temp_dir = tempfile.gettempdir()
                temp_path = os.path.join(temp_dir, 'restore_backup.sql')
                backup_file.save(temp_path)

                # Restore ausführen
                env = os.environ.copy()
                env['PGPASSWORD'] = PG_PASSWORD

                result = subprocess.run([
                    'psql', '-h', PG_HOST, '-p', str(PG_PORT),
                    '-U', PG_USER, '-d', PG_DATABASE, '-f', temp_path
                ], env=env, capture_output=True, text=True)

                os.remove(temp_path)

                if result.returncode != 0:
                    flash(f'Restore-Fehler: {result.stderr[:500]}', 'danger')
                else:
                    # Schema-Migration nach Restore
                    try:
                        from utils.schema_migration import run_migrations_with_report
                        migration_report = run_migrations_with_report()

                        if migration_report.get('tables_added'):
                            flash(f"Fehlende Tabellen hinzugefügt: {', '.join(migration_report['tables_added'])}", 'info')
                    except:
                        pass

                    flash('Backup erfolgreich wiederhergestellt!', 'success')
            else:
                flash('SQLite-Restore nicht implementiert', 'warning')

        except Exception as e:
            flash(f'Fehler bei Wiederherstellung: {str(e)}', 'danger')

        return redirect(url_for('setup.setup_index', token=token))

    # GET: Formular anzeigen
    file_extension = '.sql' if USING_POSTGRESQL else '.db'
    return render_template('setup_restore.html',
                          file_extension=file_extension,
                          token=token,
                          two_person_mode=is_two_person_mode(),
                          admin_role=admin_role)


@setup_bp.route('/confirm/<code>', methods=['GET', 'POST'])
@token_required
def confirm_restore(code):
    """Backup-Restore bestätigen (Admin 2)"""
    from database import USING_POSTGRESQL

    cleanup_expired_requests()

    token = request.args.get('token') or request.form.get('token')
    admin_role = get_admin_role(token)

    if not is_two_person_mode():
        flash('Zwei-Personen-Modus nicht aktiv.', 'warning')
        return redirect(url_for('setup.setup_index', token=token))

    if code not in pending_requests:
        flash('Ungültiger oder abgelaufener Bestätigungs-Code!', 'danger')
        return redirect(url_for('setup.setup_index', token=token))

    req = pending_requests[code]

    # Prüfen ob anderer Admin bestätigt
    if req['admin1'] == admin_role:
        flash('Sie können Ihre eigene Anfrage nicht bestätigen! Der andere Administrator muss bestätigen.', 'warning')
        return redirect(url_for('setup.setup_index', token=token))

    if request.method == 'POST':
        # Restore durchführen
        try:
            if USING_POSTGRESQL:
                from database import PG_HOST, PG_PORT, PG_DATABASE, PG_USER, PG_PASSWORD

                env = os.environ.copy()
                env['PGPASSWORD'] = PG_PASSWORD

                result = subprocess.run([
                    'psql', '-h', PG_HOST, '-p', str(PG_PORT),
                    '-U', PG_USER, '-d', PG_DATABASE, '-f', req['file_path']
                ], env=env, capture_output=True, text=True)

                # Temporäre Datei löschen
                if os.path.exists(req['file_path']):
                    os.remove(req['file_path'])

                # Anfrage entfernen
                del pending_requests[code]

                if result.returncode != 0:
                    flash(f'Restore-Fehler: {result.stderr[:500]}', 'danger')
                else:
                    # Schema-Migration nach Restore
                    try:
                        from utils.schema_migration import run_migrations_with_report
                        migration_report = run_migrations_with_report()

                        if migration_report.get('tables_added'):
                            flash(f"Fehlende Tabellen hinzugefügt: {', '.join(migration_report['tables_added'])}", 'info')
                    except:
                        pass

                    flash('Backup erfolgreich wiederhergestellt! (Bestätigt durch 2 Administratoren)', 'success')

        except Exception as e:
            flash(f'Fehler bei Wiederherstellung: {str(e)}', 'danger')

        return redirect(url_for('setup.setup_index', token=token))

    # GET: Bestätigungsformular anzeigen
    return render_template('setup_confirm.html',
                          code=code,
                          request_info=req,
                          token=token,
                          admin_role=admin_role)


@setup_bp.route('/cancel/<code>', methods=['POST'])
@token_required
def cancel_request(code):
    """Anfrage abbrechen"""
    cleanup_expired_requests()

    token = request.form.get('token')

    if code in pending_requests:
        req = pending_requests[code]
        # Temporäre Datei löschen
        if 'file_path' in req and os.path.exists(req['file_path']):
            try:
                os.remove(req['file_path'])
            except:
                pass
        del pending_requests[code]
        flash('Anfrage wurde abgebrochen.', 'info')
    else:
        flash('Anfrage nicht gefunden oder bereits abgelaufen.', 'warning')

    return redirect(url_for('setup.setup_index', token=token))


@setup_bp.route('/create-admin', methods=['GET', 'POST'])
@token_required
def create_admin():
    """Ersten Administrator erstellen"""
    from database import USING_POSTGRESQL

    token = request.args.get('token') or request.form.get('token')

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        name = request.form.get('name', '').strip()
        vorname = request.form.get('vorname', '').strip()

        if not all([username, password, name, vorname]):
            flash('Alle Felder sind erforderlich!', 'danger')
            return redirect(url_for('setup.create_admin', token=token))

        try:
            if USING_POSTGRESQL:
                from database import PG_HOST, PG_PORT, PG_DATABASE, PG_USER, PG_PASSWORD
                import psycopg2
                from werkzeug.security import generate_password_hash

                conn = psycopg2.connect(
                    host=PG_HOST,
                    port=PG_PORT,
                    database=PG_DATABASE,
                    user=PG_USER,
                    password=PG_PASSWORD
                )
                cursor = conn.cursor()

                # Prüfen ob schon Benutzer existieren
                cursor.execute("SELECT COUNT(*) FROM benutzer")
                if cursor.fetchone()[0] > 0:
                    flash('Es existieren bereits Benutzer. Admin-Erstellung über Setup nicht möglich.', 'warning')
                    conn.close()
                    return redirect(url_for('setup.setup_index', token=token))

                # Admin erstellen
                password_hash = generate_password_hash(password)
                cursor.execute("""
                    INSERT INTO benutzer (username, password_hash, name, vorname, is_admin, admin_level, aktiv)
                    VALUES (%s, %s, %s, %s, TRUE, 3, TRUE)
                """, (username, password_hash, name, vorname))

                conn.commit()
                conn.close()

                flash(f'Administrator "{username}" erfolgreich erstellt! Sie können sich jetzt anmelden.', 'success')
            else:
                flash('SQLite nicht implementiert', 'warning')

        except Exception as e:
            flash(f'Fehler beim Erstellen des Administrators: {str(e)}', 'danger')

        return redirect(url_for('setup.setup_index', token=token))

    return render_template('setup_create_admin.html', token=token)


@setup_bp.route('/backup')
@token_required
def create_backup():
    """Backup erstellen und herunterladen"""
    from database import USING_POSTGRESQL

    token = request.args.get('token')

    try:
        if USING_POSTGRESQL:
            from database import PG_HOST, PG_PORT, PG_DATABASE, PG_USER, PG_PASSWORD
            from flask import make_response

            env = os.environ.copy()
            env['PGPASSWORD'] = PG_PASSWORD

            result = subprocess.run([
                'pg_dump', '-h', PG_HOST, '-p', str(PG_PORT),
                '-U', PG_USER, PG_DATABASE
            ], env=env, capture_output=True, text=True)

            if result.returncode != 0:
                flash(f'Backup-Fehler: {result.stderr[:500]}', 'danger')
                return redirect(url_for('setup.setup_index', token=token))

            # Datei zum Download anbieten
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'backup_{PG_DATABASE}_{timestamp}.sql'

            response = make_response(result.stdout)
            response.headers['Content-Type'] = 'application/sql'
            response.headers['Content-Disposition'] = f'attachment; filename={filename}'
            return response
        else:
            flash('SQLite-Backup nicht implementiert', 'warning')

    except Exception as e:
        flash(f'Fehler beim Erstellen des Backups: {str(e)}', 'danger')

    return redirect(url_for('setup.setup_index', token=token))


@setup_bp.route('/status')
@token_required
def status():
    """Detaillierter Systemstatus als JSON"""
    from flask import jsonify
    from database import USING_POSTGRESQL

    status = {
        'timestamp': datetime.now().isoformat(),
        'two_person_mode': is_two_person_mode(),
        'pending_requests': len(pending_requests),
        'database': {
            'type': 'postgresql' if USING_POSTGRESQL else 'sqlite',
            'connected': False
        },
        'docker': {
            'in_container': os.path.exists('/.dockerenv')
        }
    }

    try:
        if USING_POSTGRESQL:
            from database import PG_HOST, PG_PORT, PG_DATABASE, PG_USER, PG_PASSWORD
            import psycopg2

            conn = psycopg2.connect(
                host=PG_HOST, port=PG_PORT, database=PG_DATABASE,
                user=PG_USER, password=PG_PASSWORD
            )
            cursor = conn.cursor()
            status['database']['connected'] = True

            # Tabellen
            cursor.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public' ORDER BY table_name
            """)
            status['database']['tables'] = [r[0] for r in cursor.fetchall()]

            # Benutzer
            try:
                cursor.execute("SELECT COUNT(*) FROM benutzer")
                status['database']['user_count'] = cursor.fetchone()[0]
            except:
                status['database']['user_count'] = 0

            conn.close()
    except Exception as e:
        status['database']['error'] = str(e)

    return jsonify(status)
