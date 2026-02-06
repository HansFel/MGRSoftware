# -*- coding: utf-8 -*-
"""
Notfall-Setup-Route mit Token-Authentifizierung

Ermöglicht:
- Erstinbetriebnahme ohne bestehende Datenbank
- Notfall-Wiederherstellung eines Backups
- Schema-Initialisierung

Zugriff nur mit SETUP_TOKEN aus Umgebungsvariablen.
"""

import os
import tempfile
import subprocess
from datetime import datetime
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response

setup_bp = Blueprint('setup', __name__, url_prefix='/setup')

# Token aus Umgebungsvariablen
SETUP_TOKEN = os.environ.get('SETUP_TOKEN', '')


def token_required(f):
    """Decorator: Prüft ob gültiger Setup-Token übergeben wurde"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.args.get('token') or request.form.get('token')

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

    return render_template('setup_index.html',
                          db_status=db_status,
                          token=request.args.get('token'))


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
    """Backup wiederherstellen"""
    from database import USING_POSTGRESQL

    if request.method == 'POST':
        if 'backup_file' not in request.files:
            flash('Keine Datei ausgewählt!', 'danger')
            return redirect(url_for('setup.restore_backup', token=request.form.get('token')))

        backup_file = request.files['backup_file']

        if backup_file.filename == '':
            flash('Keine Datei ausgewählt!', 'danger')
            return redirect(url_for('setup.restore_backup', token=request.form.get('token')))

        try:
            if USING_POSTGRESQL:
                from database import PG_HOST, PG_PORT, PG_DATABASE, PG_USER, PG_PASSWORD

                if not backup_file.filename.endswith('.sql'):
                    flash('Ungültiges Dateiformat! Nur .sql Dateien erlaubt.', 'danger')
                    return redirect(url_for('setup.restore_backup', token=request.form.get('token')))

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

        return redirect(url_for('setup.setup_index', token=request.form.get('token')))

    # GET: Formular anzeigen
    file_extension = '.sql' if USING_POSTGRESQL else '.db'
    return render_template('setup_restore.html',
                          file_extension=file_extension,
                          token=request.args.get('token'))


@setup_bp.route('/create-admin', methods=['GET', 'POST'])
@token_required
def create_admin():
    """Ersten Administrator erstellen"""
    from database import USING_POSTGRESQL

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        name = request.form.get('name', '').strip()
        vorname = request.form.get('vorname', '').strip()

        if not all([username, password, name, vorname]):
            flash('Alle Felder sind erforderlich!', 'danger')
            return redirect(url_for('setup.create_admin', token=request.form.get('token')))

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
                    return redirect(url_for('setup.setup_index', token=request.form.get('token')))

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

        return redirect(url_for('setup.setup_index', token=request.form.get('token')))

    return render_template('setup_create_admin.html', token=request.args.get('token'))


@setup_bp.route('/status')
@token_required
def status():
    """Detaillierter Systemstatus als JSON"""
    from flask import jsonify
    from database import USING_POSTGRESQL

    status = {
        'timestamp': datetime.now().isoformat(),
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
